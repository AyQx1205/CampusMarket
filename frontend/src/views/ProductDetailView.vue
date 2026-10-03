<script setup lang="ts">
/** 商品详情：图集轮播 + 商品信息 + 卖家卡 + 购买/收藏动作 + 返回顶部。 */
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChatDotRound, Goods, Star, StarFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import { createOrder } from '@/api/order'
import {
  favoriteProduct,
  getProductDetail,
  unfavoriteProduct,
} from '@/api/product'
import { listFavorites } from '@/api/favorite'
import EmptyState from '@/components/common/EmptyState.vue'
import { useUserStore } from '@/stores/user'
import { conditionLabel, formatPrice, formatTime } from '@/utils/format'
import type { ProductDetail } from '@/types/product'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const productId = Number(route.params.id)
const product = ref<ProductDetail | null>(null)
const loading = ref(true)
const failed = ref(false)

const isOwner = computed(() => userStore.isLoggedIn && userStore.profile?.id === product.value?.seller_id)
/** 只有在售商品可下单 */
const canBuy = computed(() => product.value?.status === 'on_sale' && !isOwner.value)
const isFavorited = ref(false)
const favoriteLoading = ref(false)

async function fetchProduct(): Promise<void> {
  loading.value = true
  failed.value = false
  try {
    product.value = await getProductDetail(productId)
    if (userStore.isLoggedIn) {
      // 后端暂无「是否已收藏」单查接口，用收藏列表兜底判断（超出首页 100 条的极端情况忽略）
      const favorites = await listFavorites({ page: 1, page_size: 100 })
      isFavorited.value = favorites.items.some((f) => f.product.id === productId)
    }
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
}

function requireLogin(): boolean {
  if (userStore.isLoggedIn) {
    return true
  }
  router.push({ path: '/login', query: { redirect: route.fullPath } })
  return false
}

// ---------------- 收藏 ----------------

async function toggleFavorite(): Promise<void> {
  if (!product.value || isOwner.value || favoriteLoading.value) {
    return
  }
  if (!requireLogin()) {
    return
  }
  favoriteLoading.value = true
  try {
    if (isFavorited.value) {
      await unfavoriteProduct(productId)
      isFavorited.value = false
      product.value.favorite_count -= 1
    } else {
      await favoriteProduct(productId)
      isFavorited.value = true
      product.value.favorite_count += 1
    }
  } catch {
    // 失败提示由拦截器弹出；计数以服务端为准，这里回拉一次
    product.value = await getProductDetail(productId)
  } finally {
    favoriteLoading.value = false
  }
}

// ---------------- 下单 ----------------

const orderDialogVisible = ref(false)
const orderSubmitting = ref(false)
const orderForm = ref({ trade_location: '', remark: '' })

function openOrderDialog(): void {
  if (!canBuy.value) {
    return
  }
  if (!requireLogin()) {
    return
  }
  orderForm.value.trade_location = product.value?.campus ?? ''
  orderForm.value.remark = ''
  orderDialogVisible.value = true
}

async function submitOrder(): Promise<void> {
  if (!product.value) {
    return
  }
  orderSubmitting.value = true
  try {
    await createOrder({
      product_id: product.value.id,
      trade_location: orderForm.value.trade_location.trim() || undefined,
      remark: orderForm.value.remark.trim() || undefined,
    })
    orderDialogVisible.value = false
    ElMessage.success('下单成功，请等待卖家确认')
    router.push('/orders')
  } catch {
    // 如「已被下单」等冲突提示由拦截器弹出
  } finally {
    orderSubmitting.value = false
  }
}

/** 问问 AI 助手（第 5 轮接入 AI 面板） */
function askAi(): void {
  console.log('[AI] ask about product', productId, product.value?.title)
}

onMounted(fetchProduct)
</script>

<template>
  <div class="detail-page">
    <EmptyState
      v-if="failed"
      description="商品不存在或已删除"
      action-text="回首页"
      @action="router.push('/')"
    />

    <div v-else-if="loading" class="skeleton">
      <div class="gallery-skeleton"><el-skeleton animated :rows="6" /></div>
      <div class="info-skeleton"><el-skeleton animated :rows="4" /></div>
    </div>

    <template v-else-if="product">
      <div class="layout">
        <!-- 左：图集轮播 -->
        <div class="gallery hover-card">
          <el-carousel
            v-if="product.images.length"
            height="420px"
            :autoplay="false"
            indicator-position="outside"
          >
            <el-carousel-item v-for="(img, i) in product.images" :key="i">
              <img class="gallery-img" :src="img" :alt="product.title" />
            </el-carousel-item>
          </el-carousel>
          <div v-else class="gallery-placeholder">
            <el-icon :size="56"><Goods /></el-icon>
            <span>暂无图片</span>
          </div>
        </div>

        <!-- 右：信息 + 动作 -->
        <div class="info">
          <h1 class="title">{{ product.title }}</h1>

          <div class="price-row">
            <span class="price">{{ formatPrice(product.price) }}</span>
            <span v-if="product.original_price" class="original">
              原价 {{ formatPrice(product.original_price) }}
            </span>
          </div>

          <div class="tags">
            <el-tag type="success" effect="light">{{ conditionLabel(product.condition) }}</el-tag>
            <el-tag v-if="product.campus" type="info" effect="light">{{ product.campus }}</el-tag>
            <el-tag v-if="product.status !== 'on_sale'" type="warning" effect="light">
              {{ product.status === 'sold' ? '已售出' : product.status === 'reserved' ? '已预订' : '已下架' }}
            </el-tag>
          </div>

          <div class="stats">
            <span>浏览 {{ product.view_count }}</span>
            <span>收藏 {{ product.favorite_count }}</span>
            <span>发布于 {{ formatTime(product.created_at) }}</span>
          </div>

          <p v-if="product.description" class="description">{{ product.description }}</p>

          <div class="actions">
            <el-tooltip
              :content="isOwner ? '不能购买自己发布的商品' : '当前状态不可下单'"
              :disabled="canBuy"
            >
              <span>
                <el-button type="primary" size="large" :disabled="!canBuy" @click="openOrderDialog">
                  立即购买
                </el-button>
              </span>
            </el-tooltip>

            <el-tooltip content="不能收藏自己的商品" :disabled="!isOwner">
              <span>
                <el-button
                  size="large"
                  :disabled="isOwner"
                  :loading="favoriteLoading"
                  :type="isFavorited ? 'warning' : 'default'"
                  @click="toggleFavorite"
                >
                  <el-icon v-if="isFavorited"><StarFilled /></el-icon>
                  <el-icon v-else><Star /></el-icon>
                  {{ isFavorited ? '已收藏' : '收藏' }}
                </el-button>
              </span>
            </el-tooltip>

            <el-button size="large" :icon="ChatDotRound" @click="askAi">问问 AI 助手</el-button>
          </div>

          <!-- 卖家卡：后端暂无公开用户信息接口，先展示 ID + 交易校区，昵称/信用分待接口就绪补齐 -->
          <div class="seller-card">
            <el-avatar :size="40" />
            <div class="seller-info">
              <p class="seller-name">卖家 #{{ product.seller_id }}</p>
              <p class="seller-tip">校园当面交易，请当面验货后再确认</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 下单对话框 -->
      <el-dialog v-model="orderDialogVisible" title="确认下单" width="440px">
        <el-form label-position="top">
          <el-form-item label="商品">
            <span class="order-product">{{ product.title }} · {{ formatPrice(product.price) }}</span>
          </el-form-item>
          <el-form-item label="交易地点">
            <el-input v-model="orderForm.trade_location" placeholder="如：东校区图书馆门口" />
          </el-form-item>
          <el-form-item label="给卖家留言（选填）">
            <el-input
              v-model="orderForm.remark"
              type="textarea"
              :rows="2"
              maxlength="100"
              show-word-limit
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="orderDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="orderSubmitting" @click="submitOrder">
            确认下单
          </el-button>
        </template>
      </el-dialog>
    </template>

    <el-backtop :right="24" :bottom="24" />
  </div>
</template>

<style scoped>
.skeleton {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 20px;
}

.gallery-skeleton,
.info-skeleton {
  border-radius: var(--radius-base);
  background: var(--color-bg-card);
  padding: 20px;
}

.layout {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 20px;
  align-items: start;
}

.gallery {
  overflow: hidden;
}

.gallery-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.gallery-placeholder {
  height: 420px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--color-text-muted);
  background: var(--color-bg);
}

.info {
  border-radius: var(--radius-base);
  background: var(--color-bg-card);
  box-shadow: var(--shadow-card);
  padding: 24px;
}

.title {
  margin: 0 0 12px;
  font-size: 20px;
  line-height: 1.4;
}

.price-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.price {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-primary);
}

.original {
  color: var(--color-text-muted);
  text-decoration: line-through;
}

.tags {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

.stats {
  margin-top: 14px;
  display: flex;
  gap: 16px;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.description {
  margin: 16px 0 0;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
  white-space: pre-wrap;
  line-height: 1.7;
  color: var(--color-text);
}

.actions {
  margin-top: 20px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.seller-card {
  margin-top: 24px;
  padding: 14px;
  border-radius: var(--radius-base);
  background: var(--color-bg);
  display: flex;
  align-items: center;
  gap: 12px;
}

.seller-info p {
  margin: 0;
}

.seller-name {
  font-weight: 600;
}

.seller-tip {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 2px !important;
}

.order-product {
  color: var(--color-text);
  font-weight: 600;
}

@media (max-width: 768px) {
  .layout,
  .skeleton {
    grid-template-columns: 1fr;
  }

  .gallery-placeholder {
    height: 260px;
  }
}
</style>
