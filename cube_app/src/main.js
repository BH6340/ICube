import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { StatusBar, Style } from '@capacitor/status-bar'
import { Capacitor } from '@capacitor/core'

// Vant 函数式组件（showToast 等）需手动引入样式
import 'vant/es/toast/style'

// 状态栏：白色背景，不覆盖 WebView，文字用深色（仅原生平台）
if (Capacitor.isNativePlatform()) {
  StatusBar.setStyle({ style: Style.Light })
  StatusBar.setOverlaysWebView({ overlay: false })
  StatusBar.setBackgroundColor({ color: '#FFFFFFFF' })
}

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
