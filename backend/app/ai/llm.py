"""LLM 工厂：统一创建 ChatOpenAI 兼容客户端。

- OPENAI_API_KEY 为空或为占位值时抛 AINotConfiguredError（业务码 5001），
  由全局异常处理器输出统一响应体，而不是 500。
- base_url 可指向 DeepSeek / 通义 / 智谱 / Ollama 等 OpenAI 兼容服务。
"""

from typing import Any

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import BizException


class AINotConfiguredError(BizException):
    """LLM 未配置（前端可据此隐藏 AI 入口）。"""

    def __init__(self) -> None:
        super().__init__(
            "AI 助手暂未配置，请先设置 OPENAI_API_KEY",
            code=5001,
            status_code=503,
        )


# .env  中常见的占位值，同样视为未配置
_PLACEHOLDER_KEYS = {"sk-xxx", "sk-xxxxxxxxxxxxxxxxxxxxxxxx"}


def is_llm_configured() -> bool:
    """判断 LLM 是否已正确配置。"""
    key = settings.OPENAI_API_KEY.strip()
    return bool(key) and key not in _PLACEHOLDER_KEYS


def get_llm(temperature: float | None = None) -> ChatOpenAI:
    """创建 ChatOpenAI 实例（每次新建，实例本身轻量且无状态）。"""
    if not is_llm_configured():
        raise AINotConfiguredError()

    # 供应商私有参数统一在这个 dict 上合并（新增参数继续加 key，不要整体覆盖）
    extra_body: dict[str, Any] = {}
    if settings.LLM_DISABLE_THINKING:
        # Qwen(DashScope) thinking 模式下拒绝 tool_choice="required"，
        # 而 with_structured_output(method="function_calling") 内部依赖它，
        # 故按配置禁用 thinking；DeepSeek 等其他兼容服务会忽略该字段。
        extra_body["enable_thinking"] = False

    return ChatOpenAI(
        base_url=settings.OPENAI_BASE_URL,
        api_key=settings.OPENAI_API_KEY,
        model=settings.LLM_MODEL,
        temperature=settings.LLM_TEMPERATURE if temperature is None else temperature,
        timeout=60,
        max_retries=1,
        extra_body=extra_body,
    )


def get_structured_llm(schema: type[BaseModel], temperature: float = 0):
    """所有结构化输出统一走这里，方便按供应商切换 method。

    method 固定 function_calling（Qwen / DeepSeek 都支持）：
    json_schema 模式下 Pydantic 会为 Decimal 字段生成带 lookahead 的
    pattern 正则（如 ^(?!^[-+.]*$)...），Qwen 的 schema 校验器不支持，
    且 Decimal 对 LLM 输出精度属过度设计——结构化模型一律用 float。
    """
    return get_llm(temperature=temperature).with_structured_output(
        schema,
        method="function_calling",
    )
