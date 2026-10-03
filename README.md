# Campus Market · 校园二手交易平台

面向高校学生的二手交易平台，内置**服务型 AI 助手**：自然语言找货、AI 代写商品文案、智能定价建议、平台规则问答，并支持面向老年用户的长辈模式。

## 目录结构

```text
campus-market/
├── backend/          # FastAPI + LangChain 后端
│   ├── app/
│   │   ├── core/     # 配置、安全、异常体系、Redis、日志
│   │   ├── db/       # SQLAlchemy 2.0 async 基础设施
│   │   ├── models/   # 7 张表（用户/商品/分类/收藏/订单/对话）
│   │   ├── schemas/  # Pydantic v2 请求/响应模型
│   │   ├── crud/     # 纯数据访问层
│   │   ├── services/ # 业务逻辑层（含缓存服务）
│   │   ├── api/v1/   # REST 路由（auth/users/products/orders/favorites/ai）
│   │   └── ai/       # LangChain 1.0 create_agent 服务型助手
│   ├── alembic/      # 异步迁移（含 pg_trgm GIN 索引）
│   └── requirements.txt
├── frontend/         # Vue 3 + Element Plus 前端
│   └── src/
│       ├── api/      # axios 封装（401 自动刷新重放）
│       ├── stores/   # Pinia（用户态持久化 / AI 会话持久化）
│       ├── router/   # 路由 + 登录守卫
│       ├── components/  # 布局 / 商品 / AI 悬浮助手
│       ├── views/    # 首页、发布、订单、收藏、我的商品、个人中心等
│       └── types/    # 与后端契约对齐的 TS 类型
└── README.md
```

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.12 · FastAPI · SQLAlchemy 2.0 (async) · asyncpg · Pydantic v2 · Alembic |
| AI | LangChain 1.0 `create_agent`（禁用 langgraph / AgentExecutor）· OpenAI 兼容接口 · `with_structured_output` |
| 数据 | PostgreSQL 16（pg_trgm 模糊搜索）· Redis 7（缓存 / 会话记忆 / Token 白名单 / 热门榜） |
| 认证 | JWT 双 Token（access 30min + refresh 7d，jti 白名单旋转）· pwdlib Argon2id |
| 前端 | Vue 3 · TypeScript · Vite · Pinia (+persistedstate) · Vue Router · Element Plus（按需引入）· marked + DOMPurify |

## 环境要求

- WSL2 / Ubuntu 24.04
- Python 3.12
- PostgreSQL 16、Redis 7（`sudo apt install postgresql redis-server`）
- Node.js 20+、pnpm（`npm i -g pnpm`）

## 快速启动

### 1. 启动数据库与 Redis（systemd）

```bash
sudo systemctl enable --now postgresql redis-server

# 建库建用户（与 .env.example 默认连接串一致）
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
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # 按需修改 DATABASE_URL / OPENAI_API_KEY 等
alembic upgrade head        # 建表（首次）

uvicorn app.main:app --reload --port 8000
# API 文档: http://127.0.0.1:8000/docs
```

### 3. 前端

```bash
cd frontend
pnpm install
pnpm dev
# 打开: http://localhost:5173
```

开发模式下 Vite 将 `/api` 代理到 `http://127.0.0.1:8000`，浏览器全程同源，无 CORS 问题。

## 核心功能

- **商品**：发布（图片链接）、关键词/分类/价格区间/校区组合筛选、四种排序、热门榜（Redis ZSet）、详情浏览量计数、商品缓存旁路
- **交易**：下单（金额快照）、订单状态机（pending → confirmed/completed/cancelled）、买卖双方订单列表
- **收藏**：收藏/取消/收藏夹列表
- **用户**：注册登录、资料修改、长辈模式开关
- **AI 助手**（见下）

## AI 助手能力

- **多轮对话**：`create_agent` + 11 个内部工具（调 service 层而非 HTTP），会话记忆存 Redis（`ai:chat:{user_id}:{session_id}`，TTL 24h）
- **AI 代写文案**：随手描述 → 标题 + 描述 + 成色推断（`with_structured_output`，无正则解析）
- **自然语言搜索**：「帮我找 500 块以内的自行车」→ 结构化筛选 + 直接返回分页结果
- **定价建议 / 平台规则问答**：估价链（区间 + 理由）与规则库兜底
- **长辈模式**：开启后 System Prompt 切换为更耐心的表达风格
- **降级策略**：`OPENAI_API_KEY` 未配置时接口返回业务码 `5001`（而非 500），前端展示「AI 助手暂未上线」

## LLM 供应商切换

后端统一走 OpenAI 兼容接口，改 `backend/.env` 三项即可：

| 供应商 | `OPENAI_BASE_URL` | `LLM_MODEL` |
|---|---|---|
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| 智谱 | `https://open.bigmodel.cn/api/paas/v4` | `glm-4-flash` |
| Ollama 本地 | `http://127.0.0.1:11434/v1` | 任意已 pull 模型，如 `qwen2.5:7b` |

注意：

- Ollama 不校验 key，但**不能留空也不能填占位符 `sk-xxx`**（会被判定为未配置），填任意非占位字符串如 `ollama` 即可
- Qwen3 系列默认开启 thinking，会拒绝结构化输出所需的 `tool_choice="required"`——保持 `LLM_DISABLE_THINKING=true`（默认）即可

## 常见问题

**Q：前端调接口报 CORS 错误？**
开发期请通过 Vite 代理（默认行为，前端请求 `/api` 即可）。若绕过代理直连 `http://127.0.0.1:8000`，需把来源加入后端 `CORS_ORIGINS`。

**Q：所有接口突然都返回 401？**
Access Token 过期会自动用 Refresh Token 静默续期；若 Redis 未启动，刷新白名单（`auth:refresh:{jti}`）不可用且为 fail-closed 设计，会全部 401——先确认 `redis-server` 在跑。Refresh Token 本身 7 天过期，重新登录即可。

**Q：Redis 连不上会怎样？**
分两类：缓存/会话记忆/热门榜**降级放行**（查库返回，只是变慢或不带记忆）；登录刷新白名单**直接失败**（安全优先）。日志中会有 `Redis` 相关降级告警。

**Q：Qwen 报 `The tool_choice parameter does not support being set to required ... thinking mode`？**
未关闭 thinking 模式。确认 `.env` 中 `LLM_DISABLE_THINKING=true`（默认已开启）。

**Q：安装依赖后启动报 `HasherNotAvailable`？**
pwdlib 0.2+ 的 `PasswordHash.recommended()` 需要 Argon2 支持，`requirements.txt` 已声明 `pwdlib[argon2,bcrypt]`，请确认装的是该 extra 版本而非裸 `pwdlib`。

**Q：登录失败没有 toast 提示？**
Element Plus 按需引入时，`ElMessage` 等 JS API 组件的样式需手动引入（`src/main.ts` 已补 `el-message.css` 等 5 个文件），不要删除这些 import。
