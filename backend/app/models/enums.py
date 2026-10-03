"""业务枚举集中定义。

DB 中原生 ENUM 存储英文 value（主流稳妥做法：避免数据库层依赖中文编码、
便于跨语言消费），中文含义通过注释与 Pydantic schema 映射展示。
"""

import enum

from sqlalchemy import Enum as SAEnum


class ProductCondition(str, enum.Enum):
    """商品成色。"""

    BRAND_NEW = "brand_new"        # 全新
    LIKE_NEW = "like_new"          # 几乎全新
    LIGHTLY_USED = "lightly_used"  # 轻微使用
    HEAVILY_USED = "heavily_used"  # 明显使用


class ProductStatus(str, enum.Enum):
    """商品状态。"""

    ON_SALE = "on_sale"      # 在售
    RESERVED = "reserved"    # 已预订
    SOLD = "sold"            # 已售出
    OFF_SHELF = "off_shelf"  # 下架


class OrderStatus(str, enum.Enum):
    """订单状态：线下当面交易 + 预订流程（自研决策，最简闭环）。"""

    PENDING = "pending"      # 待确认：买家已下单，等待卖家确认
    CONFIRMED = "confirmed"  # 已确认：卖家接受，约定线下交易中
    COMPLETED = "completed"  # 已完成：交易完成
    CANCELLED = "cancelled"  # 已取消：任一方取消


class ChatRole(str, enum.Enum):
    """AI 对话消息角色。"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


def pg_enum(enum_cls: type[enum.Enum], name: str) -> SAEnum:
    """构造与 PG 原生 ENUM 对应的 SQLAlchemy 类型。

    values_callable：持久化成员的 value（如 "brand_new"）而非 name（如 "BRAND_NEW"），
    保持与迁移脚本中 postgresql.ENUM 的取值一致。
    """
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=True,
        validate_strings=True,
        values_callable=lambda obj: [m.value for m in obj],
    )
