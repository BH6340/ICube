import { createApp } from 'vue'
import { createPinia } from 'pinia'// 2.1 导入
import App from './App.vue'
import router from './router' // 1.1 导入路由配置
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css' //

const app = createApp(App)

import * as ElementPlusIconsVue from '@element-plus/icons-vue'

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(ElementPlus)
app.use(router)

app.config.errorHandler = (err, instance, info) => {
  console.error('Vue Error:', err, info)
}

window.addEventListener('error', (event) => {
  if (event.error?.message?.includes('toLowerCase')) {
    event.preventDefault()
    console.warn('Ignoring toLowerCase error from library:', event.error.message)
  }
})

app.mount('#app')
