"""配置安全校验：生产环境不允许把开发默认值带上线。"""

import pytest
from pydantic import ValidationError

from app.core.config import Settings

_SAFE_PROD = {
    "ENVIRONMENT": "prod",
    "DATABASE_URL": "postgresql+asyncpg://campus_app:strong-password@db.internal:5432/campus_market",
    "JWT_SECRET_KEY": "a" * 48,
}


def test_prod_accepts_hardened_config() -> None:
    settings = Settings(_env_file=None, **_SAFE_PROD)
    assert settings.DEBUG is False
    assert "*" not in settings.CORS_ORIGINS


def test_prod_rejects_debug() -> None:
    with pytest.raises(ValidationError, match="DEBUG"):
        Settings(_env_file=None, **{**_SAFE_PROD, "DEBUG": True})


def test_prod_rejects_wildcard_cors() -> None:
    with pytest.raises(ValidationError, match="CORS"):
        Settings(_env_file=None, **{**_SAFE_PROD, "CORS_ORIGINS": ["*"]})


def test_prod_rejects_default_database_credentials() -> None:
    with pytest.raises(ValidationError, match="数据库"):
        Settings(
            _env_file=None,
            **{
                **_SAFE_PROD,
                "DATABASE_URL": "postgresql+asyncpg://campus:campus2026@127.0.0.1:5432/campus_market",
            },
        )


def test_prod_rejects_example_jwt_secret() -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(
            _env_file=None,
            **{
                **_SAFE_PROD,
                "JWT_SECRET_KEY": "please-generate-a-random-secret-at-least-32-chars",
            },
        )


def test_jwt_secret_is_required_and_long_enough() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, ENVIRONMENT="test", JWT_SECRET_KEY="too-short")