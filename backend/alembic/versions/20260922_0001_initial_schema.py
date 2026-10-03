"""初始化全部表结构：7 张表 + 4 个枚举类型 + pg_trgm 扩展 + 全部索引

Revision ID: 0001
Revises:
Create Date: 2026-09-22

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ---- PG 原生 ENUM 类型（create_type=False：由本迁移显式创建/删除） ----
product_condition = postgresql.ENUM(
    "brand_new", "like_new", "lightly_used", "heavily_used",
    name="product_condition", create_type=False,
)
product_status = postgresql.ENUM(
    "on_sale", "reserved", "sold", "off_shelf",
    name="product_status", create_type=False,
)
order_status = postgresql.ENUM(
    "pending", "confirmed", "completed", "cancelled",
    name="order_status", create_type=False,
)
chat_role = postgresql.ENUM(
    "user", "assistant", "system",
    name="chat_role", create_type=False,
)


def upgrade() -> None:
    # pg_trgm：中文模糊搜索的 GIN 索引依赖（PG13+ 为 trusted extension，库 owner 可自建）
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    bind = op.get_bind()
    product_condition.create(bind, checkfirst=True)
    product_status.create(bind, checkfirst=True)
    order_status.create(bind, checkfirst=True)
    chat_role.create(bind, checkfirst=True)

    # ---------------- users ----------------
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("student_no", sa.String(length=32), nullable=False),
        sa.Column("nickname", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=128), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column("campus", sa.String(length=64), nullable=True),
        sa.Column("credit_score", sa.Integer(), server_default=sa.text("100"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_senior_mode", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("student_no", name=op.f("uq_users_student_no")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
        sa.UniqueConstraint("phone", name=op.f("uq_users_phone")),
        comment="用户表",
    )
    op.create_index(op.f("ix_users_campus"), "users", ["campus"], unique=False)

    # ---------------- categories ----------------
    op.create_table(
        "categories",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("parent_id", sa.BigInteger(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_id"], ["categories.id"],
            name=op.f("fk_categories_parent_id_categories"), ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        comment="商品分类（两级树）",
    )
    op.create_index(op.f("ix_categories_parent_id"), "categories", ["parent_id"], unique=False)

    # ---------------- products ----------------
    op.create_table(
        "products",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("seller_id", sa.BigInteger(), nullable=False),
        sa.Column("category_id", sa.BigInteger(), nullable=True),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("original_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("condition", product_condition, nullable=False),
        sa.Column("images", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("campus", sa.String(length=64), nullable=True),
        sa.Column("status", product_status, server_default=sa.text("'on_sale'"), nullable=False),
        sa.Column("view_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("favorite_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["seller_id"], ["users.id"],
            name=op.f("fk_products_seller_id_users"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"],
            name=op.f("fk_products_category_id_categories"), ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_products")),
        comment="商品表",
    )
    op.create_index(op.f("ix_products_seller_id"), "products", ["seller_id"], unique=False)
    op.create_index(
        "ix_products_category_status_created", "products",
        ["category_id", "status", "created_at"], unique=False,
    )
    op.create_index("ix_products_price", "products", ["price"], unique=False)
    op.create_index("ix_products_campus", "products", ["campus"], unique=False)
    op.create_index(
        "ix_products_title_trgm", "products", ["title"],
        unique=False, postgresql_using="gin", postgresql_ops={"title": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_products_description_trgm", "products", ["description"],
        unique=False, postgresql_using="gin", postgresql_ops={"description": "gin_trgm_ops"},
    )

    # ---------------- orders ----------------
    op.create_table(
        "orders",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("order_no", sa.String(length=32), nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("buyer_id", sa.BigInteger(), nullable=False),
        sa.Column("seller_id", sa.BigInteger(), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", order_status, server_default=sa.text("'pending'"), nullable=False),
        sa.Column("trade_location", sa.String(length=128), nullable=True),
        sa.Column("remark", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"],
            name=op.f("fk_orders_product_id_products"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["buyer_id"], ["users.id"],
            name=op.f("fk_orders_buyer_id_users"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["seller_id"], ["users.id"],
            name=op.f("fk_orders_seller_id_users"), ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_orders")),
        sa.UniqueConstraint("order_no", name=op.f("uq_orders_order_no")),
        comment="订单表",
    )
    op.create_index(op.f("ix_orders_product_id"), "orders", ["product_id"], unique=False)
    op.create_index(op.f("ix_orders_buyer_id"), "orders", ["buyer_id"], unique=False)
    op.create_index(op.f("ix_orders_seller_id"), "orders", ["seller_id"], unique=False)

    # ---------------- favorites ----------------
    op.create_table(
        "favorites",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name=op.f("fk_favorites_user_id_users"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"],
            name=op.f("fk_favorites_product_id_products"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_favorites")),
        sa.UniqueConstraint("user_id", "product_id", name="uq_favorites_user_id_product_id"),
        comment="收藏表",
    )
    op.create_index(op.f("ix_favorites_product_id"), "favorites", ["product_id"], unique=False)

    # ---------------- chat_sessions ----------------
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name=op.f("fk_chat_sessions_user_id_users"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_sessions")),
        comment="AI 对话会话表",
    )
    op.create_index(op.f("ix_chat_sessions_user_id"), "chat_sessions", ["user_id"], unique=False)

    # ---------------- chat_messages ----------------
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.BigInteger(), nullable=False),
        sa.Column("role", chat_role, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id"], ["chat_sessions.id"],
            name=op.f("fk_chat_messages_session_id_chat_sessions"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_messages")),
        comment="AI 对话消息表",
    )
    op.create_index(
        "ix_chat_messages_session_created", "chat_messages",
        ["session_id", "created_at"], unique=False,
    )


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("favorites")
    op.drop_table("orders")
    op.drop_table("products")
    op.drop_table("categories")
    op.drop_table("users")

    chat_role.drop(bind, checkfirst=True)
    order_status.drop(bind, checkfirst=True)
    product_status.drop(bind, checkfirst=True)
    product_condition.drop(bind, checkfirst=True)
