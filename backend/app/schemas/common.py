"""通用 Schema：统一分页体。"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """统一分页数据体（外层统一响应体由 core.exceptions.success 包装）。"""

    items: list[T]
    total: int
    page: int
    page_size: int
