"""FastAPI 入口。

CORS + 统一异常处理 + v1 REST 路由 + 健康检查。
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.redis_client import close_redis, get_redis
from app.db.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    yield
    await close_redis()  # 释放 Redis 连接池
    await engine.dispose()  # 释放数据库连接池


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    # 生产环境默认不暴露交互式文档；需要时在 .env 中改为 dev
    docs_url="/docs" if settings.ENVIRONMENT != "prod" else None,
    redoc_url=None,
    lifespan=lifespan,
)

# 浏览器规范不允许 "*" 与 credentials 同开；开发期默认精确来源，
# 生产在 .env 里配精确来源列表（prod 校验会拒绝 "*"）
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


@app.get("/health", tags=["健康检查"], summary="健康检查（存活探针）")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["健康检查"], summary="就绪检查（数据库 + Redis）")
async def readiness() -> JSONResponse:
    """依赖探针：任一依赖不可用时返回 503，供容器/负载均衡摘流。"""
    components: dict[str, str] = {}

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        components["database"] = "ok"
    except Exception:
        components["database"] = "unavailable"

    try:
        await get_redis().ping()
        components["redis"] = "ok"
    except Exception:
        components["redis"] = "unavailable"

    ready = all(value == "ok" for value in components.values())
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ok" if ready else "degraded", "components": components},
    )