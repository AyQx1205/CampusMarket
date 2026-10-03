/**
 * AI 对话 composable：对 stores/ai.ts 的薄封装，供 AI 面板组件使用。
 *
 * 职责边界：
 * - 消息收发/错误映射/重试逻辑都在 store（跨页面持久化、可复用）；
 * - 本层只补组件侧的输入草稿状态与登录态快照，避免组件直接碰 store 细节。
 */
import { computed, ref } from 'vue'

import { useAiStore } from '@/stores/ai'
import { useUserStore } from '@/stores/user'

/** 首次打开时的快捷问题（面板空会话时展示） */
export const QUICK_QUESTIONS = ['怎么发布商品？', '帮我找便宜的自行车', '我想卖东西，怎么操作？'] as const

export function useAiChat() {
  const aiStore = useAiStore()
  const userStore = useUserStore()

  /** 输入框草稿（纯组件态，不进 store） */
  const draft = ref('')

  const messages = computed(() => aiStore.messages)
  const sending = computed(() => aiStore.sending)
  const isOpen = computed(() => aiStore.isOpen)
  /** 未登录时面板顶部显示引导提示，并禁用输入 */
  const isGuest = computed(() => !userStore.isLoggedIn)
  /** 空会话（无任何用户消息）时展示快捷问题 */
  const showQuickQuestions = computed(() => !messages.value.some((m) => m.role === 'user'))

  /** 发送当前草稿并清空输入框 */
  async function send(): Promise<void> {
    const text = draft.value.trim()
    if (!text || sending.value) {
      return
    }
    draft.value = ''
    await aiStore.sendMessage(text)
  }

  /** 点击快捷问题：直接作为用户消息发送 */
  async function sendQuick(question: string): Promise<void> {
    if (sending.value) {
      return
    }
    await aiStore.sendMessage(question)
  }

  /** 重试最后一条失败消息（网络错误时展示的按钮） */
  async function retry(): Promise<void> {
    await aiStore.retryLast()
  }

  function toggle(): void {
    aiStore.togglePanel()
  }

  return {
    draft,
    messages,
    sending,
    isOpen,
    isGuest,
    showQuickQuestions,
    send,
    sendQuick,
    retry,
    toggle,
  }
}
