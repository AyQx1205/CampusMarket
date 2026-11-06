"""认证相关 Schema。"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_no: str = Field(min_length=4, max_length=32, description="学号，全局唯一")
    nickname: str = Field(min_length=1, max_length=64, description="昵称")
    password: str = Field(min_length=8, max_length=64, description="密码明文（仅传输，服务端只存哈希）")
    email: EmailStr | None = Field(None, max_length=128, description="邮箱，可选")
    phone: str | None = Field(None, max_length=20, pattern=r"^1\d{10}$", description="手机号，可选")
    campus: str | None = Field(None, max_length=64, description="校区，可选")

    @field_validator("student_no", "nickname", "campus", mode="before")
    @classmethod
    def _strip_text(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value: object) -> object:
        """邮箱统一小写并去空格，避免大小写绕过唯一性检查。"""
        if isinstance(value, str):
            value = value.strip().lower()
            return value or None
        return value


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_no: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=64)

    @field_validator("student_no", mode="before")
    @classmethod
    def _strip_student_no(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="access token 有效期（秒）")


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(min_length=1, max_length=4096)