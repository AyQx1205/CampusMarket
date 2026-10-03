/** 收藏 API：我的收藏列表（收藏/取消动作挂在商品资源上，见 product.ts）。 */
import { get } from './request'

import type { Page } from '@/types/api'
import type { ProductBrief } from '@/types/product'

/** 单条收藏记录：收藏时间 + 商品精简信息（对应后端 FavoriteOut） */
export interface FavoriteOut {
  id: number
  product: ProductBrief
  created_at: string
}

/** 我的收藏列表（分页） */
export function listFavorites(
  params: { page?: number; page_size?: number } = {},
): Promise<Page<FavoriteOut>> {
  return get<Page<FavoriteOut>>('/favorites', { params })
}
