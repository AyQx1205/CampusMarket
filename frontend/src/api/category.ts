/** 分类 API：公开只读（/api/v1/categories）。 */
import { get } from './request'

import type { Category } from '@/types/product'

/** 全部分类（发布/筛选下拉） */
export function listCategories(): Promise<Category[]> {
  return get<Category[]>('/categories')
}