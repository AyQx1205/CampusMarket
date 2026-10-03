"""DeclarativeBase 与公共 Mixin。

- 命名约定（NAMING_CONVENTION）必须保留：它决定了约束/索引的自动命名规则，
  是 Alembic autogenerate 后续 diff 一致性的前提。
- 注意：Mixin 中的列不带 SQLAlchemy comment=（0001 迁移建表未加列注释），
  保持两侧一致，避免 autogenerate 产生加注释的虚假 diff。
"""

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """全部 ORM 模型的基类。"""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    def to_dict(self) -> dict[str, Any]:
        """调试辅助：把实例字段转为 dict（生产序列化请走 Pydantic schema）。"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class PkMixin:
    """自增主键（bigint，PG 下与序列/identity 配合良好）。"""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)


class TimestampMixin:
    """created_at / updated_at 时间戳（服务端 now() 生成）。

    eager_defaults=True：UPDATE 时让 PG 走 "UPDATE ... RETURNING" 把
    onupdate=func.now() 产生的新 updated_at 一并取回。
    默认值 "auto" 只对 INSERT 启用 RETURNING，UPDATE 后 SQLAlchemy 会把
    updated_at 标记为过期；随后序列化（ProductOut.model_validate）读该属性
    会触发懒加载 IO，在 async 下直接抛 MissingGreenlet → 接口 500。
    """

    __mapper_args__ = {"eager_defaults": True}

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
