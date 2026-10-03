"""AI 会话记忆(Redis,多轮对话)。

- key 统一引用 core.redis_client.RedisKeys.AI_CHAT_MEMORY（模板唯一出口）。
- Redis LIST 存最近 N 轮消息（JSON：{"role","content"}），N = AI_MEMORY_MAX_ROUNDS。
- 每次写入用 pipeline 同时 rpush + ltrim + expire（TTL 24h 滚动刷新）。
- Redis 故障时降级为无记忆，不影响单轮对话。
"""

import json
from typing import Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from loguru import logger
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.redis_client import RedisKeys, RedisTTL, get_redis

Role = Literal["user", "assistant"]


def _key(user_id: int, session_id: str) -> str:
    return RedisKeys.AI_CHAT_MEMORY.format(user_id=user_id, session_id=session_id)


def _max_messages() -> int:
    """最多保留的消息条数（1 轮 = 1 条 user + 1 条 assistant）。"""
    return settings.AI_MEMORY_MAX_ROUNDS * 2


async def append_message(user_id: int, session_id: str, role: Role, content: str) -> None:
    """追加一条消息并刷新 TTL；超长自动裁剪；故障降级为丢弃。"""
    try:
        redis = get_redis()
        payload = json.dumps({"role": role, "content": content}, ensure_ascii=False)
        pipe = redis.pipeline()
        pipe.rpush(_key(user_id, session_id), payload)
        pipe.ltrim(_key(user_id, session_id), -_max_messages(), -1)
        pipe.expire(_key(user_id, session_id), RedisTTL.AI_CHAT_MEMORY)
        await pipe.execute()
    except RedisError as exc:
        logger.warning("AI 记忆写入失败(降级): {}", exc)


async def load_history(user_id: int, session_id: str) -> list[BaseMessage]:
    """加载最近 N 轮历史（旧 -> 新），转为 LangChain 消息对象。"""
    try:
        items = await get_redis().lrange(_key(user_id, session_id), 0, -1)
    except RedisError as exc:
        logger.warning("AI 记忆读取失败(降级为无历史): {}", exc)
        return []

    messages: list[BaseMessage] = []
    for raw in items:
        try:
            data = json.loads(raw)
        except (TypeError, ValueError):
            continue  # 脏数据直接跳过
        role, content = data.get("role"), data.get("content", "")
        if not content:
            continue
        if role == "user":
            messages.append(HumanMessage(content=str(content)))
        elif role == "assistant":
            messages.append(AIMessage(content=str(content)))
    return messages[-_max_messages():]


async def clear_memory(user_id: int, session_id: str) -> None:
    """清空指定会话记忆（开启新会话时可选调用）。"""
    try:
        await get_redis().delete(_key(user_id, session_id))
    except RedisError as exc:
        logger.warning("AI 记忆清理失败: {}", exc)
