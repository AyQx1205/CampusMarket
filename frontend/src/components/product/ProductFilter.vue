<script setup lang="ts">
/** 商品筛选栏：关键词 / 分类 / 价格区间 / 校区 / 排序，emit('search') 交给父组件发请求。 */
import { reactive } from 'vue'
import { Search } from '@element-plus/icons-vue'

import { SORT_OPTIONS, type ProductSearchParams, type ProductSort } from '@/types/product'

// 分类暂硬编码（后端分类接口就绪后改为拉取，并改传 category_id）
const CATEGORY_OPTIONS = ['教材教辅', '数码电子', '生活用品', '美妆个护', '服饰鞋包', '运动健身', '其他']

const emit = defineEmits<{
  search: [filters: ProductSearchParams]
}>()

const form = reactive({
  keyword: '',
  category: '',
  minPrice: undefined as number | undefined,
  maxPrice: undefined as number | undefined,
  campus: '',
  sort: 'latest' as ProductSort,
})

/** 空字段剔除后上抛 */
function submit(): void {
  emit('search', {
    keyword: form.keyword.trim() || undefined,
    min_price: form.minPrice,
    max_price: form.maxPrice,
    campus: form.campus.trim() || undefined,
    sort: form.sort,
  })
}

function reset(): void {
  form.keyword = ''
  form.category = ''
  form.minPrice = undefined
  form.maxPrice = undefined
  form.campus = ''
  form.sort = 'latest'
  submit()
}
</script>

<template>
  <div class="filter-bar hover-card">
    <div class="row">
      <el-input
        v-model="form.keyword"
        class="keyword"
        placeholder="搜索想要的宝贝，回车触发"
        clearable
        :prefix-icon="Search"
        @keyup.enter="submit"
      />
      <el-select v-model="form.sort" class="sort" @change="submit">
        <el-option
          v-for="opt in SORT_OPTIONS"
          :key="opt.value"
          :value="opt.value"
          :label="opt.label"
        />
      </el-select>
      <el-button type="primary" @click="submit">搜索</el-button>
      <el-button text @click="reset">重置</el-button>
    </div>

    <!-- 高级筛选：窄屏折叠为可展开区 -->
    <el-collapse class="advanced">
      <el-collapse-item title="更多筛选（分类 / 价格 / 校区）" name="advanced">
        <div class="row">
          <el-select v-model="form.category" class="field" placeholder="分类" clearable>
            <el-option v-for="c in CATEGORY_OPTIONS" :key="c" :value="c" :label="c" />
          </el-select>
          <el-input-number
            v-model="form.minPrice"
            class="field"
            :min="0"
            :controls="false"
            placeholder="最低价"
          />
          <span class="divider">—</span>
          <el-input-number
            v-model="form.maxPrice"
            class="field"
            :min="0"
            :controls="false"
            placeholder="最高价"
          />
          <el-input v-model="form.campus" class="field campus" placeholder="校区" clearable @keyup.enter="submit" />
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<style scoped>
.filter-bar {
  padding: 14px 16px;
}

.row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.keyword {
  flex: 1;
  min-width: 220px;
}

.sort {
  width: 150px;
}

.field {
  width: 150px;
}

.field.campus {
  width: 130px;
}

.divider {
  color: var(--color-text-muted);
}

/* 窄屏：高级筛选区默认折叠（el-collapse 单条标题占位小） */
@media (max-width: 768px) {
  .row {
    gap: 8px;
  }

  .sort {
    width: 120px;
  }

  .field {
    width: 120px;
  }
}
</style>
