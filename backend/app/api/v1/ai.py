"""AI 助手接口：/ai/chat、/ai/listing/generate、/ai/search。

- 全部接口需要登录（CurrentUser），并按用户做分钟级限流 + 每日配额。
- 降级约定：LLM 未配置（AINotConfiguredError，业务码 5001）原样透传；
  其余非业务异常包装为 AIServiceError，统一由全局异常处理器输出响应体。
- 请求体 schema 按文件清单内联定义在路由层，不新增 schemas/ai.py。
"""

import uuid
from decimal import Decimal
from typing import Any, Awaitable, Callable

from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from app.ai.agent import run_agent
from app.ai.chains.listing_writer import generate_listing
from app.ai.chains.search_parser import parse_search
from app.ai.llm import is_llm_configured
from app.ai.memory import append_message, load_history
from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.core.exceptions import AIServiceError, BizException, success
from app.core.rate_limit import enforce_daily_quota, enforce_rate_limit
from app.models import User
from app.schemas.product import ProductSearchParams
from app.services import product_service

router = APIRouter(prefix="/ai", tags=["AI 助手"])


class ChatRequest(BaseModel):
    """POST /ai/chat 请求体。"""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=2000, description="用户消息")
    session_id: str | None = Field(
        None,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="会话 ID；不传则开启新会话并返回",
    )


class ListingRequest(BaseModel):
    """POST /ai/listing/generate 请求体。"""

    model_config = ConfigDict(extra="forbid")

    raw_info: str = Field(min_length=1, max_length=2000, description="卖家原始描述")
    expected_price: Decimal | None = Field(None, gt=0, description="期望售价（元）")
    condition_hint: str | None = Field(None, max_length=200, description="成色提示")


class SearchRequest(BaseModel):
    """POST /ai/search 请求体。"""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=200, description="自然语言找货需求")


async def _guarded(op: Callable[[], Awaitable[Any]]) -> Any:
    """AI 执行包装：业务异常原样透传，其余异常统一降级为 AIServiceError。"""
    try:
        return await op()
    except BizException:
        raise
    except Exception as exc:
        logger.warning("AI 调用失败(降级): {}", exc)
        raise AIServiceError() from exc


async def _enforce_ai_limits(user: User) -> None:
    """分钟级限流 + 每日配额（Redis 故障时 fail-open，不阻断主流程）。"""
    await enforce_rate_limit(
        scope="ai",
        identity=str(user.id),
        limit=settings.AI_RATE_LIMIT_PER_MINUTE,
        window_seconds=60,
    )
    if is_llm_configured():
        await enforce_daily_quota(user_id=user.id, limit=settings.AI_DAILY_QUOTA)


@router.post("/chat", summary="AI 助手多轮对话")
async def chat(data: ChatRequest, db: DbSession, current_user: CurrentUser) -> dict:
    """session_id 维度多轮记忆（Redis），主服务 Agent 完成答复。"""
    await _enforce_ai_limits(current_user)
    session_id = data.session_id or uuid.uuid4().hex
    history = await load_history(current_user.id, session_id)

    reply = await _guarded(lambda: run_agent(db, current_user, data.message, history))
    reply = (reply or "").strip()
    if not reply:
        raise AIServiceError("助手没有生成有效回复，请换个说法再试")

    # 只在成功回复后写记忆，失败轮次不污染上下文（Redis 故障内部已降级）
    await append_message(current_user.id, session_id, "user", data.message)
    await append_message(current_user.id, session_id, "assistant", reply)
    return success({"session_id": session_id, "reply": reply})


@router.post("/listing/generate", summary="AI 生成商品文案草稿")
async def generate_listing_api(
    data: ListingRequest, current_user: CurrentUser
) -> dict:
    """卖家原始描述 → 结构化 ListingDraft（发布前仍由卖家确认/修改）。"""
    await _enforce_ai_limits(current_user)
    draft = await _guarded(
        lambda: generate_listing(data.raw_info, data.expected_price, data.condition_hint)
    )
    return success(draft.model_dump(mode="json"))


@router.post("/search", summary="AI 自然语言搜索商品")
async def ai_search(
    data: SearchRequest, db: DbSession, current_user: CurrentUser
) -> dict:
    """LLM 解析自然语言 → 结构化筛选 → 复用商品搜索服务。"""
    await _enforce_ai_limits(current_user)
    parsed = await _guarded(lambda: parse_search(data.query))

    min_price = parsed.min_price
    max_price = parsed.max_price
    if min_price is not None and max_price is not None and min_price > max_price:
        min_price, max_price = max_price, min_price
    # LLM 可能给出负数；这里钳到契约范围，避免 Pydantic 校验异常变成 500
    if min_price is not None:
        min_price = max(0.0, min_price)
    if max_price is not None:
        max_price = max(0.0, max_price)
    # 返回给前端的筛选条件与真正执行的查询保持一致
    parsed.min_price = min_price
    parsed.max_price = max_price

    # 在路由层裁剪到契约范围，避免 LLM 输出超长关键词触发 500
    params = ProductSearchParams(
        keyword=(parsed.keyword or None) and parsed.keyword[:64].strip() or None,
        min_price=Decimal(str(min_price)) if min_price is not None else None,
        max_price=Decimal(str(max_price)) if max_price is not None else None,
        campus=(parsed.campus or None) and parsed.campus[:64].strip() or None,
        sort=parsed.sort,
        page=1,
        page_size=20,
    )
    # 搜索本身不依赖 LLM（参数已在上面清洗），失败走全局 500
    result = await product_service.search(db, params)
    return success(
        {
            "filters": parsed.model_dump(mode="json"),
            "result": result.model_dump(mode="json"),
        }
    )