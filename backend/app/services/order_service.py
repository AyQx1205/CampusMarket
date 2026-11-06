"""订单服务：下单 / 列表 / 详情 / 状态流转（按角色收敛的状态机）。

状态规则（避免任一方单方面把订单推进到终态）：

| 当前 | 买家可做 | 卖家可做 |
|---|---|---|
| pending | 取消 | 确认 / 取消 |
| confirmed | 确认完成 | 取消 |
| completed / cancelled | 无 | 无 |

- 买家确认完成，代表「已当面验货并收货」；
- 卖家不能替买家确认完成，避免卖家在未交付时把订单标记完成；
- 同状态重复调用幂等返回，不报错（网络重试友好）。
"""

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.crud import order_crud, product_crud
from app.models import Order, User
from app.models.enums import OrderStatus, ProductStatus
from app.schemas.common import Page
from app.schemas.order import OrderCreate, OrderDetailOut, OrderOut
from app.services import cache_service

# 买卖双方各自允许的目标状态
_BUYER_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.COMPLETED},
    OrderStatus.COMPLETED: set(),
    OrderStatus.CANCELLED: set(),
}
_SELLER_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.CANCELLED},
    OrderStatus.COMPLETED: set(),
    OrderStatus.CANCELLED: set(),
}


def _generate_order_no() -> str:
    """订单号 = UTC 时间戳 + 8 位随机串（22 字符，唯一性足够）。"""
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + uuid4().hex[:8].upper()


async def create_order(db: AsyncSession, buyer: User, data: OrderCreate) -> OrderOut:
    # 行锁读取：下面的「校验可售 → 置为已预订」必须与并发下单互斥，
    # 否则两个请求都能读到 ON_SALE 并各自建单（超卖）。
    product = await product_crud.get_by_id_for_update(db, data.product_id)
    if product is None:
        raise NotFoundError("商品不存在")
    if product.status != ProductStatus.ON_SALE:
        raise ConflictError("商品当前不可下单（已预订/已售出/已下架）")
    if product.seller_id == buyer.id:
        raise ForbiddenError("不能购买自己发布的商品")
    if await order_crud.count_active_orders(db, product.id) > 0:
        # 数据库部分唯一索引兜底前的友好拦截（修复历史脏数据场景）
        raise ConflictError("该商品已有进行中的订单")

    order = Order(
        order_no=_generate_order_no(),
        product_id=product.id,
        buyer_id=buyer.id,
        seller_id=product.seller_id,
        amount=product.price,  # 金额快照：以商品当时售价为准，前端不可传
        status=OrderStatus.PENDING,
        # 面交地点缺省用商品校区；两者都为空时存 NULL
        trade_location=data.trade_location or product.campus,
        remark=data.remark,
    )
    order.product = product  # 预挂关系，避免异步环境懒加载报错
    product.status = ProductStatus.RESERVED

    try:
        await order_crud.create(db, order)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        # 部分唯一索引 / order_no 唯一约束：并发下单或极小概率订单号碰撞
        raise ConflictError("该商品刚刚被其他买家下单，请刷新后重试") from None

    await cache_service.invalidate_product_detail(product.id)
    return OrderOut.model_validate(order)


async def list_my_orders(
    db: AsyncSession,
    user: User,
    role: Literal["buyer", "seller"] | None,
    page: int,
    page_size: int,
) -> Page[OrderDetailOut]:
    items, total = await order_crud.list_for_user(db, user.id, role, page, page_size)
    return Page(
        items=[OrderDetailOut.model_validate(o) for o in items],
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_order(db: AsyncSession, user: User, order_id: int) -> OrderDetailOut:
    order = await order_crud.get_by_id(db, order_id)
    if order is None:
        raise NotFoundError("订单不存在")
    if user.id not in (order.buyer_id, order.seller_id):
        raise ForbiddenError("无权查看该订单")
    return OrderDetailOut.model_validate(order)


async def update_order_status(
    db: AsyncSession, user: User, order_id: int, target: OrderStatus
) -> OrderDetailOut:
    # 先锁订单行：同一订单的并发流转串行化，避免重复完成/取消
    order = await order_crud.get_by_id_for_update(db, order_id)
    if order is None:
        raise NotFoundError("订单不存在")
    if user.id not in (order.buyer_id, order.seller_id):
        raise ForbiddenError("无权操作该订单")

    # 幂等：重复提交同一目标状态直接返回当前结果（提交空事务释放行锁）
    if target == order.status:
        await db.commit()
        return OrderDetailOut.model_validate(order)

    allowed = (
        _BUYER_TRANSITIONS if user.id == order.buyer_id else _SELLER_TRANSITIONS
    )[order.status]
    if target not in allowed:
        raise ConflictError(
            f"当前身份不允许把订单从「{order.status.value}」变更为「{target.value}」"
        )

    # 再锁商品（固定「订单 -> 商品」的加锁顺序），保护商品状态与订单一致
    product = await product_crud.get_by_id_for_update(db, order.product_id)
    if product is None:
        raise ConflictError("订单关联的商品不存在，请联系平台管理员")

    now = datetime.now(timezone.utc)
    order.status = target
    if target == OrderStatus.COMPLETED:
        order.finished_at = now
        product.status = ProductStatus.SOLD
    elif target == OrderStatus.CONFIRMED:
        # 正常流程下单时已置为 RESERVED；历史脏数据可能仍是 ON_SALE，这里补正
        if product.status == ProductStatus.ON_SALE:
            product.status = ProductStatus.RESERVED
    elif target == OrderStatus.CANCELLED:
        order.finished_at = now
        if product.status == ProductStatus.RESERVED:
            # 只有不存在其它进行中订单时才重新上架，避免把已被别人预订的商品
            # 误置回在售（历史数据可能存在同商品多活跃订单）
            others = await order_crud.count_other_active_orders(
                db, order.product_id, exclude_order_id=order.id
            )
            if others == 0:
                product.status = ProductStatus.ON_SALE

    await db.flush()
    await db.commit()
    await cache_service.invalidate_product_detail(order.product_id)
    return OrderDetailOut.model_validate(order)