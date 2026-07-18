import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// 1. 导入 Element Plus 相关的插件
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    // 2. 配置自动导入
    AutoImport({
      resolvers: [ElementPlusResolver()],
      imports: ['vue', 'vue-router', 'pinia']
    }),
    Components({
      resolvers: [ElementPlusResolver()]
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      // 匹配所有以 /api 开头的请求
      '/api': {
        target: 'http://127.0.0.1:8000', // 后端真实地址
        changeOrigin: true,             // 允许跨域
        // 如果后端接口本身不带 /api 前缀，则需要重写路径
        // rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
