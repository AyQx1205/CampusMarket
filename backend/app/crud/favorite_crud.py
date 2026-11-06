"""收藏数据访问层。"""

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Favorite


async def get(db: AsyncSession, user_id: int, product_id: int) -> Favorite | None:
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user_id, Favorite.product_id == product_id
        )
    )
    return result.scalar_one_or_none()


async def add(db: AsyncSession, user_id: int, product_id: int) -> Favorite:
    favorite = Favorite(user_id=user_id, product_id=product_id)
    db.add(favorite)
    await db.flush()
    return favorite


async def remove(db: AsyncSession, favorite: Favorite) -> bool:
    """按主键原子删除；返回是否真的删掉了这一行。

    并发取消收藏时，后到的 DELETE 命中 0 行，不能让它再去扣减一次
    favorite_count（否则计数会漂移）。直接执行 Core DELETE 也避免了
    ORM 对已消失对象 flush 时抛 StaleDataError。
    """
    result = await db.execute(
        delete(Favorite)
        .where(Favorite.id == favorite.id)
        .execution_options(synchronize_session=False)
    )
    await db.flush()
    return bool(result.rowcount)


async def list_by_user(
    db: AsyncSession, user_id: int, page: int, page_size: int
) -> tuple[list[Favorite], int]:
    stmt = (
        select(Favorite)
        .where(Favorite.user_id == user_id)
        .options(selectinload(Favorite.product))  # 嵌套序列化需要 product，避免异步懒加载
        .order_by(Favorite.created_at.desc())
    )
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().all()), total
