"""订单相关 Schema。"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import OrderStatus
from app.schemas.product import ProductBrief


class OrderCreate(BaseModel):
    """POST /orders 请求体。金额不传，服务端按商品售价快照。"""

    product_id: int
    trade_location: str | None = Field(None, max_length=128, description="面交地点，缺省用商品校区")
    remark: str | None = Field(None, max_length=255, description="买家留言")


class OrderStatusUpdate(BaseModel):
    """PATCH /orders/{id}/status 请求体。"""

    status: OrderStatus = Field(description="目标状态；流转合法性由服务层状态机校验")


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_no: str
    product_id: int
    buyer_id: int
    seller_id: int
    amount: Decimal
    status: OrderStatus
    trade_location: str | None = None
    remark: str | None = None
    created_at: datetime
    finished_at: datetime | None = None
    product: ProductBrief | None = None
