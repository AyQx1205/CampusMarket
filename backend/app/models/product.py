"""商品模型（含搜索相关索引：复合索引 + pg_trgm GIN 索引）。

列注释一律用 Python # 注释保留（不写 SQLAlchemy comment=），
与 0001 迁移建表语句完全对齐，避免 autogenerate 虚假 diff。
"""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PkMixin, TimestampMixin
from app.models.enums import ProductCondition, ProductStatus, pg_enum

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.favorite import Favorite
    from app.models.user import User


class Product(PkMixin, TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        # 列表页核心查询：分类 + 状态 + 时间排序
        Index("ix_products_category_status_created", "category_id", "status", "created_at"),
        Index("ix_products_price", "price"),
        Index("ix_products_campus", "campus"),
        # 模糊搜索走 pg_trgm GIN 索引（0001 迁移中已 CREATE EXTENSION pg_trgm）
        Index(
            "ix_products_title_trgm",
            "title",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
        ),
        Index(
            "ix_products_description_trgm",
            "description",
            postgresql_using="gin",
            postgresql_ops={"description": "gin_trgm_ops"},
        ),
        {"comment": "商品表"},
    )

    # 卖家；用户注销时其商品级联删除
    seller_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    # 分类；分类删除时置空
    category_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("categories.id", ondelete="SET NULL"),
    )
    # 标题
    title: Mapped[str] = mapped_column(String(128))
    # 描述，允许发布后补全
    description: Mapped[str | None] = mapped_column(Text)
    # 售价（元）
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    # 原价（元），估价参考
    original_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    # 成色
    condition: Mapped[ProductCondition] = mapped_column(
        pg_enum(ProductCondition, "product_condition")
    )
    # 图片 URL 数组
    images: Mapped[list[str]] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )
    # 交易校区；缺省可继承卖家校区
    campus: Mapped[str | None] = mapped_column(String(64))
    # 商品状态
    status: Mapped[ProductStatus] = mapped_column(
        pg_enum(ProductStatus, "product_status"),
        default=ProductStatus.ON_SALE,
        server_default=text("'on_sale'"),
    )
    # 浏览量（同步写 Redis ZSet 榜）
    view_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    # 收藏数（冗余计数）
    favorite_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0")
    )

    seller: Mapped["User"] = relationship(back_populates="products")
    category: Mapped["Category | None"] = relationship(back_populates="products")
    favorites: Mapped[list["Favorite"]] = relationship(
        back_populates="product", passive_deletes=True
    )
