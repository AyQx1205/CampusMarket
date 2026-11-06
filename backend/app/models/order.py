"""订单模型。

列注释一律用 Python # 注释保留（不写 SQLAlchemy comment=），
与迁移建表语句完全对齐，避免 autogenerate 虚假 diff。

并发约束：一个商品最多只能有一条「进行中」订单（pending/confirmed），
由部分唯一索引 `uq_orders_active_product` 在数据库层兜底，防止
两个买家同时下单造成重复售卖。
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PkMixin
from app.models.enums import OrderStatus, pg_enum

if TYPE_CHECKING:
    from app.models.product import Product  # noqa: F401
    from app.models.user import User  # noqa: F401


class Order(PkMixin, Base):
    __tablename__ = "orders"
    # UPDATE 时用 RETURNING 取回 onupdate=func.now() 生成的新 updated_at，
    # 避免提交后序列化触发异步懒加载（MissingGreenlet）
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (
        CheckConstraint("amount >= 0", name="amount_non_negative"),
        Index(
            "uq_orders_active_product",
            "product_id",
            unique=True,
            postgresql_where=text("status IN ('pending', 'confirmed')"),
        ),
        Index("ix_orders_buyer_created", "buyer_id", "created_at"),
        Index("ix_orders_seller_created", "seller_id", "created_at"),
        Index("ix_orders_product_status", "product_id", "status"),
        {"comment": "订单表"},
    )

    # 业务订单号，service 层生成（日期+随机串）
    order_no: Mapped[str] = mapped_column(String(32), unique=True)
    # 商品；已有订单的商品禁止删除，保护交易记录
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.id", ondelete="RESTRICT"),
        index=True,
    )
    buyer_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    seller_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    # 成交金额（元），下单时快照
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    # 订单状态
    status: Mapped[OrderStatus] = mapped_column(
        pg_enum(OrderStatus, "order_status"),
        default=OrderStatus.PENDING,
        server_default=text("'pending'"),
    )
    # 线下面交地点
    trade_location: Mapped[str | None] = mapped_column(String(128))
    # 买家留言
    remark: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    # 完成时间，status=completed 时写入
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    product: Mapped["Product"] = relationship()
    buyer: Mapped["User"] = relationship(foreign_keys=[buyer_id])
    seller: Mapped["User"] = relationship(foreign_keys=[seller_id])