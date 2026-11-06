"""主服务 Agent：langchain 1.0 create_agent 组装。

- 严格使用 `from langchain.agents import create_agent`；
  禁止 import langgraph、禁止 AgentExecutor。
- 不使用 checkpointer：多轮记忆由 app/ai/memory.py 基于 Redis 自管
  （/ai/chat 每次把历史消息随输入传入，回复后写回）。
- db/user 通过 config["configurable"] 注入工具链（见 tools._ctx）。
- recursion_limit 限制单轮工具调用轮数，防止模型死循环消耗额度。
"""

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import get_llm
from app.ai.prompts import build_system_prompt
from app.ai.tools import build_tools
from app.core.config import settings
from app.models import User


def _extract_reply(result: dict) -> str:
    """取最后一轮模型输出；部分模型 content 为分段列表，统一拼接为纯文本。"""
    content = result["messages"][-1].content
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        text = block.get("text", "") if isinstance(block, dict) else str(block)
        if text:
            parts.append(text)
    return "\n".join(parts)


async def run_agent(
    db: AsyncSession,
    user: User,
    message: str,
    history: list,
) -> str:
    """执行一轮 Agent 对话，返回助手回复文本。

    每次按用户画像构建 agent（构建成本为本地图组装，无网络调用）。
    """
    agent = create_agent(
        get_llm(),
        tools=build_tools(),
        system_prompt=build_system_prompt(
            is_senior=user.is_senior_mode,
            write_tools_enabled=settings.AI_ENABLE_WRITE_TOOLS,
        ),
    )
    config = {
        "configurable": {"db": db, "user": user},
        # LangGraph 的 recursion_limit 统计图步数（模型 + 工具各算一步），
        # 留出 2 步余量给最终回复
        "recursion_limit": settings.AI_MAX_TOOL_ROUNDS * 2 + 2,
    }
    result = await agent.ainvoke(
        {"messages": [*history, HumanMessage(content=message)]},
        config=config,
    )
    return _extract_reply(result)