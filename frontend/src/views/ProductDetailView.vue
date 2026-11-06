<script setup lang="ts">
/** 商品详情：图集轮播 + 商品信息 + 卖家卡 + 购买/收藏动作 + 返回顶部。 */
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChatDotRound, Goods, Star, StarFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import { createOrder } from '@/api/order'
import {
  favoriteProduct,
  getFavoriteStatus,
  getProductDetail,
  unfavoriteProduct,
} from '@/api/product'
import { getUser } from '@/api/user'
import EmptyState from '@/components/common/EmptyState.vue'
import { useAiStore } from '@/stores/ai'
import { useUserStore } from '@/stores/user'
import { conditionLabel, formatPrice, formatTime } from '@/utils/format'
import { STATUS_LABELS, type ProductDetail } from '@/types/product'
import type { UserPublic } from '@/types/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const aiStore = useAiStore()

/** route.params.id 是响应式的；用 computed 保证详情页之间跳转也能重新加载 */
const productId = computed(() => Number(route.params.id))
const product = ref<ProductDetail | null>(null)
const seller = ref<UserPublic | null>(null)
const loading = ref(true)
const failed = ref(false)

const isOwner = computed(() => userStore.isLoggedIn && userStore.profile?.id === product.value?.seller_id)
/** 只有在售商品可下单 */
const canBuy = computed(() => product.value?.status === 'on_sale' && !isOwner.value)
/** 按钮禁用原因：区分「自己的商品」和「状态不可下单」 */
const buyHint = computed(() => {
  if (isOwner.value) {
    return '不能购买自己发布的商品'
  }
  switch (product.value?.status) {
    case 'reserved':
      return '商品已被预订'
    case 'sold':
      return '商品已售出'
    case 'off_shelf':
      return '商品已下架'
    default:
      return '当前状态不可下单'
  }
})
const isFavorited = ref(false)
const favoriteLoading = ref(false)

async function fetchFavoriteStatus(id: number): Promise<void> {
  if (!userStore.isLoggedIn) {
    isFavorited.value = false
    return
  }
  // 收藏状态是独立接口：即使它失败，也不能把整个商品页标记为加载失败
  try {
    const result = await getFavoriteStatus(id)
    if (id === productId.value) {
      isFavorited.value = result.favorited
    }
  } catch {
    isFavorited.value = false
  }
}

async function fetchSeller(id: number): Promise<void> {
  try {
    const result = await getUser(id)
    if (id === productId.value) {
      seller.value = result
    }
  } catch {
    seller.value = null
  }
}

async function fetchProduct(): Promise<void> {
  const id = productId.value
  if (!Number.isInteger(id) || id <= 0) {
    failed.value = true
    loading.value = false
    return
  }
  loading.value = true
  failed.value = false
  seller.value = null
  try {
    const detail = await getProductDetail(id)
    if (id !== productId.value) {
      return
    }
    product.value = detail
    // 收藏状态与卖家资料互不依赖，并行加载
    void fetchFavoriteStatus(id)
    void fetchSeller(detail.seller_id)
  } catch {
    if (id === productId.value) {
      failed.value = true
    }
  } finally {
    if (id === productId.value) {
      loading.value = false
    }
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
  const id = product.value.id
  try {
    if (isFavorited.value) {
      await unfavoriteProduct(id)
      isFavorited.value = false
      product.value.favorite_count = Math.max(0, product.value.favorite_count - 1)
    } else {
      await favoriteProduct(id)
      isFavorited.value = true
      product.value.favorite_count += 1
    }
  } catch {
    // 失败提示由拦截器弹出；计数以服务端为准，这里回拉一次
    try {
      product.value = await getProductDetail(id)
      void fetchFavoriteStatus(id)
    } catch {
      // 回拉失败保持当前页面，不把整页切成错误态
    }
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

/** 问问 AI 助手：把当前商品作为上下文发给助手，并打开全局面板 */
function askAi(): void {
  if (!product.value || !requireLogin()) {
    return
  }
  if (aiStore.sending) {
    ElMessage.info('助手正在回复上一条消息，请稍候')
    return
  }
  aiStore.isOpen = true
  const question =
    `我想了解这件商品：${product.value.title}，售价 ${formatPrice(product.value.price)}，` +
    `成色「${conditionLabel(product.value.condition)}」，校区 ${product.value.campus ?? '未填写'}。` +
    '能帮我分析是否值得买、交易时要注意什么吗？'
  void aiStore.sendMessage(question)
}

watch(productId, fetchProduct)
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
              <img
                class="gallery-img"
                :src="img"
                :alt="product.title"
                loading="lazy"
                referrerpolicy="no-referrer"
              />
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
              {{ STATUS_LABELS[product.status] }}
            </el-tag>
          </div>

          <div class="stats">
            <span>浏览 {{ product.view_count }}</span>
            <span>收藏 {{ product.favorite_count }}</span>
            <span>发布于 {{ formatTime(product.created_at) }}</span>
          </div>

          <p v-if="product.description" class="description">{{ product.description }}</p>

          <div class="actions">
            <el-tooltip :content="buyHint" :disabled="canBuy">
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

          <!-- 卖家卡：公开资料（昵称/头像/校区/信用分），联系方式需在下单后查看 -->
          <div class="seller-card">
            <el-avatar :size="40" :src="seller?.avatar_url ?? undefined">
              {{ seller?.nickname?.slice(0, 1) ?? '卖' }}
            </el-avatar>
            <div class="seller-info">
              <p class="seller-name">{{ seller?.nickname ?? `卖家 #${product.seller_id}` }}</p>
              <p class="seller-tip">
                {{ seller?.campus ?? product.campus ?? '校区未填写' }} · 信用分
                {{ seller?.credit_score ?? '—' }}
              </p>
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
            <el-input v-model="orderForm.trade_location" placeholder="如：东校区图书馆门口" maxlength="128" />
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
