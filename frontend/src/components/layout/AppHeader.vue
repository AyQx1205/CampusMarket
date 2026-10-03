<script setup lang="ts">
/** 全局顶栏：Logo / 主导航 / 登录态区（头像下拉 或 登录注册按钮）。 */
import { useRouter } from 'vue-router'
import { UserFilled } from '@element-plus/icons-vue'

import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

/** 退出登录：清登录态后回首页（守卫会自动拦截需登录页面） */
async function handleLogout(): Promise<void> {
  await userStore.logout()
  router.push('/')
}
</script>

<template>
  <header class="app-header">
    <div class="container header-inner">
      <RouterLink to="/" class="logo">校园二手集市</RouterLink>

      <nav class="nav">
        <RouterLink to="/" class="nav-item">首页</RouterLink>
        <RouterLink v-if="userStore.isLoggedIn" to="/publish" class="nav-item">发布</RouterLink>
        <RouterLink v-if="userStore.isLoggedIn" to="/orders" class="nav-item">我的订单</RouterLink>
        <RouterLink v-if="userStore.isLoggedIn" to="/favorites" class="nav-item">收藏</RouterLink>
        <RouterLink v-if="userStore.isLoggedIn" to="/my-products" class="nav-item">我的商品</RouterLink>
      </nav>

      <div class="actions">
        <template v-if="userStore.isLoggedIn">
          <el-dropdown trigger="click">
            <span class="user-entry">
              <el-avatar :size="30" :icon="UserFilled" />
              <span class="nickname">{{ userStore.profile?.nickname ?? '用户' }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push('/profile')">个人中心</el-dropdown-item>
                <el-dropdown-item @click="router.push('/my-products')">我的商品</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <template v-else>
          <RouterLink to="/login">
            <el-button text>登录</el-button>
          </RouterLink>
          <RouterLink to="/register">
            <el-button type="primary">注册</el-button>
          </RouterLink>
        </template>
      </div>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  height: var(--header-height);
  background: var(--color-bg-card);
  border-bottom: 1px solid var(--color-border);
}

.header-inner {
  display: flex;
  align-items: center;
  gap: 28px;
  height: 100%;
}

.logo {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-primary);
  text-decoration: none;
  white-space: nowrap;
}

.nav {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
}

.nav-item {
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  text-decoration: none;
  transition:
    color 0.15s,
    background 0.15s;
}

.nav-item:hover,
.nav-item.router-link-active {
  color: var(--color-primary);
  background: var(--color-primary-light);
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-entry {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  outline: none;
}

.nickname {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 窄屏：只保留 Logo + 登录态，导航收起（第 3 轮页面填充后可加抽屉菜单） */
@media (max-width: 768px) {
  .nav {
    display: none;
  }
}
</style>
