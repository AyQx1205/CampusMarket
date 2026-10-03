"""crud 层：纯数据访问层（只做数据读写，不含业务规则，不依赖 HTTP/Redis）。

事务约定：本层只 flush 不 commit，提交由 db.session.get_db 的请求级事务统一完成。
"""
