<script setup lang="ts">
/** 商品筛选栏：关键词 / 分类 / 价格区间 / 校区 / 排序，emit('search') 交给父组件发请求。 */
import { onMounted, reactive, ref } from 'vue'
import { Search } from '@element-plus/icons-vue'

import { listCategories } from '@/api/category'
import {
  SORT_OPTIONS,
  type Category,
  type ProductSearchParams,
  type ProductSort,
} from '@/types/product'

const emit = defineEmits<{
  search: [filters: ProductSearchParams]
}>()

const categories = ref<Category[]>([])
const categoryLoading = ref(false)

async function fetchCategories(): Promise<void> {
  categoryLoading.value = true
  try {
    categories.value = await listCategories()
  } catch {
    // 分类接口失败不阻塞搜索：仍可按关键词/价格/校区筛选
    categories.value = []
  } finally {
    categoryLoading.value = false
  }
}

const form = reactive({
  keyword: '',
  categoryId: undefined as number | undefined,
  minPrice: undefined as number | undefined,
  maxPrice: undefined as number | undefined,
  campus: '',
  sort: 'latest' as ProductSort,
})

/** 空字段剔除后上抛 */
function submit(): void {
  let minPrice = form.minPrice
  let maxPrice = form.maxPrice
  if (typeof minPrice === 'number' && typeof maxPrice === 'number' && minPrice > maxPrice) {
    // 用户填反了价格区间：按意图交换，避免后端 422
    ;[minPrice, maxPrice] = [maxPrice, minPrice]
  }
  emit('search', {
    keyword: form.keyword.trim() || undefined,
    category_id: form.categoryId || undefined,
    min_price: minPrice ?? undefined,
    max_price: maxPrice ?? undefined,
    campus: form.campus.trim() || undefined,
    sort: form.sort,
  })
}

function reset(): void {
  form.keyword = ''
  form.categoryId = undefined
  form.minPrice = undefined
  form.maxPrice = undefined
  form.campus = ''
  form.sort = 'latest'
  submit()
}

onMounted(fetchCategories)
</script>

<template>
  <div class="filter-bar hover-card">
    <div class="row">
      <el-input
        v-model="form.keyword"
        class="keyword"
        placeholder="搜索想要的宝贝，回车触发"
        maxlength="64"
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
          <el-select
            v-model="form.categoryId"
            class="field"
            placeholder="分类"
            clearable
            :loading="categoryLoading"
          >
            <el-option v-for="c in categories" :key="c.id" :value="c.id" :label="c.name" />
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
          <el-input v-model="form.campus" class="field campus" placeholder="校区" maxlength="64" clearable @keyup.enter="submit" />
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
