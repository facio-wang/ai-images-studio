# 应用配置：从 .env / 环境变量读取，禁止硬编码密钥
import os
from pathlib import Path

from dotenv import load_dotenv

# 加载 backend/.env（存在才加载，docker 场景直接用环境变量）
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
# 兼容仓库根目录 .env（docker-compose 的 env_file 即它；本机裸跑 uvicorn 时也一并读取）
load_dotenv(BASE_DIR.parent / ".env")


def _get_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).strip().lower() in ("1", "true", "yes", "on")


class Settings:
    """全局配置（单例风格，import settings 即用）"""

    # 应用
    APP_NAME: str = os.getenv("STUDIO_APP_NAME", "AI Images Studio")
    APP_VERSION: str = os.getenv("STUDIO_APP_VERSION", "0.1.0")
    HOST: str = os.getenv("STUDIO_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("STUDIO_PORT", "8191"))
    DEBUG: bool = _get_bool("STUDIO_DEBUG", False)

    # 鉴权：单用户 Bearer Token（.env 配置 STUDIO_TOKEN）
    STUDIO_TOKEN: str = os.getenv("STUDIO_TOKEN", "studio-dev-token")

    # 数据目录：SQLite 与资产文件均在此
    DATA_DIR: Path = Path(os.getenv("STUDIO_DATA_DIR", str(BASE_DIR / "data")))
    ASSETS_DIR: Path = DATA_DIR / "assets"
    DB_PATH: Path = DATA_DIR / "studio.db"

    # ComfyUI 生图引擎
    COMFYUI_URL: str = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")
    COMFYUI_TIMEOUT: int = int(os.getenv("COMFYUI_TIMEOUT", "300"))

    # 一键启动 ComfyUI（两种方式二选一，都不配则一键启动按钮降级为手动指引提示）：
    # 1) 后端直跑 Windows 且与 ComfyUI 同机：配启动脚本路径（等价资源管理器双击）
    #    COMFYUI_START_SCRIPT=D:\AI\ComfyUI\start_comfyui.bat
    # 2) 后端在 Docker/Linux（本仓库默认形态）：配宿主机启动助手地址，
    #    助手脚本在仓库 scripts/host/comfyui_launcher.py，于 Win11 宿主机常驻
    #    COMFYUI_START_AGENT=http://host.docker.internal:8192
    COMFYUI_START_SCRIPT: str = os.getenv("COMFYUI_START_SCRIPT", "")
    COMFYUI_START_AGENT: str = os.getenv("COMFYUI_START_AGENT", "")
    # 启动后轮询探活的最长等待秒数（首次加载模型可能较慢）
    COMFYUI_START_TIMEOUT: int = int(os.getenv("COMFYUI_START_TIMEOUT", "90"))

    # Z-Image Turbo（GGUF 底模）配套组件：文本编码器与 VAE 位于 ComfyUI 对应模型目录
    ZIMAGE_TEXT_ENCODER: str = os.getenv("STUDIO_ZIMAGE_TEXT_ENCODER", "qwen_3_4b_fp8_mixed.safetensors")
    ZIMAGE_VAE: str = os.getenv("STUDIO_ZIMAGE_VAE", "ae.safetensors")

    # 抠图：默认 u2net（CPU 数秒~分钟级）；bria-rmbg/birefnet 效果更好但算力需求高
    REMBG_MODEL: str = os.getenv("REMBG_MODEL", "u2net")
    # ONNX 推理线程数：默认 3，给 Web 事件循环留 CPU（全占会导致其他请求超时）
    MATTING_THREADS: int = int(os.getenv("MATTING_THREADS", "3"))
    # 抠图推理前最大边长：超过则降采样，跑完把蒙版放大回原尺寸（防 4K 大图内存爆/超时）
    MATTING_MAX_SIDE: int = int(os.getenv("MATTING_MAX_SIDE", "2048"))

    # 任务队列 worker 轮询间隔（秒）
    WORKER_POLL_INTERVAL: float = float(os.getenv("WORKER_POLL_INTERVAL", "1.0"))
    # 任务失败自动重试次数
    TASK_MAX_RETRY: int = int(os.getenv("TASK_MAX_RETRY", "2"))

    # 静态资源对外路径前缀
    ASSETS_URL_PREFIX: str = "/files"

    def ensure_dirs(self) -> None:
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.ASSETS_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
