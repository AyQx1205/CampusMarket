# 角色
你是一位资深 Python 后端架构师，精通 FastAPI + LangChain 的工程化落地，
熟悉 Python 3.12 生态，也熟悉异步 ORM、Redis 缓存设计与 LLM 应用架构。
你了解 LangChain 1.0 的 create_agent API，并清楚它与 LangGraph 的分工边界。

# 任务
从零搭建一个「校园二手交易平台」后端项目，内嵌一个**服务型 AI 助手**。
请直接产出可运行的完整代码，而不是伪代码或片段。

# 硬性环境约束（非常重要）
1. 运行环境整体在 WSL2 Ubuntu 24.04 内部，通过 Trae 的 WSL Remote 打开开发。
   项目根目录为 /home/xingwenlei/projects/campus-market。
2. Python 使用 WSL 系统自带的 /usr/bin/python3（Python 3.12.3），
   项目 venv 位于 .venv/，通过 `source .venv/bin/activate` 激活。
3. PostgreSQL 16.15 与 Redis 7.0.15 均运行在同一个 WSL Ubuntu 内，通过 127.0.0.1 访问：
   - PostgreSQL: 127.0.0.1:5432，用户 campus / 密码 campus2026 / 库 campus_market
   - Redis: 127.0.0.1:6379，默认无密码
   - 两者均已 systemctl active，无需在代码里做启动管理
4. 你执行的所有 shell 命令都在 WSL bash 内，用 Linux 语法。
   不要生成 PowerShell 语法或 Windows 路径（如 C:\...）。
5. **禁止使用任何 Docker / docker-compose / k8s 相关的内容**，
   不要生成 Dockerfile、不要用容器化启动脚本。
6. 不要用 SQLite 兜底，必须真实连接 PostgreSQL。
7. 数据库表结构用 Alembic 迁移管理，不要用 create_all 建表。
8. 所有依赖必须选择支持 Python 3.12 的稳定版本，requirements.txt 中锁定最低版本。

# 技术栈（严格遵循）
- Web 框架：FastAPI>=0.115.0 + Uvicorn[standard]>=0.32.0
- ORM：SQLAlchemy 2.0 异步版（sqlalchemy[asyncio]>=2.0.35）+ asyncpg>=0.30.0 + Alembic>=1.14.0
- 数据校验：Pydantic v2（>=2.7.0）+ pydantic-settings>=2.3.0
- 认证：JWT（python-jose[cryptography]>=3.3.0）+ pwdlib[bcrypt]>=0.2.0 + bcrypt>=4.0.0
  Access + Refresh 双 Token
- 缓存/会话：redis-py 异步客户端（redis.asyncio），redis>=5.0.0
- AI：
  - langchain>=1.0.0（**必须使用 1.0 的 create_agent API，禁止使用已废弃的 AgentExecutor**）
  - langchain-openai>=0.3.0
  - langchain-community>=0.4.0
  - **不要直接使用 langgraph 的 StateGraph / 节点 / 边等低层 API。**
    LangChain 1.0 的 create_agent 已经跑在 LangGraph 运行时之上，
    本项目的所有 Agent 需求都用 create_agent 完成。
  - LLM 必须通过 OpenAI 兼容接口调用（base_url 可配置），方便切换 DeepSeek / 通义千问 / 智谱 / Ollama
  - 所有模型名、base_url、api_key 走 .env
- 后台任务：FastAPI BackgroundTasks（轻量场景），不引入 Celery
- 日志：loguru>=0.7.0
- 其他：python-multipart>=0.0.12、httpx>=0.28.0
- 测试：pytest>=8.3.0 + pytest-asyncio>=0.24.0 + httpx.AsyncClient

# 密码哈希规范
- 不使用 passlib（上游 2020 年后停止维护，不建议新项目引入）。
- 密码哈希统一使用 pwdlib[bcrypt]，用法参考：
  ```python
  from pwdlib import PasswordHash
  password_hash = PasswordHash.recommended()
  hashed = password_hash.hash("password")
  password_hash.verify("password", hashed)
  ```
- 在 app/core/security.py 中封装 hash_password / verify_password 两个函数，
  其余业务代码只调用这两个函数，不直接 import pwdlib。

# AI 助手的产品定位（非常重要，决定 System Prompt 与工具设计）
这是一个**服务型 AI 助手**，服务对象是所有校园用户（买家、卖家、潜在用户、老年人）。
它不是通用聊天机器人，而是一个「校园二手交易向导 + 客服」的结合体。

它需要覆盖以下典型服务场景：
1. **买家模糊询价**：用户说“我想买一台便宜的自行车”，助手应主动追问关键信息
   （预算范围、校区、成色要求），然后调用 search_products 工具返回候选商品，
   并给出简明的推荐理由（价格、成色、距离）。
2. **买家商品细节咨询**：用户对某个商品提问“这个还能用多久”“有没有划痕”，
   助手调用 get_product_detail 取真实数据回答，不得编造。
3. **买家下单引导**：用户问“怎么买”，助手用清晰步骤介绍下单流程，
   并在用户确认购买意图后调用 get_order_guide 或引导到相应接口。
4. **卖家发布引导**：用户说“我想卖个 iPad”，助手调用
   generate_listing_draft 工具生成标题/描述/建议售价，并一步步引导用户补全信息。
5. **卖家流程咨询**：用户问“怎么收款”“怎么发货”，助手回答平台规则。
6. **平台规则介绍**：用户问“手续费多少”“怎么申诉”，助手通过 RAG
   检索平台规则库后回答。
7. **老年人 / 新手友好模式**：用户主动说“我是第一次用”或明确表示“说简单点”，
   助手切换到**耐心、步骤化、提供选项式回答**的风格，
   一次只问一个问题，避免多问题轰炸，用简短句子。
8. **超出范围拒答**：涉及法律、医疗、代写作业等请求，礼貌拒绝并引导回平台话题。

# 目录结构（按此生成）
campus-market/
├── app/
│   ├── main.py                 # FastAPI 实例、路由挂载、生命周期钩子
│   ├── core/
│   │   ├── config.py           # pydantic-settings 读取 .env
│   │   ├── security.py         # 密码哈希（pwdlib）、JWT 签发/校验
│   │   ├── redis_client.py     # Redis 连接池单例
│   │   ├── logging.py
│   │   └── exceptions.py       # 全局异常 + 统一响应体
│   ├── db/
│   │   ├── session.py          # async engine + async_sessionmaker
│   │   └── base.py             # DeclarativeBase
│   ├── models/                 # SQLAlchemy ORM 模型
│   ├── schemas/                # Pydantic 请求/响应模型
│   ├── crud/                   # 纯数据访问层
│   ├── services/               # 业务逻辑层（不直接依赖 HTTP）
│   ├── api/v1/
│   │   ├── router.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── products.py
│   │   ├── orders.py
│   │   ├── favorites.py
│   │   └── ai.py               # AI 助手相关接口
│   ├── ai/
│   │   ├── llm.py              # LLM 工厂（可切换模型）
│   │   ├── prompts.py          # 所有 Prompt 集中管理（含不同服务场景的 System Prompt）
│   │   ├── memory.py           # 基于 Redis 的对话记忆
│   │   ├── tools.py            # LangChain @tool 定义（全部服务能力封装为工具）
│   │   ├── agent.py            # 用 create_agent 组装主服务 Agent
│   │   ├── router.py           # 意图识别 + 用户画像识别（可选：老年人模式）
│   │   └── chains/             # 独立可复用的链（非 Agent 场景）
│   │       ├── listing_writer.py   # 商品文案生成
│   │       ├── search_parser.py    # 自然语言 → 结构化筛选
│   │       ├── price_advisor.py    # 定价建议
│   │       └── qa_chain.py         # 平台规则 RAG
│   └── utils/
├── alembic/
├── tests/
├── .env.example
├── requirements.txt
├── pyproject.toml
├── Makefile                    # 只用本地命令，如 make dev / make migrate
└── README.md                   # 含 WSL 下 Redis/PostgreSQL 的初始化步骤

# 数据模型（至少包含）
- User: id, student_no(唯一), nickname, email, phone, hashed_password, avatar_url,
  campus, credit_score, is_active, is_senior_mode(布尔, 用于记录用户是否偏好简洁模式), created_at
- Category: id, name, parent_id, sort_order
- Product: id, seller_id, category_id, title, description, price, original_price,
  condition(枚举: 全新/几乎全新/轻微使用/明显使用),
  images(JSONB 数组), campus, status(枚举: 在售/已预订/已售出/下架),
  view_count, favorite_count, created_at, updated_at
- Order: id, order_no, product_id, buyer_id, seller_id, amount,
  status(枚举), trade_location, remark, created_at, finished_at
- Favorite: id, user_id, product_id, created_at （联合唯一）
- ChatSession / ChatMessage: 用于 AI 对话历史持久化
- 索引要求：
  - Product 按 (category_id, status, created_at)、按 price、按 campus 建索引
  - title/description 建 GIN 索引（中文用 pg_trgm，请在迁移里开启 pg_trgm 扩展）

# 接口清单（RESTful，前缀 /api/v1）
认证：
- POST /auth/register、POST /auth/login、POST /auth/refresh、POST /auth/logout
用户：
- GET /users/me、PATCH /users/me、GET /users/{id}/products
商品：
- GET /products（分页 + 关键词 + 分类 + 价格区间 + 校区 + 排序）
- POST /products、GET /products/{id}、PATCH /products/{id}、DELETE /products/{id}
- POST /products/{id}/favorite、DELETE /products/{id}/favorite
- GET /products/hot（走 Redis ZSet 排行榜）
订单：
- POST /orders、GET /orders（我买到的/我卖出的）、PATCH /orders/{id}/status
AI：
- POST /ai/chat                  服务型多轮对话（session_id 维度记忆），支持 SSE 流式
- POST /ai/chat/simple           老年人 / 简洁模式对话（可选，也可靠 system prompt 里的字段）
- POST /ai/listing/generate      根据关键词/成色/原价生成标题+描述+建议售价
- POST /ai/listing/price         给定商品信息返回定价区间与理由
- POST /ai/search                自然语言 → 结构化查询参数，并直接返回商品列表
- WS   /ai/chat/ws               WebSocket 流式对话（可选加分项）

# AI 助手设计要点（使用 LangChain 1.0 create_agent）
1. **LLM 工厂**：ai/llm.py 暴露 get_llm(temperature, streaming) 和 get_embeddings()，
   全部从 settings 读取 OPENAI_BASE_URL / OPENAI_API_KEY / LLM_MODEL / EMBEDDING_MODEL。
2. **主 Agent**：ai/agent.py 使用 `from langchain.agents import create_agent`：
   ```python
   agent = create_agent(
       model=llm,
       tools=ALL_TOOLS,
       system_prompt=MAIN_SERVICE_PROMPT,
   )
   ```
   **不要使用 AgentExecutor，不要直接使用 LangGraph 的 StateGraph。**
3. **System Prompt 必须显式覆盖以下指令**（在 ai/prompts.py 中集中管理）：
   - 「你是校园二手交易助手，服务对象包括买家、卖家、新用户和老年用户。」
   - 「你只能基于工具返回的真实数据回答商品信息，禁止编造商品、价格、库存。」
   - 「用户意图模糊时，主动用一次只问一个问题的方式追问关键信息（预算/校区/成色）。」
   - 「如果用户表示自己是老年人、第一次使用，或请求说得简单一点，
      切换到简洁模式：短句、步骤化、一次只问一个问题、避免专业术语。」
   - 「涉及法律、医疗、代写作业等平台外话题，礼貌拒绝并引导回二手交易。」
   - 「回答使用简体中文，语气亲切、简洁、可执行。」
4. **记忆**：基于 redis.asyncio 实现，key 形如 `ai:chat:{user_id}:{session_id}`，
   TTL 24 小时，只保留最近 N 轮（N 可配置），超长做摘要压缩。
   记忆以 message list 形式在每轮调用时传入 agent。
5. **工具（LangChain @tool，全部放在 ai/tools.py）**：
   买家向：
   - search_products(keyword, category, min_price, max_price, campus, condition, limit)
   - get_product_detail(product_id)
   - get_order_guide()                # 返回下单流程说明
   卖家向：
   - generate_listing_draft(keyword, condition, original_price)  # 调用 listing_writer 链
   - get_selling_guide()              # 返回卖货流程说明
   个人数据：
   - get_my_orders(user_id, role)     # role: buyer / seller
   - get_user_favorites(user_id)
   平台规则：
   - search_platform_rules(question)  # RAG 检索平台规则库
   估价：
   - estimate_price(category, condition, original_price, age_months)
   **所有工具内部直接调用 service 层（不走 HTTP），保证可测。**
6. **意图路由（轻量实现）**：优先靠 System Prompt + 工具描述让 LLM 自行选择工具。
   只有在需要「老年人模式」这类影响全局风格时，才在 ai/router.py 里做一次
   轻量预判断（如关键词「第一次用」「说简单点」），把结果注入 system prompt。
   **不要为此引入 LangGraph 或复杂的多 Agent 编排。**
7. **Prompt 全部集中**在 ai/prompts.py，用中文，且要求 LLM 输出 JSON 时使用
   `with_structured_output(PydanticModel)` 而不是正则解析。
8. **降级策略**：所有 AI 接口在 LLM 调用失败时返回友好错误
   （如「助手暂时不可用，你仍可正常浏览和下单」），不影响主交易流程。
9. **流式输出**：/ai/chat 使用 StreamingResponse + agent.astream_events，
   前端能看到「AI 正在查询商品…」这类工具调用过程。

# Redis 使用规范（必须体现）
- 商品详情缓存：`product:detail:{id}`，TTL 300s，更新/删除商品时主动失效
- 热门商品榜：`product:hot` ZSet，浏览 +1，定时或按需取 Top N
- 接口限流：滑动窗口，key `rate:{user_id}:{path}`，AI 接口单独更严格
- Refresh Token 黑名单/白名单：`auth:refresh:{jti}`
- AI 会话记忆：`ai:chat:{user_id}:{session_id}`
- 请统一封装在 core/redis_client.py 和 services/cache_service.py，
  业务代码不直接拼写 key 字符串，key 模板集中定义。

# 工程规范
- 分层严格：api → service → crud → model，禁止在 api 层直接写 SQL
- 统一响应体：{"code": 0, "message": "ok", "data": {...}}，
  用自定义异常 + 全局 exception handler 实现
- 所有配置走 .env，提供完整的 .env.example 并写清每一项含义
- 类型注解齐全，关键函数写 docstring
- 每个模块给出一个 pytest 用例示例（认证流程、商品 CRUD、AI 接口 mock LLM）
- README 里必须包含 WSL Ubuntu 下初始化步骤：
  sudo apt install postgresql redis-server
  sudo systemctl start postgresql redis-server
  sudo -u postgres createuser / createdb / 授权
  以及 alembic upgrade head、uvicorn 启动命令

# 依赖版本规范
requirements.txt 中所有关键依赖显式写出下限（当前 Python 3.12.3 环境已验证兼容）：
- fastapi>=0.115.0
- uvicorn[standard]>=0.32.0
- sqlalchemy[asyncio]>=2.0.35
- asyncpg>=0.30.0
- alembic>=1.14.0
- pydantic>=2.7.0
- pydantic-settings>=2.3.0
- python-jose[cryptography]>=3.3.0
- pwdlib[bcrypt]>=0.2.0
- bcrypt>=4.0.0
- redis>=5.0.0
- langchain>=1.0.0
- langchain-openai>=0.3.0
- langchain-community>=0.4.0
- loguru>=0.7.0
- python-multipart>=0.0.12
- httpx>=0.28.0
- pytest>=8.3.0
- pytest-asyncio>=0.24.0

**不要**把 langgraph 单独列进 requirements.txt（它作为 langchain 1.0 的传递依赖已自动安装）。

# 输出要求
按以下顺序输出，每部分给完整文件内容 + 文件路径：
1. 项目树
2. requirements.txt 与 .env.example
3. core 层（config / security / redis_client / exceptions / logging）
4. db 层与所有 models
5. Alembic 配置与首个迁移脚本
6. schemas 与 crud
7. services（含 cache_service）
8. api/v1 全部路由
9. ai/ 全部模块（llm / prompts / memory / tools / router / agent / chains）
10. main.py
11. tests 示例
12. README.md（含 WSL 环境初始化与启动步骤）
13. 一段「本地验证清单」：列出用 curl 或 httpie 依次验证各接口的命令
    包括一段完整的 /ai/chat 多轮对话示例（含买家询价、卖家发布、老年人模式三个场景）

不要省略代码，不要写 "此处略"。如果某处需要你自行决策，选择最主流稳妥的方案并在注释里说明理由。