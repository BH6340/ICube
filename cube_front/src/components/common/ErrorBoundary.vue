<template>
  <slot v-if="!error" />
  <section v-else class="error-boundary" :class="{ 'error-boundary-full': fullPage }" role="alert">
    <div class="error-boundary-card">
      <div class="error-boundary-icon">!</div>
      <h2>页面运行异常</h2>
      <p>页面在渲染时发生错误，可能导致部分功能不可用。可尝试重试，或返回首页。</p>
      <details class="error-boundary-detail">
        <summary>查看错误详情</summary>
        <pre>{{ errorMessage }}</pre>
      </details>
      <div class="error-boundary-actions">
        <el-button type="primary" @click="retry">重试</el-button>
        <el-button @click="returnHome">返回首页</el-button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onErrorCaptured } from 'vue'
import { useRouter } from 'vue-router'

defineProps({
  fullPage: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['error'])

const error = ref(null)
const errorMessage = ref('')
const router = useRouter()

onErrorCaptured((err, instance, info) => {
  error.value = err
  errorMessage.value = err?.message || String(err)
  emit('error', err, info)
  return false
})

const retry = () => {
  error.value = null
  errorMessage.value = ''
}

const returnHome = () => {
  error.value = null
  errorMessage.value = ''
  router.push('/')
}
</script>

<style scoped>
.error-boundary {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 220px);
  padding: 24px;
}

.error-boundary-full {
  min-height: 100vh;
  background: #f5f7fa;
}

.error-boundary-card {
  width: min(440px, 100%);
  padding: 44px 38px;
  text-align: center;
  background: #fff;
  border: 1px solid #fde2e2;
  border-radius: 16px;
  box-shadow: 0 10px 32px rgba(245, 108, 108, 0.1);
}

.error-boundary-icon {
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

.error-boundary-card h2 {
  margin: 0 0 10px;
  color: #303133;
  font-size: 23px;
}

.error-boundary-card p {
  margin: 0 0 20px;
  color: #909399;
  font-size: 14px;
  line-height: 1.7;
}

.error-boundary-detail {
  margin: 0 0 24px;
  text-align: left;
}

.error-boundary-detail summary {
  cursor: pointer;
  color: #909399;
  font-size: 13px;
  user-select: none;
}

.error-boundary-detail pre {
  margin: 10px 0 0;
  padding: 12px;
  max-height: 160px;
  overflow: auto;
  background: #f5f7fa;
  border-radius: 8px;
  color: #c45656;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}

.error-boundary-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}
</style>
