<script setup lang="ts">
/** 全局顶栏：Logo / 主导航 / 登录态区（头像下拉 或 登录注册按钮）。 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Menu as MenuIcon, UserFilled } from '@element-plus/icons-vue'

import { useAiStore } from '@/stores/ai'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const aiStore = useAiStore()
const drawerOpen = ref(false)

/** 退出登录：清登录态后回首页（守卫会自动拦截需登录页面） */
async function handleLogout(): Promise<void> {
  drawerOpen.value = false
  await userStore.logout()
  // 避免下一个登录用户看到上一个用户的 AI 会话
  aiStore.resetSession()
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
        <el-button
          class="menu-btn"
          text
          :icon="MenuIcon"
          aria-label="打开导航菜单"
          @click="drawerOpen = true"
        />
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

  <!-- 窄屏导航抽屉：顶栏只保留 Logo + 登录态，功能入口收进菜单 -->
  <el-drawer v-model="drawerOpen" direction="rtl" size="72%" title="导航菜单">
    <nav class="drawer-nav">
      <RouterLink to="/" class="drawer-item" @click="drawerOpen = false">首页</RouterLink>
      <template v-if="userStore.isLoggedIn">
        <RouterLink to="/publish" class="drawer-item" @click="drawerOpen = false">发布商品</RouterLink>
        <RouterLink to="/orders" class="drawer-item" @click="drawerOpen = false">我的订单</RouterLink>
        <RouterLink to="/favorites" class="drawer-item" @click="drawerOpen = false">我的收藏</RouterLink>
        <RouterLink to="/my-products" class="drawer-item" @click="drawerOpen = false">我的商品</RouterLink>
        <RouterLink to="/profile" class="drawer-item" @click="drawerOpen = false">个人中心</RouterLink>
        <el-button class="drawer-logout" type="danger" plain @click="handleLogout">退出登录</el-button>
      </template>
      <template v-else>
        <RouterLink to="/login" class="drawer-item" @click="drawerOpen = false">登录</RouterLink>
        <RouterLink to="/register" class="drawer-item" @click="drawerOpen = false">注册</RouterLink>
      </template>
    </nav>
  </el-drawer>
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

.menu-btn {
  display: none;
  font-size: 20px;
}

.drawer-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.drawer-item {
  padding: 12px 8px;
  border-radius: var(--radius-sm);
  color: var(--color-text);
  text-decoration: none;
  font-size: 15px;
}

.drawer-item:hover,
.drawer-item.router-link-active {
  color: var(--color-primary);
  background: var(--color-primary-light);
}

.drawer-logout {
  margin-top: 16px;
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

/* 窄屏：只保留 Logo + 登录态，导航收进抽屉 */
@media (max-width: 768px) {
  .nav {
    display: none;
  }

  .menu-btn {
    display: inline-flex;
  }

  .nickname {
    display: none;
  }
}
</style>
