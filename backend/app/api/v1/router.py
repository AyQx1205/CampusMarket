"""v1 路由聚合。"""

from fastapi import APIRouter

from app.api.v1 import ai, auth, favorites, orders, products, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(products.router)
api_router.include_router(favorites.router)
api_router.include_router(orders.router)
api_router.include_router(ai.router)
