<script setup lang="ts">
/** 通用空状态：图标 + 文案 + 可选操作按钮。 */
withDefaults(
  defineProps<{
    description?: string
    actionText?: string
  }>(),
  {
    description: '暂无内容',
    actionText: '',
  },
)

const emit = defineEmits<{
  action: []
}>()
</script>

<template>
  <div class="empty-state">
    <el-empty :description="description">
      <el-button v-if="actionText" type="primary" @click="emit('action')">
        {{ actionText }}
      </el-button>
    </el-empty>
  </div>
</template>

<style scoped>
.empty-state {
  padding: 40px 0;
}
</style>
