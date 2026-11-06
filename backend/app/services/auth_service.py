"""认证服务：注册 / 登录 / 刷新 / 登出（Access + Refresh 双 Token）。

Refresh Token 白名单存 Redis（auth:refresh:{jti}）：
- 登录写入、刷新旋转（GETDEL 原子消费旧 jti）、登出吊销。
- 认证链路对 Redis 故障采取 fail-closed（快速失败，返回 503），
  与缓存「降级为未命中」的策略不同：登录态不能靠猜。

事务约定：写操作在本层显式 commit（请求级 get_db 只负责回滚/关闭），
保证响应发出前事务已经落库，避免「200 已返回但 commit 失败」。
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    ServiceUnavailableError,
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

# 用户不存在时也跑一次哈希校验，避免通过响应时间枚举学号。
# 进程启动时生成一次，不在请求路径里重复计算。
_DUMMY_PASSWORD_HASH = hash_password("dummy-password-for-timing-equalization")


async def register(db: AsyncSession, data: RegisterRequest) -> User:
    """注册新用户（唯一性冲突抛 409）。

    先查一次是为了给出友好提示；并发下仍可能双双通过，最终由数据库
    唯一约束兜底，这里把 IntegrityError 转成 409，避免冒泡成 500。
    """
    if await user_crud.get_by_student_no(db, data.student_no):
        raise ConflictError("该学号已注册")
    if data.email and await user_crud.get_by_email(db, data.email):
        raise ConflictError("该邮箱已被使用")
    if data.phone and await user_crud.get_by_phone(db, data.phone):
        raise ConflictError("该手机号已被使用")

    try:
        user = await user_crud.create(
            db,
            student_no=data.student_no,
            nickname=data.nickname,
            hashed_password=hash_password(data.password),
            email=data.email,
            phone=data.phone,
            campus=data.campus,
        )
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ConflictError("学号/邮箱/手机号已被注册，请直接登录") from None
    return user


async def _issue_tokens(user: User) -> TokenPair:
    """签发双 Token，refresh 的 jti 写入 Redis 白名单。"""
    access_token = create_access_token(user.id)
    refresh_token, jti = create_refresh_token(user.id)
    try:
        await get_redis().setex(
            RedisKeys.AUTH_REFRESH.format(jti=jti), RedisTTL.AUTH_REFRESH, str(user.id)
        )
    except Exception as exc:
        # 认证依赖 Redis：写不进白名单就不能签发，否则 refresh 必然失败
        raise ServiceUnavailableError("登录服务暂时不可用，请稍后再试") from exc
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def login(db: AsyncSession, student_no: str, password: str) -> TokenPair:
    user = await user_crud.get_by_student_no(db, student_no)
    # 用户不存在与密码错误返回同一提示并消耗相近时间，避免枚举学号
    if user is None:
        verify_password(password, _DUMMY_PASSWORD_HASH)
        raise UnauthorizedError("学号或密码错误")
    if not verify_password(password, user.hashed_password):
        raise UnauthorizedError("学号或密码错误")
    if not user.is_active:
        raise ForbiddenError("账号已被禁用，请联系管理员")
    return await _issue_tokens(user)


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> TokenPair:
    """刷新双 Token（旋转：旧 refresh 原子消费，只能使用一次）。

    GETDEL 把「读取白名单 -> 删除」合并成一条命令，避免并发刷新时
    两个请求都读到旧 jti、各自签发一对新 Token（重放窗口）。
    """
    payload = decode_token(refresh_token)  # 过期/伪造统一抛 401
    if payload.get("type") != "refresh":
        raise TokenInvalidError

    jti = str(payload["jti"])
    try:
        whitelist_user_id = await get_redis().getdel(
            RedisKeys.AUTH_REFRESH.format(jti=jti)
        )
    except Exception as exc:
        raise ServiceUnavailableError("认证服务暂时不可用，请稍后再试") from exc
    if whitelist_user_id is None:
        # 不在白名单 = 已登出/已旋转/被吊销
        raise UnauthorizedError("登录状态已失效，请重新登录")
    if str(payload["sub"]) != str(whitelist_user_id):
        raise TokenInvalidError

    try:
        user_id = int(str(payload["sub"]))
    except (TypeError, ValueError) as exc:
        raise TokenInvalidError from exc
    user = await user_crud.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("用户不存在或已被禁用")

    return await _issue_tokens(user)


async def logout(refresh_token: str) -> None:
    """登出：吊销 refresh token。幂等 —— token 无效也返回成功。"""
    try:
        payload = decode_token(refresh_token)
    except Exception:
        # 无效/过期 token 视为已登出
        return
    if payload.get("type") == "refresh":
        try:
            await get_redis().delete(RedisKeys.AUTH_REFRESH.format(jti=str(payload["jti"])))
        except Exception as exc:
            # 本地登录态仍会被前端清掉；提示用户服务端吊销暂未完成
            raise ServiceUnavailableError("登出服务暂时不可用，请稍后重试") from exc