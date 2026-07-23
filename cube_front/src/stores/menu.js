/**
 * 导航菜单状态管理 Store
 *
 * 管理前端导航菜单的动态加载和分类，支持：
 *   - 从后端 API 拉取菜单配置
 *   - 区分主导航栏和个人中心菜单
 *   - 防止重复请求
 *
 * 状态字段：
 *   - allMenus: 所有菜单列表
 *   - isLoaded: 菜单是否已加载（防止重复请求）
 *
 * 计算属性：
 *   - mainMenus: 主导航栏菜单（category === 'main'）
 *   - profileMenus: 个人中心菜单（category === 'profile'）
 *
 * 设计特点：
 *   - **懒加载**：首次调用 fetchMenus 时加载，后续调用直接返回
 *   - **分类过滤**：通过 computed 属性自动过滤不同类型的菜单
 *   - **错误处理**：API 请求失败时打印错误日志，不阻断页面渲染
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getMenusApi } from '@/api/home'

export const useMenuStore = defineStore('menu', () => {
    /** 所有菜单列表 */
    const allMenus = ref([])
    /** 菜单是否已加载 */
    const isLoaded = ref(false)

    /**
     * 主导航栏菜单
     *
     * 过滤 category 为 'main' 的菜单，用于顶部导航栏渲染。
     */
    const mainMenus = computed(() => allMenus.value.filter(m => m.category === 'main'))

    /**
     * 个人中心菜单
     *
     * 过滤 category 为 'profile' 的菜单，用于侧边栏渲染。
     */
    const profileMenus = computed(() => allMenus.value.filter(m => m.category === 'profile'))

    /**
     * 拉取菜单数据
     *
     * 从后端 API 获取菜单配置，支持重复调用拦截（已加载时直接返回）。
     *
     * @returns {Promise<void>}
     */
    const fetchMenus = async () => {
        if (isLoaded.value) return

        try {
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