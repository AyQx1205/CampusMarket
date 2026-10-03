<script setup lang="ts">
/** AI 助手悬浮面板：FAB + 对话窗口，全局挂载在 App.vue，所有页面可用。
 *  窄屏（≤768px）改为全屏；关闭面板不清空会话（消息存 Pinia 持久化）。 */
import { nextTick, ref, watch } from 'vue'

import AiLauncher from './AiLauncher.vue'
import AiMessage from './AiMessage.vue'
import { QUICK_QUESTIONS, useAiChat } from '@/composables/useAiChat'

const {
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
} = useAiChat()

const listRef = ref<HTMLElement>()

/** 消息变化（新增/占位更新完成）时滚到底部 */
watch(
  messages,
  () => {
    nextTick(() => {
      listRef.value?.scrollTo({ top: listRef.value.scrollHeight, behavior: 'smooth' })
    })
  },
  { deep: true },
)
</script>

<template>
  <AiLauncher />

  <Transition name="panel">
    <section v-if="isOpen" class="panel" aria-label="AI 助手">
      <!-- 头部 -->
      <header class="panel-head">
        <span class="title">校园小助手</span>
        <span class="subtitle">有问必答的二手交易向导</span>
        <el-button class="close" text @click="toggle">关闭</el-button>
      </header>

      <!-- 未登录引导 -->
      <div v-if="isGuest" class="guest-tip">
        <p>请先登录后使用 AI 助手</p>
        <RouterLink to="/login">
          <el-button type="primary" size="small">去登录</el-button>
        </RouterLink>
      </div>

      <template v-else>
        <!-- 消息列表 -->
        <div ref="listRef" class="msg-list">
          <div v-if="messages.length === 0" class="welcome">
            <p>你好，我是校园小助手 👋</p>
            <p>可以问我怎么买卖东西、平台规则，也可以让我帮你找宝贝～</p>
          </div>

          <AiMessage v-for="msg in messages" :key="msg.id" :message="msg" @retry="retry" />

          <!-- 空会话时的快捷问题 -->
          <div v-if="showQuickQuestions" class="quick">
            <el-button
              v-for="q in QUICK_QUESTIONS"
              :key="q"
              size="small"
              round
              plain
              type="primary"
              :disabled="sending"
              @click="sendQuick(q)"
            >
              {{ q }}
            </el-button>
          </div>
        </div>

        <!-- 输入区 -->
        <div class="composer">
          <el-input
            v-model="draft"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 4 }"
            placeholder="输入你想问的..."
            resize="none"
            :disabled="sending"
            @keydown.enter.exact.prevent="send"
          />
          <el-button
            class="send"
            type="primary"
            :loading="sending"
            :disabled="!draft.trim()"
            @click="send"
          >
            发送
          </el-button>
        </div>
        <p class="hint">回车发送，Shift + 回车换行</p>
      </template>
    </section>
  </Transition>
</template>

<style scoped>
.panel {
  position: fixed;
  right: 88px;
  bottom: 24px;
  z-index: 1100;
  width: 380px;
  height: 560px;
  max-height: calc(100vh - 48px);
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
  border-radius: var(--radius-lg, 12px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.16);
  overflow: hidden;
}

.panel-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 14px 16px;
  background: var(--color-primary);
  color: #fff;
  flex-shrink: 0;
}

.title {
  font-size: 16px;
  font-weight: 700;
}

.subtitle {
  font-size: 12px;
  opacity: 0.85;
  flex: 1;
}

.close {
  color: #fff;

  --el-button-hover-text-color: #fff;
  --el-button-hover-bg-color: rgba(255, 255, 255, 0.15);
}

/* 未登录引导 */
.guest-tip {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--color-text-secondary);
}

.guest-tip p {
  margin: 0;
}

/* 消息列表 */
.msg-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.welcome {
  color: var(--color-text-secondary);
  font-size: 13px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-base);
  padding: 10px 12px;
  margin-bottom: 14px;
}

.welcome p {
  margin: 2px 0;
}

/* 快捷问题 */
.quick {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}

/* 输入区 */
.composer {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 12px 12px 0;
  flex-shrink: 0;
}

.send {
  flex-shrink: 0;
}

.hint {
  margin: 4px 16px 8px;
  font-size: 11px;
  color: var(--color-text-muted);
  flex-shrink: 0;
}

/* 展开/收起动效 */
.panel-enter-active,
.panel-leave-active {
  transition:
    opacity 0.18s ease,
    transform 0.18s ease;
}

.panel-enter-from,
.panel-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.98);
}

/* 窄屏：全屏（右下角 FAB 悬浮于面板之上，输入区右侧留出位置避免遮挡发送按钮） */
@media (max-width: 768px) {
  .panel {
    right: 0;
    bottom: 0;
    width: 100vw;
    height: 100vh;
    max-height: none;
    border-radius: 0;
  }

  .composer {
    padding-right: 72px;
  }
}
</style>
