"""分类服务。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import category_crud
from app.schemas.category import CategoryOut


async def list_categories(db: AsyncSession) -> list[CategoryOut]:
    """返回全部分类（前端用 id 提交 category_id，不再硬编码中文名）。"""
    rows = await category_crud.list_all(db)
    return [CategoryOut.model_validate(row) for row in rows]