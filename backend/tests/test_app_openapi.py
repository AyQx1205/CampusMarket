"""路由契约（OpenAPI）：核心端点是否真的注册成功。"""

from app.main import app


def _schema() -> dict:
    return app.openapi()


def test_new_and_core_routes_are_registered() -> None:
    paths = _schema()["paths"]
    expected = {
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/logout",
        "/api/v1/categories",
        "/api/v1/products",
        "/api/v1/products/hot",
        "/api/v1/products/{product_id}",
        "/api/v1/products/{product_id}/status",
        "/api/v1/products/{product_id}/favorite",
        "/api/v1/orders",
        "/api/v1/orders/{order_id}",
        "/api/v1/orders/{order_id}/status",
        "/api/v1/users/me",
        "/api/v1/users/{user_id}",
        "/api/v1/users/{user_id}/products",
        "/api/v1/ai/chat",
        "/api/v1/ai/search",
        "/api/v1/ai/listing/generate",
    }
    assert expected <= set(paths)


def test_product_patch_documentation_does_not_accept_status() -> None:
    schema = _schema()
    patch_body = schema["paths"]["/api/v1/products/{product_id}"]["patch"]["requestBody"]
    ref = patch_body["content"]["application/json"]["schema"]["$ref"]
    name = ref.rsplit("/", 1)[-1]
    properties = schema["components"]["schemas"][name]["properties"]
    assert "status" not in properties
    assert "status" in schema["components"]["schemas"]["ProductStatusUpdate"]["properties"]