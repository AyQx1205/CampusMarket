"""异步数据库引擎与会话工厂。

事务模式（重要）：
- **写操作在 service 层显式 `await db.commit()`**，保证 HTTP 响应发出前
  事务已经落库；缓存失效等副作用放在 commit 之后。
- `get_db` 只负责「异常回滚 + 关闭会话」，不再在请求结束时 commit。
  原因：FastAPI 会先发送响应、再执行依赖的 teardown，旧模式里的
  commit 失败无法再改变已经发送的 200，客户端会误以为成功。
- 只读请求无需 commit；会话关闭时未提交的事务自动回滚。
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
    """FastAPI 依赖：按请求注入 AsyncSession；异常时回滚，正常时由 service 提交。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise