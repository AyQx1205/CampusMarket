"""认证接口。"""

from fastapi import APIRouter, Request

from app.api.deps import DbSession
from app.core.config import settings
from app.core.exceptions import success
from app.core.rate_limit import client_ip, enforce_rate_limit
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest
from app.schemas.user import UserMeOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", summary="注册")
async def register(request: Request, db: DbSession, data: RegisterRequest) -> dict:
    await enforce_rate_limit(
        scope="register",
        identity=client_ip(request),
        limit=settings.REGISTER_RATE_LIMIT_PER_HOUR,
        window_seconds=3600,
    )
    user = await auth_service.register(db, data)
    return success(UserMeOut.model_validate(user).model_dump(mode="json"), "注册成功")


@router.post("/login", summary="登录（返回双 Token）")
async def login(request: Request, db: DbSession, data: LoginRequest) -> dict:
    # 按 IP 限流，配合「统一错误提示」抵御学号枚举与密码爆破
    await enforce_rate_limit(
        scope="login",
        identity=client_ip(request),
        limit=settings.LOGIN_RATE_LIMIT_PER_5MIN,
        window_seconds=300,
    )
    tokens = await auth_service.login(db, data.student_no, data.password)
    return success(tokens.model_dump(mode="json"), "登录成功")


@router.post("/refresh", summary="刷新双 Token（旧 refresh 立即作废）")
async def refresh(request: Request, db: DbSession, data: RefreshRequest) -> dict:
    await enforce_rate_limit(
        scope="refresh",
        identity=client_ip(request),
        limit=settings.REFRESH_RATE_LIMIT_PER_MINUTE,
        window_seconds=60,
    )
    tokens = await auth_service.refresh_tokens(db, data.refresh_token)
    return success(tokens.model_dump(mode="json"))


@router.post("/logout", summary="登出（吊销 refresh token，幂等）")
async def logout(data: RefreshRequest) -> dict:
    await auth_service.logout(data.refresh_token)
    return success(None, "已退出登录")