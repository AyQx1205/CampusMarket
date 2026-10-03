"""收藏模型（user_id + product_id 联合唯一）。

列注释一律用 Python # 注释保留（不写 SQLAlchemy comment=），
与 0001 迁移建表语句完全对齐，避免 autogenerate 虚假 diff。
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PkMixin

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


class Favorite(PkMixin, Base):
    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_favorites_user_id_product_id"),
        {"comment": "收藏表"},
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE")
    )
    # 反查"商品被谁收藏"走 product_id 索引
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
    )
    # 收藏时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="favorites")
    product: Mapped["Product"] = relationship(back_populates="favorites")
