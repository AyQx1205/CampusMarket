"""Redis 固定窗口限流与 AI 每日配额。

设计取舍：
- 交易主流程不因 Redis 故障被阻断：限流采用 fail-open（仅告警），
  Redis 恢复后自动重新生效。
- 固定窗口足够覆盖登录爆破 / AI 刷量场景，且实现简单、可预测；
  需要更平滑的曲线再换滑动窗口（Lua 脚本）。
"""

from datetime import datetime, timezone

from loguru import logger
from redis.exceptions import RedisError
from starlette.requests import Request

from app.core.config import settings
from app.core.exceptions import RateLimitError
from app.core.redis_client import RedisKeys, get_redis


def client_ip(request: Request) -> str:
    """取客户端地址。

    默认只信任 socket 地址；部署在反向代理后时，把 TRUST_PROXY_HEADERS=true
    并确保代理覆盖（而不是追加）客户端传入的 X-Forwarded-For，否则可被伪造。
    """
    if settings.TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # 取最左侧（原始客户端）；限制长度避免把超长头写进 Redis key
            candidate = forwarded.split(",", 1)[0].strip()
            if candidate:
                return candidate[:64]
    return request.client.host if request.client else "unknown"


async def enforce_rate_limit(
    *,
    scope: str,
    identity: str,
    limit: int,
    window_seconds: int,
) -> None:
    """计数 +1；超过 limit 抛 429（带 Retry-After）。"""
    if limit <= 0:
        return
    key = RedisKeys.RATE_LIMIT.format(scope=scope, identity=identity)
    try:
        redis = get_redis()
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, window_seconds)
        if count > limit:
            ttl = await redis.ttl(key)
            raise RateLimitError(
                f"操作太频繁，请 {max(ttl, 1)} 秒后再试",
                retry_after=max(ttl, 1),
            )
    except RateLimitError:
        raise
    except RedisError as exc:
        # fail-open：限流是保护措施，不应成为新的单点故障
        logger.warning("限流检查失败(降级放行): scope={} err={}", scope, exc)


async def enforce_daily_quota(*, user_id: int, limit: int) -> None:
    """AI 每日调用配额；跨天自动过期（key 内含 UTC 日期）。"""
    if limit <= 0:
        return
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    key = RedisKeys.AI_DAILY_QUOTA.format(user_id=user_id, date=day)
    try:
        redis = get_redis()
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 24 * 3600)
        if count > limit:
            raise RateLimitError(
                f"今日 AI 使用次数已达上限（{limit} 次），请明天再试",
                retry_after=3600,
            )
    except RateLimitError:
        raise
    except RedisError as exc:
        logger.warning("AI 配额检查失败(降级放行): user_id={} err={}", user_id, exc)