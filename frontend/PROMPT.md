# 角色
你是一位资深 Vue 3 前端工程师，精通 Vue 3 组合式 API、TypeScript、
Element Plus、Pinia、Vue Router，也熟悉与 FastAPI 后端对接的最佳实践。

# 任务
从零搭建「校园二手交易平台」的 Web 前端。后端已完成，
所有 API 已在 http://127.0.0.1:8000/api/v1 提供。请直接产出可运行的完整代码。

# 硬性环境约束
1. 运行环境是 WSL2 Ubuntu 24.04，Node.js 20 LTS 或更高，包管理器使用 pnpm（若未安装，用 npm 代替）。
2. **前端项目根目录为 /home/xingwenlei/projects/campus-market/frontend**。
3. 这是 monorepo 结构：
   - /home/xingwenlei/projects/campus-market/backend/  ← 后端（已存在，不要动）
   - /home/xingwenlei/projects/campus-market/frontend/ ← 你正在此目录工作
4. 后端已运行在 http://127.0.0.1:8000，所有接口前缀 /api/v1。
5. 你执行的所有 shell 命令都在 WSL bash 内，用 Linux 语法。
   不要生成 PowerShell 语法或 Windows 路径。
6. **禁止使用任何 Docker / docker-compose 相关的内容**。
7. 所有页面使用简体中文，代码注释也用中文。

# 技术栈（严格遵循）
- 框架：Vue 3.4+（组合式 API + `<script setup>` 语法）
- 构建：Vite 5+
- 语言：TypeScript 5+
- UI 组件：Element Plus 2.x（按需引入）
- 状态管理：Pinia 2.x（含持久化插件 pinia-plugin-persistedstate）
- 路由：Vue Router 4.x
- HTTP：Axios 1.x（封装拦截器）
- 日期处理：dayjs
- 图标：@element-plus/icons-vue
- Markdown 渲染：marked + DOMPurify
- 代码检查：ESLint + Prettier

# 目录结构（按此生成，位于 frontend/ 下）
frontend/
├── src/
│   ├── main.ts
│   ├── App.vue
│   ├── router/
│   │   ├── index.ts
│   │   └── guards.ts
│   ├── stores/
│   │   ├── user.ts
│   │   └── ai.ts
│   ├── api/
│   │   ├── request.ts            # Axios 实例 + 401 自动刷新 Token
│   │   ├── auth.ts
│   │   ├── user.ts
│   │   ├── product.ts
│   │   ├── order.ts
│   │   ├── favorite.ts
│   │   └── ai.ts
│   ├── types/
│   │   ├── api.ts                # ApiResponse<T>
│   │   ├── user.ts
│   │   ├── product.ts
│   │   ├── order.ts
│   │   └── ai.ts
│   ├── views/
│   │   ├── HomeView.vue
│   │   ├── LoginView.vue
│   │   ├── RegisterView.vue
│   │   ├── ProductDetailView.vue
│   │   ├── ProductPublishView.vue
│   │   ├── OrderListView.vue
│   │   ├── FavoriteView.vue
│   │   ├── MyProductsView.vue
│   │   ├── ProfileView.vue
│   │   └── NotFoundView.vue
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppHeader.vue
│   │   │   └── AppFooter.vue
│   │   ├── product/
│   │   │   ├── ProductCard.vue
│   │   │   ├── ProductFilter.vue
│   │   │   └── ProductGrid.vue
│   │   ├── ai/
│   │   │   ├── AiAssistant.vue
│   │   │   ├── AiMessage.vue
│   │   │   └── AiLauncher.vue
│   │   └── common/
│   │       └── EmptyState.vue
│   ├── composables/
│   │   └── useAiChat.ts
│   ├── utils/
│   │   ├── format.ts
│   │   └── storage.ts
│   ├── assets/styles/
│   │   ├── main.css
│   │   └── variables.css
│   └── env.d.ts
├── public/
├── .env.development              # VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
├── .env.production
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
├── .eslintrc.cjs
├── .prettierrc
├── .gitignore
└── README.md

# 后端 API 契约（已确认可用）
统一响应体：{"code": 0, "message": "ok", "data": {...}}
成功 code=0；业务错误 code≠0；认证失败 HTTP 401

## 认证 /api/v1/auth
- POST /auth/register  body: {student_no, nickname, password, email?, phone?}
- POST /auth/login     body: {student_no, password}
                      返回 data: {access_token, refresh_token, token_type, expires_in}
- POST /auth/refresh   body: {refresh_token}
- POST /auth/logout    需要 Bearer

## 用户 /api/v1/users
- GET /users/me        需要 Bearer
                      返回 {id, student_no, nickname, email, phone, avatar_url,
                            campus, credit_score, is_senior_mode, created_at}
- PATCH /users/me      需要 Bearer，body: {nickname?, email?, phone?, campus?, is_senior_mode?}
- GET /users/{user_id}/products

## 商品 /api/v1/products
- GET /products        查询: page, page_size, keyword, category_id,
                       min_price, max_price, campus, sort (latest|price_asc|price_desc|hottest)
                      返回 data: {items: [...], total, page, page_size}
- POST /products       需要 Bearer
                      body: {title, description?, price, original_price?, condition,
                             category_id?, images?: string[], campus?}
                      condition: brand_new | like_new | lightly_used | heavily_used
- GET /products/{id}   返回 data: 商品详情
- PATCH /products/{id} 需要 Bearer
- DELETE /products/{id} 需要 Bearer
- POST /products/{id}/favorite    需要 Bearer
- DELETE /products/{id}/favorite  需要 Bearer
- GET /products/hot    返回 data: 商品数组

## 订单 /api/v1/orders
- POST /orders         需要 Bearer，body: {product_id, trade_location?, remark?}
- GET /orders          需要 Bearer，查询 role=buyer|seller
- PATCH /orders/{order_id}/status 需要 Bearer，body: {status}

## 收藏 /api/v1/favorites
- GET /favorites       需要 Bearer

## AI /api/v1/ai（全部需要 Bearer）
- POST /ai/chat
      body: {message: string, session_id: string}
      返回 data: {session_id, reply: string}
      注意：code=5001 表示未配置 LLM，HTTP 503 表示 AI 暂时不可用

- POST /ai/listing/generate
      body: {raw_info: string, expected_price?: number, condition_hint?: string}
      返回 data: {title, description, highlights: string[], condition}

- POST /ai/search
      body: {query: string}
      返回 data: {
        filters: {keyword?, min_price?, max_price?, campus?, sort},
        result: {items, total, page, page_size}
      }

# 页面设计

## 1. 首页 / 商品列表 (HomeView)
- 顶部筛选栏：关键词、分类下拉、价格区间、校区输入、排序切换
- 商品网格（ProductCard）：首图、标题、价格、原价划线、成色标签、校区
- 分页组件
- 空状态组件
- 右上角悬浮 AI 助手按钮

## 2. 商品详情 (ProductDetailView)
- 图片轮播、商品信息、卖家信息卡片
- 操作按钮：「立即购买」「收藏」「问问 AI」
- 若是自己发布的商品，「立即购买」禁用

## 3. 发布商品 (ProductPublishView)
- 表单：标题、描述、价格、原价、成色、校区、图片 URL
- **「AI 帮我写」按钮**：调 /ai/listing/generate 自动填充标题和描述

## 4. 登录 / 注册
- Element Plus 表单校验
- 登录成功存 token 到 Pinia + localStorage

## 5. 我的订单 (OrderListView)
- Tab：我买到的 / 我卖出的
- 表格展示 + 状态操作

## 6. 我的收藏 (FavoriteView)
- 网格布局，复用 ProductCard

## 7. 我的商品 (MyProductsView)
- 列表，可编辑状态 / 删除

## 8. 个人中心 (ProfileView)
- 展示和修改昵称、邮箱、电话、校区
- 老年人模式开关

# AI 助手组件设计（核心）

## AiAssistant.vue
- 右下角悬浮按钮（FAB），点击展开为右侧抽屉或悬浮窗口
- 消息列表（滚动），用户消息靠右蓝底，AI 消息靠左白底
- AI 消息支持 markdown 渲染（marked + DOMPurify）
- 底部输入框 + 发送按钮
- 首次打开展示快捷问题按钮：
  「怎么发布商品？」「帮我找便宜的自行车」「我想卖东西，怎么操作？」
- session_id 格式：`web-{userId}-{timestamp}`，首次打开生成
- 错误处理：
  - code=5001 → 显示「AI 助手暂未上线」
  - HTTP 503 → 显示「助手忙不过来，稍后再试」
  - 网络错误 → 显示重试按钮

## 关键交互
- 回车发送，Shift+回车换行
- 发送中显示 loading
- 消息自动滚到底部

# API 客户端设计（request.ts）

1. Axios 实例：
   - baseURL 从 VITE_API_BASE_URL 读取
   - timeout: 60000
   - 请求拦截器：加 Authorization: Bearer {access_token}
   - 响应拦截器：
     - code === 0 → resolve data
     - code !== 0 → reject + toast message
     - HTTP 401 → 自动调 /auth/refresh 刷新 Token 并重放请求
       并发请求用 promise 缓存，避免重复刷新
     - HTTP 5xx → toast「服务器错误」
2. 所有 API 方法返回 Promise<T>（已剥掉外层）

# 路由设计

- /                        HomeView
- /login                   LoginView
- /register                RegisterView
- /product/:id             ProductDetailView
- /publish                 ProductPublishView（需登录）
- /orders                  OrderListView（需登录）
- /favorites               FavoriteView（需登录）
- /my-products             MyProductsView（需登录）
- /profile                 ProfileView（需登录）
- /:pathMatch(.*)*         NotFoundView

路由守卫：
- meta.requiresAuth 页面未登录时跳 /login
- 已登录访问 /login 或 /register 时跳 /

# 样式要求

- 主色调：#10b981（青绿色，年轻感）
- 圆角：8px
- 卡片阴影柔和，悬停轻微上浮
- 响应式，桌面优先，适配到 768px

# 工程规范

- 所有 Vue 组件用 `<script setup lang="ts">`
- 所有 API 方法加中文 JSDoc 注释
- 类型集中在 src/types
- 环境变量用 VITE_ 前缀
- Element Plus 按需引入（unplugin-auto-import + unplugin-vue-components）

# 输出要求
按以下顺序输出，每部分给完整文件内容 + 文件路径：
1. package.json 与依赖版本
2. vite.config.ts / tsconfig.json / .env.development
3. src/main.ts 与 src/App.vue
4. src/types/ 下所有类型
5. src/api/request.ts（含 401 自动刷新完整实现）
6. src/api/ 下所有 API 模块
7. src/stores/ 下所有 store
8. src/router/ 路由配置与守卫
9. src/utils/ 与 src/composables/
10. src/components/ 全部组件
11. src/views/ 全部页面
12. 样式文件
13. README.md

不要省略代码，不要写 "此处略"。如果某处需要你自行决策，选择最主流稳妥的方案并在注释里说明理由。