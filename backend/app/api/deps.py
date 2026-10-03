"""FastAPI 依赖：数据库会话 + 当前登录用户。"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
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


CurrentUser = Annotated[User, Depends(get_current_user)]
