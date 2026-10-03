"""统一响应体 + 自定义业务异常 + 全局异常处理器。

约定：
- 所有接口统一返回 {"code": 0, "message": "ok", "data": {...}}。
- 业务代码只抛 BizException 及其子类，由全局 handler 转为统一响应体；
  不要在路由层手写 JSONResponse 错误体。
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException


def success(data: Any = None, message: str = "ok") -> dict[str, Any]:
    """构造成功响应体（统一响应体契约集中在本模块维护）。"""
    return {"code": 0, "message": message, "data": data}


def _error_body(code: int, message: str) -> dict[str, Any]:
    return {"code": code, "message": message, "data": None}


class BizException(Exception):
    """业务异常基类。

    code: 业务错误码（当前与 HTTP 状态码保持一致，便于前端统一处理）。
    """

    status_code: int = 400
    code: int = 400
    message: str = "请求参数错误"

    def __init__(
        self,
        message: str | None = None,
        *,
        code: int | None = None,
        status_code: int | None = None,
    ) -> None:
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)


class UnauthorizedError(BizException):
    status_code = 401
    code = 401
    message = "未登录或登录凭证无效"


class TokenExpiredError(UnauthorizedError):
    message = "登录已过期，请重新登录"


class TokenInvalidError(UnauthorizedError):
    message = "无效的登录凭证"


class ForbiddenError(BizException):
    status_code = 403
    code = 403
    message = "没有权限执行此操作"


class NotFoundError(BizException):
    status_code = 404
    code = 404
    message = "资源不存在"


class ConflictError(BizException):
    status_code = 409
    code = 409
    message = "资源冲突，请检查后重试"


class RateLimitError(BizException):
    status_code = 429
    code = 429
    message = "请求太频繁，请稍后再试"


class AIServiceError(BizException):
    """LLM 调用失败时的降级异常：不影响主交易流程，返回友好提示。"""

    status_code = 503
    code = 503
    message = "助手暂时不可用，你仍可正常浏览和下单"


def register_exception_handlers(app: FastAPI) -> None:
    """在 FastAPI 实例上注册全局异常处理器。"""

    @app.exception_handler(BizException)
    async def biz_exception_handler(request: Request, exc: BizException) -> JSONResponse:
        # 业务异常属预期行为，记 info 便于排查但不刷 error
        logger.info("业务异常: code={} message={} path={}", exc.code, exc.message, request.url.path)
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # 只取前 3 条错误，避免响应过长；字段名取 loc 去掉开头的 "body"/"query" 前缀
        errors = exc.errors()[:3]
        detail = "; ".join(
            "{}: {}".format(
                ".".join(str(loc) for loc in err.get("loc", ())[1:]) or "body",
                err.get("msg", ""),
            )
            for err in errors
        )
        return JSONResponse(status_code=422, content=_error_body(422, f"参数错误: {detail}"))

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        # 让 404（路由不存在）等框架异常也走统一响应体
        return JSONResponse(status_code=exc.status_code, content=_error_body(exc.status_code, str(exc.detail)))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("未处理异常: path={} error={}", request.url.path, exc)
        return JSONResponse(status_code=500, content=_error_body(500, "服务器内部错误，请稍后再试"))
