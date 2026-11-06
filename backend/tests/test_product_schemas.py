"""商品 Schema 契约：状态隔离、价格区间、长度上限、未知字段拒绝。"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.enums import ProductCondition, ProductStatus
from app.schemas.product import (
    ProductCreate,
    ProductSearchParams,
    ProductStatusUpdate,
    ProductUpdate,
)


def _create(**overrides):
    data = {
        "title": "九成新自行车",
        "price": Decimal("300.00"),
        "condition": ProductCondition.LIGHTLY_USED,
    }
    data.update(overrides)
    return ProductCreate(**data)


def test_public_search_is_locked_to_on_sale() -> None:
    assert ProductSearchParams().status is ProductStatus.ON_SALE
    with pytest.raises(ValidationError):
        ProductSearchParams(status=ProductStatus.OFF_SHELF)


def test_search_price_range_is_validated() -> None:
    with pytest.raises(ValidationError):
        ProductSearchParams(min_price=Decimal("100"), max_price=Decimal("50"))


def test_search_keyword_and_campus_have_upper_bounds() -> None:
    with pytest.raises(ValidationError):
        ProductSearchParams(keyword="x" * 65)
    with pytest.raises(ValidationError):
        ProductSearchParams(campus="x" * 65)


def test_seller_status_endpoint_rejects_reserved_and_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ProductStatusUpdate(status=ProductStatus.RESERVED)
    with pytest.raises(ValidationError):
        ProductStatusUpdate(status=ProductStatus.SOLD, extra="x")  # type: ignore[call-arg]


def test_generic_update_cannot_change_status() -> None:
    # status 不在 ProductUpdate 中，且 extra=forbid，必须 422 而不是静默忽略
    with pytest.raises(ValidationError):
        ProductUpdate(status=ProductStatus.SOLD)  # type: ignore[call-arg]


def test_original_price_cannot_be_lower_than_price() -> None:
    with pytest.raises(ValidationError, match="原价"):
        _create(original_price=Decimal("100"))
    assert _create(original_price=Decimal("500")).original_price == Decimal("500")


def test_description_and_images_have_upper_bounds() -> None:
    with pytest.raises(ValidationError):
        _create(description="x" * 5001)
    with pytest.raises(ValidationError):
        _create(images=[f"https://img.example/{i}.jpg" for i in range(10)])


def test_update_allows_only_known_editable_fields() -> None:
    update = ProductUpdate(title="新标题", price=Decimal("88.50"))
    assert update.model_dump(exclude_unset=True, exclude_none=True) == {
        "title": "新标题",
        "price": Decimal("88.50"),
    }


def test_product_out_tolerates_legacy_dirty_rows() -> None:
    """0002 用 NOT VALID 保留历史脏数据，输出模型不能因此把列表打成 500。"""
    from datetime import datetime, timezone

    from app.schemas.product import ProductOut

    now = datetime.now(timezone.utc)
    out = ProductOut.model_validate(
        {
            "id": 1,
            "seller_id": 2,
            "title": "历史商品",
            "description": "x" * 6000,
            "price": Decimal("0"),
            "original_price": Decimal("0"),
            "condition": ProductCondition.LIGHTLY_USED,
            "category_id": None,
            "images": [f"https://img.example/{i}.jpg" for i in range(20)],
            "campus": None,
            "status": ProductStatus.ON_SALE,
            "view_count": 0,
            "favorite_count": 0,
            "created_at": now,
            "updated_at": now,
        }
    )
    assert out.price == Decimal("0")