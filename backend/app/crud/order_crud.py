"""订单数据访问层。"""

from typing import Literal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Order


async def get_by_id(db: AsyncSession, order_id: int) -> Order | None:
    result = await db.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.product))
    )
    return result.scalar_one_or_none()


async def list_for_user(
    db: AsyncSession,
    user_id: int,
    role: Literal["buyer", "seller"] | None,
    page: int,
    page_size: int,
) -> tuple[list[Order], int]:
    """我买到的 / 我卖出的 / 全部（role=None）。"""
    stmt = select(Order).options(selectinload(Order.product))
    if role == "buyer":
        stmt = stmt.where(Order.buyer_id == user_id)
    elif role == "seller":
        stmt = stmt.where(Order.seller_id == user_id)
    else:
        stmt = stmt.where(or_(Order.buyer_id == user_id, Order.seller_id == user_id))
    stmt = stmt.order_by(Order.created_at.desc())

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().all()), total


async def create(db: AsyncSession, order: Order) -> Order:
    db.add(order)
    await db.flush()
    return order
