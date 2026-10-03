"""chains 层：场景化结构化输出链（with_structured_output，无正则解析）。

结构化模型通用兜底：Qwen 等模型在 function_calling 模式下，可能把
「无此值」输出为字符串 "None"/"null"/"无" 而不是省略字段或真 null。
各结构化模型统一用本模块的 before 校验器（mode="before"，类型解析前
执行）清洗，避免 float/枚举校验直接报错。
"""

from typing import Any

# LLM 常见的「空值」字面量（英文不区分大小写）
_EMPTY_TOKENS = {"none", "null", "n/a", "无", "空"}


def _is_empty_text(s: str) -> bool:
    return s == "" or s.lower() in _EMPTY_TOKENS


def clear_optional(v: Any) -> Any:
    """Optional 字段 before 校验：空值字符串 -> None，其余原样交回 pydantic。"""
    if isinstance(v, str) and _is_empty_text(v.strip()):
        return None
    return v


def parse_price(v: Any) -> Any:
    """价格字段 before 校验：清洗货币符号/千分位/单位后转 float；无法解析视为未提供。"""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip()
        if _is_empty_text(s):
            return None
        for token in ("￥", "¥", "$", ",", "，", "元", "块", "约"):
            s = s.replace(token, "")
        s = s.strip()
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None
    return v
