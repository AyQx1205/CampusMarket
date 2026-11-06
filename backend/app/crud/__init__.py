"""crud 层：纯数据访问层（只做数据读写，不含业务规则，不依赖 HTTP/Redis）。

事务约定：本层只 flush，不 commit；写操作的 commit 由 service 层显式执行，
保证 HTTP 响应发出前事务已提交（详见 app/db/session.py）。
"""