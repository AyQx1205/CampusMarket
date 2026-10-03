"""用户相关 Schema。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserBrief(BaseModel):
    """公开精简用户信息（商品/订单里嵌套展示用）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nickname: str
    avatar_url: str | None = None
    campus: str | None = None


class UserOut(UserBrief):
    """公开用户信息。"""

    credit_score: int
    created_at: datetime


class UserMeOut(UserOut):
    """当前登录用户的完整信息（含私密字段，仅本人可见）。"""

    student_no: str
    email: str | None = None
    phone: str | None = None
    is_senior_mode: bool


class UserUpdate(BaseModel):
    """PATCH /users/me 请求体。字段不传或为 null 表示不修改（不支持显式清空）。"""

    nickname: str | None = Field(None, min_length=1, max_length=64)
    email: str | None = Field(None, max_length=128)
    phone: str | None = Field(None, max_length=20, pattern=r"^1\d{10}$")
    avatar_url: str | None = Field(None, max_length=512)
    campus: str | None = Field(None, max_length=64)
    is_senior_mode: bool | None = None
