/** 订单 API：下单 / 双视角列表 / 状态流转（/api/v1/orders）。 */
import { get, patch, post } from './request'

import type { Page } from '@/types/api'
import type {
  OrderCreateParams,
  OrderOut,
  OrderRole,
  OrderStatusUpdateParams,
} from '@/types/order'

/** 下单（面交模式：金额由服务端按商品售价快照，缺省地点用商品校区） */
export function createOrder(params: OrderCreateParams): Promise<OrderOut> {
  return post<OrderOut>('/orders', params)
}

/** 我的订单列表：role=buyer 我买到的 / seller 我卖出的（分页） */
export function listOrders(
  role: OrderRole,
  params: { page?: number; page_size?: number } = {},
): Promise<Page<OrderOut>> {
  return get<Page<OrderOut>>('/orders', { params: { role, ...params } })
}

/** 更新订单状态（流转合法性由服务端状态机校验） */
export function updateOrderStatus(
  orderId: number,
  params: OrderStatusUpdateParams,
): Promise<OrderOut> {
  return patch<OrderOut>(`/orders/${orderId}/status`, params)
}
