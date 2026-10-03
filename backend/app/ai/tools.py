"""AI Agent 工具集。

- 全部 @tool 定义；`config: RunnableConfig` 参数由运行时注入（不暴露给 LLM），
  configurable 中携带 db（AsyncSession）与 user（当前登录用户），由 /ai/chat 传入。
- 工具内部只调用 service 层（不走 HTTP），保证可单测。
- 返回值统一为 JSON 字符串（ensure_ascii=False），便于 LLM 阅读与测试断言。
- 业务冲突（BizException）原样抛出，Agent 会把 message 转述给用户。
"""

import json
from decimal import Decimal
from typing import Any, Literal, Optional

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chains.price_advisor import advise_price
from app.ai.chains.qa_chain import answer_rules_question
from app.models import User
from app.models.enums import ProductCondition, ProductStatus
from app.schemas.order import OrderCreate
from app.schemas.product import (
    ProductCreate,
    ProductSearchParams,
    ProductSort,
    ProductUpdate,
)
from app.services import favorite_service, order_service, product_service

# 传给 LLM 的商品摘要字段，控制上下文长度
_BRIEF_FIELDS = ("id", "title", "price", "campus", "status", "condition", "view_count")


def _ctx(config: RunnableConfig) -> tuple[AsyncSession, User]:
    ctx = config.get("configurable") or {}
    return ctx["db"], ctx["user"]


def _dump(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _brief(products: list) -> list[dict[str, Any]]:
    return [{f: getattr(p, f) for f in _BRIEF_FIELDS} for p in products]


# ==================== 买家工具 ====================


@tool
async def search_products(
    config: RunnableConfig,
    keyword: str = "",
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    campus: str = "",
    sort: Literal["latest", "price_asc", "price_desc", "hottest"] = "latest",
    page: int = 1,
) -> str:
    """搜索平台在售商品。可按关键词、价格区间（元）、校区筛选和排序，帮买家快速找货。"""
    db, _ = _ctx(config)
    params = ProductSearchParams(
        keyword=keyword or None,
        min_price=Decimal(str(min_price)) if min_price is not None else None,
        max_price=Decimal(str(max_price)) if max_price is not None else None,
        campus=campus or None,
        sort=ProductSort(sort),
        page=max(1, page),
        page_size=10,
    )
    result = await product_service.search(db, params)
    return _dump(
        {
            "total": result.total,
            "page": result.page,
            "items": [item.model_dump(mode="json", include=_BRIEF_FIELDS) for item in result.items],
        }
    )


@tool
async def get_product_detail(config: RunnableConfig, product_id: int) -> str:
    """查看商品详情（完整描述、图片、卖家信息）。给用户展示商品或下单前确认时使用。"""
    db, _ = _ctx(config)
    # count_view=False：助手内嵌预览不重复计浏览量，用户打开详情页才计数
    detail = await product_service.get_detail(db, product_id, count_view=False)
    return _dump(detail.model_dump(mode="json"))


@tool
async def create_order(
    config: RunnableConfig,
    product_id: int,
    trade_location: str = "",
    remark: str = "",
) -> str:
    """以当前用户（买家）身份对商品下单。下单后商品转为「已预订」，金额按商品现价快照。"""
    db, user = _ctx(config)
    order = await order_service.create_order(
        db, user, OrderCreate(product_id=product_id, trade_location=trade_location or None, remark=remark or None)
    )
    return _dump({"order_id": order.id, "order_no": order.order_no, "amount": str(order.amount), "status": order.status.value})


@tool
async def add_favorite(config: RunnableConfig, product_id: int) -> str:
    """收藏商品，之后可在「我的收藏」里找到。"""
    db, user = _ctx(config)
    await favorite_service.add_favorite(db, user, product_id)
    return _dump({"ok": True, "message": "收藏成功"})


@tool
async def list_my_orders(
    config: RunnableConfig,
    role: Literal["buyer", "seller", "all"] = "all",
) -> str:
    """查询当前用户的订单（role=buyer 我买到的 / seller 我卖出的 / all 全部）。"""
    db, user = _ctx(config)
    role_arg: Literal["buyer", "seller"] | None = None if role == "all" else role
    result = await order_service.list_my_orders(db, user, role_arg, page=1, page_size=10)
    return _dump(
        {
            "total": result.total,
            "orders": [
                {
                    "id": o.id,
                    "order_no": o.order_no,
                    "amount": str(o.amount),
                    "status": o.status.value,
                    "product": o.product.title if o.product else None,
                    "buyer_id": o.buyer_id,
                    "seller_id": o.seller_id,
                }
                for o in result.items
            ],
        }
    )


# ==================== 卖家工具 ====================


@tool
async def create_listing(
    config: RunnableConfig,
    title: str,
    price: float,
    condition: Literal["brand_new", "like_new", "lightly_used", "heavily_used"],
    description: str = "",
    images: Optional[list[str]] = None,
) -> str:
    """以当前用户（卖家）身份发布商品。发布前应先与用户确认标题、价格、成色与描述。"""
    db, user = _ctx(config)
    product = await product_service.create(
        db,
        user,
        ProductCreate(
            title=title,
            description=description or None,
            price=Decimal(str(price)).quantize(Decimal("0.01")),
            condition=ProductCondition(condition),
            images=images or [],
        ),
    )
    return _dump({"product_id": product.id, "title": product.title, "price": str(product.price), "status": product.status.value})


@tool
async def list_my_products(config: RunnableConfig) -> str:
    """查看当前用户（卖家）自己发布的商品列表及状态。"""
    db, user = _ctx(config)
    # 服务层标注为 ProductStatus；传 None 时运行时等价于"不过滤状态"（crud 支持），用于返回全部
    result = await product_service.list_seller_products(db, user.id, None, page=1, page_size=20)  # type: ignore[arg-type]
    return _dump({"total": result.total, "items": [i.model_dump(mode="json", include=_BRIEF_FIELDS) for i in result.items]})


@tool
async def update_my_product_status(
    config: RunnableConfig,
    product_id: int,
    status: Literal["on_sale", "reserved", "sold", "off_shelf"],
) -> str:
    """修改自己商品的状态（重新上架 on_sale / 下架 off_shelf / 已售出 sold）。仅限卖家本人。"""
    db, user = _ctx(config)
    detail = await product_service.update(
        db, user, product_id, ProductUpdate(status=ProductStatus(status))
    )
    return _dump({"product_id": detail.id, "status": detail.status.value})


# ==================== 个人工具 ====================


@tool
async def get_my_profile(config: RunnableConfig) -> str:
    """查看当前用户的个人资料（学号、昵称、校区、信用分、是否老年模式等）。"""
    _, user = _ctx(config)
    return _dump(
        {
            "id": user.id,
            "nickname": user.nickname,
            "campus": user.campus,
            "credit_score": user.credit_score,
            "is_senior_mode": user.is_senior_mode,
        }
    )


# ==================== 平台规则 / 估价 ====================


@tool
async def qa_platform_rules(config: RunnableConfig, question: str) -> str:
    """平台规则问答：交易流程、信用分、纠纷处理、禁售品、面交安全等。"""
    return _dump({"answer": await answer_rules_question(question)})


@tool
async def estimate_price(
    config: RunnableConfig,
    title: str,
    condition: Literal["brand_new", "like_new", "lightly_used", "heavily_used"],
    description: str = "",
    original_price: Optional[float] = None,
) -> str:
    """为二手物品给出建议定价区间（元）。结果仅供参考。"""
    advice = await advise_price(
        title=title,
        description=description,
        condition=ProductCondition(condition),
        original_price=Decimal(str(original_price)) if original_price is not None else None,
    )
    return _dump(
        {
            "estimated_price": str(advice.estimated_price),
            "range": f"{advice.low} ~ {advice.high} 元",
            "rationale": advice.rationale,
            "tips": advice.tips,
        }
    )


def build_tools() -> list:
    """组装主服务 Agent 的全部工具（按买家/卖家/个人/规则/估价分组）。"""
    return [
        # 买家
        search_products,
        get_product_detail,
        create_order,
        add_favorite,
        list_my_orders,
        # 卖家
        create_listing,
        list_my_products,
        update_my_product_status,
        # 个人
        get_my_profile,
        # 平台规则 / 估价
        qa_platform_rules,
        estimate_price,
    ]
