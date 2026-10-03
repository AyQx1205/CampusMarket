"""用户数据访问层。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
    return await db.get(User, user_id)


async def get_by_student_no(db: AsyncSession, student_no: str) -> User | None:
    result = await db.execute(select(User).where(User.student_no == student_no))
    return result.scalar_one_or_none()


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_by_phone(db: AsyncSession, phone: str) -> User | None:
    result = await db.execute(select(User).where(User.phone == phone))
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    *,
    student_no: str,
    nickname: str,
    hashed_password: str,
    email: str | None = None,
    phone: str | None = None,
    campus: str | None = None,
) -> User:
    user = User(
        student_no=student_no,
        nickname=nickname,
        hashed_password=hashed_password,
        email=email,
        phone=phone,
        campus=campus,
    )
    db.add(user)
    await db.flush()
    return user
