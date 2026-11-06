"""分类相关 Schema。"""

from pydantic import BaseModel, ConfigDict


class CategoryOut(BaseModel):
    """分类信息（当前为两级树，parent_id 为空表示一级分类）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: int | None = None
    sort_order: int