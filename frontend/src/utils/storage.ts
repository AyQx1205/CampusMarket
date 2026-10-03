/**
 * Token 本地存储读写：登录态在 localStorage 的单一事实源。
 *
 * 为什么不放进 Pinia state：axios 请求拦截器（api/request.ts）在每个请求
 * 发出时同步读 token，扁平 localStorage 不依赖 Pinia 初始化时序，
 * 也避免 store 与拦截器双写同一份 token 造成漂移。
 * user store 只持有 profile（UI 展示态），登录态判断走 getAccessToken()。
 */

const ACCESS_KEY = 'campus_access_token'
const REFRESH_KEY = 'campus_refresh_token'

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY)
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem(ACCESS_KEY, access)
  localStorage.setItem(REFRESH_KEY, refresh)
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}
