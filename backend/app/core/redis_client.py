"""Redis 连接池单例 + 全局 key 模板。

规范：
- 业务代码禁止直接拼写 key 字符串，统一引用 RedisKeys 中的模板。
- TTL 常量集中在 RedisTTL，避免魔法数字散落各处。
- 客户端来自 redis.asyncio，decode_responses=True 直接返回 str。
"""

from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings


class RedisKeys:
    """所有 Redis key 模板集中定义（PROMPT.md Redis 使用规范）。"""

    # 商品详情缓存，TTL 300s，更新/删除商品时主动失效
    PRODUCT_DETAIL = "product:detail:{product_id}"
    # 热门商品榜 ZSet（member=product_id, score=浏览量）
    PRODUCT_HOT = "product:hot"
    # 滑动窗口限流
    RATE_LIMIT = "rate:{user_id}:{path}"
    # Refresh Token 白名单（jti -> user_id）
    AUTH_REFRESH = "auth:refresh:{jti}"
    # AI 会话记忆，TTL 24h，只保留最近 N 轮
    AI_CHAT_MEMORY = "ai:chat:{user_id}:{session_id}"


class RedisTTL:
    """各 key 的默认 TTL（秒）。"""

    PRODUCT_DETAIL = 300
    AUTH_REFRESH = 7 * 24 * 3600  # 与 REFRESH_TOKEN_EXPIRE_DAYS 对齐
    AI_CHAT_MEMORY = 24 * 3600

_pool: ConnectionPool | None = None


def _get_pool() -> ConnectionPool:
    """懒加载全局连接池（进程内单例）。"""
    global _pool
    if _pool is None:
        _pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True,  # 统一返回 str，避免业务层到处 decode
        )
    return _pool


def get_redis() -> Redis:
    """获取 Redis 异步客户端（共享全局连接池）。

    用法：
        redis = get_redis()
        await redis.set("k", "v", ex=60)
    """
    return Redis(connection_pool=_get_pool())


async def close_redis() -> None:
    """应用关闭时释放连接池（main.py 生命周期钩子调用）。"""
    global _pool
    if _pool is not None:
        await _pool.disconnect()
        _pool = None
