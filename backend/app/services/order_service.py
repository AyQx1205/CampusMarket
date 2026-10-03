"""订单服务：下单 / 列表 / 状态流转（状态机）。"""

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.crud import order_crud, product_crud
from app.models import Order, User
from app.models.enums import OrderStatus, ProductStatus
from app.schemas.common import Page
from app.schemas.order import OrderCreate, OrderOut
from app.services import cache_service

# 订单状态机。面交场景允许 pending 直接跳 completed
# （双方当面完成交易很常见，不必强制经过 confirmed）。
_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {
        OrderStatus.CONFIRMED,
        OrderStatus.COMPLETED,
        OrderStatus.CANCELLED,
    },
    OrderStatus.CONFIRMED: {OrderStatus.COMPLETED, OrderStatus.CANCELLED},
    OrderStatus.COMPLETED: set(),
    OrderStatus.CANCELLED: set(),
}


def _generate_order_no() -> str:
    """订单号 = UTC 时间戳 + 8 位随机串（22 字符，唯一性足够）。"""
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + uuid4().hex[:8].upper()


async def create_order(db: AsyncSession, buyer: User, data: OrderCreate) -> OrderOut:
    # 行锁读取：下面的「校验可售 → 置为已预订」必须与并发下单互斥，
    # 否则两个请求都能读到 ON_SALE 并各自建单（超卖）
    product = await product_crud.get_by_id_for_update(db, data.product_id)
    if product is None:
        raise NotFoundError("商品不存在")
    if product.status != ProductStatus.ON_SALE:
        raise ConflictError("商品当前不可下单（已预订/已售出/已下架）")
    if product.seller_id == buyer.id:
        raise ForbiddenError("不能购买自己发布的商品")

    order = Order(
        order_no=_generate_order_no(),
        product_id=product.id,
        buyer_id=buyer.id,
        seller_id=product.seller_id,
        amount=product.price,  # 金额快照：以商品当时售价为准，前端不可传
        status=OrderStatus.PENDING,
        trade_location=data.trade_location,
        remark=data.remark,
    )
    order.product = product  # 预挂关系，避免异步环境懒加载报错
    product.status = ProductStatus.RESERVED
    await order_crud.create(db, order)
    await cache_service.invalidate_product_detail(product.id)
    return OrderOut.model_validate(order)


async def list_my_orders(
    db: AsyncSession,
    user: User,
    role: Literal["buyer", "seller"] | None,
    page: int,
    page_size: int,
) -> Page[OrderOut]:
    items, total = await order_crud.list_for_user(db, user.id, role, page, page_size)
    return Page(
        items=[OrderOut.model_validate(o) for o in items],
        total=total,
        page=page,
        page_size=page_size,
    )


async def update_order_status(
    db: AsyncSession, user: User, order_id: int, target: OrderStatus
) -> OrderOut:
    order = await order_crud.get_by_id(db, order_id)
    if order is None:
        raise NotFoundError("订单不存在")
    if user.id not in (order.buyer_id, order.seller_id):
        raise ForbiddenError("无权操作该订单")
    if target not in _TRANSITIONS[order.status]:
        raise ConflictError(
            f"订单不允许从「{order.status.value}」变更为「{target.value}」"
        )

    order.status = target
    if target == OrderStatus.COMPLETED:
        order.finished_at = datetime.now(timezone.utc)
        order.product.status = ProductStatus.SOLD
    elif target == OrderStatus.CANCELLED and order.product.status == ProductStatus.RESERVED:
        order.product.status = ProductStatus.ON_SALE  # 取消后商品重新在售

    await db.flush()
    await cache_service.invalidate_product_detail(order.product_id)
    return OrderOut.model_validate(order)
