"""pytest 全局配置：在任何 app 模块导入前提供最小可用的环境变量。

本地/CI 都不应该依赖开发者机器上的 backend/.env：测试用固定测试密钥，
且 ENVIRONMENT=test 不会触发生产配置校验。
"""

import os

os.environ["ENVIRONMENT"] = "test"
os.environ.setdefault(
    "JWT_SECRET_KEY", "test-only-secret-key-with-at-least-32-characters"
)
os.environ.setdefault("DEBUG", "false")