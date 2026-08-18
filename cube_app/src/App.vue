<template>
  <div class="app-container">
    <div
      class="app-content"
      @touchstart.passive="onTouchStart"
      @touchend.passive="onTouchEnd"
    >
      <router-view v-slot="{ Component }">
        <transition :name="transitionName">
          <keep-alive exclude="FormulaDetailView,PostDetailView">
            <component :is="Component" />
          </keep-alive>
        </transition>
      </router-view>
    </div>
    <van-tabbar v-if="!$route.meta.noTabbar" v-model="active" route :fixed="false" safe-area-inset-bottom>
      <van-tabbar-item to="/formula" icon="search" @click="onFormulaTap">公式</van-tabbar-item>
      <van-tabbar-item to="/timer" icon="clock-o">计时</van-tabbar-item>
      <van-tabbar-item to="/forum" icon="chat-o">论坛</van-tabbar-item>
      <van-tabbar-item to="/profile" icon="user-o">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useTabReset } from '@/composables/useTabReset'

const active = ref(0)
const router = useRouter()
const route = useRoute()
const { triggerReset } = useTabReset()

let lastFormulaTap = 0
function onFormulaTap() {
  const now = Date.now()
  if (now - lastFormulaTap < 400) {
    triggerReset()
    lastFormulaTap = 0
  } else {
    lastFormulaTap = now
  }
}

const transitionName = ref('')

// 主 Tab 页路径（按顺序排列，用于滑动切换）
const tabPaths = ['/formula', '/timer', '/forum', '/profile']

// 监听路由变化，自动设置过渡方向
watch(() => route.path, (newPath, oldPath) => {
  const newRoot = '/' + (newPath?.split('/')[1] || '')
  const oldRoot = '/' + (oldPath?.split('/')[1] || '')
  const newIdx = tabPaths.indexOf(newRoot)
  const oldIdx = tabPaths.indexOf(oldRoot)
  if (newIdx === -1 || oldIdx === -1) {
    transitionName.value = 'fade'
  } else if (newIdx > oldIdx) {
    transitionName.value = 'slide-left'
  } else {
    transitionName.value = 'slide-right'
  }
})

// 触摸滑动状态
let touchStartX = 0
let touchStartY = 0
let touchStartTime = 0
let touchStartFromEdge = false
const EDGE_SWIPE_WIDTH = 40

function onTouchStart(e) {
  if (route.meta.noTabbar) return
  const touch = e.touches[0]
  touchStartX = touch.clientX
  touchStartY = touch.clientY
  touchStartTime = Date.now()
  // 判断是否从屏幕左右边缘开始触摸
  touchStartFromEdge = touch.clientX <= EDGE_SWIPE_WIDTH || touch.clientX >= window.innerWidth - EDGE_SWIPE_WIDTH
}

function onTouchEnd(e) {
  if (route.meta.noTabbar) return
  if (document.querySelector('.van-popup--show')) return

  const touch = e.changedTouches[0]
  const deltaX = touch.clientX - touchStartX
  const deltaY = touch.clientY - touchStartY
  const elapsed = Date.now() - touchStartTime

  // 阈值：水平位移 > 80px，水平位移 > 1.5x 垂直位移，时间 < 500ms
  if (Math.abs(deltaX) < 80) return
  if (Math.abs(deltaX) < Math.abs(deltaY) * 1.5) return
  if (elapsed > 500) return

  // 排除 swipe-cell
  if (e.target.closest('.van-swipe-cell')) return

  // 在 van-tabs 内容区内：仅允许边缘滑动切换大 Tab，中间区域交给 swipeable
  if (e.target.closest('.van-tabs__content') && !touchStartFromEdge) return

  // 查找当前 tab 索引
  const currentPath = '/' + (route.path.split('/')[1] || '')
  const currentIndex = tabPaths.indexOf(currentPath)
  if (currentIndex === -1) return

  // 右滑 → 上一页，左滑 → 下一页
  const nextIndex = deltaX > 0 ? currentIndex - 1 : currentIndex + 1
  if (nextIndex >= 0 && nextIndex < tabPaths.length) {
    router.push(tabPaths[nextIndex])
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body,
#app {
  height: 100%;
}

body {
  font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  -webkit-tap-highlight-color: transparent;
}

.app-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.app-content {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  position: relative;
}

/* Tab 页滑动过渡 */
.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 0.3s ease;
  position: absolute;
  width: 100%;
  top: 0;
  left: 0;
}

.slide-left-enter-from {
  transform: translateX(100%);
}

.slide-left-leave-to {
  transform: translateX(-100%);
}

.slide-right-enter-from {
  transform: translateX(-100%);
}

.slide-right-leave-to {
  transform: translateX(100%);
}

/* 非 Tab 页淡入淡出 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
