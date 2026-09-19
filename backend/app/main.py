# FastAPI 入口：路由挂载 / 静态资产 / worker 生命周期 / MCP
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import studio
from app.config import settings
from app.models import init_db
from app.response import register_exception_handlers
from app.services import task_service

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动：建库 + 起任务 worker + MCP 会话管理器；关闭：依次停止"""
    await init_db()
    settings.ensure_dirs()
    worker = asyncio.create_task(task_service.worker_loop())
    logging.getLogger("studio").info(
        "%s v%s 启动于 :%s", settings.APP_NAME, settings.APP_VERSION, settings.PORT
    )
    # MCP streamable-http 会话管理器需用 async with 驱动其 TaskGroup 生命周期
    mcp_run = getattr(app.state, "mcp_lifespan", None)
    if mcp_run is not None:
        async with mcp_run():
            yield
    else:
        yield
    worker.cancel()


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

# 统一响应/异常
register_exception_handlers(app)

# 业务路由（Bearer 鉴权）
app.include_router(studio.meta_router)
app.include_router(studio.router)

# 资产静态文件（目录级只读托管，内网环境）
app.mount(settings.ASSETS_URL_PREFIX, StaticFiles(directory=settings.ASSETS_DIR), name="assets")

# MCP server（同进程，/mcp 端点，鉴权同主 API）
try:
    from app.mcp_server import mount_mcp

    mount_mcp(app)
except ImportError as exc:  # mcp SDK 未安装不影响主服务
    logging.getLogger("studio").warning("MCP 未启用: %s", exc)
