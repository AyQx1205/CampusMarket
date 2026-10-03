"""收藏服务。"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.crud import favorite_crud, product_crud
from app.models import User
from app.schemas.common import Page
from app.schemas.favorite import FavoriteOut
from app.services import cache_service


async def add_favorite(db: AsyncSession, user: User, product_id: int) -> None:
    product = await product_crud.get_by_id(db, product_id)
    if product is None:
        raise NotFoundError("商品不存在")
    # 先查一次给出干净提示；并发下仍可能双双通过，由唯一约束兜底（见下）
    if await favorite_crud.get(db, user.id, product_id):
        raise ConflictError("已收藏该商品")

    try:
        await favorite_crud.add(db, user.id, product_id)
    except IntegrityError:
        # (user_id, product_id) 唯一约束冲突 = 并发重复收藏，
        # 转成业务冲突（409）而不是让 IntegrityError 冒泡成 500
        raise ConflictError("已收藏该商品") from None

    await product_crud.adjust_favorite_count(db, product_id, 1)
    await cache_service.invalidate_product_detail(product_id)


async def remove_favorite(db: AsyncSession, user: User, product_id: int) -> None:
    favorite = await favorite_crud.get(db, user.id, product_id)
    if favorite is None:
        raise NotFoundError("尚未收藏该商品")

    await favorite_crud.remove(db, favorite)
    await product_crud.adjust_favorite_count(db, product_id, -1)
    await cache_service.invalidate_product_detail(product_id)


async def list_my_favorites(
    db: AsyncSession, user: User, page: int, page_size: int
) -> Page[FavoriteOut]:
    items, total = await favorite_crud.list_by_user(db, user.id, page, page_size)
    return Page(
        items=[FavoriteOut.model_validate(f) for f in items],
        total=total,
        page=page,
        page_size=page_size,
    )
