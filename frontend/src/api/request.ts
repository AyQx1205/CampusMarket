/**
 * Axios 客户端封装：统一响应体剥壳 + 401 自动刷新重放。
 *
 * 契约（与后端 core/exceptions.py 对齐）：
 * - 统一响应体 {code, message, data}，code=0 成功；
 * - 业务错误 code≠0 走 HTTP 4xx/5xx，都 reject 出 BizError；
 *   FastAPI 原生 422 的 detail 也会被归一化成 BizError；
 * - HTTP 401 → 用 refresh_token 静默刷新并重放原请求一次；
 *   并发 401 共享同一个刷新 Promise（单飞），避免重复刷新；
 * - 刷新失败只清理本地登录态并广播 auth:logout，由 main.ts 用 router
 *   跳转（不做 window.location 硬刷新，避免丢失当前页面状态）。
 */
import axios, {
  type AxiosError,
  type AxiosResponse,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from 'axios'
import { ElMessage } from 'element-plus'

import type { ApiResponse } from '@/types/api'
import type { LoginResult } from '@/types/user'
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from '@/utils/storage'

/** 登录态失效广播：main.ts 监听后清理 store 并跳转登录页 */
export const AUTH_LOGOUT_EVENT = 'campus:auth-logout'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

// ---------------- 业务错误类型 ----------------

/** 携带后端业务码/HTTP 状态的错误（如 5001=AI 未配置，AI 组件按 code 定制 UI） */
export class BizError extends Error {
  code: number
  status: number

  constructor(code: number, message: string, status = 0) {
    super(message)
    this.name = 'BizError'
    this.code = code
    this.status = status
  }
}

// ---------------- 实例与拦截器 ----------------

const request = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
})

request.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/** 用裸 axios（不带拦截器）刷新，避免 401 循环 */
async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    return false
  }
  try {
    const resp = await axios.post<ApiResponse<LoginResult>>(
      `${API_BASE_URL}/auth/refresh`,
      { refresh_token: refreshToken },
      { timeout: 15000 },
    )
    if (resp.data.code !== 0) {
      return false
    }
    setTokens(resp.data.data.access_token, resp.data.data.refresh_token)
    return true
  } catch {
    return false
  }
}

/** 清本地登录态并通知应用跳登录页（保留 SPA 体验） */
function handleSessionExpired(): void {
  clearTokens()
  window.dispatchEvent(new CustomEvent(AUTH_LOGOUT_EVENT))
}

// 单飞刷新：并发 401 共享同一个 Promise，刷新完成后统一重放
let refreshingPromise: Promise<boolean> | null = null

function extractMessage(data: unknown, fallback: string): string {
  if (!data || typeof data !== 'object') {
    return fallback
  }
  const body = data as { message?: string; detail?: unknown }
  if (typeof body.message === 'string' && body.message) {
    return body.message
  }
  if (typeof body.detail === 'string' && body.detail) {
    return body.detail
  }
  // FastAPI 422：detail 是 [{loc, msg, type}, ...]
  if (Array.isArray(body.detail) && body.detail.length > 0) {
    const first = body.detail[0] as { msg?: unknown }
    if (typeof first?.msg === 'string') {
      return first.msg
    }
  }
  return fallback
}

async function onFulfilled(response: AxiosResponse): Promise<any> {
  const body = response.data as ApiResponse
  if (body.code === 0) {
    return body.data
  }
  const message = body.message || '操作失败'
  ElMessage.error(message)
  return Promise.reject(new BizError(body.code, message, response.status))
}

async function onRejected(error: AxiosError<ApiResponse>): Promise<any> {
  const config = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined
  const status = error.response?.status ?? 0

  // HTTP 401：静默刷新后重放一次（刷新/登录/登出接口自身 401 不重试）
  // 登出不重试很重要：它只需要 body 里的 refresh_token，access 过期也能吊销；
  // 若先刷新会白白轮换出一枚即将被本地丢弃的新 refresh token。
  const isNoRefreshUrl = ['/auth/refresh', '/auth/login', '/auth/logout'].some((path) =>
    config?.url?.includes(path),
  )
  if (status === 401 && config && !config._retried && !isNoRefreshUrl) {
    config._retried = true
    refreshingPromise = refreshingPromise ?? refreshAccessToken()
    const ok = await refreshingPromise.finally(() => {
      refreshingPromise = null
    })
    if (ok) {
      config.headers.Authorization = `Bearer ${getAccessToken()}`
      return request(config)
    }
    handleSessionExpired()
    return Promise.reject(new BizError(401, '登录已过期，请重新登录', 401))
  }

  // 已重试过仍 401：refresh 成功但 access 仍无效，直接结束登录态
  if (status === 401 && config?._retried) {
    handleSessionExpired()
    return Promise.reject(new BizError(401, '登录已过期，请重新登录', 401))
  }

  let message = '请求失败'
  if (status >= 500) {
    // 503 等降级响应带有可操作提示（如「登录服务暂时不可用」），优先展示
    message = extractMessage(error.response?.data, '服务器错误，请稍后再试')
  } else if (status === 0) {
    message = '网络异常，请检查网络连接'
  } else {
    message = extractMessage(error.response?.data, '请求失败')
  }

  ElMessage.error(message)
  const code =
    (error.response?.data as ApiResponse | undefined)?.code ?? (status || 0)
  return Promise.reject(new BizError(code, message, status))
}

request.interceptors.response.use(onFulfilled, onRejected)

// ---------------- 泛型请求方法（拦截器已剥壳，直接返回业务数据） ----------------

export function get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return request.get(url, config) as Promise<T>
}

export function post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  return request.post(url, data, config) as Promise<T>
}

export function patch<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  return request.patch(url, data, config) as Promise<T>
}

export function del<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return request.delete(url, config) as Promise<T>
}

export default request