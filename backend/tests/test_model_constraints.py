"""ORM 约束/索引名称与迁移脚本保持一致（命名约定容易重复前缀）。

回归背景：SQLAlchemy 的 ck 命名约定是 ck_%(table_name)s_%(constraint_name)s，
如果 CheckConstraint 再传完整名字，会生成 ck_products_ck_products_xxx。
"""

from app.models import Favorite, Order, Product, User


def _checks(table) -> set[str]:
    return {
        constraint.name
        for constraint in table.constraints
        if constraint.__class__.__name__ == "CheckConstraint"
    }


def test_check_constraint_names_have_single_prefix() -> None:
    assert _checks(User.__table__) == {"ck_users_credit_score_range"}
    assert _checks(Product.__table__) == {
        "ck_products_price_positive",
        "ck_products_original_price_gte_price",
        "ck_products_view_count_non_negative",
        "ck_products_favorite_count_non_negative",
    }
    assert _checks(Order.__table__) == {"ck_orders_amount_non_negative"}


def test_active_order_partial_unique_index_is_declared() -> None:
    index = next(i for i in Order.__table__.indexes if i.name == "uq_orders_active_product")
    assert index.unique is True
    assert "pending" in str(index.dialect_options["postgresql"]["where"])


def test_query_indexes_exist_in_models() -> None:
    product_indexes = {i.name for i in Product.__table__.indexes}
    order_indexes = {i.name for i in Order.__table__.indexes}
    favorite_indexes = {i.name for i in Favorite.__table__.indexes}

    assert {"ix_products_status_created", "ix_products_status_view"} <= product_indexes
    assert {"ix_orders_buyer_created", "ix_orders_seller_created", "ix_orders_product_status"} <= order_indexes
    assert "ix_favorites_user_created" in favorite_indexes