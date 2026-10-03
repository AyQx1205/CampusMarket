/** 后端统一响应体：{code, message, data}（code=0 成功） */
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

/** 统一分页数据体（对应后端 schemas/common.py Page[T]） */
export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
