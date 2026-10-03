"""收藏接口（收藏/取消收藏动作挂在商品资源上，见 products.py）。"""

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import success
from app.services import favorite_service

router = APIRouter(prefix="/favorites", tags=["收藏"])


@router.get("", summary="我的收藏列表")
async def list_my_favorites(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    result = await favorite_service.list_my_favorites(db, current_user, page, page_size)
    return success(result.model_dump(mode="json"))
