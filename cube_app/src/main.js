import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// Vant 函数式组件（showToast 等）需手动引入样式
import 'vant/es/toast/style'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
