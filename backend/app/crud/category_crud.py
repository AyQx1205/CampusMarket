"""分类数据访问层。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category


async def get_by_id(db: AsyncSession, category_id: int) -> Category | None:
    return await db.get(Category, category_id)
