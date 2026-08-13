<template>
  <transition name="route-loading-fade">
    <div
      v-if="visible"
      class="route-loading-mask"
      :class="{ 'route-loading-full-page': fullPage }"
      role="status"
      aria-live="polite"
    >
      <div class="route-loading-box">
        <span class="route-loading-spinner"></span>
        <span>页面加载中...</span>
      </div>
    </div>
  </transition>
</template>

<script setup>
defineProps({
  visible: {
    type: Boolean,
    required: true
  },
  fullPage: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.route-loading-mask {
  position: absolute;
  z-index: 10;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.38);
}

.route-loading-full-page {
  position: fixed;
  z-index: 2000;
}

.route-loading-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 18px 24px;
  color: #409eff;
  font-size: 14px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #ecf5ff;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(64, 158, 255, 0.14);
}

.route-loading-spinner {
  width: 34px;
  height: 34px;
  border: 3px solid #d9ecff;
  border-top-color: #409eff;
  border-radius: 50%;
  animation: route-spin 0.8s linear infinite;
}

.route-loading-fade-enter-active,
.route-loading-fade-leave-active {
  transition: opacity 0.18s ease;
}

.route-loading-fade-enter-from,
.route-loading-fade-leave-to {
  opacity: 0;
}

@keyframes route-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .route-loading-spinner {
    animation-duration: 2s;
  }

  .route-loading-fade-enter-active,
  .route-loading-fade-leave-active {
    transition: none;
  }
}
</style>
