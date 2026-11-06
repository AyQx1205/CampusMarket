"""数据完整性补丁：订单 updated_at、活跃订单唯一索引、检查约束与分类种子。

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-06

背景（对应 ARCHITECTURE_REVIEW 的 P0/P2）：
1. 同一商品可能被并发下两单：用部分唯一索引兜底「一个商品同时最多一条
   pending/confirmed 订单」。
2. 订单缺 updated_at，状态变更无法审计。
3. 金额/价格/信用分缺少数据库层校验。
4. 分类表为空，前端只能硬编码分类；在迁移里种入基础分类。
5. 首页/热门榜缺 (status, created_at) / (status, view_count) 索引。

检查约束使用 NOT VALID：对历史脏数据不阻断上线，但会约束之后的新写入。
运维可在数据清洗后执行 `ALTER TABLE ... VALIDATE CONSTRAINT ...`。
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------- orders.updated_at ----------------
    op.add_column(
        "orders",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # ---------------- 清理历史重复活跃订单，再建部分唯一索引 ----------------
    # 同一商品若已有多条 pending/confirmed，只保留 id 最大（最新）的一条，
    # 其余置为 cancelled；这样迁移不会因为历史脏数据直接失败。
    op.execute(
        """
        UPDATE orders AS o
        SET status = 'cancelled',
            finished_at = now(),
            updated_at = now()
        WHERE o.status IN ('pending', 'confirmed')
          AND EXISTS (
              SELECT 1
              FROM orders AS newer
              WHERE newer.product_id = o.product_id
                AND newer.status IN ('pending', 'confirmed')
                AND newer.id > o.id
          )
        """
    )
    op.create_index(
        "uq_orders_active_product",
        "orders",
        ["product_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('pending', 'confirmed')"),
    )

    # ---------------- 查询索引 ----------------
    op.create_index("ix_orders_buyer_created", "orders", ["buyer_id", "created_at"])
    op.create_index("ix_orders_seller_created", "orders", ["seller_id", "created_at"])
    op.create_index("ix_orders_product_status", "orders", ["product_id", "status"])
    op.create_index("ix_products_status_created", "products", ["status", "created_at"])
    op.create_index("ix_products_status_view", "products", ["status", "view_count"])
    op.create_index("ix_favorites_user_created", "favorites", ["user_id", "created_at"])

    # 历史脏数据：商品是 reserved 但没有任何 pending/confirmed 订单，会卡住卖家
    # 上下架与编辑；确认没有活跃订单后安全恢复为在售。
    op.execute(
        """
        UPDATE products AS p
        SET status = 'on_sale'
        WHERE p.status = 'reserved'
          AND NOT EXISTS (
              SELECT 1 FROM orders AS o
              WHERE o.product_id = p.id
                AND o.status IN ('pending', 'confirmed')
          )
        """
    )

    # ---------------- 检查约束（NOT VALID） ----------------
    op.execute(
        "ALTER TABLE products ADD CONSTRAINT ck_products_price_positive "
        "CHECK (price > 0) NOT VALID"
    )
    op.execute(
        "ALTER TABLE products ADD CONSTRAINT ck_products_original_price_gte_price "
        "CHECK (original_price IS NULL OR original_price >= price) NOT VALID"
    )
    op.execute(
        "ALTER TABLE products ADD CONSTRAINT ck_products_view_count_non_negative "
        "CHECK (view_count >= 0) NOT VALID"
    )
    op.execute(
        "ALTER TABLE products ADD CONSTRAINT ck_products_favorite_count_non_negative "
        "CHECK (favorite_count >= 0) NOT VALID"
    )
    op.execute(
        "ALTER TABLE orders ADD CONSTRAINT ck_orders_amount_non_negative "
        "CHECK (amount >= 0) NOT VALID"
    )
    op.execute(
        "ALTER TABLE users ADD CONSTRAINT ck_users_credit_score_range "
        "CHECK (credit_score >= 0 AND credit_score <= 100) NOT VALID"
    )

    # ---------------- 基础分类种子 ----------------
    # 仅当分类表为空时写入，避免覆盖已有自定义分类。
    op.execute(
        """
        INSERT INTO categories (name, sort_order)
        SELECT v.name, v.sort_order
        FROM (VALUES
            ('教材教辅', 10),
            ('数码电子', 20),
            ('生活用品', 30),
            ('美妆个护', 40),
            ('服饰鞋包', 50),
            ('运动健身', 60),
            ('其他', 99)
        ) AS v(name, sort_order)
        WHERE NOT EXISTS (SELECT 1 FROM categories)
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_credit_score_range")
    op.execute("ALTER TABLE orders DROP CONSTRAINT IF EXISTS ck_orders_amount_non_negative")
    op.execute(
        "ALTER TABLE products DROP CONSTRAINT IF EXISTS ck_products_favorite_count_non_negative"
    )
    op.execute(
        "ALTER TABLE products DROP CONSTRAINT IF EXISTS ck_products_view_count_non_negative"
    )
    op.execute(
        "ALTER TABLE products DROP CONSTRAINT IF EXISTS ck_products_original_price_gte_price"
    )
    op.execute("ALTER TABLE products DROP CONSTRAINT IF EXISTS ck_products_price_positive")

    op.drop_index("ix_favorites_user_created", table_name="favorites")
    op.drop_index("ix_products_status_view", table_name="products")
    op.drop_index("ix_products_status_created", table_name="products")
    op.drop_index("ix_orders_product_status", table_name="orders")
    op.drop_index("ix_orders_seller_created", table_name="orders")
    op.drop_index("ix_orders_buyer_created", table_name="orders")
    op.drop_index("uq_orders_active_product", table_name="orders")
    op.drop_column("orders", "updated_at")