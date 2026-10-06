# LoRA 训练服务：数据集文件系统真源 + 训练日志读取
#
# 数据集 = 目录：settings.DATA_DIR / "lora_datasets" / <name>/，目录里的图片文件即样本；
# 训练日志由宿主机训练脚本写入 data/lora_train/<dataset>.log（同一 docker 卷，
# 宿主机视角 = 仓库根 data/lora_train/），后端只读尾部展示。
import logging
import re
import time
from pathlib import Path

from app.config import settings

logger = logging.getLogger("studio.lora")

# 安全硬约束：数据集名/触发词白名单（防路径穿越，仅字母数字下划线连字符，1-64 位）
NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
# 图片文件名白名单：字母数字_-. 组成的主文件名 + 已知图片扩展名
FILENAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,128}\.(png|jpg|jpeg|webp)$", re.IGNORECASE)

# 数据集内统计/允许落盘的图片扩展
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

# 单张样本大小上限（与 API 层上传限制一致）
MAX_IMAGE_BYTES = 15 * 1024 * 1024


def datasets_root() -> Path:
    return settings.DATA_DIR / "lora_datasets"


def logs_root() -> Path:
    return settings.DATA_DIR / "lora_train"


def validate_name(name: str, label: str = "数据集名") -> str:
    """白名单校验数据集名/触发词，非法时抛 ValueError（中文 message 直接给前端）"""
    name = (name or "").strip()
    if not NAME_RE.match(name):
        raise ValueError(
            f"{label}只能包含字母、数字、下划线和连字符（1-64 位），不允许路径分隔符等特殊字符"
        )
    return name


def list_datasets() -> list[dict]:
    """扫描数据集根目录：目录即数据集，统计图片数与最近更新时间（按 mtime）"""
    root = datasets_root()
    result: list[dict] = []
    if not root.is_dir():
        return result
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        count = 0
        latest = entry.stat().st_mtime
        for f in entry.iterdir():
            try:
                if f.is_file() and f.suffix.lower() in IMAGE_EXTS:
                    count += 1
                    latest = max(latest, f.stat().st_mtime)
            except OSError:
                continue
        result.append(
            {
                "name": entry.name,
                "count": count,
                "updated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(latest)),
            }
        )
    result.sort(key=lambda d: d["updated_at"], reverse=True)
    return result


def dataset_dir(name: str, *, must_exist: bool = True) -> Path:
    """校验并解析数据集目录路径（拼接后仍强制位于根目录内，双保险防穿越）"""
    name = validate_name(name)
    path = datasets_root() / name
    if must_exist and not path.is_dir():
        raise FileNotFoundError(f"数据集不存在: {name}")
    return path


def create_dataset(name: str) -> dict:
    """创建数据集目录（已存在则幂等返回）"""
    path = dataset_dir(name, must_exist=False)
    existed = path.is_dir()
    path.mkdir(parents=True, exist_ok=True)
    logger.info("数据集%s: %s", "已存在" if existed else "已创建", path.name)
    return {"name": path.name, "created": not existed}


def delete_dataset(name: str) -> bool:
    """整目录删除数据集（含全部样本图片）；不存在返回 False"""
    path = dataset_dir(name)
    import shutil

    shutil.rmtree(path)
    logger.info("数据集已删除: %s", name)
    return True


def save_image(name: str, filename: str, data: bytes) -> str:
    """写原图入数据集目录；文件名冲突时加时间戳前缀，返回最终文件名"""
    path = dataset_dir(name)
    filename = (filename or "").strip()
    if not FILENAME_RE.match(filename):
        raise ValueError("图片文件名只能包含字母、数字、下划线、连字符，且扩展名为 png/jpg/jpeg/webp")
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("单张图片不能超过 15MB")
    target = path / filename
    if target.exists():
        stamp = time.strftime("%Y%m%d%H%M%S")
        target = path / f"{stamp}_{filename}"
    target.write_bytes(data)
    return target.name


def delete_image(name: str, filename: str) -> bool:
    """删除数据集内一张样本图；文件名同样走白名单校验"""
    path = dataset_dir(name)
    filename = (filename or "").strip()
    if not FILENAME_RE.match(filename):
        raise ValueError("图片文件名只能包含字母、数字、下划线、连字符，且扩展名为 png/jpg/jpeg/webp")
    target = path / filename
    if not target.is_file():
        return False
    target.unlink()
    return True


def list_images(name: str) -> list[str]:
    """列出数据集内全部图片文件名（按修改时间倒序，新的在前）"""
    path = dataset_dir(name)
    items = []
    for f in path.iterdir():
        try:
            if f.is_file() and f.suffix.lower() in IMAGE_EXTS:
                items.append((f.name, f.stat().st_mtime))
        except OSError:
            continue
    items.sort(key=lambda x: x[1], reverse=True)
    return [n for n, _ in items]


def read_log_tail(name: str, lines: int = 60) -> str:
    """读训练日志尾部 N 行（日志由宿主机写，仅只读；不存在返回空串）"""
    name = validate_name(name, label="数据集名")
    log_path = logs_root() / f"{name}.log"
    if not log_path.is_file():
        return ""
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        logger.warning("读取训练日志失败 %s: %s", log_path, exc)
        return ""
    return "\n".join(text.splitlines()[-lines:])
