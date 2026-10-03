/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 后端 API 基础地址（含 /api/v1 前缀） */
  readonly VITE_API_BASE_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}
