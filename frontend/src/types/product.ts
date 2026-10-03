/** 商品成色（与后端 ProductCondition 枚举 value 对齐） */
export type ProductCondition = 'brand_new' | 'like_new' | 'lightly_used' | 'heavily_used'

/** 商品状态 */
export type ProductStatus = 'on_sale' | 'reserved' | 'sold' | 'off_shelf'

/** 列表排序方式 */
export type ProductSort = 'latest' | 'price_asc' | 'price_desc' | 'hottest'

/** 成色中文标签（下拉/标签展示用） */
export const CONDITION_LABELS: Record<ProductCondition, string> = {
  brand_new: '全新',
  like_new: '几乎全新',
  lightly_used: '轻微使用',
  heavily_used: '明显使用',
}

/** 状态中文标签 */
export const STATUS_LABELS: Record<ProductStatus, string> = {
  on_sale: '在售',
  reserved: '已预订',
  sold: '已售出',
  off_shelf: '已下架',
}

/** 排序选项 */
export const SORT_OPTIONS: { value: ProductSort; label: string }[] = [
  { value: 'latest', label: '最新发布' },
  { value: 'price_asc', label: '价格从低到高' },
  { value: 'price_desc', label: '价格从高到低' },
  { value: 'hottest', label: '浏览最多' },
]

/**
 * 商品精简信息（订单/收藏里嵌套展示，对应后端 ProductBrief）。
 * 价格由后端 Decimal 序列化为两位小数字符串（如 "12.50"），前端不做二次格式化。
 */
export interface ProductBrief {
  id: number
  title: string
  price: string
  images: string[]
  status: ProductStatus
  campus: string | null
}

/** 商品完整信息（详情/列表共用，对应后端 ProductOut） */
export interface ProductDetail {
  id: number
  seller_id: number
  title: string
  description: string | null
  price: string
  original_price: string | null
  condition: ProductCondition
  category_id: number | null
  images: string[]
  campus: string | null
  status: ProductStatus
  view_count: number
  favorite_count: number
  created_at: string
  updated_at: string
}

/** GET /products 查询参数 */
export interface ProductSearchParams {
  page?: number
  page_size?: number
  keyword?: string
  category_id?: number
  min_price?: number
  max_price?: number
  campus?: string
  condition?: ProductCondition
  sort?: ProductSort
}

/** POST /products 发布商品 */
export interface ProductPublishParams {
  title: string
  description?: string
  price: number
  original_price?: number
  condition: ProductCondition
  category_id?: number
  images?: string[]
  campus?: string
}

/** PATCH /products/{id}：允许部分更新，含状态流转 */
export type ProductUpdateParams = Partial<ProductPublishParams> & {
  status?: ProductStatus
}
