# MCP server：同进程挂 /mcp（streamable-http），暴露 Studio 工具给对话层（如 Hermes/Zeus）
import base64
import logging

from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount

from app.config import settings
from app.services import chat_service

logger = logging.getLogger("studio.mcp")

mcp = FastMCP("ai-images-studio", stateless_http=True)


@mcp.tool()
async def studio_generate_image(prompt: str, width: int = 1024, height: int = 1024, count: int = 1) -> dict:
    """提交文生图任务。返回 task_id，完成后产物在资产库。"""
    import aiosqlite

    from app.services import task_service

    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        task = await task_service.create_task(
            db, "generate", {"prompt": prompt, "width": width, "height": height, "count": count}
        )
    return {"task_id": task["id"], "status": task["status"], "prompt": prompt}


@mcp.tool()
async def studio_remove_bg(asset_id: int) -> dict:
    """对资产库中指定图片执行抠图，输出透明 PNG。返回 task_id。"""
    import aiosqlite

    from app.services import task_service

    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        task = await task_service.create_task(db, "matting", {"asset_id": asset_id, "model": settings.REMBG_MODEL})
    return {"task_id": task["id"], "status": task["status"], "source_asset_id": asset_id}


@mcp.tool()
async def studio_list_assets(asset_type: str = "", limit: int = 10) -> dict:
    """列出资产库最近产物（generate/matting/upload）。"""
    import aiosqlite

    from app.models import fetch_all

    sql = "SELECT id, type, file_path, labels, created_at FROM assets"
    args: tuple = ()
    if asset_type:
        sql += " WHERE type=?"
        args = (asset_type,)
    sql += " ORDER BY id DESC LIMIT ?"
    args = args + (limit,)
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        items = await fetch_all(db, sql, args)
    for it in items:
        it["url"] = f"{settings.ASSETS_URL_PREFIX}/{it.pop('file_path')}"
    return {"items": items}


@mcp.tool()
async def studio_chat(message: str, session_id: int = 0) -> dict:
    """对话工作台：自然语言下发指令（规则引擎编排），返回 AI 回复与触发的任务。"""
    import aiosqlite

    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        result = await chat_service.send_message(db, session_id or None, message)
    return result


class _BearerMiddleware(BaseHTTPMiddleware):
    """MCP 端点 Bearer 鉴权（同主 API 的 STUDIO_TOKEN）"""

    async def dispatch(self, request: Request, call_next):
        header = request.headers.get("authorization", "")
        if header != f"Bearer {settings.STUDIO_TOKEN}":
            return JSONResponse({"code": 401, "msg": "未授权"}, status_code=401)
        return await call_next(request)


def mount_mcp(app) -> None:
    """把 MCP streamable-http 应用挂到 /mcp 路径"""
    mcp.settings.streamable_http_path = "/mcp"
    asgi_app = mcp.streamable_http_app()
    asgi_app.add_middleware(_BearerMiddleware)
    # streamable-http 会话管理器的 TaskGroup 由其自带 lifespan 初始化：
    # 主 app 在启动时驱动该 lifespan（见 main.py）
    app.state.mcp_asgi = asgi_app
    app.state.mcp_lifespan = mcp.session_manager.run
    app.router.routes.append(Mount("/", app=asgi_app, name="mcp"))
    logger.info("MCP 已挂载: /mcp (streamable-http)")
