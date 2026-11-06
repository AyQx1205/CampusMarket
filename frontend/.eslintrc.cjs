/* ESLint 8 legacy 配置：Vue 3 + TypeScript。
 * 只开 essential 规则，避免把历史项目大量格式问题一次性变成 CI 失败；
 * 格式统一交给 Prettier。 */
module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    node: true,
  },
  extends: ['eslint:recommended', 'plugin:vue/vue3-essential'],
  parser: 'vue-eslint-parser',
  parserOptions: {
    parser: '@typescript-eslint/parser',
    ecmaVersion: 'latest',
    sourceType: 'module',
    extraFileExtensions: ['.vue'],
  },
  plugins: ['@typescript-eslint'],
  globals: {
    // Vue <script setup> 编译宏（无需 import）
    defineProps: 'readonly',
    defineEmits: 'readonly',
    defineExpose: 'readonly',
    withDefaults: 'readonly',
  },
  rules: {
    'vue/multi-word-component-names': 'off',
    // 项目用 DOMPurify 清洗后再 v-html（AiMessage）
    'vue/no-v-html': 'off',
    'no-unused-vars': 'off',
    // TypeScript 自己检查未定义标识符；核心 no-undef 不认识 TS 类型（Record/Partial 等）
    'no-undef': 'off',
    // 大量接口调用使用「catch { // 提示由拦截器统一处理 }」的写法
    'no-empty': ['error', { allowEmptyCatch: true }],
    // 未使用变量交给 vue-tsc 的 noUnusedLocals，ESLint 不重复报（历史文件较多）
    '@typescript-eslint/no-unused-vars': 'off',
    '@typescript-eslint/no-explicit-any': 'off',
  },
  ignorePatterns: ['dist', 'node_modules', 'auto-imports.d.ts', 'components.d.ts'],
  overrides: [
    {
      files: ['**/*.ts'],
      parser: '@typescript-eslint/parser',
    },
  ],
}