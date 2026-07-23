/**
 * 购物车刷新机制 Store
 *
 * 提供轻量级的购物车版本控制，用于跨组件同步购物车状态。
 *
 * 设计原理：
 *   - 使用 cartVersion 计数器作为版本标识
 *   - 任何组件修改购物车后调用 bumpCartVersion() 递增版本号
 *   - Header 组件 watch cartVersion，版本变化时自动重新拉取购物车数量
 *
 * 设计特点：
 *   - **轻量级**：不存储购物车数据，只管理版本号，避免数据冗余
 *   - **跨组件通信**：无需事件总线，通过 Pinia 的响应式特性实现
 *   - **性能优化**：按需刷新，只在版本变化时重新请求
 */

import { ref } from 'vue'

/** 购物车版本号，用于触发刷新 */
const cartVersion = ref(0)

/**
 * 购物车刷新 hook
 *
 * @returns {Object} 包含 cartVersion 和 bumpCartVersion
 */
export const useCartRefresh = () => {
    /**
     * 递增购物车版本号
     *
     * 购物车数据变更时调用，触发监听该版本号的组件重新拉取数据。
     */
    const bumpCartVersion = () => {
        cartVersion.value++
    }

    return {
        cartVersion,
        bumpCartVersion
    }
}