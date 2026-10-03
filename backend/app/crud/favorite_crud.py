"""收藏数据访问层。"""

from sqlalchemy import func, select
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


async def remove(db: AsyncSession, favorite: Favorite) -> None:
    await db.delete(favorite)
    await db.flush()


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
