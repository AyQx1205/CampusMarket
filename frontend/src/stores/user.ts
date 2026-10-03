/**
 * 用户 store：个人信息（持久化）+ 登录态。
 *
 * token 不放进 state：axios 拦截器在每个请求发出时同步读 localStorage
 * （utils/storage.ts），扁平 key 不依赖 Pinia 时序；store 里再存一份
 * 只会得到一份陈旧镜像（401 刷新时 request 层更新的是 storage）。
 * 登录态的响应式开关用 hasToken ref 维护，与 storage 严格同步。
 */
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { getMe } from '@/api/user'
import { login as loginApi, logout as logoutApi } from '@/api/auth'
import type { LoginParams, UserProfile } from '@/types/user'
import { clearTokens, getAccessToken, setTokens } from '@/utils/storage'

export const useUserStore = defineStore(
  'user',
  () => {
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
      profile.value = await getMe()
      return profile.value
    }

    /** 同步 token（供 token 刷新等场景手动维护登录态） */
    function applyTokens(access: string, refresh: string): void {
      setTokens(access, refresh)
      hasToken.value = true
    }

    /** 退出登录：尽力吊销服务端 refresh 白名单，无论如何清本地态 */
    async function logout(): Promise<void> {
      try {
        await logoutApi()
      } catch {
        // 服务端登出失败不阻塞本地清理（token 已无效时接口本身就会 401）
      }
      clearTokens()
      hasToken.value = false
      profile.value = null
    }

    return {
      profile,
      hasToken,
      isLoggedIn,
      isSeniorMode,
      login,
      fetchMe,
      applyTokens,
      logout,
    }
  },
  {
    // 持久化个人信息；token 不持久化进 store（单一事实源在 utils/storage.ts）
    persist: { pick: ['profile'] },
  },
)
