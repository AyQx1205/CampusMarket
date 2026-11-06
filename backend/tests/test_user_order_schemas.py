"""用户 / 订单 Schema 契约：邮箱电话校验、未知字段拒绝、文本清洗。"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.enums import OrderStatus
from app.schemas.order import OrderCreate, OrderStatusUpdate
from app.schemas.user import UserUpdate


def test_user_update_validates_email_and_phone() -> None:
    with pytest.raises(ValidationError):
        UserUpdate(email="not-an-email")
    with pytest.raises(ValidationError):
        UserUpdate(phone="12345")
    assert UserUpdate(phone="13800138000").phone == "13800138000"


def test_user_update_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        UserUpdate(credit_score=100)  # type: ignore[call-arg]


def test_user_update_strips_blank_text() -> None:
    assert UserUpdate(nickname="  小明  ").nickname == "小明"
    assert UserUpdate(nickname="   ").nickname is None


def test_order_create_rejects_client_supplied_amount() -> None:
    with pytest.raises(ValidationError):
        OrderCreate(product_id=1, amount=Decimal("0.01"))  # type: ignore[call-arg]


def test_order_create_strips_text_and_requires_positive_product() -> None:
    data = OrderCreate(product_id=2, trade_location="  图书馆门口 ", remark="  ")
    assert data.trade_location == "图书馆门口"
    assert data.remark is None
    with pytest.raises(ValidationError):
        OrderCreate(product_id=0)


def test_order_status_update_rejects_unknown_status_or_extra_field() -> None:
    assert OrderStatusUpdate(status=OrderStatus.CONFIRMED).status is OrderStatus.CONFIRMED
    with pytest.raises(ValidationError):
        OrderStatusUpdate(status="shipped")  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        OrderStatusUpdate(status=OrderStatus.CANCELLED, refund=True)  # type: ignore[call-arg]