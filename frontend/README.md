# Campus Market 前端（Vue 3 + Vite）

## 启动

```bash
pnpm install
cp .env.example .env.local   # 可选：默认走 /api/v1 相对路径
pnpm dev
```

Vite 开发服务器默认 `http://localhost:5173`，`/api` 代理到 `http://127.0.0.1:8000`；`pnpm preview` 使用同样的代理。

环境变量：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `VITE_API_BASE_URL` | `/api/v1` | 后端 API 前缀；生产同源部署保持默认即可 |

## 脚本

```bash
pnpm dev          # 开发
pnpm build        # vue-tsc 类型检查 + 生产构建
pnpm preview      # 预览构建产物
pnpm lint         # ESLint（Vue 3 + TS）
pnpm format       # Prettier 写入
pnpm format:check # Prettier 检查
```

## 约定

- **API 错误**：`src/api/request.ts` 把 HTTP 错误统一转成 `BizError(code, message, status)`；组件只处理视图状态，toast 由拦截器统一弹出。
- **登录态**：token 存在 `localStorage`（`campus_access_token` / `campus_refresh_token`），user store 只保存 `profile` 且**不持久化**（避免 PII 落盘）；刷新页面后由 `main.ts` 调 `fetchMe()` 恢复。
- **401 刷新**：单飞 `refresh` 重放原请求；刷新失败广播 `campus:auth-logout`，`main.ts` 清理 store，仅对 `meta.requiresAuth` 页面跳登录。
- **商品状态**：普通编辑不传 `status`；上下架/标记已售调用 `updateProductStatus`（`PATCH /products/{id}/status`）。`reserved` 只能由下单流程产生。
- **订单**：列表/详情返回 `OrderDetail`（含买卖双方联系方式）；按钮按角色显示，服务端状态机二次校验。
- **AI 会话**：`stores/ai.ts` 持久化到 localStorage，最多保留 100 条；刷新后丢弃未完成的 `pending` 占位。AI 写操作默认关闭（后端配置）。

## 目录

```text
src/
├── api/          # axios 封装与各领域 API
├── assets/       # 全局样式
├── components/   # 布局 / 商品 / AI 组件
├── composables/  # useAiChat 等组合式逻辑
├── router/       # 路由表 + 登录守卫
├── stores/       # Pinia user / ai
├── types/        # 与后端契约对齐的 TS 类型
├── utils/        # 格式化、token 存储
└── views/        # 页面
```