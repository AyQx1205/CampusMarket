/** 用户 API：个人信息维护（/api/v1/users）。 */
import { get, patch } from './request'

import type { Page } from '@/types/api'
import type { ProductDetail } from '@/types/product'
import type { UserProfile, UserUpdateParams } from '@/types/user'

/** 获取当前登录用户完整信息 */
export function getMe(): Promise<UserProfile> {
  return get<UserProfile>('/users/me')
}

/** 修改个人信息（字段不传表示不修改） */
export function updateMe(params: UserUpdateParams): Promise<UserProfile> {
  return patch<UserProfile>('/users/me', params)
}

/** 查看指定用户发布的商品（分页） */
export function listUserProducts(
  userId: number,
  params: { status?: string; page?: number; page_size?: number } = {},
): Promise<Page<ProductDetail>> {
  return get<Page<ProductDetail>>(`/users/${userId}/products`, { params })
}
