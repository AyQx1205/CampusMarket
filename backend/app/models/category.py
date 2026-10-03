"""商品分类模型（两级树结构，自引用外键）。

列注释一律用 Python # 注释保留（不写 SQLAlchemy comment=），
与 0001 迁移建表语句完全对齐，避免 autogenerate 虚假 diff。
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PkMixin

if TYPE_CHECKING:
    from app.models.product import Product


class Category(PkMixin, Base):
    __tablename__ = "categories"
    __table_args__ = {"comment": "商品分类（两级树）"}

    # 分类名，如 教材/数码/自行车
    name: Mapped[str] = mapped_column(String(64))
    # 父分类；删除父分类时子分类保留并置空
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("categories.id", ondelete="SET NULL"),
        index=True,
    )
    # 展示排序，越小越靠前；server_default 必须与 0001 迁移一致
    sort_order: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    parent: Mapped["Category | None"] = relationship(
        "Category", remote_side="Category.id", back_populates="children"
    )
    children: Mapped[list["Category"]] = relationship(
        back_populates="parent", passive_deletes=True
    )
    products: Mapped[list["Product"]] = relationship(back_populates="category")
