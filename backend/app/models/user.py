"""用户模型。

列注释一律用 Python # 注释保留（不写 SQLAlchemy comment=），
与 0001 迁移建表语句完全对齐，避免 autogenerate 虚假 diff。
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PkMixin

if TYPE_CHECKING:
    from app.models.chat import ChatSession
    from app.models.favorite import Favorite
    from app.models.product import Product


class User(PkMixin, Base):
    __tablename__ = "users"
    __table_args__ = {"comment": "用户表"}

    # 学号，全局唯一，注册/登录凭证
    student_no: Mapped[str] = mapped_column(String(32), unique=True)
    # 昵称
    nickname: Mapped[str] = mapped_column(String(64))
    # 邮箱，可选
    email: Mapped[str | None] = mapped_column(String(128), unique=True)
    # 手机号，可选
    phone: Mapped[str | None] = mapped_column(String(20), unique=True)
    # bcrypt 哈希，绝不存明文
    hashed_password: Mapped[str] = mapped_column(String(255))
    # 头像 URL
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    # 所属校区
    campus: Mapped[str | None] = mapped_column(String(64), index=True)
    # 信用分，满分 100 起步
    credit_score: Mapped[int] = mapped_column(Integer, server_default=text("100"))
    # 是否启用（封禁置 false）
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    # 是否偏好老年/简洁模式
    is_senior_mode: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # 关系：用户删除时级联清理（ondelete 见各 FK）
    products: Mapped[list["Product"]] = relationship(
        back_populates="seller", passive_deletes=True
    )
    favorites: Mapped[list["Favorite"]] = relationship(
        back_populates="user", passive_deletes=True
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        back_populates="user", passive_deletes=True
    )
