# Campus Market · 校园二手交易平台

面向高校学生的二手交易平台，内置服务型 AI 助手：自然语言找货、AI 代写商品文案、智能定价建议、平台规则问答，并支持面向长辈用户的简洁模式。

## 目录结构

```text
campus-market/
├── backend/                  # FastAPI + LangChain 后端
│   ├── app/
│   │   ├── core/             # 配置、安全、异常体系、Redis、限流、日志
│   │   ├── db/               # SQLAlchemy 2.0 async 基础设施
│   │   ├── models/           # 用户/商品/分类/收藏/订单/对话模型
│   │   ├── schemas/          # Pydantic v2 请求/响应模型
│   │   ├── crud/             # 纯数据访问层（只 flush，不 commit）
│   │   ├── services/         # 业务逻辑层（显式 commit + 缓存失效）
│   │   ├── api/v1/           # REST 路由
│   │   └── ai/               # LangChain 1.0 create_agent 服务型助手
│   ├── alembic/              # 迁移（0001 初始 + 0002 完整性补丁）
│   ├── tests/                # pytest 契约/安全/状态机测试
│   ├── requirements.txt
│   └── requirements-dev.txt
├── frontend/                 # Vue 3 + Element Plus 前端
│   └── src/
│       ├── api/              # axios 封装（统一错误 + 401 刷新重放）
│       ├── stores/           # Pinia（用户态不持久化 PII；AI 会话持久化）
│       ├── router/           # 路由 + 登录守卫
│       ├── components/       # 布局 / 商品 / AI 悬浮助手
│       ├── views/            # 首页、发布、订单、收藏、我的商品、个人中心等
│       └── types/            # 与后端契约对齐的 TS 类型
├── .github/workflows/ci.yml  # 后端 lint/迁移/测试 + 前端 lint/build
└── README.md
```

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.12 · FastAPI · SQLAlchemy 2.0 (async) · asyncpg · Pydantic v2 · Alembic |
| AI | LangChain 1.0 `create_agent` · OpenAI 兼容接口 · `with_structured_output` |
| 数据 | PostgreSQL 16（pg_trgm 模糊搜索）· Redis 7（缓存 / 会话记忆 / Token 白名单 / 热门榜 / 限流） |
| 认证 | JWT 双 Token（access 30min + refresh 7d，jti 白名单 + GETDEL 原子旋转）· pwdlib Argon2id（兼容旧 bcrypt） |
| 前端 | Vue 3 · TypeScript · Vite 5 · Pinia (+persistedstate) · Vue Router · Element Plus（按需引入）· marked + DOMPurify |

## 环境要求

- Python 3.12+
- PostgreSQL 16、Redis 7
- Node.js 20+、pnpm 9+

## 快速启动

### 1. 启动数据库与 Redis

```bash
sudo systemctl enable --now postgresql redis-server

# 建库建用户（与 .env.example 默认连接串一致；生产请改强口令）
sudo -u postgres psql <<'SQL'
CREATE USER campus WITH PASSWORD 'campus2026';
CREATE DATABASE campus_market OWNER campus;
\c campus_market
CREATE EXTENSION IF NOT EXISTS pg_trgm;
SQL
```

### 2. 后端

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

cp .env.example .env
# 必改：JWT_SECRET_KEY（至少 32 字符）
python -c "import secrets; print(secrets.token_urlsafe(48))"

alembic upgrade head        # 0001 建表 + 0002 约束/索引/分类种子
uvicorn app.main:app --reload --port 8000
# API 文档: http://127.0.0.1:8000/docs （prod 环境自动关闭）
```

### 3. 前端

```bash
cd frontend
pnpm install
pnpm dev
# 打开: http://localhost:5173
```

开发模式下 Vite 将 `/api` 代理到 `http://127.0.0.1:8000`，浏览器同源，无 CORS 问题。`pnpm preview` 也配置了同一代理。

## 核心功能

- **商品**：发布（图片链接，最多 9 张）、关键词/分类/价格区间/校区组合筛选、四种排序、热门榜（Redis ZSet）、详情浏览量计数、商品缓存旁路；分类由 `GET /categories` 提供，不再前端硬编码
- **交易**：下单（金额按商品售价快照，行锁 + 部分唯一索引防止超卖）；订单状态机按角色收敛：
  - `pending`：买家可取消；卖家可确认或取消
  - `confirmed`：买家确认完成；卖家可取消
  - `completed / cancelled`：终态，重复调用幂等
  - 约定「买家当面验货后确认完成」，卖家不能替买家完成订单
- **商品状态**：`PATCH /products/{id}/status` 仅卖家可用，只允许 `on_sale / off_shelf / sold`；`reserved` 只能由下单流程写入，有进行中订单时禁止手工改状态
- **收藏**：收藏/取消/收藏夹分页；详情页通过 `GET /products/{id}/favorite` 单查状态
- **用户**：注册登录、资料修改、长辈模式开关；公开资料 `GET /users/{id}` 不含学号/邮箱/手机号，联系方式仅订单参与者可见

## AI 助手能力

- **多轮对话**：`create_agent` + 内部工具（调 service 层而非 HTTP），会话记忆存 Redis（`ai:chat:{user_id}:{session_id}`，TTL 由 `AI_MEMORY_TTL_HOURS` 控制）
- **AI 代写文案**：随手描述 → 标题 + 描述 + 成色推断（`with_structured_output`）
- **自然语言搜索**：「帮我找 500 块以内的自行车」→ 结构化筛选 + 分页结果
- **定价建议 / 平台规则问答**
- **长辈模式**：System Prompt 切换为更耐心的表达
- **写操作默认关闭**：`AI_ENABLE_WRITE_TOOLS=false` 时只暴露只读工具；开启后 AI 才能代下单/发布/改状态/收藏
- **配额**：按用户分钟级限流 + 每日配额（Redis；故障时 fail-open）
- **降级**：`OPENAI_API_KEY` 未配置时返回业务码 `5001`，前端展示「AI 助手暂未上线」

## 安全与并发要点

- `JWT_SECRET_KEY` 无默认值，至少 32 字符；`ENVIRONMENT=prod` 时额外拒绝 DEBUG、CORS `*`、默认数据库口令和示例密钥
- 登录/注册/刷新按 IP 固定窗口限流；AI 按用户限流 + 每日配额；超限返回 429 + `Retry-After`
  - 部署在 Nginx 等可信代理后，设置 `TRUST_PROXY_HEADERS=true` 并使用代理覆盖的 `X-Forwarded-For`；直连公网时保持 `false`
- Refresh Token 白名单存 Redis，刷新用 `GETDEL` 原子消费，旧 token 立即失效；登出吊销 refresh
- Redis 在认证链路 fail-closed（不可用时 503），在缓存/记忆/热门榜链路 fail-open
- 同一商品最多一条 `pending/confirmed` 订单，由部分唯一索引 `uq_orders_active_product` 兜底
- 商品编辑/上下架与下单都使用行锁；服务层在返回响应前显式 `commit`，避免「200 已返回但事务回滚」
- 商品搜索转义 `%/_`，AI/搜索参数有长度上限；请求体统一 `extra="forbid"`，误传 `status`/`amount` 直接 422

## LLM 供应商切换

改 `backend/.env` 三项即可：

| 供应商 | `OPENAI_BASE_URL` | `LLM_MODEL` |
|---|---|---|
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| 智谱 | `https://open.bigmodel.cn/api/paas/v4` | `glm-4-flash` |
| Ollama 本地 | `http://127.0.0.1:11434/v1` | 任意已 pull 模型，如 `qwen2.5:7b` |

注意：

- Ollama 不校验 key，但不能留空或填占位符 `sk-xxx`（会被判定未配置），填任意非占位字符串如 `ollama`
- Qwen3 系列默认开启 thinking，会拒绝结构化输出所需的 `tool_choice="required"`；保持 `LLM_DISABLE_THINKING=true`

## 开发与质量

```bash
# 后端（backend/）
make test          # pytest
make lint          # ruff check app tests
make fmt           # ruff format app tests
make migrate       # alembic upgrade head

# 前端（frontend/）
pnpm lint          # eslint
pnpm build         # vue-tsc --noEmit && vite build
pnpm format:check  # prettier
```

CI 会在 PostgreSQL 16 + Redis 7 服务容器上跑迁移与测试，并对前端执行 lint/build。

## 常见问题

**Q：前端调接口报 CORS 错误？**
开发期通过 Vite 代理（前端请求 `/api`）。若直连 `http://127.0.0.1:8000`，需把来源加入后端 `CORS_ORIGINS`（JSON 数组）。

**Q：所有接口突然都返回 401 / 503？**
Access Token 过期会自动用 Refresh Token 静默续期。若 Redis 不可用，Refresh 白名单无法读写，认证链路返回 **503**（安全优先）；先确认 `redis-server` 在跑。Refresh Token 7 天过期后重新登录。

**Q：Redis 连不上会怎样？**
缓存/会话记忆/热门榜降级放行（查库、变慢、无记忆）；认证白名单直接失败（503）；限流与 AI 配额 fail-open。日志中会有 Redis 降级告警。

**Q：Qwen 报 `The tool_choice parameter does not support being set to required ... thinking mode`？**
确认 `.env` 中 `LLM_DISABLE_THINKING=true`。

**Q：启动报 `HasherNotAvailable`？**
`core/security.py` 使用 `Argon2Hasher + BcryptHasher`，`requirements.txt` 已声明 `pwdlib[argon2,bcrypt]`；请确认装的是该 extra，而不是裸 `pwdlib`。

**Q：启动报缺少 `JWT_SECRET_KEY` / `email-validator`？**
`JWT_SECRET_KEY` 为必填项（无默认值）；`EmailStr` 依赖 `email-validator`，两者都已在 `.env.example` / `requirements.txt` 中说明。

**Q：登录失败没有 toast 提示？**
Element Plus 按需引入时，`ElMessage` 等 JS API 组件的样式需手动引入（`src/main.ts` 已补 `el-message.css` 等），不要删除这些 import。