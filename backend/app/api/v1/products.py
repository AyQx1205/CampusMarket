"""商品接口。"""

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import success
from app.schemas.product import (
    ProductCreate,
    ProductSearchParams,
    ProductUpdate,
)
from app.services import favorite_service, product_service

router = APIRouter(prefix="/products", tags=["商品"])

# 注意：/hot 必须注册在 /{product_id} 之前，否则会被路径参数吞掉


@router.get("", summary="商品搜索（关键词/分类/价格/校区/排序 + 分页）")
async def search_products(
    db: DbSession,
    params: Annotated[ProductSearchParams, Query()],
) -> dict:
    result = await product_service.search(db, params)
    return success(result.model_dump(mode="json"))


@router.get("/hot", summary="热门商品榜（Redis ZSet Top N）")
async def hot_products(
    db: DbSession, limit: int = Query(10, ge=1, le=50)
) -> dict:
    items = await product_service.hot(db, limit)
    return success([p.model_dump(mode="json") for p in items])


@router.post("", summary="发布商品")
async def create_product(
    db: DbSession, current_user: CurrentUser, data: ProductCreate
) -> dict:
    detail = await product_service.create(db, current_user, data)
    return success(detail.model_dump(mode="json"), "发布成功")


@router.get("/{product_id}", summary="商品详情（浏览量 +1，缓存旁路）")
async def get_product(db: DbSession, product_id: int) -> dict:
    detail = await product_service.get_detail(db, product_id)
    return success(detail.model_dump(mode="json"))


@router.patch("/{product_id}", summary="修改商品（仅卖家）")
async def update_product(
    db: DbSession, current_user: CurrentUser, product_id: int, data: ProductUpdate
) -> dict:
    detail = await product_service.update(db, current_user, product_id, data)
    return success(detail.model_dump(mode="json"))


@router.delete("/{product_id}", summary="删除商品（仅卖家，有订单时拒绝）")
async def delete_product(
    db: DbSession, current_user: CurrentUser, product_id: int
) -> dict:
    await product_service.delete(db, current_user, product_id)
    return success(None, "删除成功")


@router.post("/{product_id}/favorite", summary="收藏商品")
async def add_favorite(
    db: DbSession, current_user: CurrentUser, product_id: int
) -> dict:
    await favorite_service.add_favorite(db, current_user, product_id)
    return success(None, "收藏成功")


@router.delete("/{product_id}/favorite", summary="取消收藏")
async def remove_favorite(
    db: DbSession, current_user: CurrentUser, product_id: int
) -> dict:
    await favorite_service.remove_favorite(db, current_user, product_id)
    return success(None, "已取消收藏")
