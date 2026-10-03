"""异步数据库引擎与会话工厂。

事务模式：请求级事务 —— get_db 依赖在请求成功返回后统一 commit，
异常时回滚。业务层（service/crud）不需要手动 commit/rollback，
保证 api -> service -> crud 分层里事务边界清晰一致。
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,  # 连接被 PG/防火墙回收后自动剔除，避免拿死连接
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # commit 后仍可访问属性，避免异步环境触发隐式 IO
    autoflush=False,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI 依赖：按请求注入 AsyncSession，请求结束统一提交/回滚。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
