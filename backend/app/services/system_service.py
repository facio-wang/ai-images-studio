# 系统状态服务（移植自 webUI-v1.0 services_admin）：
# 生图服务（ComfyUI）连通性检测 + GPU 显存/系统内存资源占用
# 架构差异：旧版跑在 Win11 本机用 nvidia-smi/netstat；现版 Studio 在 Docker（Orange Pi），
# ComfyUI 是远程引擎 —— 资源数据统一从 ComfyUI /system_stats 与 /queue 拉取，自身存活单独上报
import logging
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
