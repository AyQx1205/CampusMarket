<script setup lang="ts">
/** 发布商品：手工表单 + 「AI 帮我写」文案生成（POST /ai/listing/generate）。 */
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { MagicStick, Delete, Plus } from '@element-plus/icons-vue'

import { createProduct } from '@/api/product'
import { generateListing } from '@/api/ai'
import { BizError } from '@/api/request'
import { CONDITION_LABELS, type ProductCondition } from '@/types/product'

const router = useRouter()

const formRef = ref<FormInstance>()
const submitting = ref(false)

const form = reactive({
  title: '',
  description: '',
  price: undefined as number | undefined,
  originalPrice: undefined as number | undefined,
  condition: '' as ProductCondition | '',
  campus: '',
  images: [''] as string[],
})

const conditionOptions = (Object.keys(CONDITION_LABELS) as ProductCondition[]).map((value) => ({
  value,
  label: CONDITION_LABELS[value],
}))

const rules: FormRules = {
  title: [
    { required: true, message: '请输入商品标题', trigger: 'blur' },
    { max: 128, message: '标题最长 128 字', trigger: 'blur' },
  ],
  price: [{ required: true, message: '请输入售价', trigger: 'blur' }],
  condition: [{ required: true, message: '请选择成色', trigger: 'change' }],
}

async function handleSubmit(): Promise<void> {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) {
    return
  }
  submitting.value = true
  try {
    const product = await createProduct({
      title: form.title.trim(),
      description: form.description.trim() || undefined,
      price: form.price as number,
      original_price: form.originalPrice,
      condition: form.condition as ProductCondition,
      campus: form.campus.trim() || undefined,
      images: form.images.map((s) => s.trim()).filter(Boolean),
    })
    router.push(`/product/${product.id}`)
  } catch {
    // 错误提示由 request.ts 拦截器统一弹出
  } finally {
    submitting.value = false
  }
}

// ---------------- AI 帮我写 ----------------

const aiDialogVisible = ref(false)
const aiGenerating = ref(false)
const aiError = ref('')
const aiForm = reactive({
  rawInfo: '',
  expectedPrice: undefined as number | undefined,
  conditionHint: '',
})

function openAiDialog(): void {
  aiError.value = ''
  aiDialogVisible.value = true
}

async function handleGenerate(): Promise<void> {
  if (!aiForm.rawInfo.trim() || aiGenerating.value) {
    return
  }
  aiGenerating.value = true
  aiError.value = ''
  try {
    const draft = await generateListing({
      raw_info: aiForm.rawInfo.trim(),
      expected_price: aiForm.expectedPrice,
      condition_hint: aiForm.conditionHint.trim() || undefined,
    })
    form.title = draft.title
    form.description = draft.description
    // 成色未选时顺带填入 AI 推断值
    if (!form.condition) {
      form.condition = draft.condition
    }
    aiDialogVisible.value = false
  } catch (err) {
    // 拦截器已弹原始 message；对话框内再做一轮友好文案（5001=未配置 / 503=繁忙）
    if (err instanceof BizError) {
      aiError.value =
        err.code === 5001
          ? 'AI 助手暂未上线，请手动填写'
          : err.code === 503
            ? '助手忙不过来，稍后再试'
            : err.message
    } else {
      aiError.value = '生成失败，请稍后再试'
    }
  } finally {
    aiGenerating.value = false
  }
}

function addImageRow(): void {
  form.images.push('')
}

function removeImageRow(index: number): void {
  form.images.splice(index, 1)
}
</script>

<template>
  <div class="publish-page">
    <div class="publish-card hover-card">
      <div class="head">
        <h2>发布商品</h2>
        <el-button type="primary" plain :icon="MagicStick" @click="openAiDialog">
          AI 帮我写
        </el-button>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="一句话说清是什么宝贝" maxlength="128" show-word-limit />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="购买渠道、使用时长、瑕疵情况等"
          />
        </el-form-item>

        <div class="row">
          <el-form-item label="售价（元）" prop="price">
            <el-input-number v-model="form.price" :min="0.01" :precision="2" :controls="false" placeholder="0.00" />
          </el-form-item>
          <el-form-item label="原价（选填）" prop="originalPrice">
            <el-input-number v-model="form.originalPrice" :min="0" :precision="2" :controls="false" placeholder="划线展示" />
          </el-form-item>
        </div>

        <el-form-item label="成色" prop="condition">
          <el-radio-group v-model="form.condition">
            <el-radio-button v-for="opt in conditionOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="校区（选填）" prop="campus">
          <el-input v-model="form.campus" placeholder="如：东校区" clearable />
        </el-form-item>

        <el-form-item label="图片链接（选填，第一张为封面）">
          <div class="image-list">
            <div v-for="(_, index) in form.images" :key="index" class="image-row">
              <el-input v-model="form.images[index]" placeholder="https://..." clearable />
              <el-button
                :icon="Delete"
                text
                type="danger"
                :disabled="form.images.length === 1"
                @click="removeImageRow(index)"
              />
            </div>
            <el-button text type="primary" :icon="Plus" @click="addImageRow">添加一张</el-button>
          </div>
        </el-form-item>

        <el-button class="submit" type="primary" size="large" :loading="submitting" @click="handleSubmit">
          发布
        </el-button>
      </el-form>
    </div>

    <!-- AI 文案生成对话框 -->
    <el-dialog v-model="aiDialogVisible" title="AI 帮我写" width="480px">
      <el-alert
        v-if="aiError"
        :title="aiError"
        type="warning"
        show-icon
        :closable="false"
        class="ai-error"
      />
      <el-form label-position="top">
        <el-form-item label="随手描述一下宝贝">
          <el-input
            v-model="aiForm.rawInfo"
            type="textarea"
            :rows="3"
            placeholder="例：小米台灯，去年双十一买的，用了不到一年，有点灰没坏"
          />
        </el-form-item>
        <el-form-item label="期望价格（选填）">
          <el-input-number v-model="aiForm.expectedPrice" :min="0" :precision="2" :controls="false" placeholder="元" />
        </el-form-item>
        <el-form-item label="成色提示（选填）">
          <el-input v-model="aiForm.conditionHint" placeholder="如：九成新 / 全新未拆" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="aiDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="aiGenerating" @click="handleGenerate">
          {{ aiGenerating ? '生成中...' : '生成' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.publish-page {
  display: flex;
  justify-content: center;
}

.publish-card {
  width: 640px;
  max-width: 100%;
  padding: 28px;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

h2 {
  margin: 0;
}

.row {
  display: flex;
  gap: 24px;
}

.row .el-form-item {
  flex: 1;
}

.image-list {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-start;
}

.image-row {
  width: 100%;
  display: flex;
  gap: 8px;
  align-items: center;
}

.submit {
  width: 100%;
}

.ai-error {
  margin-bottom: 12px;
}

@media (max-width: 768px) {
  .row {
    flex-direction: column;
    gap: 0;
  }
}
</style>
