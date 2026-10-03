"""FastAPI 入口。

本轮为最小可运行版：CORS + 统一异常处理 + v1 REST 路由。
AI 助手路由（/ai/*，第 9 部分）生成后在此挂载。
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.redis_client import close_redis


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    yield
    await close_redis()  # 释放 Redis 连接池


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    lifespan=lifespan,
)

# 浏览器规范不允许 "*" 与 credentials 同开；开发期 "*" 不带 cookie，
# 生产在 .env 里配精确来源列表即可
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials="*" not in settings.CORS_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["健康检查"], summary="健康检查（不走统一前缀与响应体）")
async def health() -> dict[str, str]:
    return {"status": "ok"}
