"""定价建议链：商品信息 → 建议价格区间（LLM 经验估价，附免责提示由调用方拼接）。"""

from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from app.ai.chains import clear_optional, parse_price
from app.ai.llm import get_structured_llm
from app.ai.prompts import PRICE_ADVISOR_PROMPT
from app.models.enums import ProductCondition


class PriceAdvice(BaseModel):
    """估价结果（仅供参考，平台不担保成交价）。

    价格用 float 而非 Decimal：Decimal 的 JSON Schema 会生成带 lookahead 的
    pattern 正则，Qwen 校验器不支持；LLM 输出精度用 float 足够。
    空值/单位兜底：Qwen 可能输出「约50元」「None」等字符串，before 校验器清洗。
    """

    estimated_price: float = Field(gt=0, description="最可能成交价（元）")
    low: float = Field(gt=0, description="合理区间下限（元）")
    high: float = Field(gt=0, description="合理区间上限（元）")
    rationale: str = Field(description="定价依据")
    tips: list[str] = Field(default_factory=list, description="加快出手建议")

    @field_validator("estimated_price", "low", "high", mode="before")
    @classmethod
    def _coerce_price(cls, v: Any) -> Any:
        """清洗「约50元」类输出并转 float；彻底解析不出按 None 交由必填校验报错。"""
        return parse_price(v)

    @field_validator("tips", mode="before")
    @classmethod
    def _empty_list_to_default(cls, v: Any) -> Any:
        """建议列表输出空值字符串（"None" 等）时回落为空列表。"""
        v = clear_optional(v)
        return v if v is not None else []


async def advise_price(
    title: str,
    description: str = "",
    condition: ProductCondition = ProductCondition.LIGHTLY_USED,
    original_price: Optional[Decimal] = None,
) -> PriceAdvice:
    """给出建议定价。condition 使用商品成色枚举的 value（如 lightly_used）。"""
    prompt = PRICE_ADVISOR_PROMPT.format(
        title=title,
        description=description or "无补充描述",
        condition=f"{condition.value}（{condition.name}）",
        original_price=f"{original_price} 元" if original_price else "未提供",
    )
    structured = get_structured_llm(PriceAdvice)
    return await structured.ainvoke(prompt)
