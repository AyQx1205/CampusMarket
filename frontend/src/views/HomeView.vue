<script setup lang="ts">
/** 首页：筛选栏 + 商品网格 + 分页，请求参数完全由筛选条件驱动。 */
import { onMounted, ref, watch } from 'vue'

import { listProducts } from '@/api/product'
import ProductFilter from '@/components/product/ProductFilter.vue'
import ProductGrid from '@/components/product/ProductGrid.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import type { ProductDetail, ProductSearchParams } from '@/types/product'

const PAGE_SIZE = 20

const filters = ref<ProductSearchParams>({})
const page = ref(1)
const total = ref(0)
const products = ref<ProductDetail[]>([])
const loading = ref(false)
const failed = ref(false)
/** 请求序号：只接受最后一次请求的结果，避免快速筛选时旧响应覆盖新响应 */
let requestSeq = 0

async function fetchProducts(): Promise<void> {
  const seq = ++requestSeq
  loading.value = true
  failed.value = false
  try {
    const result = await listProducts({
      ...filters.value,
      page: page.value,
      page_size: PAGE_SIZE,
    })
    if (seq !== requestSeq) {
      return
    }
    products.value = result.items
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

function handleSearch(next: ProductSearchParams): void {
  filters.value = next
  page.value = 1 // 筛选变化回到第一页
}

function handleRetry(): void {
  fetchProducts()
}

watch([filters, page], fetchProducts)

onMounted(fetchProducts)
</script>

<template>
  <div class="home">
    <ProductFilter @search="handleSearch" />

    <EmptyState
      v-if="failed"
      description="商品加载失败，请稍后重试"
      action-text="重新加载"
      @action="handleRetry"
    />
    <ProductGrid v-else :products="products" :loading="loading" />

    <!-- 翻页（加载中禁用防连点） -->
    <div v-if="!failed && total > PAGE_SIZE" class="pagination">
      <el-pagination
        v-model:current-page="page"
        background
        layout="prev, pager, next, jumper, total"
        :total="total"
        :page-size="PAGE_SIZE"
        :disabled="loading"
      />
    </div>
  </div>
</template>

<style scoped>
.pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
