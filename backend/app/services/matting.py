# 抠图服务：rembg 集成（bria-rmbg 默认 / birefnet 可选）
import io
import logging

from PIL import Image
from rembg import remove, new_session

from app.config import settings

logger = logging.getLogger("studio.matting")

# 模型会话缓存（避免每次请求重复加载 onnx）
_sessions: dict[str, object] = {}


def _get_session(model: str):
    """获取（并缓存）rembg 模型会话"""
    if model not in _sessions:
        logger.info("加载 rembg 模型: %s", model)
        _sessions[model] = new_session(model)
    return _sessions[model]


async def remove_background(image_bytes: bytes, model: str | None = None) -> bytes:
    """抠图：输入图片字节 → 输出透明 PNG 字节。CPU 密集，由任务 worker 在线程池执行"""
    model = model or settings.REMBG_MODEL
    import asyncio

    loop = asyncio.get_running_loop()
    result: bytes = await loop.run_in_executor(None, _run_rembg, image_bytes, model)
    logger.info("抠图完成: model=%s, in=%dB, out=%dB", model, len(image_bytes), len(result))
    return result


def _run_rembg(image_bytes: bytes, model: str) -> bytes:
    """同步 rembg 调用（在线程池中运行）"""
    session = _get_session(model)
    im = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    out = remove(im, session=session)
    buf = io.BytesIO()
    out.save(buf, "PNG")
    return buf.getvalue()
