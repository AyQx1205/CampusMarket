<script setup lang="ts">
/** 我的收藏：网格展示（复用 ProductCard）+ 取消收藏 + 分页。 */
import { onMounted, ref, watch } from 'vue'

import { unfavoriteProduct } from '@/api/product'
import { listFavorites, type FavoriteOut } from '@/api/favorite'
import ProductCard from '@/components/product/ProductCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const PAGE_SIZE = 12

const favorites = ref<FavoriteOut[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const failed = ref(false)
/** 行级取消 loading */
const removingId = ref<number | null>(null)
/** 请求序号：翻页/重试过快时只接受最后一次响应 */
let requestSeq = 0

async function fetchFavorites(): Promise<void> {
  const seq = ++requestSeq
  loading.value = true
  failed.value = false
  try {
    const result = await listFavorites({ page: page.value, page_size: PAGE_SIZE })
    if (seq !== requestSeq) {
      return
    }
    favorites.value = result.items
    total.value = result.total
  } catch {
    if (seq === requestSeq) {
      failed.value = true
    }
  } finally {
    if (seq === requestSeq) {
      loading.value = false
    }
  }
}

async function removeFavorite(item: FavoriteOut): Promise<void> {
  removingId.value = item.id
  try {
    await unfavoriteProduct(item.product.id)
    // 本地移除；当前页被清空时回退一页重新拉取
    favorites.value = favorites.value.filter((f) => f.id !== item.id)
    total.value = Math.max(0, total.value - 1)
    if (favorites.value.length === 0 && page.value > 1) {
      page.value -= 1
    }
  } catch {
    // 提示由拦截器弹出
  } finally {
    removingId.value = null
  }
}

function handleRetry(): void {
  fetchFavorites()
}

watch(page, fetchFavorites)
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

    <div v-if="!failed && total > PAGE_SIZE" class="pagination">
      <el-pagination
        v-model:current-page="page"
        background
        layout="prev, pager, next, total"
        :total="total"
        :page-size="PAGE_SIZE"
        :disabled="loading"
      />
    </div>
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

.pagination {
  display: flex;
  justify-content: center;
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
