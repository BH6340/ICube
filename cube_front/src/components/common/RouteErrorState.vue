<template>
  <section class="route-error-state" :class="{ 'route-error-full-page': fullPage }" role="alert">
    <div class="route-error-card">
      <div class="route-error-icon">!</div>
      <h2>页面加载失败</h2>
      <p>网络连接异常或页面资源暂时不可用，请检查网络后重新加载。</p>
      <el-button type="primary" @click="retryRoute">重新加载</el-button>
      <el-button @click="returnHome">返回首页</el-button>
    </div>
  </section>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { useRouteLoading } from '@/stores/routeLoading'

defineProps({
  fullPage: {
    type: Boolean,
    default: false
  }
})

const route = useRoute()
const router = useRouter()
const { targetPath, reset } = useRouteLoading()

const retryRoute = () => {
  const path = targetPath.value || route.fullPath
  reset()
  window.location.assign(path)
}

const returnHome = async () => {
  reset()
  await router.push('/')
}
</script>

<style scoped>
.route-error-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 220px);
}

.route-error-full-page {
  min-height: 100vh;
  padding: 24px;
  background: #f5f7fa;
}

.route-error-card {
  width: min(440px, 100%);
  padding: 44px 38px;
  text-align: center;
  background: #fff;
  border: 1px solid #fde2e2;
  border-radius: 16px;
  box-shadow: 0 10px 32px rgba(245, 108, 108, 0.1);
}

.route-error-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 68px;
  height: 68px;
  margin: 0 auto 20px;
  color: #f56c6c;
  font-size: 38px;
  font-weight: 300;
  background: #fef0f0;
  border-radius: 50%;
}

.route-error-card h2 {
  margin: 0 0 10px;
  color: #303133;
  font-size: 23px;
}

.route-error-card p {
  margin: 0 0 24px;
  color: #909399;
  font-size: 14px;
  line-height: 1.7;
}
</style>
