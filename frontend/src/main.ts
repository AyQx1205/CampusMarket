// Element Plus 按需引入时，ElMessage/ElMessageBox/ElLoading
// 这类 JS API 组件的样式不会随组件自动注入，需手动补齐（否则弹窗无样式不可见）
import 'element-plus/theme-chalk/el-message.css'
import 'element-plus/theme-chalk/el-message-box.css'
import 'element-plus/theme-chalk/el-loading.css'
import 'element-plus/theme-chalk/el-overlay.css'

import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import { AUTH_LOGOUT_EVENT } from '@/api/request'
import { useAiStore } from '@/stores/ai'
import { useUserStore } from '@/stores/user'
import '@/assets/styles/main.css'

const app = createApp(App)

// Pinia + 持久化插件（当前仅 AI 会话使用；用户资料含 PII，不再落 localStorage）
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)
app.use(pinia)

// 路由（含登录态守卫，见 router/guards.ts）
app.use(router)

// 401 刷新失败：request 层广播事件，这里统一清 store 并跳登录页。
// 只对需要登录的页面跳转，避免首页匿名浏览时被过期 token 打断。
window.addEventListener(AUTH_LOGOUT_EVENT, () => {
  const userStore = useUserStore(pinia)
  userStore.clearLocalSession()
  // 会话失效也要清掉 AI 历史，避免残留上一个账号的聊天内容
  useAiStore(pinia).resetSession()
  const current = router.currentRoute.value
  if (current.meta.requiresAuth) {
    router.push({ path: '/login', query: { redirect: current.fullPath } })
  }
})

// 刷新页面后重新拉取个人信息（token 仍在时）；失败由拦截器统一处理
const userStore = useUserStore(pinia)
if (userStore.isLoggedIn) {
  void userStore.fetchMe()
}

// Element Plus 组件与 ElMessage 等按 unplugin-vue-components / unplugin-auto-import
// 按需引入（见 vite.config.ts），无需全局 app.use(ElementPlus)。

// 等首次路由解析完再挂载，深链刷新时不会先闪一帧空 RouterView
void router.isReady().finally(() => {
  app.mount('#app')
})