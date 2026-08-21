import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { VantResolver } from '@vant/auto-import-resolver'
import { fileURLToPath, URL } from 'node:url'

// 移动端 Vite 配置
// 与 cube_front 对齐：自动导入 Vue/Router/Pinia API + Vant 组件
// proxy target 读取 .env 中的 VITE_PROXY_TARGET，默认指向本地后端
export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      imports: ['vue', 'vue-router', 'pinia'],
      resolvers: [VantResolver()],
      dts: false,
    }),
    Components({
      resolvers: [VantResolver()],
      dts: false,
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // 允许局域网访问，供 Capacitor 实时刷新调试
    host: '0.0.0.0',
    port: 5174,
    // 开发环境代理：target 从 .env 读取，本地开发留空走 Vite proxy，远程调试填服务器地址
    proxy: {
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
      '/media': {
        target: process.env.VITE_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
