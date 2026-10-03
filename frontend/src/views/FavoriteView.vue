<script setup lang="ts">
/** 我的收藏：网格展示（复用 ProductCard）+ 取消收藏。 */
import { onMounted, ref } from 'vue'

import { unfavoriteProduct } from '@/api/product'
import { listFavorites, type FavoriteOut } from '@/api/favorite'
import ProductCard from '@/components/product/ProductCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const favorites = ref<FavoriteOut[]>([])
const total = ref(0)
const loading = ref(false)
const failed = ref(false)
/** 行级取消 loading */
const removingId = ref<number | null>(null)

async function fetchFavorites(): Promise<void> {
  loading.value = true
  failed.value = false
  try {
    const result = await listFavorites({ page: 1, page_size: 100 })
    favorites.value = result.items
    total.value = result.total
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
}

async function removeFavorite(item: FavoriteOut): Promise<void> {
  removingId.value = item.id
  try {
    await unfavoriteProduct(item.product.id)
    // 本地移除，避免整页刷新
    favorites.value = favorites.value.filter((f) => f.id !== item.id)
    total.value -= 1
  } catch {
    // 提示由拦截器弹出
  } finally {
    removingId.value = null
  }
}

function handleRetry(): void {
  fetchFavorites()
}

onMounted(fetchFavorites)
</script>

<template>
  <div class="favorite-page">
    <div class="head">
      <h2>我的收藏</h2>
      <span v-if="!failed && !loading" class="count">共 {{ total }} 件</span>
    </div>

    <EmptyState
      v-if="failed"
      description="收藏加载失败，请稍后重试"
      action-text="重新加载"
      @action="handleRetry"
    />

    <div v-else-if="loading" class="grid">
      <div v-for="i in 4" :key="i" class="skeleton-item">
        <el-skeleton animated :rows="3" />
      </div>
    </div>

    <EmptyState
      v-else-if="favorites.length === 0"
      description="还没有收藏任何商品"
      action-text="去逛逛"
      @action="$router.push('/')"
    />

    <template v-else>
      <div class="grid">
        <div v-for="item in favorites" :key="item.id" class="cell">
          <ProductCard :product="item.product" />
          <el-button
            class="remove"
            size="small"
            text
            type="danger"
            :loading="removingId === item.id"
            @click="removeFavorite(item)"
          >
            取消收藏
          </el-button>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.favorite-page {
  max-width: var(--content-max-width);
  margin: 0 auto;
}

.head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 12px;
}

h2 {
  margin: 0;
  font-size: 18px;
}

.count {
  color: var(--color-text-secondary);
  font-size: 13px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.remove {
  align-self: center;
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
