<script setup lang="ts">
/** 商品网格：桌面 4 列 / 平板 3 列 / 手机 2 列，空状态走 EmptyState。 */
import ProductCard from './ProductCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import type { ProductDetail } from '@/types/product'

withDefaults(
  defineProps<{
    products: ProductDetail[]
    loading?: boolean
    emptyText?: string
    emptyActionText?: string
  }>(),
  {
    loading: false,
    emptyText: '没有找到相关商品',
    emptyActionText: '',
  },
)

const emit = defineEmits<{
  emptyAction: []
}>()
</script>

<template>
  <!-- 首次加载显示骨架 -->
  <div v-if="loading" class="grid">
    <div v-for="i in 8" :key="i" class="skeleton-item">
      <el-skeleton animated :rows="3" />
    </div>
  </div>

  <EmptyState
    v-else-if="products.length === 0"
    :description="emptyText"
    :action-text="emptyActionText"
    @action="emit('emptyAction')"
  />

  <div v-else class="grid">
    <ProductCard v-for="p in products" :key="p.id" :product="p" />
  </div>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-top: 16px;
}

.skeleton-item {
  border-radius: var(--radius-base);
  background: var(--color-bg-card);
  padding: 12px;
}

@media (max-width: 1024px) {
  .grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
}
</style>
