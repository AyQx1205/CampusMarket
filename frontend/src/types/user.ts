/** 当前登录用户完整信息（GET /users/me，对应后端 UserMeOut） */
export interface UserProfile {
  id: number
  student_no: string
  nickname: string
  email: string | null
  phone: string | null
  avatar_url: string | null
  campus: string | null
  credit_score: number
  is_senior_mode: boolean
  created_at: string
}

/** 公开用户信息（商品/订单里嵌套展示，对应后端 UserOut） */
export interface UserBrief {
  id: number
  nickname: string
  avatar_url: string | null
  campus: string | null
  credit_score: number
  created_at: string
}

/** 登录/刷新成功返回的令牌对（对应后端 TokenPair） */
export interface LoginResult {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface RegisterParams {
  student_no: string
  nickname: string
  password: string
  email?: string
  phone?: string
  campus?: string
}

export interface LoginParams {
  student_no: string
  password: string
}

/** PATCH /users/me 请求体（字段不传表示不修改） */
export interface UserUpdateParams {
  nickname?: string
  email?: string
  phone?: string
  avatar_url?: string
  campus?: string
  is_senior_mode?: boolean
}
