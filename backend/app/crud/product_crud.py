"""商品数据访问层。"""

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product
from app.models.enums import ProductStatus
from app.schemas.product import ProductSearchParams, ProductSort

_ORDER_BY: dict[ProductSort, object] = {
    ProductSort.LATEST: Product.created_at.desc(),
    ProductSort.PRICE_ASC: Product.price.asc(),
    ProductSort.PRICE_DESC: Product.price.desc(),
    ProductSort.HOTTEST: Product.view_count.desc(),
}


async def get_by_id(db: AsyncSession, product_id: int) -> Product | None:
    return await db.get(Product, product_id)


def _apply_filters(stmt: select, params: ProductSearchParams) -> select:
    if params.keyword:
        # ilike '%kw%' 可命中 pg_trgm GIN 索引（gin_trgm_ops）
        kw = f"%{params.keyword}%"
        stmt = stmt.where(or_(Product.title.ilike(kw), Product.description.ilike(kw)))
    if params.category_id is not None:
        stmt = stmt.where(Product.category_id == params.category_id)
    if params.min_price is not None:
        stmt = stmt.where(Product.price >= params.min_price)
    if params.max_price is not None:
        stmt = stmt.where(Product.price <= params.max_price)
    if params.campus:
        stmt = stmt.where(Product.campus == params.campus)
    if params.condition is not None:
        stmt = stmt.where(Product.condition == params.condition)
    if params.status is not None:
        stmt = stmt.where(Product.status == params.status)
    return stmt


async def search(
    db: AsyncSession, params: ProductSearchParams
) -> tuple[list[Product], int]:
    """按条件搜索商品，返回 (当前页数据, 总数)。"""
    stmt = _apply_filters(select(Product), params).order_by(_ORDER_BY[params.sort])
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    result = await db.execute(
        stmt.offset((params.page - 1) * params.page_size).limit(params.page_size)
    )
    return list(result.scalars().all()), total


async def create(db: AsyncSession, **fields: object) -> Product:
    product = Product(**fields)
    db.add(product)
    await db.flush()
    return product


# 注意：不能用 update 作函数名——会覆盖顶部 from sqlalchemy import update，
# 导致 increment_view 里的 update(Product) 语句调用变成本函数（500 根因）
async def update_product(db: AsyncSession, product: Product, fields: dict[str, object]) -> Product:
    for key, value in fields.items():
        setattr(product, key, value)
    await db.flush()
    return product


async def delete(db: AsyncSession, product: Product) -> None:
    await db.delete(product)
    # 提前 flush 触发 orders 表 RESTRICT 外键约束，
    # 把"已有订单不能删"转成业务冲突异常，而不是请求提交时的 500
    await db.flush()


async def increment_view(db: AsyncSession, product_id: int) -> None:
    """浏览量 +1（原子自增，不加载 ORM 对象）。"""
    await db.execute(
        update(Product)
        .where(Product.id == product_id)
        .values(view_count=Product.view_count + 1)
    )


async def list_by_seller(
    db: AsyncSession,
    seller_id: int,
    status: ProductStatus | None,
    page: int,
    page_size: int,
) -> tuple[list[Product], int]:
    stmt = select(Product).where(Product.seller_id == seller_id)
    if status is not None:
        stmt = stmt.where(Product.status == status)
    stmt = stmt.order_by(Product.created_at.desc())
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().all()), total


async def get_many_by_ids(db: AsyncSession, ids: list[int]) -> list[Product]:
    if not ids:
        return []
    result = await db.execute(select(Product).where(Product.id.in_(ids)))
    return list(result.scalars().all())


async def list_latest_on_sale(db: AsyncSession, limit: int) -> list[Product]:
    """最新在售商品（热门榜 ZSet 为空时的兜底数据源）。"""
    result = await db.execute(
        select(Product)
        .where(Product.status == ProductStatus.ON_SALE)
        .order_by(Product.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
