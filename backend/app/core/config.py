"""全局配置：pydantic-settings 读取 backend/.env（固定路径，不依赖启动目录）。

所有配置项集中在此，业务代码统一 `from app.core.config import settings`，
不允许散落各处自行读取环境变量。

安全约定：
- JWT_SECRET_KEY 没有默认值，必须在 .env / 进程环境中显式提供（至少 32 字符）。
  `backend/.env.example` 提供了生成命令，复制后请替换为随机值。
- prod 环境启动时额外校验：禁止 DEBUG、禁止 CORS "*"、禁止默认数据库口令、
  禁止示例密钥，避免把开发配置直接带上线。
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 固定指向 backend/.env，避免从仓库根目录启动时读不到配置
_BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ---------- 应用基础 ----------
    PROJECT_NAME: str = "校园二手交易平台"
    ENVIRONMENT: Literal["dev", "test", "prod"] = "dev"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    # 仅当应用只接受可信反向代理流量时开启；直连公网时开启会被伪造 XFF 绕过限流
    TRUST_PROXY_HEADERS: bool = False

    # ---------- 数据库 ----------
    DATABASE_URL: str = "postgresql+asyncpg://campus:campus2026@127.0.0.1:5432/campus_market"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False

    # ---------- Redis ----------
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50
    # 秒；Redis 故障时快速失败（限流/缓存为旁路，不能拖死请求）
    REDIS_SOCKET_TIMEOUT: float = 3.0

    # ---------- JWT ----------
    # 必填：不提供安全的默认值，避免「默认密钥直接上线」这类事故
    JWT_SECRET_KEY: str = Field(
        min_length=32,
        description="JWT 签名密钥，至少 32 字符；生产环境请使用随机值",
    )
    JWT_ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---------- 登录 / 注册限流（Redis 固定窗口） ----------
    LOGIN_RATE_LIMIT_PER_5MIN: int = 10
    REGISTER_RATE_LIMIT_PER_HOUR: int = 5
    REFRESH_RATE_LIMIT_PER_MINUTE: int = 30

    # ---------- LLM（OpenAI 兼容接口，可切换 DeepSeek / 通义 / 智谱 / Ollama） ----------
    OPENAI_BASE_URL: str = "https://api.deepseek.com/v1"
    OPENAI_API_KEY: str = "sk-xxx"
    LLM_MODEL: str = "deepseek-chat"
    LLM_TEMPERATURE: float = 0.7
    LLM_TIMEOUT_SECONDS: int = 45
    LLM_MAX_TOKENS: int = 1024
    # 是否禁用 LLM 的 thinking/推理模式（Qwen 结构化输出场景建议 true）
    LLM_DISABLE_THINKING: bool = True
    # Agent 单轮最大工具调用轮数，防止模型陷入循环
    AI_MAX_TOOL_ROUNDS: int = 8
    # AI 写操作（下单/发布/改状态）默认关闭：需要用户在 UI 明确确认后再开启
    AI_ENABLE_WRITE_TOOLS: bool = False
    # 每用户 AI 调用配额（Redis 计数）
    AI_RATE_LIMIT_PER_MINUTE: int = 10
    AI_DAILY_QUOTA: int = 100

    # ---------- AI 会话记忆 ----------
    AI_MEMORY_TTL_HOURS: int = 24
    AI_MEMORY_MAX_ROUNDS: int = 20
    # 单条消息与单会话的最大字符数，防止 Redis 被超长内容撑爆
    AI_MEMORY_MAX_CHARS: int = 8000

    # ---------- CORS ----------
    # .env 中写 JSON 数组字符串，例如 ["http://localhost:5173"]
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @model_validator(mode="after")
    def _validate_production(self) -> "Settings":
        if self.ENVIRONMENT != "prod":
            return self

        if self.DEBUG:
            raise ValueError("生产环境禁止开启 DEBUG")
        if "*" in self.CORS_ORIGINS:
            raise ValueError("生产环境 CORS_ORIGINS 不能包含通配符 *")
        if self.DATABASE_URL == (
            "postgresql+asyncpg://campus:campus2026@127.0.0.1:5432/campus_market"
        ) or "campus2026" in self.DATABASE_URL:
            raise ValueError("生产环境请修改默认数据库连接串（含默认口令 campus2026）")
        lowered = self.JWT_SECRET_KEY.lower()
        if any(marker in lowered for marker in ("change-me", "please-generate", "dev-only")):
            raise ValueError("生产环境 JWT_SECRET_KEY 不能使用示例值，请生成随机密钥")
        return self


@lru_cache
def get_settings() -> Settings:
    """返回全局唯一的 Settings 实例（进程内缓存）。"""
    return Settings()


settings = get_settings()