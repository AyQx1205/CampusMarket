"""全局配置：pydantic-settings 读取项目根目录 .env。

所有配置项集中在此，业务代码统一 `from app.core.config import settings`，
不允许散落各处自行读取环境变量。
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ---------- 应用基础 ----------
    PROJECT_NAME: str = "校园二手交易平台"
    ENVIRONMENT: Literal["dev", "test", "prod"] = "dev"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # ---------- 数据库 ----------
    DATABASE_URL: str = "postgresql+asyncpg://campus:campus2026@127.0.0.1:5432/campus_market"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False

    # ---------- Redis ----------
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50

    # ---------- JWT ----------
    JWT_SECRET_KEY: str = "dev-only-secret-change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---------- LLM（OpenAI 兼容接口，可切换 DeepSeek / 通义 / 智谱 / Ollama） ----------
    OPENAI_BASE_URL: str = "https://api.deepseek.com/v1"
    OPENAI_API_KEY: str = "sk-xxx"
    LLM_MODEL: str = "deepseek-chat"
    EMBEDDING_MODEL: str = "text-embedding-v3"
    LLM_TEMPERATURE: float = 0.7
    # 是否禁用 LLM 的 thinking/推理模式（Qwen 结构化输出场景建议 true）
    LLM_DISABLE_THINKING: bool = True

    # ---------- AI 会话记忆 ----------
    AI_MEMORY_TTL_HOURS: int = 24
    AI_MEMORY_MAX_ROUNDS: int = 20

    # ---------- CORS ----------
    # .env 中以 JSON 数组字符串书写，pydantic-settings 自动反序列化为 list[str]
    CORS_ORIGINS: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    """返回全局唯一的 Settings 实例（进程内缓存）。"""
    return Settings()


settings = get_settings()
