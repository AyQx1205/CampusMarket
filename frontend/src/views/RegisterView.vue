<script setup lang="ts">
/** 注册页：学号 / 昵称 / 密码 / 确认密码 / 邮箱 / 手机号，成功后跳登录并预填学号。 */
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'

import { register } from '@/api/auth'
import type { RegisterParams } from '@/types/user'

const router = useRouter()

const formRef = ref<FormInstance>()
const submitting = ref(false)
const form = reactive({
  studentNo: '',
  nickname: '',
  password: '',
  confirmPassword: '',
  email: '',
  phone: '',
})

const rules: FormRules = {
  studentNo: [{ required: true, message: '请输入学号', trigger: 'blur' }],
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 32, message: '密码长度 6~32 位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule, value: string, callback) => {
        if (value !== form.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
  phone: [{ pattern: /^1\d{10}$/, message: '手机号格式不正确', trigger: 'blur' }],
}

async function handleSubmit(): Promise<void> {
  // validate 失败会 reject，这里转成布尔值；校验不过直接 return
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) {
    return
  }
  submitting.value = true
  try {
    const params: RegisterParams = {
      student_no: form.studentNo.trim(),
      nickname: form.nickname.trim(),
      password: form.password,
    }
    if (form.email.trim()) params.email = form.email.trim()
    if (form.phone.trim()) params.phone = form.phone.trim()

    await register(params)
    router.push(`/login?student_no=${encodeURIComponent(params.student_no)}`)
  } catch {
    // 错误提示（如「学号已注册」）由 request.ts 拦截器统一弹出
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card hover-card">
      <h2>注册</h2>
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
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="form.nickname" placeholder="给自己起个名字" clearable />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="6~32 位" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="再输入一次"
            show-password
          />
        </el-form-item>
        <el-form-item label="邮箱（选填）" prop="email">
          <el-input v-model="form.email" placeholder="用于找回密码" clearable />
        </el-form-item>
        <el-form-item label="手机号（选填）" prop="phone">
          <el-input v-model="form.phone" placeholder="方便买家联系你" clearable />
        </el-form-item>
        <el-button
          class="submit"
          type="primary"
          size="large"
          :loading="submitting"
          @click="handleSubmit"
        >
          注册
        </el-button>
      </el-form>

      <p class="switch">
        已有账号？
        <RouterLink to="/login">去登录</RouterLink>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  padding: 32px 0;
}

.auth-card {
  width: 440px;
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
