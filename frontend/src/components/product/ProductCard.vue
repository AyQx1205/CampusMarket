<script setup lang="ts">
/** 商品卡片：首图 + 标题 + 价格/原价 + 成色标签 + 校区，整卡可点击进详情。
 *  props 放宽为 ProductBrief（收藏/订单等精简数据可复用）；
 *  condition/original_price 等完整字段存在时才渲染对应区块。 */
import { conditionLabel, formatPrice } from '@/utils/format'
import type { ProductBrief, ProductDetail } from '@/types/product'

defineProps<{
  product: ProductBrief & Partial<ProductDetail>
}>()
</script>

<template>
  <RouterLink :to="`/product/${product.id}`" class="card-link">
    <div class="product-card hover-card">
      <!-- 首图缺失时用占位块 -->
      <div class="thumb">
        <img v-if="product.images.length" :src="product.images[0]" :alt="product.title" />
        <span v-else class="thumb-placeholder">暂无图片</span>
      </div>

      <div class="info">
        <p class="title">{{ product.title }}</p>
        <div class="price-row">
          <span class="price">{{ formatPrice(product.price) }}</span>
          <span v-if="product.original_price" class="original">
            {{ formatPrice(product.original_price) }}
          </span>
        </div>
        <div class="meta-row">
          <el-tag v-if="product.condition" size="small" type="success" effect="light">
            {{ conditionLabel(product.condition) }}
          </el-tag>
          <span v-if="product.campus" class="campus">{{ product.campus }}</span>
        </div>
      </div>
    </div>
  </RouterLink>
</template>

<style scoped>
.card-link {
  text-decoration: none;
  display: block;
}

.product-card {
  overflow: hidden;
  cursor: pointer;
}

.thumb {
  aspect-ratio: 4 / 3;
  background: var(--color-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumb-placeholder {
  color: var(--color-text-muted);
  font-size: 13px;
}

.info {
  padding: 10px 12px 12px;
}

.title {
  margin: 0;
  font-size: 14px;
  color: var(--color-text);
  /* 两行截断 */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 40px;
}

.price-row {
  margin-top: 6px;
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.price {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-primary);
}

.original {
  font-size: 12px;
  color: var(--color-text-muted);
  text-decoration: line-through;
}

.meta-row {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.campus {
  font-size: 12px;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
