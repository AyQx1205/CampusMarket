// Element Plus 按需引入时，ElMessage/ElMessageBox/ElLoading/ElNotification
// 这类 JS API 组件的样式不会随组件自动注入，需手动补齐（否则弹窗无样式不可见）
import 'element-plus/theme-chalk/el-message.css'
import 'element-plus/theme-chalk/el-message-box.css'
import 'element-plus/theme-chalk/el-loading.css'
import 'element-plus/theme-chalk/el-notification.css'
import 'element-plus/theme-chalk/el-overlay.css'

import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import '@/assets/styles/main.css'

const app = createApp(App)

// Pinia + 持久化插件（user/ai store 的 profile 与会话消息写入 localStorage）
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)
app.use(pinia)

// 路由（含登录态守卫，见 router/guards.ts）
app.use(router)

// Element Plus 组件与 ElMessage 等按 unplugin-vue-components / unplugin-auto-import
// 按需引入（见 vite.config.ts），无需全局 app.use(ElementPlus)。

app.mount('#app')
