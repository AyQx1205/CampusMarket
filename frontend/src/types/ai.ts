import type { Page } from './api'
import type { ProductCondition, ProductDetail, ProductSort } from './product'

/** POST /ai/chat 请求体（session_id 由前端生成并复用，多轮记忆） */
export interface ChatParams {
  message: string
  session_id: string
}

/** POST /ai/chat 返回体 */
export interface ChatResult {
  session_id: string
  reply: string
}

/** POST /ai/listing/generate 请求体 */
export interface ListingDraftParams {
  raw_info: string
  expected_price?: number
  condition_hint?: string
}

/** AI 生成的商品文案草稿（发布前仍由卖家确认） */
export interface ListingDraftResult {
  title: string
  description: string
  highlights: string[]
  condition: ProductCondition
}

/** POST /ai/search 解析出的筛选条件 */
export interface AiSearchFilters {
  keyword?: string
  min_price?: number
  max_price?: number
  campus?: string
  sort: ProductSort
}

/** POST /ai/search 返回体：筛选条件 + 分页搜索结果 */
export interface AiSearchResult {
  filters: AiSearchFilters
  result: Page<ProductDetail>
}

/** AI 助手面板内的一条消息（stores/ai.ts 用） */
export interface AiChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  /** pending=等待回复；done=正常；error=失败（errorCode 区分原因） */
  status: 'pending' | 'done' | 'error'
  /** 失败时的业务码：5001=LLM 未配置；503=服务繁忙；无值=网络错误 */
  errorCode?: number
}
