"""商品服务：搜索 / 详情（缓存旁路）/ 发布 / 更新 / 删除 / 热门榜。"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.crud import category_crud, product_crud
from app.models import Product, User
from app.models.enums import ProductStatus
from app.schemas.common import Page
from app.schemas.product import (
    ProductCreate,
    ProductOut,
    ProductSearchParams,
    ProductUpdate,
)
from app.services import cache_service


async def search(db: AsyncSession, params: ProductSearchParams) -> Page[ProductOut]:
    items, total = await product_crud.search(db, params)
    return Page(
        items=[ProductOut.model_validate(p) for p in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
    )


async def get_detail(
    db: AsyncSession, product_id: int, *, count_view: bool = True
) -> ProductOut:
    """商品详情：缓存旁路（先读 Redis，未命中回源 PG 并回写）。

    count_view=True 时浏览量 +1 并写热门 ZSet；缓存里的 view_count 允许
    短暂滞后（TTL 300s），符合商品场景的一致性要求。
    """
    if count_view:
        await product_crud.increment_view(db, product_id)
        await cache_service.incr_hot_score(product_id)

    cached = await cache_service.get_product_detail_json(product_id)
    if cached:
        try:
            return ProductOut.model_validate_json(cached)
        except ValueError:
            # 缓存内容损坏：失效后回源
            await cache_service.invalidate_product_detail(product_id)

    product = await product_crud.get_by_id(db, product_id)
    if product is None:
        raise NotFoundError("商品不存在")
    detail = ProductOut.model_validate(product)
    await cache_service.set_product_detail_json(product_id, detail.model_dump_json())
    return detail


async def create(db: AsyncSession, seller: User, data: ProductCreate) -> ProductOut:
    if data.category_id is not None:
        if await category_crud.get_by_id(db, data.category_id) is None:
            raise NotFoundError("分类不存在")

    product = await product_crud.create(
        db,
        seller_id=seller.id,
        title=data.title,
        description=data.description,
        price=data.price,
        original_price=data.original_price,
        condition=data.condition,
        category_id=data.category_id,
        images=data.images,
        campus=data.campus or seller.campus,  # 校区缺省继承卖家
    )
    return ProductOut.model_validate(product)


async def update(
    db: AsyncSession, user: User, product_id: int, data: ProductUpdate
) -> ProductOut:
    product = await product_crud.get_by_id(db, product_id)
    if product is None:
        raise NotFoundError("商品不存在")
    if product.seller_id != user.id:
        raise ForbiddenError("只能修改自己发布的商品")

    fields = data.model_dump(exclude_unset=True, exclude_none=True)
    if "category_id" in fields:
        if await category_crud.get_by_id(db, int(fields["category_id"])) is None:
            raise NotFoundError("分类不存在")

    product = await product_crud.update_product(db, product, fields)
    await cache_service.invalidate_product_detail(product_id)
    return ProductOut.model_validate(product)


async def delete(db: AsyncSession, user: User, product_id: int) -> None:
    product = await product_crud.get_by_id(db, product_id)
    if product is None:
        raise NotFoundError("商品不存在")
    if product.seller_id != user.id:
        raise ForbiddenError("只能删除自己发布的商品")

    try:
        await product_crud.delete(db, product)
    except IntegrityError:
        # orders.product_id RESTRICT：已有交易记录的商品不允许物理删除
        raise ConflictError("商品已有订单记录，无法删除，请改为下架")
    await cache_service.invalidate_product_detail(product_id)


async def hot(db: AsyncSession, limit: int = 10) -> list[ProductOut]:
    """热门榜：优先 Redis ZSet Top N；为空时兜底返回最新在售商品。"""
    ids = await cache_service.get_hot_product_ids(limit)
    if ids:
        products = await product_crud.get_many_by_ids(db, ids)
        by_id = {p.id: p for p in products}
        ordered = [ProductOut.model_validate(by_id[i]) for i in ids if i in by_id]
        if ordered:
            return ordered

    latest = await product_crud.list_latest_on_sale(db, limit)
    return [ProductOut.model_validate(p) for p in latest]


async def list_seller_products(
    db: AsyncSession,
    seller_id: int,
    status: ProductStatus | None,
    page: int,
    page_size: int,
) -> Page[ProductOut]:
    """某卖家发布的商品；status 传 None 表示不过滤（返回全部状态）。"""
    items, total = await product_crud.list_by_seller(
        db, seller_id, status, page, page_size
    )
    return Page(
        items=[ProductOut.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )
