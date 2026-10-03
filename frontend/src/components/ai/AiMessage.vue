<script setup lang="ts">
/** 单条 AI 消息：用户右对齐蓝底白字；AI 左对齐白底 markdown（DOMPurify 消毒防 XSS）。 */
import { computed } from 'vue'
import DOMPurify from 'dompurify'
import { marked } from 'marked'

import type { AiChatMessage } from '@/types/ai'

const props = defineProps<{
  message: AiChatMessage
}>()

const emit = defineEmits<{
  retry: []
}>()

/** AI 正常回复走 markdown；用户消息/错误/占位一律纯文本（模板插值，天然防注入） */
const markdownHtml = computed(() => {
  if (props.message.role !== 'assistant' || props.message.status !== 'done') {
    return ''
  }
  // marked v14 同步模式；DOMPurify 清掉脚本/事件属性后再 v-html
  return DOMPurify.sanitize(marked.parse(props.message.content, { async: false }))
})

/** 网络错误（无业务码）才给重试按钮；5001/503 只展示文案 */
const canRetry = computed(
  () => props.message.status === 'error' && props.message.errorCode === undefined,
)
</script>

<template>
  <div class="msg-row" :class="message.role === 'user' ? 'is-user' : 'is-ai'">
    <!-- AI 头像 -->
    <div v-if="message.role === 'assistant'" class="avatar">助</div>

    <div class="bubble-wrap">
      <!-- 思考中：三点打字动画 -->
      <div v-if="message.status === 'pending'" class="bubble pending">
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
      </div>

      <!-- 失败：文案 +（网络错误时）重试按钮 -->
      <div v-else-if="message.status === 'error'" class="bubble error">
        <p class="error-text">{{ message.content }}</p>
        <el-button v-if="canRetry" size="small" text type="primary" @click="emit('retry')">
          重新发送
        </el-button>
      </div>

      <!-- 用户消息：纯文本，蓝底白字 -->
      <div v-else-if="message.role === 'user'" class="bubble user-bubble">
        {{ message.content }}
      </div>

      <!-- AI 回复：markdown 渲染 -->
      <!-- eslint-disable-next-line vue/no-v-html —— 内容已经 DOMPurify 消毒 -->
      <div v-else class="bubble ai-bubble markdown" v-html="markdownHtml"></div>
    </div>
  </div>
</template>

<style scoped>
.msg-row {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
  align-items: flex-start;
}

.is-user {
  justify-content: flex-end;
}

.avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--color-primary);
  color: #fff;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.bubble-wrap {
  max-width: 82%;
  min-width: 0;
}

.is-user .bubble-wrap {
  display: flex;
  justify-content: flex-end;
}

.bubble {
  padding: 8px 12px;
  border-radius: var(--radius-base);
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

/* 用户：蓝底白字 */
.user-bubble {
  background: var(--el-color-primary, #409eff);
  color: #fff;
  border-bottom-right-radius: 4px;
}

/* AI：白底黑字 */
.ai-bubble {
  background: var(--color-bg-card);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-bottom-left-radius: 4px;
}

/* markdown 内元素贴合气泡 */
.markdown :deep(p) {
  margin: 0 0 6px;
}

.markdown :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown :deep(ul),
.markdown :deep(ol) {
  margin: 4px 0;
  padding-left: 18px;
}

.markdown :deep(code) {
  background: var(--color-bg);
  padding: 1px 4px;
  border-radius: 4px;
  font-size: 13px;
}

.markdown :deep(pre) {
  background: var(--color-bg);
  padding: 8px;
  border-radius: var(--radius-sm);
  overflow-x: auto;
}

.markdown :deep(a) {
  color: var(--color-primary);
}

/* 错误气泡 */
.error {
  background: #fdf0ef;
  color: var(--el-color-danger, #f56c6c);
  border: 1px solid #fde2e2;
}

.error-text {
  margin: 0;
}

/* 思考中：三点跳动 */
.pending {
  display: flex;
  gap: 4px;
  align-items: center;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  padding: 12px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-text-muted);
  animation: bounce 1.2s infinite ease-in-out;
}

.dot:nth-child(2) {
  animation-delay: 0.15s;
}

.dot:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes bounce {
  0%,
  60%,
  100% {
    transform: translateY(0);
    opacity: 0.5;
  }

  30% {
    transform: translateY(-4px);
    opacity: 1;
  }
}
</style>
