"""用户接口。"""

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import NotFoundError, success
from app.crud import user_crud
from app.models.enums import ProductStatus
from app.schemas.product import ProductOut
from app.schemas.user import UserMeOut, UserUpdate
from app.services import product_service, user_service

router = APIRouter(prefix="/users", tags=["用户"])


@router.get("/me", summary="我的信息")
async def get_me(current_user: CurrentUser) -> dict:
    return success(UserMeOut.model_validate(current_user).model_dump(mode="json"))


@router.patch("/me", summary="修改我的信息")
async def update_me(
    db: DbSession, current_user: CurrentUser, data: UserUpdate
) -> dict:
    user = await user_service.update_profile(db, current_user, data)
    return success(UserMeOut.model_validate(user).model_dump(mode="json"))


@router.get("/{user_id}/products", summary="某人发布的商品")
async def list_user_products(
    db: DbSession,
    user_id: int,
    status: ProductStatus = Query(ProductStatus.ON_SALE, description="商品状态"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    if await user_crud.get_by_id(db, user_id) is None:
        raise NotFoundError("用户不存在")
    result = await product_service.list_seller_products(
        db, user_id, status, page, page_size
    )
    return success(result.model_dump(mode="json"))
