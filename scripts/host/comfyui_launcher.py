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
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# 防抖窗口：探活期间重复点击 / 重试风暴只触发一次启动
_DEBOUNCE_SECONDS = 15


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


class LauncherHandler(BaseHTTPRequestHandler):
    token: str = ""
    script: str = ""
    pid_file: str = ""
    last_start: float = 0.0

    def _reply(self, code: int, message: str) -> None:
        body = json.dumps({"ok": code == 200, "message": message}, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802  # http.server 命名约定
        if self.path == "/ping":
            return self._reply(200, "pong")
        self._reply(404, "not found")

    def do_POST(self):  # noqa: N802
        if self.path == "/stop":
            return self._handle_stop()
        if self.path != "/start":
            return self._reply(404, "not found")

        length = int(self.headers.get("Content-Length") or 0)
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return self._reply(400, "请求体不是合法 JSON")
        if not self.token or payload.get("token") != self.token:
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
