"""订单接口。"""

from typing import Literal

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import success
from app.schemas.order import OrderCreate, OrderStatusUpdate
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["订单"])


@router.post("", summary="下单（商品自动转「已预订」，金额按售价快照）")
async def create_order(
    db: DbSession, current_user: CurrentUser, data: OrderCreate
) -> dict:
    order = await order_service.create_order(db, current_user, data)
    return success(order.model_dump(mode="json"), "下单成功")


@router.get("", summary="我的订单（role=buyer 我买到的 / role=seller 我卖出的）")
async def list_orders(
    db: DbSession,
    current_user: CurrentUser,
    role: Literal["buyer", "seller"] | None = Query(
        None, description="不传 = 全部与我相关的订单"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    result = await order_service.list_my_orders(db, current_user, role, page, page_size)
    return success(result.model_dump(mode="json"))


@router.patch("/{order_id}/status", summary="流转订单状态（买卖双方均可操作）")
async def update_order_status(
    db: DbSession, current_user: CurrentUser, order_id: int, data: OrderStatusUpdate
) -> dict:
    order = await order_service.update_order_status(db, current_user, order_id, data.status)
    return success(order.model_dump(mode="json"))
