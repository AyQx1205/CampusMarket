"""Redis key / TTL 契约：模板集中管理，TTL 与对应配置对齐。"""

from app.core.config import settings
from app.core.redis_client import RedisKeys, RedisTTL


def test_rate_limit_and_quota_key_templates() -> None:
    assert RedisKeys.RATE_LIMIT.format(scope="login", identity="127.0.0.1") == (
        "rate:login:127.0.0.1"
    )
    assert RedisKeys.AI_DAILY_QUOTA.format(user_id=7, date="20261106") == (
        "quota:ai:day:7:20261106"
    )


def test_auth_refresh_ttl_matches_token_lifetime() -> None:
    expected = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    assert RedisTTL.AUTH_REFRESH == expected


def test_ai_memory_ttl_matches_config() -> None:
    assert RedisTTL.AI_CHAT_MEMORY == settings.AI_MEMORY_TTL_HOURS * 3600