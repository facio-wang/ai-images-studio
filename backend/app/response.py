# 统一响应结构 + 统一异常处理
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("studio")

# 业务错误码
CODE_OK = 200
CODE_BAD_REQUEST = 400
CODE_UNAUTHORIZED = 401
CODE_NOT_FOUND = 404
CODE_SERVER_ERROR = 500


def resp(code: int = CODE_OK, msg: str = "ok", data=None) -> dict:
    """统一响应体 {code, msg, data}"""
    return {"code": code, "msg": msg, "data": data}


def ok(data=None, msg: str = "ok") -> JSONResponse:
    return JSONResponse(resp(CODE_OK, msg, data))


def fail(code: int, msg: str, data=None) -> JSONResponse:
    return JSONResponse(resp(code, msg, data), status_code=200)


def register_exception_handlers(app: FastAPI) -> None:
    """统一异常 → 统一响应结构"""

    @app.exception_handler(StarletteHTTPException)
    async def _http_exc(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        # 401 等鉴权错误保持 HTTP 状态码，便于前端拦截器统一跳登录
        return JSONResponse(
            resp(exc.status_code, str(exc.detail)), status_code=exc.status_code
        )

    @app.exception_handler(RequestValidationError)
    async def _valid_exc(request: Request, exc: RequestValidationError) -> JSONResponse:
        return fail(CODE_BAD_REQUEST, f"参数错误: {exc.errors()[0]['msg'] if exc.errors() else 'invalid'}")

    @app.exception_handler(Exception)
    async def _generic_exc(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("未处理异常: %s %s", request.method, request.url.path)
        return fail(CODE_SERVER_ERROR, f"服务器内部错误: {exc}")
