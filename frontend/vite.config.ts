import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import Components from 'unplugin-vue-components/vite'
import { defineConfig, loadEnv } from 'vite'

// Element Plus 按需引入：AutoImport 负责 ElMessage 等 API，
// Components 负责 el-* 组件；两者都生成 dts 供 TS 类型提示。
export default defineConfig(({ mode }) => {
  // 配置文件执行时 Vite 还没把 .env 注入 process.env，必须用 loadEnv 显式读取
  const env = loadEnv(mode, process.cwd(), '')
  const proxyTarget = env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000'
  const apiProxy = {
    '/api': {
      target: proxyTarget,
      changeOrigin: true,
    },
  }

  return {
    plugins: [
      vue(),
      AutoImport({
        imports: ['vue', 'vue-router', 'pinia'],
        resolvers: [ElementPlusResolver()],
        dts: 'src/auto-imports.d.ts',
      }),
      Components({
        resolvers: [ElementPlusResolver()],
        dts: 'src/components.d.ts',
      }),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      port: 5173,
      host: true, // WSL 下允许从 Windows 侧浏览器访问
      // 开发代理：把 /api 转发到后端，浏览器侧变成同源请求，彻底绕开 CORS
      proxy: apiProxy,
    },
    // `vite preview` 不会复用 server.proxy；本地验证生产构建时需要单独配置，
    // 否则预览页面所有 /api 请求都会 404。
    preview: {
      port: 4173,
      host: true,
      proxy: apiProxy,
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            'vue-vendor': ['vue', 'vue-router', 'pinia'],
            'element-plus': ['element-plus'],
          },
        },
      },
    },
  }
})