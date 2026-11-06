/**
 * 用户 store：个人信息 + 登录态。
 *
 * token 不放进 state：axios 拦截器在每个请求发出时同步读 localStorage
 * （utils/storage.ts），扁平 key 不依赖 Pinia 时序；store 里再存一份
 * 只会得到一份陈旧镜像（401 刷新时 request 层更新的是 storage）。
 * 登录态的响应式开关用 hasToken ref 维护，与 storage 严格同步。
 *
 * 隐私：profile 含学号/邮箱/手机号，不再持久化到 localStorage；
 * 刷新页面后由 main.ts 调 fetchMe() 重新拉取（未登录不发请求）。
 */
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { getMe } from '@/api/user'
import { login as loginApi, logout as logoutApi } from '@/api/auth'
import type { LoginParams, UserProfile } from '@/types/user'
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from '@/utils/storage'

export const useUserStore = defineStore('user', () => {
  const profile = ref<UserProfile | null>(null)
  // 与 storage 中 token 是否存在保持同步的响应式标记
  const hasToken = ref(Boolean(getAccessToken()))

  const isLoggedIn = computed(() => hasToken.value)
  /** 老年/简洁模式（决定 AI 助手回复风格，后端同样按此画像） */
  const isSeniorMode = computed(() => profile.value?.is_senior_mode ?? false)

  /** 登录：换取并持久化双 Token，再拉取个人信息 */
  async function login(params: LoginParams): Promise<UserProfile> {
    const result = await loginApi(params)
    setTokens(result.access_token, result.refresh_token)
    hasToken.value = true
    await fetchMe()
    return profile.value as UserProfile
  }

  /** 拉取当前用户信息（未登录直接返回 null，不打接口） */
  async function fetchMe(): Promise<UserProfile | null> {
    if (!getAccessToken()) {
      return null
    }
    try {
      profile.value = await getMe()
      return profile.value
    } catch {
      // 401 已由 request 层清理登录态并广播；其它错误保留旧 profile
      return profile.value
    }
  }

  /** 只清理本地登录态（不请求服务端）；供 auth:logout 事件与登出共用 */
  function clearLocalSession(): void {
    clearTokens()
    hasToken.value = false
    profile.value = null
  }

  /** 退出登录：尽力吊销服务端 refresh 白名单，无论如何清本地态 */
  async function logout(): Promise<void> {
    const refreshToken = getRefreshToken()
    try {
      if (refreshToken) {
        await logoutApi(refreshToken)
      }
    } catch {
      // 服务端登出失败不阻塞本地清理（token 已无效时接口本身就会 401）
    }
    clearLocalSession()
  }

  return {
    profile,
    hasToken,
    isLoggedIn,
    isSeniorMode,
    login,
    fetchMe,
    clearLocalSession,
    logout,
  }
})