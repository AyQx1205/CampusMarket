"""用户接口。"""

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession, OptionalUser
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
    current_user: OptionalUser,
    user_id: int,
    status: ProductStatus | None = Query(
        None, description="商品状态；不传时本人可见全部（含下架/已售），他人仅见在售"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    if await user_crud.get_by_id(db, user_id) is None:
        raise NotFoundError("用户不存在")
    # 默认可见性：本人（「我的商品」管理页）需要看到下架/已售等全部状态，
    # 否则无法重新上架；他人只看在售，避免暴露卖家主动下架的商品
    if status is None and (current_user is None or current_user.id != user_id):
        status = ProductStatus.ON_SALE
    result = await product_service.list_seller_products(
        db, user_id, status, page, page_size
    )
    return success(result.model_dump(mode="json"))
