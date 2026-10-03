/** 商品 API：搜索 / 详情 / 发布 / 更新 / 删除 / 热门榜 / 收藏动作（/api/v1/products）。 */
import { del, get, patch, post } from './request'

import type { Page } from '@/types/api'
import type {
  ProductDetail,
  ProductPublishParams,
  ProductSearchParams,
  ProductUpdateParams,
} from '@/types/product'

/** 分页搜索商品（关键词/分类/价格区间/校区/排序组合筛选） */
export function listProducts(params: ProductSearchParams): Promise<Page<ProductDetail>> {
  return get<Page<ProductDetail>>('/products', { params })
}

/** 商品详情（后端自动累加浏览量并写热门榜） */
export function getProductDetail(id: number): Promise<ProductDetail> {
  return get<ProductDetail>(`/products/${id}`)
}

/** 热门商品榜（Redis ZSet Top N，空榜兜底最新在售） */
export function listHotProducts(limit = 10): Promise<ProductDetail[]> {
  return get<ProductDetail[]>('/products/hot', { params: { limit } })
}

/** 发布商品 */
export function createProduct(params: ProductPublishParams): Promise<ProductDetail> {
  return post<ProductDetail>('/products', params)
}

/** 更新自己发布的商品（部分更新 + 状态流转） */
export function updateProduct(id: number, params: ProductUpdateParams): Promise<ProductDetail> {
  return patch<ProductDetail>(`/products/${id}`, params)
}

/** 删除自己发布的商品（已有订单记录会被后端拒绝，提示改为下架） */
export function deleteProduct(id: number): Promise<null> {
  return del<null>(`/products/${id}`)
}

/** 收藏商品 */
export function favoriteProduct(id: number): Promise<null> {
  return post<null>(`/products/${id}/favorite`)
}

/** 取消收藏 */
export function unfavoriteProduct(id: number): Promise<null> {
  return del<null>(`/products/${id}/favorite`)
}
