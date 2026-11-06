"""商品服务：搜索 / 详情（缓存旁路）/ 发布 / 更新 / 状态 / 删除 / 热门榜。

事务约定：所有写操作在本层显式 commit，commit 成功后再失效缓存；
这样响应发出前数据已落库，也不会出现「缓存已删、事务又回滚」的脏读窗口。
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.crud import category_crud, order_crud, product_crud
from app.models import Product, User
from app.models.enums import ProductStatus
from app.schemas.common import Page
from app.schemas.product import (
    ProductCreate,
    ProductOut,
    ProductSearchParams,
    ProductStatusUpdate,
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
    浏览计数本身是写操作，需要显式提交才能落库。
    """
    if count_view:
        bumped = await product_crud.increment_view(db, product_id)
        if bumped:
            await cache_service.incr_hot_score(product_id)
            await db.commit()
        else:
            # 商品已不存在：顺手清掉可能残留的详情缓存
            await cache_service.invalidate_product_detail(product_id)
            raise NotFoundError("商品不存在")

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
    await db.commit()
    return ProductOut.model_validate(product)


async def _get_owned_product(
    db: AsyncSession, user: User, product_id: int, *, for_update: bool = False
) -> Product:
    getter = product_crud.get_by_id_for_update if for_update else product_crud.get_by_id
    product = await getter(db, product_id)
    if product is None:
        raise NotFoundError("商品不存在")
    if product.seller_id != user.id:
        raise ForbiddenError("只能操作自己发布的商品")
    return product


async def _assert_no_active_order(db: AsyncSession, product_id: int) -> None:
    if await order_crud.count_active_orders(db, product_id) > 0:
        raise ConflictError("该商品有进行中订单，请先在订单页处理")


async def update(
    db: AsyncSession, user: User, product_id: int, data: ProductUpdate
) -> ProductOut:
    # 行锁：与下单/状态流转互斥，避免编辑的同时商品被别人预订
    product = await _get_owned_product(db, user, product_id, for_update=True)
    if product.status in (ProductStatus.RESERVED, ProductStatus.SOLD):
        raise ConflictError("已预订/已售出的商品不能再编辑")
    await _assert_no_active_order(db, product_id)

    fields = data.model_dump(exclude_unset=True, exclude_none=True)
    if "category_id" in fields:
        if await category_crud.get_by_id(db, int(fields["category_id"])) is None:
            raise NotFoundError("分类不存在")

    if not fields:
        # 无字段可更新：提交空事务释放 FOR UPDATE 行锁（expire_on_commit=False，
        # 提交后仍可直接序列化，不会触发异步懒加载）
        await db.commit()
        return ProductOut.model_validate(product)

    # 价格一致性：无论只改 price、只改 original_price 还是两者都改，
    # 都要保证「原价 >= 现价」。exclude_none=True 清不掉原价，这里只做校验。
    new_price = fields.get("price", product.price)
    new_original = fields.get("original_price", product.original_price)
    if new_original is not None and new_original < new_price:
        raise ConflictError("原价不能低于售价")

    product = await product_crud.update_product(db, product, fields)
    await db.commit()
    await cache_service.invalidate_product_detail(product_id)
    return ProductOut.model_validate(product)


async def update_status(
    db: AsyncSession, user: User, product_id: int, data: ProductStatusUpdate
) -> ProductOut:
    """卖家手工上下架/标记已售。

    规则：
    - RESERVED 只能由下单流程写入，卖家家不能手工设置，也不能在预订中改动；
    - 有进行中订单时必须走订单状态流转（避免绕过买家）；
    - SOLD 是终态：已售出商品不能重新上架（如需再卖请重新发布）；
    - 同状态重复调用视为幂等成功。
    """
    product = await _get_owned_product(db, user, product_id, for_update=True)
    target = data.status

    if product.status == target:
        # 幂等：提交空事务释放行锁，返回当前值
        await db.commit()
        return ProductOut.model_validate(product)

    if product.status == ProductStatus.RESERVED:
        raise ConflictError("商品已被预订，请先在订单页处理订单")
    if product.status == ProductStatus.SOLD:
        raise ConflictError("已售出商品不能改回其它状态，如需再卖请重新发布")
    if await order_crud.count_active_orders(db, product_id) > 0:
        raise ConflictError("该商品有进行中订单，请先在订单页处理")

    product.status = target
    await db.commit()
    await cache_service.invalidate_product_detail(product_id)
    return ProductOut.model_validate(product)


async def delete(db: AsyncSession, user: User, product_id: int) -> None:
    product = await _get_owned_product(db, user, product_id, for_update=True)

    try:
        await product_crud.delete(db, product)
        await db.commit()
    except IntegrityError:
        # orders.product_id RESTRICT：已有交易记录的商品不允许物理删除
        await db.rollback()
        raise ConflictError("商品已有订单记录，无法删除，请改为下架") from None
    await cache_service.invalidate_product_detail(product_id)


async def hot(db: AsyncSession, limit: int = 10) -> list[ProductOut]:
    """热门榜：优先 Redis ZSet Top N；为空时兜底返回最新在售商品。"""
    ids = await cache_service.get_hot_product_ids(limit)
    if ids:
        products = await product_crud.get_many_by_ids(db, ids)
        by_id = {p.id: p for p in products}
        # 已下架/已售出的商品不进热门榜
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
    """某卖家发布的商品；status 传 None 表示不过滤（由路由层做可见性收敛）。"""
    items, total = await product_crud.list_by_seller(
        db, seller_id, status, page, page_size
    )
    return Page(
        items=[ProductOut.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )