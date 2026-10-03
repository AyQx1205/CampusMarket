/**
 * 登录态路由守卫。
 *
 * - meta.requiresAuth 且未登录 → /login?redirect=原路径（登录成功后回跳）
 * - 已登录访问 /login、/register → /
 */
import type { Router } from 'vue-router'

import { useUserStore } from '@/stores/user'

export function setupRouterGuards(router: Router): void {
  router.beforeEach((to) => {
    const userStore = useUserStore()

    if (to.meta.requiresAuth && !userStore.isLoggedIn) {
      return { path: '/login', query: { redirect: to.fullPath } }
    }
    if (userStore.isLoggedIn && (to.name === 'login' || to.name === 'register')) {
      return { path: '/' }
    }
    return true
  })
}
