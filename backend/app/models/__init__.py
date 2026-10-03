"""models 层：SQLAlchemy ORM 模型（Alembic 迁移管理的唯一事实来源）。"""

from app.db.base import Base
from app.models.category import Category
from app.models.chat import ChatMessage, ChatRole, ChatSession
from app.models.enums import OrderStatus, ProductCondition, ProductStatus
from app.models.favorite import Favorite
from app.models.order import Order
from app.models.product import Product
from app.models.user import User

__all__ = [
    "Base",
    "Category",
    "ChatMessage",
    "ChatRole",
    "ChatSession",
    "Favorite",
    "Order",
    "OrderStatus",
    "Product",
    "ProductCondition",
    "ProductStatus",
    "User",
]
