<script setup lang="ts">
/** 个人中心：资料修改（昵称/邮箱/电话/校区）+ 老年人模式开关，均调 PATCH /users/me。 */
import { reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'

import { updateMe } from '@/api/user'
import { useUserStore } from '@/stores/user'
import { formatTime } from '@/utils/format'
import type { UserUpdateParams } from '@/types/user'

const userStore = useUserStore()

const formRef = ref<FormInstance>()
const submitting = ref(false)

const form = reactive({
  nickname: userStore.profile?.nickname ?? '',
  email: userStore.profile?.email ?? '',
  phone: userStore.profile?.phone ?? '',
  campus: userStore.profile?.campus ?? '',
})

// profile 可能尚未加载（刷新后 hydrate 是同步的，persist 插件已恢复；兜底再拉一次）
if (!userStore.profile) {
  userStore.fetchMe().then(() => {
    form.nickname = userStore.profile?.nickname ?? ''
    form.email = userStore.profile?.email ?? ''
    form.phone = userStore.profile?.phone ?? ''
    form.campus = userStore.profile?.campus ?? ''
  })
}

const rules: FormRules = {
  nickname: [{ required: true, message: '昵称不能为空', trigger: 'blur' }],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
  phone: [{ pattern: /^1\d{10}$/, message: '手机号格式不正确', trigger: 'blur' }],
}

async function handleSave(): Promise<void> {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) {
    return
  }
  submitting.value = true
  try {
    // 仅传非空字段：后端「不传=不修改」，前端不支持通过清空输入框清空资料
    const params: UserUpdateParams = { nickname: form.nickname.trim() }
    if (form.email.trim()) params.email = form.email.trim()
    if (form.phone.trim()) params.phone = form.phone.trim()
    if (form.campus.trim()) params.campus = form.campus.trim()
    const updated = await updateMe(params)
    userStore.profile = updated
    ElMessage.success('保存成功')
  } catch {
    // 提示由拦截器弹出
  } finally {
    submitting.value = false
  }
}

/** 老年人模式：切换即保存（后端 AI 助手按此调整回复风格） */
async function toggleSeniorMode(enabled: boolean | string | number): Promise<void> {
  try {
    const updated = await updateMe({ is_senior_mode: Boolean(enabled) })
    userStore.profile = updated
    ElMessage.success(enabled ? '已开启长辈模式，AI 助手会更有耐心' : '已关闭长辈模式')
  } catch {
    // 失败回滚开关（以服务端为准）
    if (userStore.profile) {
      userStore.profile = { ...userStore.profile }
    }
  }
}
</script>

<template>
  <div class="profile-page">
    <div class="profile-card hover-card">
      <h2>个人中心</h2>
      <p class="meta">
        学号 {{ userStore.profile?.student_no ?? '—' }} · 信用分
        {{ userStore.profile?.credit_score ?? '—' }} · 注册于
        {{ userStore.profile ? formatTime(userStore.profile.created_at, 'YYYY-MM-DD') : '—' }}
      </p>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent="handleSave"
      >
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="form.nickname" maxlength="30" show-word-limit />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="用于找回密码" clearable />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="方便买家联系你" clearable />
        </el-form-item>
        <el-form-item label="校区" prop="campus">
          <el-input v-model="form.campus" placeholder="如：东校区" clearable />
        </el-form-item>
        <el-button class="submit" type="primary" :loading="submitting" @click="handleSave">
          保存修改
        </el-button>
      </el-form>
    </div>

    <div class="senior-card hover-card">
      <div class="senior-row">
        <div>
          <p class="senior-title">长辈模式</p>
          <p class="senior-desc">开启后 AI 助手会用更大字号提示、更耐心的说法帮你操作</p>
        </div>
        <el-switch
          :model-value="userStore.isSeniorMode"
          size="large"
          @change="toggleSeniorMode"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  max-width: 720px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.profile-card {
  padding: 28px;
}

h2 {
  margin: 0 0 4px;
}

.meta {
  margin: 0 0 20px;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.submit {
  width: 100%;
}

.senior-card {
  padding: 20px 28px;
}

.senior-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.senior-title {
  margin: 0;
  font-weight: 600;
}

.senior-desc {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  font-size: 13px;
}

@media (max-width: 768px) {
  .profile-card {
    padding: 20px;
  }
}
</style>
