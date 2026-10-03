/** 展示格式化工具。 */

import dayjs from 'dayjs'

import { CONDITION_LABELS, type ProductCondition } from '@/types/product'

/**
 * 价格展示：后端 Decimal 已序列化为两位小数字符串（如 "12.50"），
 * 这里只补货币符号，不做数值格式化，避免二次舍入。
 */
export function formatPrice(price: string | number): string {
  return `¥${price}`
}

/** 时间展示：ISO 字符串 → YYYY-MM-DD HH:mm */
export function formatTime(iso: string, fmt = 'YYYY-MM-DD HH:mm'): string {
  return dayjs(iso).format(fmt)
}

/** 成色枚举 → 中文标签（未知值原样返回） */
export function conditionLabel(condition: ProductCondition): string {
  return CONDITION_LABELS[condition] ?? condition
}
