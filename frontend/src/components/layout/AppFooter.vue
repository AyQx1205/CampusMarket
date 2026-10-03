<script setup lang="ts">
/** 全局底栏：简单版权信息。 */
const year = new Date().getFullYear()
</script>

<template>
  <footer class="app-footer">
    <div class="container">
      <p>© {{ year }} 校园二手集市 · 让闲置流转起来</p>
      <p class="tip">仅限校园内线下当面交易，请勿站外转账</p>
    </div>
  </footer>
</template>

<style scoped>
.app-footer {
  margin-top: auto;
  padding: 20px 0;
  background: var(--color-bg-card);
  border-top: 1px solid var(--color-border);
  text-align: center;
  color: var(--color-text-muted);
  font-size: 13px;
}

p {
  margin: 4px 0;
}

.tip {
  font-size: 12px;
}
</style>
