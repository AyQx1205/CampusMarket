"""services 层：业务逻辑层（不依赖 HTTP；Redis 操作统一走本层/cache_service）。

事务约定：写操作在本层显式 `await db.commit()`，提交成功后再做缓存失效
等副作用；crud 层只 flush。只读服务不提交。
"""