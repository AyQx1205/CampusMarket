import type { ProductBrief } from './product'

/** 订单状态（与后端 OrderStatus 枚举 value 对齐） */
export type OrderStatus = 'pending' | 'confirmed' | 'completed' | 'cancelled'

/** 订单状态中文标签 */
export const ORDER_STATUS_LABELS: Record<OrderStatus, string> = {
  pending: '待确认',
  confirmed: '已确认',
  completed: '已完成',
  cancelled: '已取消',
}

/** POST /orders 下单（金额不传，服务端按商品售价快照） */
export interface OrderCreateParams {
  product_id: number
  trade_location?: string
  remark?: string
}

/** GET /orders 查询角色：我买到的 / 我卖出的 */
export type OrderRole = 'buyer' | 'seller'

/** 订单信息（对应后端 OrderOut，amount 为两位小数字符串） */
export interface OrderOut {
  id: number
  order_no: string
  product_id: number
  buyer_id: number
  seller_id: number
  amount: string
  status: OrderStatus
  trade_location: string | null
  remark: string | null
  created_at: string
  finished_at: string | null
  product: ProductBrief | null
}

/** PATCH /orders/{id}/status 请求体 */
export interface OrderStatusUpdateParams {
  status: OrderStatus
}
