# 通用工具：资产文件保存 / 缩略图
import io
import time
import uuid
from pathlib import Path

from PIL import Image

from app.config import settings

THUMB_SIZE = (320, 320)


def save_upload(data: bytes, ext: str = "png") -> str:
    """保存上传/生成文件到 assets 目录，返回相对文件名"""
    settings.ensure_dirs()
    filename = f"{time.strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.{ext}"
    (settings.ASSETS_DIR / filename).write_bytes(data)
    return filename


def make_thumbnail(filename: str) -> str | None:
    """为资产生成缩略图，失败返回 None（不阻塞主流程）"""
    src = settings.ASSETS_DIR / filename
    thumb = f"thumb_{Path(filename).stem}.jpg"
    try:
        with Image.open(src) as im:
            im = im.convert("RGB")
            im.thumbnail(THUMB_SIZE)
            im.save(settings.ASSETS_DIR / thumb, "JPEG", quality=80)
        return thumb
    except Exception:
        return None


def new_name(prefix: str, ext: str) -> str:
    """生成资产文件名：前缀_时间_随机.ext"""
    return f"{prefix}_{time.strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.{ext}"
