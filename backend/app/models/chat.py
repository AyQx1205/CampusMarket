"""AI 对话持久化模型：ChatSession（会话） + ChatMessage（消息）。

Redis 中仅存最近 N 轮热记忆（ai:chat:{user_id}:{session_id}，TTL 24h）；
本表负责长期历史落库，供会话回放与摘要压缩。

列注释一律用 Python # 注释保留（不写 SQLAlchemy comment=），
与 0001 迁移建表语句完全对齐，避免 autogenerate 虚假 diff。
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PkMixin, TimestampMixin
from app.models.enums import ChatRole, pg_enum

if TYPE_CHECKING:
    from app.models.user import User


class ChatSession(PkMixin, TimestampMixin, Base):
    __tablename__ = "chat_sessions"
    __table_args__ = {"comment": "AI 对话会话表"}

    # 会话归属用户
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    # 会话标题，可由首条消息自动生成
    title: Mapped[str] = mapped_column(String(128), default="新对话")

    user: Mapped["User"] = relationship(back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ChatMessage.created_at",
    )


class ChatMessage(PkMixin, Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        # 按会话拉取消息并按时间排序是唯一高频查询
        Index("ix_chat_messages_session_created", "session_id", "created_at"),
        {"comment": "AI 对话消息表"},
    )

    session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("chat_sessions.id", ondelete="CASCADE")
    )
    # 消息角色
    role: Mapped[ChatRole] = mapped_column(pg_enum(ChatRole, "chat_role"))
    # 消息内容
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped["ChatSession"] = relationship(back_populates="messages")
