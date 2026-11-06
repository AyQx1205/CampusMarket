"""用户相关 Schema。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserBrief(BaseModel):
    """公开精简用户信息（商品/订单里嵌套展示用）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nickname: str
    avatar_url: str | None = None
    campus: str | None = None


class UserOut(UserBrief):
    """公开用户信息（不含学号/邮箱/手机号）。"""

    credit_score: int
    created_at: datetime


class UserMeOut(UserOut):
    """当前登录用户的完整信息（含私密字段，仅本人可见）。"""

    student_no: str
    email: str | None = None
    phone: str | None = None
    is_senior_mode: bool


class UserContact(UserBrief):
    """交易对手联系方式。

    只在「订单参与者」语境下返回（OrderDetailOut），不出现在公开商品页，
    避免把手机号/邮箱暴露给任意访客。
    """

    phone: str | None = None
    email: str | None = None
    credit_score: int


class UserUpdate(BaseModel):
    """PATCH /users/me 请求体。字段不传或为 null 表示不修改（不支持显式清空）。"""

    model_config = ConfigDict(extra="forbid")

    nickname: str | None = Field(None, min_length=1, max_length=64)
    email: EmailStr | None = Field(None, max_length=128)
    phone: str | None = Field(None, max_length=20, pattern=r"^1\d{10}$")
    avatar_url: str | None = Field(None, max_length=512)
    campus: str | None = Field(None, max_length=64)
    is_senior_mode: bool | None = None

    @field_validator("nickname", "campus", "avatar_url", "phone", mode="before")
    @classmethod
    def _strip_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip() or None
        return value

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value: object) -> object:
        """邮箱统一小写并去空格，避免大小写绕过唯一性检查。"""
        if isinstance(value, str):
            value = value.strip().lower()
            return value or None
        return value