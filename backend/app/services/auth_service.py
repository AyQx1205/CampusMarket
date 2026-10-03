"""认证服务：注册 / 登录 / 刷新 / 登出（Access + Refresh 双 Token）。

Refresh Token 白名单存 Redis（auth:refresh:{jti}）：
- 登录写入、刷新旋转（旧 jti 删除）、登出吊销。
- 认证链路对 Redis 故障采取 fail-closed（快速失败），与缓存降级策略不同。
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    TokenInvalidError,
    UnauthorizedError,
)
from app.core.redis_client import RedisKeys, RedisTTL, get_redis
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.crud import user_crud
from app.models import User
from app.schemas.auth import RegisterRequest, TokenPair


async def register(db: AsyncSession, data: RegisterRequest) -> User:
    """注册新用户（唯一性冲突抛 409）。"""
    if await user_crud.get_by_student_no(db, data.student_no):
        raise ConflictError("该学号已注册")
    if data.email and await user_crud.get_by_email(db, data.email):
        raise ConflictError("该邮箱已被使用")
    if data.phone and await user_crud.get_by_phone(db, data.phone):
        raise ConflictError("该手机号已被使用")

    return await user_crud.create(
        db,
        student_no=data.student_no,
        nickname=data.nickname,
        hashed_password=hash_password(data.password),
        email=data.email,
        phone=data.phone,
        campus=data.campus,
    )


async def _issue_tokens(user: User) -> TokenPair:
    """签发双 Token，refresh 的 jti 写入 Redis 白名单。"""
    access_token = create_access_token(user.id)
    refresh_token, jti = create_refresh_token(user.id)
    await get_redis().setex(
        RedisKeys.AUTH_REFRESH.format(jti=jti), RedisTTL.AUTH_REFRESH, str(user.id)
    )
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def login(db: AsyncSession, student_no: str, password: str) -> TokenPair:
    user = await user_crud.get_by_student_no(db, student_no)
    # 用户不存在与密码错误返回同一提示，避免枚举学号
    if user is None or not verify_password(password, user.hashed_password):
        raise UnauthorizedError("学号或密码错误")
    if not user.is_active:
        raise ForbiddenError("账号已被禁用，请联系管理员")
    return await _issue_tokens(user)


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> TokenPair:
    """刷新双 Token（旋转：旧 refresh 立即作废）。"""
    payload = decode_token(refresh_token)  # 过期/伪造统一抛 401
    if payload.get("type") != "refresh":
        raise TokenInvalidError

    jti = str(payload["jti"])
    whitelist_user_id = await get_redis().get(RedisKeys.AUTH_REFRESH.format(jti=jti))
    if whitelist_user_id is None:
        # 不在白名单 = 已登出/已旋转/被吊销
        raise UnauthorizedError("登录状态已失效，请重新登录")
    if str(payload["sub"]) != str(whitelist_user_id):
        raise TokenInvalidError

    user = await user_crud.get_by_id(db, int(str(payload["sub"])))
    if user is None or not user.is_active:
        raise UnauthorizedError("用户不存在或已被禁用")

    await get_redis().delete(RedisKeys.AUTH_REFRESH.format(jti=jti))
    return await _issue_tokens(user)


async def logout(refresh_token: str) -> None:
    """登出：吊销 refresh token。幂等 —— token 无效也返回成功。"""
    try:
        payload = decode_token(refresh_token)
    except Exception:
        # 无效/过期 token 视为已登出
        return
    if payload.get("type") == "refresh":
        await get_redis().delete(RedisKeys.AUTH_REFRESH.format(jti=str(payload["jti"])))
