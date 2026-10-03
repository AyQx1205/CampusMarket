/**
 * AI 助手 store：会话消息 / session_id / 面板开关。
 *
 * - session_id 格式 web-{userId}-{timestamp}，首次打开面板时生成；
 *   检测到登录用户变化（id 不匹配）自动重置，避免串会话。
 * - messages 持久化到 localStorage，刷新页面不丢会话；
 *   isOpen 为纯 UI 态，不持久化。
 * - 错误文案约定（与 PROMPT 对齐）：
 *   code=5001 → 「AI 助手暂未上线」；HTTP 503 → 「助手忙不过来，稍后再试」；
 *   其余 → 网络错误文案 + 可重试。
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

import { chat } from '@/api/ai'
import { BizError } from '@/api/request'
import type { AiChatMessage } from '@/types/ai'
import { useUserStore } from './user'

/** 按业务码映射的失败文案 */
const ERROR_TEXT: Record<number, string> = {
  5001: 'AI 助手暂未上线',
  503: '助手忙不过来，稍后再试',
}
const NETWORK_ERROR_TEXT = '网络不太顺畅，请检查后再试'
const LOGIN_REQUIRED_TEXT = '请先登录后使用 AI 助手'

let msgSeq = 0
function nextId(): string {
  msgSeq += 1
  return `msg-${Date.now()}-${msgSeq}`
}

export const useAiStore = defineStore(
  'ai',
  () => {
    const isOpen = ref(false)
    const sessionId = ref('')
    const messages = ref<AiChatMessage[]>([])
    const sending = ref(false)

    /** 会话未创建或登录用户已切换时，重新生成 session_id 并清空消息 */
    function ensureSession(): void {
      const userId = useUserStore().profile?.id
      const prefix = `web-${userId ?? 0}-`
      if (!sessionId.value || !sessionId.value.startsWith(prefix)) {
        resetSession()
      }
    }

    /** 开新会话：重新生成 session_id、清空消息 */
    function resetSession(): void {
      const userId = useUserStore().profile?.id ?? 0
      sessionId.value = `web-${userId}-${Date.now()}`
      messages.value = []
    }

    /** 打开/收起面板；首次打开时确保会话存在 */
    function togglePanel(): void {
      isOpen.value = !isOpen.value
      if (isOpen.value) {
        ensureSession()
      }
    }

    function pushError(content: string, errorCode?: number): void {
      messages.value.push({
        id: nextId(),
        role: 'assistant',
        content,
        status: 'error',
        errorCode,
      })
    }

    /** 发送一条消息：乐观插入用户消息 + AI 占位，完成后原地更新 */
    async function sendMessage(content: string): Promise<void> {
      const text = content.trim()
      if (!text || sending.value) {
        return
      }
      if (!useUserStore().isLoggedIn) {
        pushError(LOGIN_REQUIRED_TEXT)
        return
      }
      ensureSession()

      sending.value = true
      messages.value.push({ id: nextId(), role: 'user', content: text, status: 'done' })
      const placeholderId = nextId()
      messages.value.push({
        id: placeholderId,
        role: 'assistant',
        content: '',
        status: 'pending',
      })

      try {
        const result = await chat({ message: text, session_id: sessionId.value })
        sessionId.value = result.session_id
        const target = messages.value.find((m) => m.id === placeholderId)
        if (target) {
          target.status = 'done'
          target.content = result.reply
        }
      } catch (err) {
        // 失败时移除占位，保留用户消息供重试
        messages.value = messages.value.filter((m) => m.id !== placeholderId)
        if (err instanceof BizError) {
          pushError(ERROR_TEXT[err.code] ?? err.message, err.code)
        } else {
          pushError(NETWORK_ERROR_TEXT)
        }
      } finally {
        sending.value = false
      }
    }

    /** 重试最后一条失败消息（网络错误/服务繁忙时由组件的重试按钮触发） */
    async function retryLast(): Promise<void> {
      if (sending.value) {
        return
      }
      // 从后往前找最近一条用户消息；先把尾部失败的 AI 消息清掉再重发
      for (let i = messages.value.length - 1; i >= 0; i -= 1) {
        const msg = messages.value[i]
        if (msg.role === 'user') {
          messages.value = messages.value.slice(0, i)
          await sendMessage(msg.content)
          return
        }
      }
    }

    return {
      isOpen,
      sessionId,
      messages,
      sending,
      togglePanel,
      resetSession,
      sendMessage,
      retryLast,
    }
  },
  {
    // 会话消息与 session_id 持久化（刷新不丢）；面板开合为纯 UI 态
    persist: { pick: ['sessionId', 'messages'] },
  },
)
