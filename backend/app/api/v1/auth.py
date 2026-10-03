"""认证接口。"""

from fastapi import APIRouter

from app.api.deps import DbSession
from app.core.exceptions import success
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest
from app.schemas.user import UserMeOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", summary="注册")
async def register(db: DbSession, data: RegisterRequest) -> dict:
    user = await auth_service.register(db, data)
    return success(UserMeOut.model_validate(user).model_dump(mode="json"), "注册成功")


@router.post("/login", summary="登录（返回双 Token）")
async def login(db: DbSession, data: LoginRequest) -> dict:
    tokens = await auth_service.login(db, data.student_no, data.password)
    return success(tokens.model_dump(mode="json"), "登录成功")


@router.post("/refresh", summary="刷新双 Token（旧 refresh 立即作废）")
async def refresh(db: DbSession, data: RefreshRequest) -> dict:
    tokens = await auth_service.refresh_tokens(db, data.refresh_token)
    return success(tokens.model_dump(mode="json"))


@router.post("/logout", summary="登出（吊销 refresh token，幂等）")
async def logout(data: RefreshRequest) -> dict:
    await auth_service.logout(data.refresh_token)
    return success(None, "已退出登录")
