<script setup lang="ts">
/** 我的订单：我买到的 / 我卖出的双 Tab 列表 + 状态流转（确认完成）。 */
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { listOrders, updateOrderStatus } from '@/api/order'
import EmptyState from '@/components/common/EmptyState.vue'
import { formatPrice, formatTime } from '@/utils/format'
import { ORDER_STATUS_LABELS, type OrderOut, type OrderRole, type OrderStatus } from '@/types/order'

const router = useRouter()

const PAGE_SIZE = 10
const TAB_LABELS: { role: OrderRole; label: string }[] = [
  { role: 'buyer', label: '我买到的' },
  { role: 'seller', label: '我卖出的' },
]

/** 状态 → el-tag 配色 */
const STATUS_TAG_TYPE: Record<OrderStatus, 'warning' | 'primary' | 'success' | 'info'> = {
  pending: 'warning',
  confirmed: 'primary',
  completed: 'success',
  cancelled: 'info',
}

const activeRole = ref<OrderRole>('buyer')
const orders = ref<OrderOut[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const failed = ref(false)
/** 行级操作 loading（按订单 id 记录，防止连点） */
const confirmingId = ref<number | null>(null)

async function fetchOrders(): Promise<void> {
  loading.value = true
  failed.value = false
  try {
    const result = await listOrders(activeRole.value, { page: page.value, page_size: PAGE_SIZE })
    orders.value = result.items
    total.value = result.total
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
}

/** pending → completed（面交完成后确认） */
async function confirmComplete(order: OrderOut): Promise<void> {
  confirmingId.value = order.id
  try {
    await updateOrderStatus(order.id, { status: 'completed' })
    order.status = 'completed'
  } catch {
    // 如流转非法等提示由拦截器弹出
  } finally {
    confirmingId.value = null
  }
}

function handleRetry(): void {
  fetchOrders()
}

// 切 Tab：回第一页（已是第一页则直接拉取）；翻页由 page watch 单独拉取
watch(activeRole, () => {
  if (page.value === 1) {
    fetchOrders()
  } else {
    page.value = 1
  }
})
watch(page, fetchOrders)

onMounted(fetchOrders)
</script>

<template>
  <div class="order-page">
    <el-tabs v-model="activeRole" class="tabs">
      <el-tab-pane v-for="tab in TAB_LABELS" :key="tab.role" :label="tab.label" :name="tab.role" />
    </el-tabs>

    <EmptyState
      v-if="failed"
      description="订单加载失败，请稍后重试"
      action-text="重新加载"
      @action="handleRetry"
    />

    <el-table v-else v-loading="loading" :data="orders" class="table">
      <el-table-column label="订单号" prop="order_no" width="200" show-overflow-tooltip />
      <el-table-column label="商品" min-width="180">
        <template #default="{ row }">
          <el-link
            v-if="row.product"
            type="primary"
            :underline="false"
            @click="router.push(`/product/${row.product.id}`)"
          >
            {{ row.product.title }}
          </el-link>
          <span v-else class="deleted">商品已删除</span>
        </template>
      </el-table-column>
      <el-table-column label="金额" width="110">
        <template #default="{ row }">
          <span class="amount">{{ formatPrice(row.amount) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="STATUS_TAG_TYPE[row.status as OrderStatus]" effect="light">
            {{ ORDER_STATUS_LABELS[row.status as OrderStatus] ?? row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="下单时间" width="170">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="130" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'pending'"
            type="primary"
            size="small"
            :loading="confirmingId === row.id"
            @click="confirmComplete(row as OrderOut)"
          >
            确认已完成
          </el-button>
          <span v-else class="no-action">—</span>
        </template>
      </el-table-column>
      <template #empty>
        <EmptyState description="暂无订单" />
      </template>
    </el-table>

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
.order-page {
  max-width: var(--content-max-width);
  margin: 0 auto;
}

.tabs {
  margin-bottom: 8px;
}

.amount {
  font-weight: 600;
  color: var(--color-primary);
}

.deleted {
  color: var(--color-text-muted);
}

.no-action {
  color: var(--color-text-muted);
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

/* 窄屏：表格横向滚动（el-table 自带），操作列不换行 */
@media (max-width: 768px) {
  .order-page {
    padding: 0;
  }
}
</style>
