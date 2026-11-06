<script setup lang="ts">
/** 我的订单：我买到的 / 我卖出的双 Tab 列表 + 按角色展示可执行动作。 */
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { listOrders, updateOrderStatus } from '@/api/order'
import EmptyState from '@/components/common/EmptyState.vue'
import { formatPrice, formatTime } from '@/utils/format'
import {
  ORDER_STATUS_LABELS,
  type OrderDetail,
  type OrderRole,
  type OrderStatus,
} from '@/types/order'

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
const orders = ref<OrderDetail[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const failed = ref(false)
/** 行级操作 loading（按订单 id 记录，防止连点） */
const actingId = ref<number | null>(null)
/** 请求序号：切 Tab/翻页过快时丢弃旧响应 */
let requestSeq = 0

async function fetchOrders(): Promise<void> {
  const seq = ++requestSeq
  loading.value = true
  failed.value = false
  try {
    const result = await listOrders(activeRole.value, { page: page.value, page_size: PAGE_SIZE })
    if (seq !== requestSeq) {
      return
    }
    orders.value = result.items
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

/** 当前 tab 下，交易对手是卖家还是买家 */
const counterpartLabel = computed(() => (activeRole.value === 'buyer' ? '卖家' : '买家'))

function counterpart(order: OrderDetail) {
  return activeRole.value === 'buyer' ? order.seller : order.buyer
}

function canCancel(order: OrderDetail): boolean {
  // pending 时买卖双方都可取消；confirmed 后只有卖家能取消（买家走「确认完成」）
  return (
    order.status === 'pending' ||
    (activeRole.value === 'seller' && order.status === 'confirmed')
  )
}

function canConfirm(order: OrderDetail): boolean {
  return activeRole.value === 'seller' && order.status === 'pending'
}

function canComplete(order: OrderDetail): boolean {
  return activeRole.value === 'buyer' && order.status === 'confirmed'
}

async function changeStatus(order: OrderDetail, target: OrderStatus): Promise<void> {
  const labels: Record<string, string> = {
    confirmed: '确认接单',
    completed: '确认已完成',
    cancelled: '取消订单',
  }
  const tips: Record<string, string> = {
    confirmed: '确认接单后，请与买家约定线下面交时间与地点。',
    completed: '请确认已当面验货并收到商品；完成后不可撤销。',
    cancelled: '取消后商品会重新上架，确定取消吗？',
  }
  try {
    await ElMessageBox.confirm(tips[target], labels[target], {
      type: target === 'cancelled' ? 'warning' : 'info',
      confirmButtonText: labels[target],
      cancelButtonText: '再想想',
    })
  } catch {
    return
  }

  actingId.value = order.id
  try {
    const updated = await updateOrderStatus(order.id, { status: target })
    const index = orders.value.findIndex((item) => item.id === order.id)
    if (index >= 0) {
      orders.value[index] = updated
    }
    ElMessage.success(`${labels[target]}成功`)
  } catch {
    // 如流转非法等提示由拦截器弹出；重新拉取避免本地状态与服务端不一致
    await fetchOrders()
  } finally {
    actingId.value = null
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
      <el-table-column label="订单号" prop="order_no" width="190" show-overflow-tooltip />
      <el-table-column label="商品" min-width="170">
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
      <el-table-column label="金额" width="100">
        <template #default="{ row }">
          <span class="amount">{{ formatPrice(row.amount) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="STATUS_TAG_TYPE[row.status as OrderStatus]" effect="light">
            {{ ORDER_STATUS_LABELS[row.status as OrderStatus] ?? row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="counterpartLabel" min-width="170">
        <template #default="{ row }">
          <div class="contact">
            <span class="contact-name">{{ counterpart(row as OrderDetail).nickname }}</span>
            <span v-if="counterpart(row as OrderDetail).phone" class="contact-line">
              电话 {{ counterpart(row as OrderDetail).phone }}
            </span>
            <span v-if="counterpart(row as OrderDetail).email" class="contact-line">
              邮箱 {{ counterpart(row as OrderDetail).email }}
            </span>
            <span v-if="row.trade_location" class="contact-line">地点 {{ row.trade_location }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="下单时间" width="160">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="190" fixed="right">
        <template #default="{ row }">
          <div class="actions">
            <el-button
              v-if="canConfirm(row as OrderDetail)"
              type="primary"
              size="small"
              :loading="actingId === row.id"
              @click="changeStatus(row as OrderDetail, 'confirmed')"
            >
              确认接单
            </el-button>
            <el-button
              v-if="canComplete(row as OrderDetail)"
              type="success"
              size="small"
              :loading="actingId === row.id"
              @click="changeStatus(row as OrderDetail, 'completed')"
            >
              确认已完成
            </el-button>
            <el-button
              v-if="canCancel(row as OrderDetail)"
              type="danger"
              size="small"
              plain
              :loading="actingId === row.id"
              @click="changeStatus(row as OrderDetail, 'cancelled')"
            >
              取消
            </el-button>
            <span
              v-if="!canConfirm(row as OrderDetail) && !canComplete(row as OrderDetail) && !canCancel(row as OrderDetail)"
              class="no-action"
            >
              —
            </span>
          </div>
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

.contact {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
  line-height: 1.5;
}

.contact-name {
  font-weight: 600;
  color: var(--color-text);
}

.contact-line {
  color: var(--color-text-secondary);
  word-break: break-all;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.actions :deep(.el-button + .el-button) {
  margin-left: 0;
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