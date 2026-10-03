"""商品文案生成链：卖家原始描述 → 结构化 ListingDraft。"""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.ai.chains import clear_optional
from app.ai.llm import get_structured_llm
from app.ai.prompts import LISTING_WRITER_PROMPT
from app.models.enums import ProductCondition


class ListingDraft(BaseModel):
    """生成的商品文案草稿（发布前仍由卖家确认/修改）。"""

    title: str = Field(max_length=128, description="商品标题（建议不超过 30 字）")
    description: str = Field(description="商品描述")
    highlights: list[str] = Field(default_factory=list, description="卖点短语")
    condition: ProductCondition = Field(description="推断的成色")

    @field_validator("highlights", mode="before")
    @classmethod
    def _empty_list_to_default(cls, v: Any) -> Any:
        """卖点列表输出空值字符串（"None" 等）时回落为空列表。"""
        v = clear_optional(v)
        return v if v is not None else []


async def generate_listing(
    raw_info: str,
    expected_price: Decimal | None = None,
    condition_hint: str | None = None,
) -> ListingDraft:
    """根据卖家原始描述生成商品文案草稿。"""
    prompt = LISTING_WRITER_PROMPT.format(
        raw_info=raw_info,
        expected_price=f"{expected_price} 元" if expected_price else "未提供",
        condition_hint=condition_hint or "未提供",
    )
    structured = get_structured_llm(ListingDraft)
    return await structured.ainvoke(prompt)
