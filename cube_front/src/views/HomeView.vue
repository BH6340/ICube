<template>
  <div class="common-layout">
    <el-container>
      <el-header>
        <TopHeader />
      </el-header>

      <el-main class="route-main">
        <RouteErrorState v-if="status === 'error'" />

        <template v-else>
          <div class="route-content" :class="{ 'route-content-loading': overlayVisible }">
            <ErrorBoundary>
              <router-view />
            </ErrorBoundary>
          </div>

          <RouteLoadingMask :visible="overlayVisible" />
        </template>
      </el-main>

      <el-footer>
        <Footer />
      </el-footer>
    </el-container>
  </div>
</template>

<script setup>
/**
 * HomeView.vue - 应用主布局容器
 *
 * 核心职责：
 * 1. 提供全局页面布局（顶部导航 + 主内容区 + 底部页脚）
 * 2. 作为路由容器，渲染子路由页面
 *
 * 设计要点：
 * - 使用 el-container 实现经典三段式布局
 * - 主内容区域 max-width: 1200px，居中显示
 * - 复用 Header 和 Footer 组件，保持全站一致性
 */
import TopHeader from '@/components/Header.vue'
import Footer from '@/components/Footer.vue'
import RouteErrorState from '@/components/common/RouteErrorState.vue'
import ErrorBoundary from '@/components/common/ErrorBoundary.vue'
import RouteLoadingMask from '@/components/common/RouteLoadingMask.vue'
import { onBeforeUnmount, onMounted } from 'vue'
import { useRouteLoading } from '@/stores/routeLoading'

const {
  status,
  overlayVisible,
  setLayoutMounted
} = useRouteLoading()

onMounted(() => setLayoutMounted(true))
onBeforeUnmount(() => setLayoutMounted(false))
</script>

<style>
/* 限制主内容区域的最大宽度，避免大屏下太分散 */
.el-main {
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.route-main {
  position: relative;
  min-height: calc(100vh - 180px);
}

.route-content {
  min-height: inherit;
  opacity: 1;
  transition: opacity 0.2s ease, transform 0.2s ease, filter 0.2s ease;
}

.route-content-loading {
  opacity: 0.38;
  filter: blur(0.6px);
  transform: translateY(4px);
  pointer-events: none;
}

@media (prefers-reduced-motion: reduce) {
  .route-content {
    transition: none;
  }
}
</style>
