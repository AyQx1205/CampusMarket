"""services 层：业务逻辑层（不依赖 HTTP；Redis 操作统一走本层/cache_service）。

事务约定：本层只 flush 不 commit，提交由请求级事务（db.session.get_db）统一完成。
"""
