/** 订单 API：下单 / 双视角列表 / 状态流转（/api/v1/orders）。 */
import { get, patch, post } from './request'

import type { Page } from '@/types/api'
import type {
  OrderCreateParams,
  OrderDetail,
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
): Promise<Page<OrderDetail>> {
  return get<Page<OrderDetail>>('/orders', { params: { role, ...params } })
}

/** 订单详情（含交易对手联系方式） */
export function getOrder(orderId: number): Promise<OrderDetail> {
  return get<OrderDetail>(`/orders/${orderId}`)
}

/** 更新订单状态（流转合法性由服务端状态机校验） */
export function updateOrderStatus(
  orderId: number,
  params: OrderStatusUpdateParams,
): Promise<OrderDetail> {
  return patch<OrderDetail>(`/orders/${orderId}/status`, params)
}
