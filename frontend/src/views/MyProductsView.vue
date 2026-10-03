<script setup lang="ts">
/** 我的商品：表格管理自己发布的商品（编辑 / 上下架 / 删除）。 */
import { computed, onMounted, reactive, ref } from 'vue'
import type { FormInstance } from 'element-plus'
import { ElMessageBox } from 'element-plus'

import { deleteProduct, updateProduct } from '@/api/product'
import { listUserProducts } from '@/api/user'
import { useUserStore } from '@/stores/user'
import EmptyState from '@/components/common/EmptyState.vue'
import { formatPrice, formatTime } from '@/utils/format'
import type { ProductDetail } from '@/types/product'

const userStore = useUserStore()

const products = ref<ProductDetail[]>([])
const loading = ref(false)
const failed = ref(false)
/** 行级操作 loading */
const actingId = ref<number | null>(null)

async function fetchProducts(): Promise<void> {
  if (!userStore.profile?.id) {
    await userStore.fetchMe()
  }
  const userId = userStore.profile?.id
  if (!userId) {
    return
  }
  loading.value = true
  failed.value = false
  try {
    const result = await listUserProducts(userId, { page: 1, page_size: 100 })
    products.value = result.items
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
}

const inSaleCount = computed(() => products.value.filter((p) => p.status === 'on_sale').length)

// ---------------- 编辑 ----------------

const editDialogVisible = ref(false)
const editSubmitting = ref(false)
const editFormRef = ref<FormInstance>()
const editingId = ref<number | null>(null)
const editForm = reactive({
  title: '',
  description: '',
  price: undefined as number | undefined,
  originalPrice: undefined as number | undefined,
  campus: '',
})

function openEditDialog(product: ProductDetail): void {
  editingId.value = product.id
  editForm.title = product.title
  editForm.description = product.description ?? ''
  editForm.price = Number(product.price)
  editForm.originalPrice = product.original_price ? Number(product.original_price) : undefined
  editForm.campus = product.campus ?? ''
  editDialogVisible.value = true
}

async function submitEdit(): Promise<void> {
  const valid = await editFormRef.value?.validate().catch(() => false)
  if (!valid || editingId.value === null) {
    return
  }
  editSubmitting.value = true
  try {
    const updated = await updateProduct(editingId.value, {
      title: editForm.title.trim(),
      description: editForm.description.trim() || undefined,
      price: editForm.price as number,
      original_price: editForm.originalPrice,
      campus: editForm.campus.trim() || undefined,
    })
    // 原地替换，避免整页刷新
    const index = products.value.findIndex((p) => p.id === updated.id)
    if (index >= 0) {
      products.value[index] = updated
    }
    editDialogVisible.value = false
  } catch {
    // 提示由拦截器弹出
  } finally {
    editSubmitting.value = false
  }
}

// ---------------- 上下架 / 删除 ----------------

/** 在售 ↔ 下架 互切；已预订/已售出不可操作 */
async function toggleStatus(product: ProductDetail): Promise<void> {
  const next = product.status === 'on_sale' ? 'off_shelf' : 'on_sale'
  actingId.value = product.id
  try {
    const updated = await updateProduct(product.id, { status: next })
    const index = products.value.findIndex((p) => p.id === updated.id)
    if (index >= 0) {
      products.value[index] = updated
    }
  } catch {
    // 提示由拦截器弹出
  } finally {
    actingId.value = null
  }
}

async function removeProduct(product: ProductDetail): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `确定删除「${product.title}」吗？已有订单记录的商品无法删除，建议改为下架。`,
      '删除商品',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return // 用户取消
  }
  actingId.value = product.id
  try {
    await deleteProduct(product.id)
    products.value = products.value.filter((p) => p.id !== product.id)
  } catch {
    // 如「已有订单记录」提示由拦截器弹出
  } finally {
    actingId.value = null
  }
}

function handleRetry(): void {
  fetchProducts()
}

onMounted(fetchProducts)
</script>

<template>
  <div class="my-products">
    <div class="head">
      <h2>我的商品</h2>
      <span v-if="!failed && !loading" class="count">在售 {{ inSaleCount }} / 共 {{ products.length }}</span>
    </div>

    <EmptyState
      v-if="failed"
      description="加载失败，请稍后重试"
      action-text="重新加载"
      @action="handleRetry"
    />

    <el-table v-else v-loading="loading" :data="products" class="table">
      <el-table-column label="商品" min-width="220">
        <template #default="{ row }">
          <div class="product-cell">
            <img v-if="row.images.length" :src="row.images[0]" class="thumb" :alt="row.title" />
            <div v-else class="thumb placeholder">无图</div>
            <span class="title">{{ row.title }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="价格" width="110">
        <template #default="{ row }">
          <span class="price">{{ formatPrice(row.price) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'on_sale' ? 'success' : 'info'" effect="light">
            {{ row.status === 'on_sale' ? '在售' : row.status === 'sold' ? '已售出' : row.status === 'reserved' ? '已预订' : '已下架' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="发布时间" width="170">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEditDialog(row as ProductDetail)">编辑</el-button>
          <el-button
            v-if="row.status === 'on_sale' || row.status === 'off_shelf'"
            size="small"
            :loading="actingId === row.id"
            @click="toggleStatus(row as ProductDetail)"
          >
            {{ row.status === 'on_sale' ? '下架' : '重新上架' }}
          </el-button>
          <el-button
            size="small"
            type="danger"
            plain
            :loading="actingId === row.id"
            @click="removeProduct(row as ProductDetail)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
      <template #empty>
        <EmptyState description="还没有发布过商品" action-text="去发布" @action="$router.push('/publish')" />
      </template>
    </el-table>

    <!-- 编辑对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑商品" width="480px">
      <el-form ref="editFormRef" :model="editForm" label-position="top">
        <el-form-item label="标题" required>
          <el-input v-model="editForm.title" maxlength="128" show-word-limit />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="售价（元）" required>
          <el-input-number v-model="editForm.price" :min="0.01" :precision="2" :controls="false" />
        </el-form-item>
        <el-form-item label="原价（选填）">
          <el-input-number v-model="editForm.originalPrice" :min="0" :precision="2" :controls="false" />
        </el-form-item>
        <el-form-item label="校区（选填）">
          <el-input v-model="editForm.campus" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editSubmitting" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.my-products {
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

.product-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.thumb {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-sm);
  object-fit: cover;
  flex-shrink: 0;
}

.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
  color: var(--color-text-muted);
  font-size: 12px;
}

.title {
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.price {
  font-weight: 600;
  color: var(--color-primary);
}
</style>
