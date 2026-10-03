<script setup lang="ts">
/** 404 兜底页。 */
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
</script>

<template>
  <div class="not-found">
    <p class="code">404</p>
    <p class="text">页面走丢了（{{ route.path }}）</p>
    <el-button type="primary" @click="router.push('/')">回首页</el-button>
  </div>
</template>

<style scoped>
.not-found {
  min-height: 50vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.code {
  margin: 0;
  font-size: 72px;
  font-weight: 700;
  color: var(--color-primary);
}

.text {
  margin: 0 0 12px;
  color: var(--color-text-secondary);
}
</style>
