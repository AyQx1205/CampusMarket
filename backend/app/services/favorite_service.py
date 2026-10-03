"""收藏服务。"""

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
    if await favorite_crud.get(db, user.id, product_id):
        raise ConflictError("已收藏该商品")

    await favorite_crud.add(db, user.id, product_id)
    product.favorite_count += 1  # 冗余计数，随请求事务一起提交
    await cache_service.invalidate_product_detail(product_id)


async def remove_favorite(db: AsyncSession, user: User, product_id: int) -> None:
    favorite = await favorite_crud.get(db, user.id, product_id)
    if favorite is None:
        raise NotFoundError("尚未收藏该商品")

    await favorite_crud.remove(db, favorite)
    product = await product_crud.get_by_id(db, product_id)
    if product is not None and product.favorite_count > 0:
        product.favorite_count -= 1
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
