"""商品相关 Schema。"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ProductCondition, ProductStatus


class ProductSort(str, Enum):
    """商品列表排序方式。"""

    LATEST = "latest"          # 最新发布
    PRICE_ASC = "price_asc"    # 价格从低到高
    PRICE_DESC = "price_desc"  # 价格从高到低
    HOTTEST = "hottest"        # 浏览量最高


class ProductBrief(BaseModel):
    """商品精简信息（订单/收藏里嵌套展示用）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    price: Decimal
    images: list[str] = Field(default_factory=list)
    status: ProductStatus
    campus: str | None = None


class ProductBase(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    # Text 列也必须有上限：避免单条描述把行/缓存/LLM 上下文撑爆
    description: str | None = Field(None, max_length=5000)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    original_price: Decimal | None = Field(None, gt=0, max_digits=10, decimal_places=2)
    condition: ProductCondition
    category_id: int | None = Field(None, description="分类，可空")
    images: list[str] = Field(default_factory=list, max_length=9, description="图片 URL，最多 9 张")
    campus: str | None = Field(None, max_length=64, description="缺省继承卖家校区")


class ProductCreate(ProductBase):
    """POST /products 请求体。"""

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _check_prices(self) -> "ProductCreate":
        if self.original_price is not None and self.original_price < self.price:
            raise ValueError("原价不能低于售价")
        return self


class ProductUpdate(BaseModel):
    """PATCH /products/{id} 请求体。字段不传或为 null 表示不修改。

    状态不在通用更新里出现：商品状态由独立的
    `PATCH /products/{id}/status` 控制，避免普通编辑绕过订单状态机。
    extra="forbid"：客户端误传 status 时直接 422，而不是被静默忽略。
    """

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(None, min_length=1, max_length=128)
    description: str | None = Field(None, max_length=5000)
    price: Decimal | None = Field(None, gt=0, max_digits=10, decimal_places=2)
    original_price: Decimal | None = Field(None, gt=0, max_digits=10, decimal_places=2)
    condition: ProductCondition | None = None
    category_id: int | None = None
    images: list[str] | None = Field(None, max_length=9)
    campus: str | None = Field(None, max_length=64)

    @model_validator(mode="after")
    def _check_prices(self) -> "ProductUpdate":
        if (
            self.original_price is not None
            and self.price is not None
            and self.original_price < self.price
        ):
            raise ValueError("原价不能低于售价")
        return self


class ProductStatusUpdate(BaseModel):
    """PATCH /products/{id}/status：卖家只允许在「在售 / 下架 / 已售出」间操作。

    `reserved` 只能由下单流程写入，卖家不能手工设置，否则会制造
    「有预留状态但没有订单」的脏数据并绕过超卖保护。
    """

    model_config = ConfigDict(extra="forbid")

    status: Literal[
        ProductStatus.ON_SALE,
        ProductStatus.OFF_SHELF,
        ProductStatus.SOLD,
    ]


class ProductOut(ProductBase):
    """商品完整信息（详情/列表共用）。

    输出侧刻意放宽输入校验（价格 >0、描述长度、图片数量）：0002 迁移用
    NOT VALID 保留了历史脏数据，输出模型若沿用输入约束会让一条旧记录
    把整个列表/详情打成 500。写入约束仍由 ProductCreate/ProductUpdate 保证。
    """

    model_config = ConfigDict(from_attributes=True)

    description: str | None = None
    price: Decimal
    original_price: Decimal | None = None
    images: list[str] = Field(default_factory=list)

    id: int
    seller_id: int
    status: ProductStatus
    view_count: int
    favorite_count: int
    created_at: datetime
    updated_at: datetime


class ProductSearchParams(BaseModel):
    """GET /products 查询参数模型（FastAPI 0.115+ Query Parameter Model）。"""

    keyword: str | None = Field(None, max_length=64, description="关键词，模糊匹配标题/描述（pg_trgm）")
    category_id: int | None = None
    min_price: Decimal | None = Field(None, ge=0)
    max_price: Decimal | None = Field(None, ge=0)
    campus: str | None = Field(None, max_length=64)
    condition: ProductCondition | None = None
    # 公开搜索只允许在售：下架/已售商品不应被枚举出来
    status: Literal[ProductStatus.ON_SALE] = Field(
        ProductStatus.ON_SALE, description="固定为在售（公开搜索不暴露下架/已售商品）"
    )
    sort: ProductSort = ProductSort.LATEST
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    @model_validator(mode="after")
    def _check_price_range(self) -> "ProductSearchParams":
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            raise ValueError("最低价不能高于最高价")
        return self