<script setup lang="ts">
/** AI 助手悬浮按钮（FAB）：右下角，点击开合面板；展开时变为关闭样式。 */
import { ChatDotRound, Close } from '@element-plus/icons-vue'

import { useAiStore } from '@/stores/ai'

const aiStore = useAiStore()
</script>

<template>
  <button
    class="fab"
    :class="{ open: aiStore.isOpen }"
    type="button"
    :title="aiStore.isOpen ? '收起助手' : '打开 AI 助手'"
    @click="aiStore.togglePanel()"
  >
    <el-icon :size="24">
      <Close v-if="aiStore.isOpen" />
      <ChatDotRound v-else />
    </el-icon>
  </button>
</template>

<style scoped>
.fab {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 1100;
  width: 52px;
  height: 52px;
  border: none;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-card);
  transition:
    transform 0.15s,
    background 0.15s;
}

.fab:hover {
  transform: scale(1.06);
}

/* 面板打开时按钮随面板位置（窄屏全屏时贴面板右上视觉） */
.fab.open {
  background: var(--color-text);
}

@media (max-width: 768px) {
  .fab {
    right: 16px;
    bottom: 16px;
  }
}
</style>
