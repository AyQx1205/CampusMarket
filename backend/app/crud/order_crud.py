"""订单数据访问层。"""

from typing import Literal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Order
from app.models.enums import OrderStatus

_ACTIVE_STATUSES = (OrderStatus.PENDING, OrderStatus.CONFIRMED)

# 列表/详情统一预加载，避免异步下访问关系触发懒加载
_DETAIL_OPTIONS = (
    selectinload(Order.product),
    selectinload(Order.buyer),
    selectinload(Order.seller),
)


async def get_by_id(db: AsyncSession, order_id: int) -> Order | None:
    result = await db.execute(
        select(Order).where(Order.id == order_id).options(*_DETAIL_OPTIONS)
    )
    return result.scalar_one_or_none()


async def get_by_id_for_update(db: AsyncSession, order_id: int) -> Order | None:
    """行锁读取订单（状态流转专用）。

    先锁订单、再锁商品，固定加锁顺序避免与其它订单操作交叉死锁。
    populate_existing：同一会话可能已加载过该订单，强制用最新行覆盖。
    """
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
        .with_for_update()
        .options(*_DETAIL_OPTIONS)
        .execution_options(populate_existing=True)
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
    stmt = select(Order).options(*_DETAIL_OPTIONS)
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


async def count_active_orders(db: AsyncSession, product_id: int) -> int:
    """该商品当前进行中的订单数量。"""
    result = await db.execute(
        select(func.count())
        .select_from(Order)
        .where(
            Order.product_id == product_id,
            Order.status.in_(_ACTIVE_STATUSES),
        )
    )
    return result.scalar_one()


async def count_other_active_orders(
    db: AsyncSession, product_id: int, exclude_order_id: int
) -> int:
    """同一商品除当前订单外还有多少条进行中订单（取消后判断能否重新上架）。"""
    result = await db.execute(
        select(func.count())
        .select_from(Order)
        .where(
            Order.product_id == product_id,
            Order.id != exclude_order_id,
            Order.status.in_(_ACTIVE_STATUSES),
        )
    )
    return result.scalar_one()