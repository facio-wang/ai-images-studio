# Docker 部署 ASGI 入口：前端 SPA(dist) 与后端 FastAPI 同端口合并托管
#
# 背景：app/main.py 里 MCP 以 Mount("/") 追加在路由表末尾兜底（吞掉所有未匹配路径），
# 因此不能简单地再 append 一个 SPA 挂载（永远不会被匹配）。
# 做法：
#   1. 摘除 meta_router 的根路由 "/"（其 JSON 元信息改挂到 /api/meta，供系统设置页读取），
#      否则它会先于 SPA 命中，首页永远返回 JSON 而非 index.html
#   2. 在 MCP 兜底挂载"之前"插入按路径分发的 ASGI 应用：
#      /mcp → 原 MCP streamable-http 应用；其余 → 前端静态文件（html=True 回退 index.html）
# 业务路由（/api、/files 等）位于路由表更前，优先级不受影响。
# 本地开发（无 SPA_DIR）时不做任何改动，行为与 uvicorn app.main:app 完全一致。
import os

from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

from app.api.studio import meta_router
from app.config import settings
from app.main import app

SPA_DIR = os.getenv("SPA_DIR", "/app/static")


class _SpaMcpDispatcher:
    """按路径分发：/mcp 走 MCP 应用，其余走前端静态文件"""

    def __init__(self, spa: StaticFiles, mcp_asgi, mcp_path: str = "/mcp"):
        self._spa = spa
        self._mcp = mcp_asgi
        self._mcp_path = mcp_path

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")
        if self._mcp is not None and (path == self._mcp_path or path.startswith(self._mcp_path + "/")):
            await self._mcp(scope, receive, send)
        else:
            await self._spa(scope, receive, send)


def _api_meta():
    """原根路由的元信息，挪到 /api/meta（前端系统设置页读取）"""
    return JSONResponse(
        {"code": 200, "msg": "ok", "data": {"name": settings.APP_NAME, "version": settings.APP_VERSION}}
    )


def _mount_spa() -> None:
    """存在前端构建产物时：摘除根路由 + 注入 /api/meta + 插入 SPA 挂载"""
    if not os.path.isdir(SPA_DIR):
        return

    # 1) 摘除 meta_router 的 "/" 根路由（其 JSON 元信息让位给 SPA 首页）。
    #    注意：FastAPI 新版 include_router 生成 _IncludedRouter 包装对象，
    #    须直接改 meta_router.routes 才能生效（app.router.routes 过滤无效）
    meta_router.routes[:] = [r for r in meta_router.routes if getattr(r, "path", None) != "/"]

    # 2) 元信息改挂 /api/meta（仍无需鉴权）；手工构造 APIRoute 插到 SPA 挂载之前
    meta_route = APIRoute("/api/meta", _api_meta, methods=["GET"], include_in_schema=False)

    # 3) SPA 挂载插到 MCP 兜底挂载之前（MCP 挂载时把 asgi 应用存到了 app.state.mcp_asgi）
    spa = StaticFiles(directory=SPA_DIR, html=True)
    mcp_asgi = getattr(app.state, "mcp_asgi", None)
    dispatcher = _SpaMcpDispatcher(spa, mcp_asgi)

    routes = app.router.routes
    mcp_idx = next((i for i, r in enumerate(routes) if getattr(r, "name", None) == "mcp"), None)
    spa_mount = Mount("/", app=dispatcher, name="spa")
    if mcp_idx is not None:
        # 先插 SPA 挂载再插 /api/meta，保证 meta 路由排在 SPA 兜底之前
        routes.insert(mcp_idx, spa_mount)
        routes.insert(mcp_idx, meta_route)
    else:  # MCP 未启用时直接兜底追加
        routes.append(spa_mount)
        routes.append(meta_route)


_mount_spa()
