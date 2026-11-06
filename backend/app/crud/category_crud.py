"""分类数据访问层。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category


async def get_by_id(db: AsyncSession, category_id: int) -> Category | None:
    return await db.get(Category, category_id)


async def list_all(db: AsyncSession) -> list[Category]:
    """全部分类，按 sort_order、id 升序（前端一次拉取做下拉选项）。"""
    result = await db.execute(
        select(Category).order_by(Category.sort_order.asc(), Category.id.asc())
    )
    return list(result.scalars().all())