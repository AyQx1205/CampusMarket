"""商品相关 Schema。"""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

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
    images: list[str] = []
    status: ProductStatus
    campus: str | None = None


class ProductBase(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    description: str | None = None
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    original_price: Decimal | None = Field(None, gt=0, max_digits=10, decimal_places=2)
    condition: ProductCondition
    category_id: int | None = Field(None, description="分类，可空")
    images: list[str] = Field(default_factory=list, max_length=9, description="图片 URL，最多 9 张")
    campus: str | None = Field(None, max_length=64, description="缺省继承卖家校区")


class ProductCreate(ProductBase):
    """POST /products 请求体。"""


class ProductUpdate(BaseModel):
    """PATCH /products/{id} 请求体。字段不传或为 null 表示不修改。"""

    title: str | None = Field(None, min_length=1, max_length=128)
    description: str | None = None
    price: Decimal | None = Field(None, gt=0, max_digits=10, decimal_places=2)
    original_price: Decimal | None = Field(None, gt=0, max_digits=10, decimal_places=2)
    condition: ProductCondition | None = None
    category_id: int | None = None
    images: list[str] | None = Field(None, max_length=9)
    campus: str | None = Field(None, max_length=64)
    status: ProductStatus | None = None


class ProductOut(ProductBase):
    """商品完整信息（详情/列表共用）。"""

    model_config = ConfigDict(from_attributes=True)

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
    campus: str | None = None
    condition: ProductCondition | None = None
    status: ProductStatus = Field(ProductStatus.ON_SALE, description="默认只搜在售商品")
    sort: ProductSort = ProductSort.LATEST
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
