"""自然语言搜索解析链：找货需求 → 结构化筛选参数（无正则解析，无 Decimal schema）。"""

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from app.ai.chains import clear_optional, parse_price
from app.ai.llm import get_structured_llm
from app.ai.prompts import SEARCH_PARSER_PROMPT
from app.schemas.product import ProductSort


class ParsedFilters(BaseModel):
    """解析出的筛选参数（与 ProductSearchParams 字段对齐，不含 LLM 无法映射的 category_id）。

    - 价格用 float 而非 Decimal：Decimal 的 JSON Schema 会生成带 lookahead 的
      pattern 正则，Qwen 校验器不支持；LLM 输出精度用 float 足够。
    - 空值兜底：Qwen 在 function_calling 下可能把「无此条件」输出为字符串
      "None"，before 校验器统一清洗为 None/数值。
    """

    keyword: Optional[str] = Field(None, description="核心品类词")
    min_price: Optional[float] = Field(None, ge=0, description="最低价（元）")
    max_price: Optional[float] = Field(None, ge=0, description="最高价（元）")
    campus: Optional[str] = Field(None, description="校区")
    sort: ProductSort = Field(ProductSort.LATEST, description="排序方式")

    @field_validator("keyword", "campus", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v: Any) -> Any:
        """「None/null/无/空」等空值字符串统一转 None。"""
        return clear_optional(v)

    @field_validator("min_price", "max_price", mode="before")
    @classmethod
    def _coerce_price(cls, v: Any) -> Any:
        """清洗「￥1,500元」类输出并转 float；解析不出按未提供处理。"""
        return parse_price(v)

    @field_validator("sort", mode="before")
    @classmethod
    def _fallback_sort(cls, v: Any) -> Any:
        """排序输出空值字符串时回落默认值（非法枚举值仍保持报错）。"""
        v = clear_optional(v)
        return v if v is not None else ProductSort.LATEST


async def parse_search(query: str) -> ParsedFilters:
    """把「想买个 300 以内的自行车，东校区取」解析成结构化筛选。"""
    structured = get_structured_llm(ParsedFilters)
    return await structured.ainvoke(SEARCH_PARSER_PROMPT.format(query=query))
