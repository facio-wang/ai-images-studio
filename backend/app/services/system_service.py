# 系统状态服务（移植自 webUI-v1.0 services_admin）：
# 生图服务（ComfyUI）连通性检测 + GPU 显存/系统内存资源占用
# 架构差异：旧版跑在 Win11 本机用 nvidia-smi/netstat；现版 Studio 在 Docker（Orange Pi），
# ComfyUI 是远程引擎 —— 资源数据统一从 ComfyUI /system_stats 与 /queue 拉取，自身存活单独上报
import asyncio
import logging
import os
import time

import httpx

from app.config import settings

logger = logging.getLogger("studio.system")

_START_TS = time.time()

# 探测超时：状态面板是轻量高频轮询，超时要远小于生图超时
_PING_TIMEOUT = 3.0
_STATS_TIMEOUT = 5.0


def _to_mb(v) -> float | None:
    try:
        return round(float(v) / 1048576.0, 1)
    except (TypeError, ValueError):
        return None


async def comfy_ping() -> bool:
    """探测 ComfyUI 是否可达（对话生图前的预检也用它）"""
    try:
        async with httpx.AsyncClient(timeout=_PING_TIMEOUT, trust_env=False) as client:
            r = await client.get(f"{settings.COMFYUI_URL}/system_stats")
            return r.status_code == 200
    except Exception:
        return False


async def system_status() -> dict:
    """系统状态总览。ComfyUI 不可达时降级为 status=stopped，字段置空，永不抛 500"""
    result: dict = {
        "studio": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "uptime_seconds": int(time.time() - _START_TS),
        },
        "comfyui": {
            "url": settings.COMFYUI_URL,
            "status": "stopped",
            "version": None,
            "devices": [],
            "ram_total_mb": None,
            "ram_free_mb": None,
            "queue_running": 0,
            "queue_pending": 0,
        },
    }
    try:
        async with httpx.AsyncClient(timeout=_STATS_TIMEOUT, trust_env=False) as client:
            r = await client.get(f"{settings.COMFYUI_URL}/system_stats")
            r.raise_for_status()
            stats = r.json()
            try:
                q = (await client.get(f"{settings.COMFYUI_URL}/queue")).json()
            except Exception:
                q = {}
    except Exception as exc:
        logger.debug("ComfyUI 状态探测失败: %s", exc)
        return result

    comfy = result["comfyui"]
    comfy["status"] = "running"
    system = stats.get("system") or {}
    comfy["version"] = system.get("comfyui_version")
    comfy["ram_total_mb"] = _to_mb(system.get("ram_total"))
    comfy["ram_free_mb"] = _to_mb(system.get("ram_free"))
    devices = []
    for d in stats.get("devices") or []:
        devices.append(
            {
                "name": d.get("name"),
                "type": d.get("type"),
                "vram_total_mb": _to_mb(d.get("vram_total")),
                "vram_free_mb": _to_mb(d.get("vram_free")),
                "torch_version": d.get("torch_version"),
            }
        )
    comfy["devices"] = devices
    comfy["queue_running"] = len(q.get("queue_running") or [])
    comfy["queue_pending"] = len(q.get("queue_pending") or [])
    return result


async def start_comfyui() -> dict:
    """一键启动 ComfyUI：拉起启动脚本（直跑形态）或宿主机助手（Docker 形态），并轮询探活到上线。

    请求最长阻塞 COMFYUI_START_TIMEOUT 秒，前端按钮据此展示启动进度。
    返回 {status, message}，status ∈ already_running/started/timeout/no_script/unsupported/error，
    永不抛 500 —— 两种方式都没配置时返回手动指引而不是报错堆栈。
    """
    if await comfy_ping():
        return {"status": "already_running", "message": "生图服务（ComfyUI）已在运行中，无需启动"}

    agent = settings.COMFYUI_START_AGENT.strip()
    script = settings.COMFYUI_START_SCRIPT.strip()
    if not agent and not script:
        return {
            "status": "no_script",
            "message": (
                "尚未配置一键启动：请在 .env 配置 COMFYUI_START_AGENT"
                "（Docker 部署，配合仓库 scripts/host/ 下的宿主机启动助手），"
                "或 COMFYUI_START_SCRIPT（后端直跑 Windows 时，等价双击的启动脚本路径）"
            ),
        }

    if agent:
        error = await _start_via_agent(agent)
        if error:
            return error
    elif os.name == "nt":
        # os.startfile = ShellExecute open：只接受一个脚本路径、不经过命令行解释器，
        # 等价于资源管理器里双击该脚本，ComfyUI 控制台窗口可见
        try:
            os.startfile(script)  # type: ignore[attr-defined]
        except OSError as exc:
            logger.warning("ComfyUI 启动脚本执行失败: %s (%s)", script, exc)
            return {"status": "error", "message": f"启动脚本执行失败：{script}（{exc}）"}
    else:
        return {
            "status": "unsupported",
            "message": "已配置 COMFYUI_START_SCRIPT 但当前后端非 Windows（Docker/Linux 容器），"
            "请改配 COMFYUI_START_AGENT 走宿主机启动助手，或在宿主机手动启动 ComfyUI",
        }

    return await _wait_for_comfyui()


async def _start_via_agent(agent: str) -> dict | None:
    """让宿主机侧启动助手（scripts/host/comfyui_launcher.py）拉起 ComfyUI。

    成功返回 None（随后统一走探活），失败返回错误说明。
    """
    try:
        async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
            r = await client.post(
                f"{agent.rstrip('/')}/start", json={"token": settings.STUDIO_TOKEN}
            )
    except Exception as exc:
        logger.warning("宿主机启动助手不可达: %s", exc)
        return {
            "status": "error",
            "message": f"无法连接宿主机启动助手（{agent}）：请确认助手已常驻运行"
            "（仓库 scripts/host/install-autostart.bat 注册开机自启）",
        }
    if r.status_code != 200:
        try:
            msg = r.json().get("message", "")
        except Exception:
            msg = r.text[:200]
        return {"status": "error", "message": f"启动助手返回 {r.status_code}：{msg}"}
    return None


async def _wait_for_comfyui() -> dict:
    """启动指令已发出：轮询探活直到上线或超时（首次加载模型可能较慢）"""
    timeout = max(10, settings.COMFYUI_START_TIMEOUT)
    deadline = time.time() + timeout
    while time.time() < deadline:
        await asyncio.sleep(2)
        if await comfy_ping():
            logger.info("ComfyUI 已上线（耗时约 %ds）", int(timeout - (deadline - time.time())))
            return {"status": "started", "message": "生图服务（ComfyUI）已启动，可以开始生图了"}
    return {
        "status": "timeout",
        "message": (
            f"启动指令已执行，但 {timeout}s 内未探测到服务上线"
            "（首次加载模型可能更久，请稍后点击刷新状态确认；若 ComfyUI 窗口闪退请检查启动脚本）"
        ),
    }
