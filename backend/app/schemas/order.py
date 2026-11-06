"""订单相关 Schema。"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import OrderStatus
from app.schemas.product import ProductBrief
from app.schemas.user import UserContact


class OrderCreate(BaseModel):
    """POST /orders 请求体。金额不传，服务端按商品售价快照。"""

    model_config = ConfigDict(extra="forbid")

    product_id: int = Field(gt=0)
    trade_location: str | None = Field(None, max_length=128, description="面交地点，缺省用商品校区")
    remark: str | None = Field(None, max_length=255, description="买家留言")

    @field_validator("trade_location", "remark", mode="before")
    @classmethod
    def _strip_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip() or None
        return value


class OrderStatusUpdate(BaseModel):
    """PATCH /orders/{id}/status 请求体。"""

    model_config = ConfigDict(extra="forbid")

    status: OrderStatus = Field(description="目标状态；流转合法性由服务层状态机校验")


class OrderOut(BaseModel):
    """订单基础信息（创建/状态流转响应）。"""

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
    updated_at: datetime
    finished_at: datetime | None = None
    product: ProductBrief | None = None


class OrderDetailOut(OrderOut):
    """订单详情/列表：附带买卖双方联系方式（仅订单参与者可见）。"""

    buyer: UserContact
    seller: UserContact