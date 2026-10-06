# ruff: noqa: E402
"""ComfyUI 启动助手（Win11 宿主机侧，AI Images Studio）。

AI Images Studio 后端跑在 Docker（Orange Pi / Docker Desktop）里，无法直接拉起
宿主机进程。本脚本在 Win11 宿主机上以极简 HTTP 服务（默认 0.0.0.0:8192）接收
后端 POST /start 指令，校验 token 后以「双击」方式（os.startfile）拉起
start_comfyui.bat，ComfyUI 控制台窗口可见。

仅用标准库。启动方式：
  前台调试   python comfyui_launcher.py
  开机自启   双击 install-autostart.bat（写入「启动」文件夹，pythonw 静默常驻）
"""

import argparse
import json
import os
import shutil
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Anti-abuse window: repeated clicks / retry storms during probing trigger only one start
_DEBOUNCE_SECONDS = 15

# Whitelist for dataset / trigger names (mirrors the backend rule, anti path traversal).
# ASCII only so it also fits the generated VBS payload.
import re

_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


def _load_repo_token() -> str:
    """默认鉴权 token：从仓库根目录 .env 读取 STUDIO_TOKEN（脚本位于 <repo>/scripts/host/）"""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("STUDIO_TOKEN="):
                return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return ""


def _load_train_config() -> dict:
    """Read scripts/host/train_config.json: {"command": "...", "argsTemplate": "..."}.

    Missing file or invalid JSON degrades to an empty config (env check reports it).
    """
    cfg_path = Path(__file__).with_name("train_config.json")
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


class LauncherHandler(BaseHTTPRequestHandler):
    token: str = ""
    script: str = ""
    pid_file: str = ""
    last_start: float = 0.0
    # LoRA training: hidden-launcher PS1 next to this script; per-dataset PID file prefix
    train_ps1: str = str(Path(__file__).with_name("train_lora.ps1"))
    train_dir: str = r"D:\AI\sd-train"

    def _reply_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _reply(self, code: int, message: str) -> None:
        self._reply_json(code, {"ok": code == 200, "message": message})

    def _read_json_body(self):
        """Read and parse the JSON request body; returns {} when missing/invalid"""
        length = int(self.headers.get("Content-Length") or 0)
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return None

    def _token_ok(self, payload: dict) -> bool:
        return bool(self.token) and payload.get("token") == self.token

    # ---- LoRA training helpers (host-side paths) ----

    def _train_pid_file(self, dataset: str) -> Path:
        return Path(__file__).with_name(f"lora_train_{dataset}.pid")

    def _train_log_file(self, dataset: str) -> Path:
        # Repo root = parents[2] of this script (<repo>/scripts/host/); the docker
        # volume maps <repo>/data <-> container /app/data, same physical folder.
        return Path(__file__).resolve().parents[2] / "data" / "lora_train" / f"{dataset}.log"

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        # NOTE: os.kill(pid, 0) is NOT a safe liveness probe on Windows — CPython maps
        # any sig other than CTRL_C_EVENT/CTRL_BREAK_EVENT to TerminateProcess, so it
        # would kill the training process on every poll. Use OpenProcess instead.
        if os.name == "nt":
            import ctypes

            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, pid)
            if not handle:
                return False
            kernel32.CloseHandle(handle)
            return True
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True

    @staticmethod
    def _read_tail(path: Path, lines: int = 60) -> str:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
        return "\n".join(text.splitlines()[-lines:])

    def do_GET(self):  # noqa: N802  # http.server naming convention
        parsed = urlparse(self.path)
        if parsed.path == "/ping":
            return self._reply(200, "pong")
        if parsed.path == "/train/env":
            return self._handle_train_env()
        if parsed.path == "/train/status":
            return self._handle_train_status(parse_qs(parsed.query))
        self._reply(404, "not found")

    def do_POST(self):  # noqa: N802
        if self.path == "/stop":
            return self._handle_stop()
        if self.path == "/train/start":
            return self._handle_train_start()
        if self.path == "/train/stop":
            return self._handle_train_stop()
        if self.path != "/start":
            return self._reply(404, "not found")

        payload = self._read_json_body()
        if payload is None:
            return self._reply(400, "请求体不是合法 JSON")
        if not self._token_ok(payload):
            return self._reply(403, "token 校验失败")

        if time.time() - LauncherHandler.last_start < _DEBOUNCE_SECONDS:
            return self._reply(200, "启动指令已在执行中，请等待后端探活结果")
        if not os.path.isfile(self.script):
            return self._reply(500, f"启动脚本不存在: {self.script}")

        try:
            os.startfile(self.script)
        except OSError as exc:
            return self._reply(500, f"启动脚本执行失败: {exc}")

        LauncherHandler.last_start = time.time()
        print(f"[comfyui-launcher] 已拉起启动脚本: {self.script}")
        return self._reply(200, "已后台拉起 ComfyUI（无窗口）")

    # ---- LoRA training endpoints ----

    def _handle_train_env(self):
        """Readiness check: train dir + PS1 launcher + python on PATH + command configured"""
        items = []
        train_dir = Path(self.train_dir)
        ok_dir = train_dir.is_dir()
        items.append(
            {"name": "train_dir", "ok": ok_dir, "detail": str(train_dir) + ("" if ok_dir else " (missing)")}
        )
        ps1 = Path(self.train_ps1)
        ok_ps1 = ps1.is_file()
        items.append(
            {"name": "train_script", "ok": ok_ps1, "detail": str(ps1) + ("" if ok_ps1 else " (missing)")}
        )
        python_path = shutil.which("python")
        items.append(
            {
                "name": "python",
                "ok": python_path is not None,
                "detail": python_path or "python not found on PATH",
            }
        )
        cfg = _load_train_config()
        ok_cfg = bool(cfg.get("command"))
        items.append(
            {
                "name": "train_config",
                "ok": ok_cfg,
                "detail": (
                    "command configured"
                    if ok_cfg
                    else "command empty: edit scripts/host/train_config.json"
                ),
            }
        )
        return self._reply_json(200, {"ready": all(item["ok"] for item in items), "items": items})

    def _handle_train_start(self):
        """Launch LoRA training: write a per-run hidden VBS (args embedded), then
        os.startfile it (same double-click style as ComfyUI start; no subprocess)."""
        payload = self._read_json_body()
        if payload is None:
            return self._reply(400, "请求体不是合法 JSON")
        if not self._token_ok(payload):
            return self._reply(403, "token 校验失败")

        dataset = str(payload.get("dataset") or "")
        trigger = str(payload.get("trigger") or "")
        if not _NAME_RE.match(dataset) or not _NAME_RE.match(trigger):
            return self._reply(400, "dataset/trigger 只能包含字母数字下划线连字符（1-64 位）")

        ps1 = Path(self.train_ps1)
        if not ps1.is_file():
            return self._reply(500, f"训练脚本不存在: {ps1}")

        # Generated per-run VBS must live next to train_lora.ps1 so its
        # GetParentFolderName resolves the script dir correctly.
        vbs_lines = [
            "' AI Images Studio - hidden LoRA train launcher (generated by comfyui_launcher.py)",
            "' ASCII + CRLF only. Runs train_lora.ps1 hidden with dataset/trigger args.",
            "Set fso = CreateObject(\"Scripting.FileSystemObject\")",
            "dir = fso.GetParentFolderName(WScript.ScriptFullName)",
            "Set sh = CreateObject(\"WScript.Shell\")",
            'sh.Run "powershell -NoProfile -ExecutionPolicy Bypass -File """ & dir & "\\train_lora.ps1"" '
            f"-Dataset {dataset} -Trigger {trigger}"
            '", 0, False',
        ]
        vbs_path = Path(__file__).with_name(f"lora_train_{dataset}.vbs")
        try:
            vbs_path.write_text("\r\n".join(vbs_lines) + "\r\n", encoding="ascii")
        except OSError as exc:
            return self._reply(500, f"写入训练启动器失败: {exc}")

        try:
            os.startfile(str(vbs_path))
        except OSError as exc:
            return self._reply(500, f"训练启动器执行失败: {exc}")

        print(f"[comfyui-launcher] 已拉起 LoRA 训练: dataset={dataset} trigger={trigger}")
        return self._reply(200, f"已在宿主机后台拉起训练（dataset={dataset}），日志见 data/lora_train/{dataset}.log")

    def _handle_train_stop(self):
        """Stop training: terminate the PID recorded by train_lora.ps1, then drop the file"""
        payload = self._read_json_body()
        if payload is None:
            return self._reply(400, "请求体不是合法 JSON")
        if not self._token_ok(payload):
            return self._reply(403, "token 校验失败")

        dataset = str(payload.get("dataset") or "")
        if not _NAME_RE.match(dataset):
            return self._reply(400, "dataset 只能包含字母数字下划线连字符（1-64 位）")

        pid_file = self._train_pid_file(dataset)
        if not pid_file.exists():
            return self._reply(404, f"没有运行中的训练记录（dataset={dataset}），进程可能已自行退出")
        try:
            pid = int(pid_file.read_text(encoding="ascii").strip())
        except (OSError, ValueError):
            pid_file.unlink(missing_ok=True)
            return self._reply(500, "PID 记录损坏，已清除")

        try:
            # Windows: os.kill(pid, 9) == TerminateProcess, no extra dependency
            os.kill(pid, 9)
        except OSError as exc:
            pid_file.unlink(missing_ok=True)
            return self._reply(500, f"停止失败（进程可能已自行退出）: {exc}")

        pid_file.unlink(missing_ok=True)
        print(f"[comfyui-launcher] 已停止 LoRA 训练 (dataset={dataset}, pid={pid})")
        return self._reply(200, f"已停止训练 (dataset={dataset}, pid={pid})")

    def _handle_train_status(self, query: dict):
        """Training status: PID liveness + last 60 log lines from data/lora_train/<dataset>.log"""
        token = (query.get("token") or [""])[0]
        if not self.token or token != self.token:
            return self._reply(403, "token 校验失败")
        dataset = (query.get("dataset") or [""])[0]
        if not _NAME_RE.match(dataset):
            return self._reply(400, "dataset 只能包含字母数字下划线连字符（1-64 位）")

        running = False
        pid = None
        pid_file = self._train_pid_file(dataset)
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text(encoding="ascii").strip())
                running = self._pid_alive(pid)
            except (OSError, ValueError):
                pid = None
        return self._reply_json(
            200,
            {
                "ok": True,
                "running": running,
                "pid": pid,
                "log_tail": self._read_tail(self._train_log_file(dataset), 60),
            },
        )

    def _handle_stop(self):
        """一键停止：终止本助手此前记录的 ComfyUI 进程（PID 记录在 comfyui.pid）"""
        length = int(self.headers.get("Content-Length") or 0)
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return self._reply(400, "请求体不是合法 JSON")
        if not self.token or payload.get("token") != self.token:
            return self._reply(403, "token 校验失败")

        pid_file = Path(self.pid_file)
        if not pid_file.exists():
            return self._reply(
                404,
                "没有可停止的记录：当前服务不是由一键启动拉起的（或 PID 记录已清除），请直接关闭其控制台窗口",
            )
        try:
            pid = int(pid_file.read_text(encoding="ascii").strip())
        except (OSError, ValueError):
            pid_file.unlink(missing_ok=True)
            return self._reply(500, "PID 记录损坏，已清除；请手动关闭 ComfyUI")

        try:
            # Windows 下 os.kill(pid, 9) 等价 TerminateProcess，无需额外依赖
            os.kill(pid, 9)
        except OSError as exc:
            pid_file.unlink(missing_ok=True)
            return self._reply(500, f"停止失败（进程可能已自行退出）: {exc}")

        pid_file.unlink(missing_ok=True)
        print(f"[comfyui-launcher] 已停止 ComfyUI (pid={pid})")
        return self._reply(200, f"已停止 ComfyUI (pid={pid})")

    def log_message(self, fmt, *args):  # 静默默认访问日志，只保留关键动作
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Images Studio ComfyUI 启动助手")
    parser.add_argument("--port", type=int, default=8192)
    # 默认拉起隐藏窗口版启动器：ComfyUI 在后台运行，避免误关控制台窗口导致服务退出
    parser.add_argument("--script", default=str(Path(__file__).with_name("start_comfyui_hidden.vbs")))
    parser.add_argument("--pidfile", default=str(Path(__file__).with_name("comfyui.pid")))
    parser.add_argument("--token", default=_load_repo_token(), help="鉴权 token，默认取仓库 .env 的 STUDIO_TOKEN")
    args = parser.parse_args()

    LauncherHandler.token = args.token
    LauncherHandler.script = args.script
    LauncherHandler.pid_file = args.pidfile
    if not args.token:
        print("[comfyui-launcher] 警告：未配置 token，任何来源都能触发启动（建议在仓库 .env 设置 STUDIO_TOKEN）")

    server = ThreadingHTTPServer(("0.0.0.0", args.port), LauncherHandler)
    print(f"[comfyui-launcher] 监听 0.0.0.0:{args.port}，启动脚本: {args.script}")
    server.serve_forever()


if __name__ == "__main__":
    main()
