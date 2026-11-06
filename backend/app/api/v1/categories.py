"""分类接口（公开只读）。"""

from fastapi import APIRouter

from app.api.deps import DbSession
from app.core.exceptions import success
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["分类"])


@router.get("", summary="全部分类（发布/筛选下拉使用）")
async def list_categories(db: DbSession) -> dict:
    items = await category_service.list_categories(db)
    return success([item.model_dump(mode="json") for item in items])