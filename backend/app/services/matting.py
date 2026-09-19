# 抠图服务：rembg 集成（bria-rmbg 默认 / birefnet 可选）
#
# 资源约束（低配设备友好）：
# - ONNX 推理线程数可配（MATTING_THREADS，默认 3）——全核推理会把 Web 事件循环
#   饿死，其他请求（含前端任务轮询）集体超时报"服务器异常"
# - 推理前把输入图最大边降到 MATTING_MAX_SIDE（默认 2048），蒙版放大回原尺寸合成
#   —— 防 4K 大图内存爆与超长推理（历史任务 #15 教训）
import io
import logging

from PIL import Image
from rembg import remove, new_session

from app.config import settings

logger = logging.getLogger("studio.matting")

# 模型会话缓存（避免每次请求重复加载 onnx）
_sessions: dict[str, object] = {}


def _get_session(model: str):
    """获取（并缓存）rembg 模型会话；线程数受 MATTING_THREADS 约束"""
    if model not in _sessions:
        import onnxruntime as ort

        sess_opts = ort.SessionOptions()
        sess_opts.intra_op_num_threads = max(1, settings.MATTING_THREADS)
        sess_opts.inter_op_num_threads = 1
        logger.info("加载 rembg 模型: %s (threads=%s)", model, sess_opts.intra_op_num_threads)
        _sessions[model] = new_session(model, sess_opts=sess_opts)
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
    """同步 rembg 调用（在线程池中运行）。大图先降采样推理，蒙版放大回原尺寸合成"""
    session = _get_session(model)
    im = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

    max_side = max(1, settings.MATTING_MAX_SIDE)
    scale = min(1.0, max_side / max(im.size))
    if scale < 1.0:
        work_size = (max(1, round(im.width * scale)), max(1, round(im.height * scale)))
        work = im.resize(work_size, Image.BILINEAR)
        logger.info("抠图降采样: %sx%s -> %sx%s", im.width, im.height, *work_size)
    else:
        work = im

    # only_mask=True 只产出蒙版：降采样场景把蒙版放大后贴回原尺寸，画质不缩水
    mask = remove(work.convert("RGB"), session=session, only_mask=True)
    if scale < 1.0:
        mask = mask.resize(im.size, Image.LANCZOS)

    out = im.copy()
    out.putalpha(mask)
    buf = io.BytesIO()
    out.save(buf, "PNG")
    return buf.getvalue()
