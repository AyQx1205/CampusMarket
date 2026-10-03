/**
 * Axios 客户端封装：统一响应体剥壳 + 401 自动刷新重放。
 *
 * 契约（与后端 core/exceptions.py 对齐）：
 * - 统一响应体 {code, message, data}，code=0 成功；
 * - 业务错误 code≠0 走 HTTP 4xx/5xx 或 200，都 reject 出 BizError；
 * - HTTP 401 → 用 refresh_token 静默刷新并重放原请求一次；
 *   并发 401 共享同一个刷新 Promise（单飞），避免重复刷新。
 *
 * Token 读写统一在 utils/storage.ts（登录态单一事实源），
 * stores/user 登录成功后调用 setTokens 持久化。
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

// ---------------- 业务错误类型 ----------------

/** 携带后端业务码的错误（如 5001=AI 未配置，AI 组件按 code 定制 UI） */
export class BizError extends Error {
  code: number

  constructor(code: number, message: string) {
    super(message)
    this.code = code
  }
}

// ---------------- 实例与拦截器 ----------------

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
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
      `${import.meta.env.VITE_API_BASE_URL}/auth/refresh`,
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

/** 清登录态并回登录页（路由未接入前用 location 兜底，router 接入后行为一致） */
function redirectToLogin(): void {
  clearTokens()
  if (!window.location.pathname.startsWith('/login')) {
    window.location.href = '/login'
  }
}

// 单飞刷新：并发 401 共享同一个 Promise，刷新完成后统一重放
let refreshingPromise: Promise<boolean> | null = null

// 拦截器剥壳后返回的是业务数据（非 AxiosResponse），
// 返回类型 Promise<any> 有意豁免 axios 的泛型约束（主流做法）。
async function onFulfilled(response: AxiosResponse): Promise<any> {
  const body = response.data as ApiResponse
  if (body.code === 0) {
    return body.data
  }
  // code≠0：统一 toast（调用方可通过 BizError.code 定制处理）
  ElMessage.error(body.message || '操作失败')
  return Promise.reject(new BizError(body.code, body.message || '操作失败'))
}

async function onRejected(error: AxiosError<ApiResponse>): Promise<any> {
  const config = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined

  // HTTP 401：静默刷新后重放一次（刷新接口/登录接口自身 401 不重试）
  const isAuthUrl = config?.url?.includes('/auth/refresh') || config?.url?.includes('/auth/login')
  if (error.response?.status === 401 && config && !config._retried && !isAuthUrl) {
    config._retried = true
    refreshingPromise = refreshingPromise ?? refreshAccessToken()
    const ok = await refreshingPromise.finally(() => {
      refreshingPromise = null
    })
    if (ok) {
      config.headers.Authorization = `Bearer ${getAccessToken()}`
      return request(config)
    }
    redirectToLogin()
    return Promise.reject(new BizError(401, '登录已过期，请重新登录'))
  }

  if (error.response && error.response.status >= 500) {
    ElMessage.error('服务器错误，请稍后再试')
  } else if (error.response) {
    // 4xx：优先统一响应体 message；兜底 FastAPI 原生 detail（个别未走统一响应体的校验错误）
    const data = error.response.data as ApiResponse | undefined
    const message =
      data?.message || (data as { detail?: string } | undefined)?.detail || '请求失败'
    ElMessage.error(message)
  } else {
    ElMessage.error('网络异常，请检查网络连接')
  }
  return Promise.reject(error)
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
