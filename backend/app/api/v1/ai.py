"""AI 助手接口：/ai/chat、/ai/listing/generate、/ai/search。

- 全部接口需要登录（CurrentUser）。
- 降级约定：LLM 未配置（AINotConfiguredError，业务码 5001）原样透传；
  其余非业务异常包装为 AIServiceError，统一由全局异常处理器输出响应体。
- 请求体 schema 按文件清单内联定义在路由层，不新增 schemas/ai.py。
"""

import uuid
from decimal import Decimal
from typing import Any, Awaitable, Callable

from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel, Field

from app.ai.agent import run_agent
from app.ai.chains.listing_writer import generate_listing
from app.ai.chains.search_parser import parse_search
from app.ai.memory import append_message, load_history
from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import AIServiceError, BizException, success
from app.schemas.product import ProductSearchParams
from app.services import product_service

router = APIRouter(prefix="/ai", tags=["AI 助手"])


class ChatRequest(BaseModel):
    """POST /ai/chat 请求体。"""

    message: str = Field(min_length=1, max_length=2000, description="用户消息")
    session_id: str | None = Field(
        None, max_length=64, description="会话 ID；不传则开启新会话并返回"
    )


class ListingRequest(BaseModel):
    """POST /ai/listing/generate 请求体。"""

    raw_info: str = Field(min_length=1, max_length=2000, description="卖家原始描述")
    expected_price: Decimal | None = Field(None, gt=0, description="期望售价（元）")
    condition_hint: str | None = Field(None, max_length=200, description="成色提示")


class SearchRequest(BaseModel):
    """POST /ai/search 请求体。"""

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


@router.post("/chat", summary="AI 助手多轮对话")
async def chat(data: ChatRequest, db: DbSession, current_user: CurrentUser) -> dict:
    """session_id 维度多轮记忆（Redis），主服务 Agent 完成答复。"""
    session_id = data.session_id or uuid.uuid4().hex
    history = await load_history(current_user.id, session_id)

    reply = await _guarded(lambda: run_agent(db, current_user, data.message, history))

    # 只在成功回复后写记忆，失败轮次不污染上下文（Redis 故障内部已降级）
    await append_message(current_user.id, session_id, "user", data.message)
    await append_message(current_user.id, session_id, "assistant", reply)
    return success({"session_id": session_id, "reply": reply})


@router.post("/listing/generate", summary="AI 生成商品文案草稿")
async def generate_listing_api(data: ListingRequest, _: CurrentUser) -> dict:
    """卖家原始描述 → 结构化 ListingDraft（发布前仍由卖家确认/修改）。"""
    draft = await _guarded(
        lambda: generate_listing(data.raw_info, data.expected_price, data.condition_hint)
    )
    return success(draft.model_dump(mode="json"))


@router.post("/search", summary="AI 自然语言搜索商品")
async def ai_search(data: SearchRequest, db: DbSession, _: CurrentUser) -> dict:
    """LLM 解析自然语言 → 结构化筛选 → 复用商品搜索服务。"""
    parsed = await _guarded(lambda: parse_search(data.query))

    params = ProductSearchParams(
        keyword=parsed.keyword,
        min_price=parsed.min_price,
        max_price=parsed.max_price,
        campus=parsed.campus,
        sort=parsed.sort,
        page=1,
        page_size=20,
    )
    # 搜索本身不依赖 LLM，无需 _guarded（失败走全局 500）
    result = await product_service.search(db, params)
    return success(
        {
            "filters": parsed.model_dump(mode="json"),
            "result": result.model_dump(mode="json"),
        }
    )
