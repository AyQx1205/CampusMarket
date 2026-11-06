/** 用户 API：个人信息维护（/api/v1/users）。 */
import { get, patch } from './request'

import type { Page } from '@/types/api'
import type { ProductDetail, ProductStatus } from '@/types/product'
import type { UserProfile, UserPublic, UserUpdateParams } from '@/types/user'

/** 获取当前登录用户完整信息 */
export function getMe(): Promise<UserProfile> {
  return get<UserProfile>('/users/me')
}

/** 获取指定用户公开资料（不含学号/邮箱/手机号） */
export function getUser(userId: number): Promise<UserPublic> {
  return get<UserPublic>(`/users/${userId}`)
}

/** 修改个人信息（字段不传表示不修改） */
export function updateMe(params: UserUpdateParams): Promise<UserProfile> {
  return patch<UserProfile>('/users/me', params)
}

/** 查看指定用户发布的商品（分页） */
export function listUserProducts(
  userId: number,
  params: { status?: ProductStatus; page?: number; page_size?: number } = {},
): Promise<Page<ProductDetail>> {
  return get<Page<ProductDetail>>(`/users/${userId}/products`, { params })
}
