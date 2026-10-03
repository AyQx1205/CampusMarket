"""FastAPI 依赖：数据库会话 + 当前登录用户。"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BizException, UnauthorizedError
from app.core.security import decode_token
from app.crud import user_crud
from app.db.session import get_db
from app.models import User

# auto_error=False：未带 Authorization 头时拿到 None，由我们抛统一 401 响应体
_bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """解析 Bearer access token 并加载当前用户。"""
    if credentials is None:
        raise UnauthorizedError("请先登录")
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise UnauthorizedError("请使用 access token 访问")

    user = await user_crud.get_by_id(db, int(str(payload["sub"])))
    if user is None or not user.is_active:
        raise UnauthorizedError("用户不存在或已被禁用")
    return user


async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    """可选登录：匿名或凭证失效一律返回 None，不抛 401。

    供公开接口做「本人 / 他人」的可见性判断使用（如某人发布的商品）。
    这里刻意把过期/伪造 token 视为匿名而非报错，避免登录态过期
    的用户连公开列表都打不开。
    """
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials)
    except BizException:
        return None
    if payload.get("type") != "access":
        return None
    try:
        user_id = int(str(payload.get("sub")))
    except (TypeError, ValueError):
        return None

    user = await user_crud.get_by_id(db, user_id)
    if user is None or not user.is_active:
        return None
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
