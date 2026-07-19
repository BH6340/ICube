// src/stores/menu.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
// 💡 导入刚才补充的 API 接口
import { getMenusApi } from '@/api/home'

export const useMenuStore = defineStore('menu', () => {
  const allMenus = ref([])
  const isLoaded = ref(false)

  // 区分主菜单和个人中心菜单
  const mainMenus = computed(() => allMenus.value.filter(m => m.category === 'main'))
  const profileMenus = computed(() => allMenus.value.filter(m => m.category === 'profile'))

  // 拉取菜单方法
  const fetchMenus = async () => {
    if (isLoaded.value) return // 拦截重复请求，防止刷新路由时频繁轰炸数据库
    try {
      // 💡 优雅地直接调用 API 函数
      const res = await getMenusApi()
      if (res && res.code === 100) {
        allMenus.value = res.data || []
        isLoaded.value = true
      }
    } catch (err) {
      console.error('动态菜单加载失败:', err)
    }
  }

  return { allMenus, mainMenus, profileMenus, isLoaded, fetchMenus }
})