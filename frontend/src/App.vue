<script setup lang="ts">
// 根组件：顶栏 + 路由出口 + 底栏（flex 布局，底栏贴底）+ 全局 AI 助手悬浮面板
import AppFooter from '@/components/layout/AppFooter.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import AiAssistant from '@/components/ai/AiAssistant.vue'
</script>

<template>
  <div class="app-shell">
    <AppHeader />
    <main class="app-main container">
      <RouterView />
    </main>
    <AppFooter />
    <!-- AI 助手：所有页面可开合（FAB + 面板均在组件内部） -->
    <AiAssistant />
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-main {
  flex: 1;
  width: 100%;
  padding-top: 20px;
  padding-bottom: 32px;
}
</style>
