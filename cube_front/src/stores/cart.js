import { ref } from 'vue'

// 轻量级购物车刷新机制：任何组件修改购物车后调用 bumpCartVersion()，
// Header 组件 watch 到变化后自动重新拉取购物车数量
const cartVersion = ref(0)

export const useCartRefresh = () => {
  const bumpCartVersion = () => {
    cartVersion.value++
  }

  return {
    cartVersion,
    bumpCartVersion
  }
}
