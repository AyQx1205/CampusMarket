/** AI 助手 API：对话 / 文案生成 / 自然语言搜索（/api/v1/ai，全部需要登录）。
 *
 * 错误处理约定（配合 request.ts 的 BizError）：
 * - code=5001 → LLM 未配置，AI 组件显示「AI 助手暂未上线」；
 * - HTTP 503（code=503）→ 助手繁忙，显示「助手忙不过来，稍后再试」。
 */
import { post } from './request'

import type {
  AiSearchResult,
  ChatParams,
  ChatResult,
  ListingDraftParams,
  ListingDraftResult,
} from '@/types/ai'

/** 多轮对话：session_id 由前端生成（web-{userId}-{timestamp}）并复用 */
export function chat(params: ChatParams): Promise<ChatResult> {
  return post<ChatResult>('/ai/chat', params)
}

/** 卖家文案生成：原始描述 → 结构化草稿（发布前仍由卖家确认） */
export function generateListing(params: ListingDraftParams): Promise<ListingDraftResult> {
  return post<ListingDraftResult>('/ai/listing/generate', params)
}

/** 自然语言搜索：LLM 解析筛选条件并直接返回分页结果 */
export function aiSearch(query: string): Promise<AiSearchResult> {
  return post<AiSearchResult>('/ai/search', { query })
}
