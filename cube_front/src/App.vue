<template>
  <div v-if="progressVisible" class="route-progress" role="progressbar" aria-label="页面加载进度">
    <span></span>
  </div>

  <RouteErrorState v-if="status === 'error' && !layoutMounted" full-page />
  <template v-else>
    <ErrorBoundary full-page>
      <router-view />
    </ErrorBoundary>
    <RouteLoadingMask :visible="overlayVisible && !layoutMounted" full-page />
  </template>
</template>

<script setup>
import RouteErrorState from '@/components/common/RouteErrorState.vue'
import ErrorBoundary from '@/components/common/ErrorBoundary.vue'
import RouteLoadingMask from '@/components/common/RouteLoadingMask.vue'
import { useRouteLoading } from '@/stores/routeLoading'

const {
  status,
  progressVisible,
  overlayVisible,
  layoutMounted
} = useRouteLoading()
</script>

<style>
/* 清除默认边距，让导航栏撑满 */
body {
  margin: 0;
  padding: 0;
}

.route-progress {
  position: fixed;
  z-index: 3000;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  overflow: hidden;
  pointer-events: none;
}

.route-progress span {
  display: block;
  width: 82%;
  height: 100%;
  background: linear-gradient(90deg, #409eff, #67c23a);
  box-shadow: 0 0 8px rgba(64, 158, 255, 0.5);
  animation: route-progress 1.2s ease-out infinite;
}

@keyframes route-progress {
  0% {
    opacity: 0.5;
    transform: translateX(-100%);
  }

  100% {
    opacity: 1;
    transform: translateX(125%);
  }
}

@media (prefers-reduced-motion: reduce) {
  .route-progress span {
    animation-duration: 2s;
  }
}
</style>
