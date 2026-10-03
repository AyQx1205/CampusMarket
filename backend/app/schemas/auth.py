"""认证相关 Schema。"""

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    student_no: str = Field(min_length=4, max_length=32, description="学号，全局唯一")
    nickname: str = Field(min_length=1, max_length=64, description="昵称")
    password: str = Field(min_length=8, max_length=64, description="密码明文（仅传输，服务端只存哈希）")
    email: str | None = Field(None, max_length=128, description="邮箱，可选")
    phone: str | None = Field(None, max_length=20, pattern=r"^1\d{10}$", description="手机号，可选")
    campus: str | None = Field(None, max_length=64, description="校区，可选")


class LoginRequest(BaseModel):
    student_no: str = Field(description="学号")
    password: str = Field(description="密码")


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="access token 有效期（秒）")


class RefreshRequest(BaseModel):
    refresh_token: str
