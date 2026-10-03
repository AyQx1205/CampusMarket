"""缓存服务：商品详情缓存 + 热门商品榜（Redis）。

- key 一律引用 core.redis_client.RedisKeys 模板，本文件是唯一允许使用这些 key 的地方。
- 所有缓存操作降级容错：Redis 不可用时按未命中处理，不影响主交易流程。
"""

from loguru import logger
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.redis_client import RedisKeys, RedisTTL, get_redis


def _redis() -> Redis:
    return get_redis()


async def get_product_detail_json(product_id: int) -> str | None:
    """读取商品详情缓存（JSON 字符串），未命中/故障返回 None。"""
    try:
        return await _redis().get(RedisKeys.PRODUCT_DETAIL.format(product_id=product_id))
    except RedisError as exc:
        logger.warning("读取商品详情缓存失败(降级为未命中): {}", exc)
        return None


async def set_product_detail_json(product_id: int, detail_json: str) -> None:
    """写入商品详情缓存，TTL 300s。"""
    try:
        await _redis().set(
            RedisKeys.PRODUCT_DETAIL.format(product_id=product_id),
            detail_json,
            ex=RedisTTL.PRODUCT_DETAIL,
        )
    except RedisError as exc:
        logger.warning("写入商品详情缓存失败: {}", exc)


async def invalidate_product_detail(product_id: int) -> None:
    """商品更新/删除/收藏数变化时主动失效。"""
    try:
        await _redis().delete(RedisKeys.PRODUCT_DETAIL.format(product_id=product_id))
    except RedisError as exc:
        logger.warning("失效商品详情缓存失败: {}", exc)


async def incr_hot_score(product_id: int, delta: float = 1.0) -> None:
    """热门榜分数 +1（浏览时调用）。"""
    try:
        await _redis().zincrby(RedisKeys.PRODUCT_HOT, delta, str(product_id))
    except RedisError as exc:
        logger.warning("热门榜写入失败: {}", exc)


async def get_hot_product_ids(limit: int) -> list[int]:
    """热门榜 Top N 商品 id（分数从高到低）。"""
    try:
        members = await _redis().zrevrange(RedisKeys.PRODUCT_HOT, 0, limit - 1)
        return [int(m) for m in members]
    except RedisError as exc:
        logger.warning("热门榜读取失败: {}", exc)
        return []
