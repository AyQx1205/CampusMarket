"""用户服务。"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.crud import user_crud
from app.models import User
from app.schemas.user import UserUpdate


async def update_profile(db: AsyncSession, user: User, data: UserUpdate) -> User:
    """修改个人资料（邮箱/手机号唯一性校验；不支持显式清空字段）。

    先查后写只用于友好提示；并发下最终由数据库唯一约束兜底，捕获
    IntegrityError 转为 409，避免 500。
    """
    fields = data.model_dump(exclude_unset=True, exclude_none=True)
    if "email" in fields and fields["email"] != user.email:
        if await user_crud.get_by_email(db, str(fields["email"])):
            raise ConflictError("该邮箱已被使用")
    if "phone" in fields and fields["phone"] != user.phone:
        if await user_crud.get_by_phone(db, str(fields["phone"])):
            raise ConflictError("该手机号已被使用")

    if not fields:
        return user

    for key, value in fields.items():
        setattr(user, key, value)
    try:
        await db.flush()
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ConflictError("邮箱或手机号已被其他账号使用") from None
    return user