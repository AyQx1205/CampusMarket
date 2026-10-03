/**
 * 路由表：页面组件全部懒加载（路由级代码分割，首屏只加载首页）。
 * views 本轮为占位页，第 3 轮填充内容。
 */
import { createRouter, createWebHistory } from 'vue-router'

import { setupRouterGuards } from './guards'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: () => import('@/views/HomeView.vue') },
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
    },
    {
      path: '/product/:id',
      name: 'product-detail',
      component: () => import('@/views/ProductDetailView.vue'),
    },
    {
      path: '/publish',
      name: 'publish',
      component: () => import('@/views/ProductPublishView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/orders',
      name: 'orders',
      component: () => import('@/views/OrderListView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/favorites',
      name: 'favorites',
      component: () => import('@/views/FavoriteView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/my-products',
      name: 'my-products',
      component: () => import('@/views/MyProductsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
    },
  ],
  // 切换路由回到顶部（长列表页跳详情的常见体验）
  scrollBehavior: () => ({ top: 0 }),
})

setupRouterGuards(router)

export default router
