"""订单状态机：角色权限边界 + 订单号格式。

这些规则直接决定「谁能把订单推进到终态」，用纯函数断言即可，
不需要数据库（行锁/并发由集成测试覆盖）。
"""

from app.models.enums import OrderStatus
from app.services.order_service import (
    _BUYER_TRANSITIONS,
    _SELLER_TRANSITIONS,
    _generate_order_no,
)


def test_buyer_can_only_cancel_pending_and_complete_confirmed() -> None:
    assert _BUYER_TRANSITIONS[OrderStatus.PENDING] == {OrderStatus.CANCELLED}
    assert _BUYER_TRANSITIONS[OrderStatus.CONFIRMED] == {OrderStatus.COMPLETED}


def test_seller_can_confirm_or_cancel_pending_but_never_complete() -> None:
    assert _SELLER_TRANSITIONS[OrderStatus.PENDING] == {
        OrderStatus.CONFIRMED,
        OrderStatus.CANCELLED,
    }
    assert OrderStatus.COMPLETED not in _SELLER_TRANSITIONS[OrderStatus.CONFIRMED]
    assert _SELLER_TRANSITIONS[OrderStatus.CONFIRMED] == {OrderStatus.CANCELLED}


def test_terminal_states_have_no_outgoing_transitions() -> None:
    for table in (_BUYER_TRANSITIONS, _SELLER_TRANSITIONS):
        assert table[OrderStatus.COMPLETED] == set()
        assert table[OrderStatus.CANCELLED] == set()


def test_order_no_is_22_chars_and_unique_enough() -> None:
    numbers = {_generate_order_no() for _ in range(100)}
    assert all(len(number) == 22 for number in numbers)
    assert len(numbers) == 100