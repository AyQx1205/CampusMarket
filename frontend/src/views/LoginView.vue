<script setup lang="ts">
/** 登录页：学号 + 密码，成功后回跳 redirect 或首页。 */
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'

import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const submitting = ref(false)
const form = reactive({
  studentNo: String(route.query.student_no ?? ''),
  password: '',
})

const rules: FormRules = {
  studentNo: [{ required: true, message: '请输入学号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleSubmit(): Promise<void> {
  // validate 失败会 reject，这里转成布尔值；校验不过直接 return
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) {
    return
  }
  submitting.value = true
  try {
    await userStore.login({ student_no: form.studentNo.trim(), password: form.password })
    // 登录成功后回跳来源页（守卫跳登录时带上的 redirect）
    const redirect = String(route.query.redirect ?? '/')
    router.replace(redirect)
  } catch {
    // 错误提示（如「学号或密码错误」）由 request.ts 拦截器统一弹出
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card hover-card">
      <h2>登录</h2>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        size="large"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="学号" prop="studentNo">
          <el-input v-model="form.studentNo" placeholder="请输入学号" clearable />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
            @keyup.enter="handleSubmit"
          />
        </el-form-item>
        <el-button
          class="submit"
          type="primary"
          size="large"
          :loading="submitting"
          @click="handleSubmit"
        >
          登录
        </el-button>
      </el-form>

      <p class="switch">
        还没有账号？
        <RouterLink to="/register">立即注册</RouterLink>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  padding: 48px 0;
}

.auth-card {
  width: 400px;
  max-width: 100%;
  padding: 32px;
}

h2 {
  margin: 0 0 20px;
  text-align: center;
  color: var(--color-text);
}

.submit {
  width: 100%;
  margin-top: 4px;
}

.switch {
  margin: 16px 0 0;
  text-align: center;
  color: var(--color-text-secondary);
}

.switch a {
  color: var(--color-primary);
  text-decoration: none;
}
</style>
