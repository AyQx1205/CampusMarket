"""轻量意图/画像识别：只做提示词级路由，不做多 Agent 编排、不 import langgraph。

- 用户画像（老年/简洁模式）决定 System Prompt 附加段 —— 由 prompts.build_system_prompt 承担。
- 本模块保留 intent 识别函数：当前 Agent 单体已覆盖全部场景，
  预留该入口给后续「按意图直连 chain」的优化（先识别再走结构化链，省 Agent 循环）。
"""

from typing import Literal

from pydantic import BaseModel, Field

from app.ai.llm import get_structured_llm

Intent = Literal["general", "sell_help", "search_help", "price_help", "rules_help"]

_INTENT_PROMPT = """把用户消息分类到最合适的场景：
- sell_help：想卖东西/发布商品/改价格改状态
- search_help：想找货/想买某物
- price_help：问值多少钱/定价
- rules_help：问平台规则/安全/流程
- general：闲聊、其他或复合请求（无法明确归类时也选 general）

用户消息：{message}"""


class RouteDecision(BaseModel):
    """意图路由结果（service 场景已由单体 Agent 覆盖，此结果仅用于提示词微调/统计）。"""

    intent: Intent = Field(description="场景分类")
    senior_friendly: bool = Field(False, description="是否建议用更简单的表达回答")


async def route_message(message: str) -> RouteDecision:
    """LLM 结构化输出识别意图；配置缺失/调用失败由上层统一降级。"""
    structured = get_structured_llm(RouteDecision)
    return await structured.ainvoke(_INTENT_PROMPT.format(message=message[:500]))
