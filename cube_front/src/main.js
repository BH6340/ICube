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
app.use(router) // 1.2 插件必须在 mount 之前使用

app.mount('#app')
