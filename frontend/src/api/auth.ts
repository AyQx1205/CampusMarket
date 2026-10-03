/** 认证 API：注册 / 登录 / 刷新 / 登出（/api/v1/auth）。 */
import { del, post } from './request'

import type { LoginParams, LoginResult, RegisterParams, UserProfile } from '@/types/user'

/** 注册新账号，成功后返回用户公开信息 */
export function register(params: RegisterParams): Promise<UserProfile> {
  return post<UserProfile>('/auth/register', params)
}

/** 学号 + 密码登录，返回双 Token（调用方负责 setTokens 持久化） */
export function login(params: LoginParams): Promise<LoginResult> {
  return post<LoginResult>('/auth/login', params)
}

/** 用 refresh_token 换新令牌对（request.ts 的 401 拦截器已自动处理，一般无需手动调用） */
export function refreshToken(refreshToken: string): Promise<LoginResult> {
  return post<LoginResult>('/auth/refresh', { refresh_token: refreshToken })
}

/** 登出：服务端吊销 refresh_token 白名单（jti），前端配合 clearTokens */
export function logout(): Promise<null> {
  return del<null>('/auth/logout')
}
