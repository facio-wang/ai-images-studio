# 鉴权依赖：单用户 Bearer Token（STUDIO_TOKEN 配置于 .env）
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.response import CODE_OK, CODE_UNAUTHORIZED, resp

_bearer = HTTPBearer(auto_error=False)


class AuthContext:
    """鉴权结果上下文（预留多用户扩展位，P1 单用户）"""

    def __init__(self, token: str):
        self.token = token


async def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthContext:
    """校验 Bearer Token，失败抛 401"""
    if credentials is None or credentials.credentials != settings.STUDIO_TOKEN:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="未授权或 token 无效")
    return AuthContext(credentials.credentials)


async def require_auth_query(request: Request) -> AuthContext:
    """兼容静态文件等无法带 Header 的场景：支持 ?token= 查询参数鉴权"""
    token = request.query_params.get("token", "")
    if token != settings.STUDIO_TOKEN:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="未授权或 token 无效")
    return AuthContext(token)
