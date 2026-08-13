<template>
  <div class="app-container">
    <div
      class="app-content"
      @touchstart.passive="onTouchStart"
      @touchend.passive="onTouchEnd"
    >
      <router-view v-slot="{ Component }">
        <keep-alive exclude="FormulaDetailView,PostDetailView">
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </div>
    <van-tabbar v-if="!$route.meta.noTabbar" v-model="active" route :fixed="false" safe-area-inset-bottom>
      <van-tabbar-item to="/formula" icon="search">公式</van-tabbar-item>
      <van-tabbar-item to="/timer" icon="clock-o">计时</van-tabbar-item>
      <van-tabbar-item to="/forum" icon="chat-o">论坛</van-tabbar-item>
      <van-tabbar-item to="/profile" icon="user-o">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const active = ref(0)
const router = useRouter()
const route = useRoute()

// 主 Tab 页路径（按顺序排列，用于滑动切换）
const tabPaths = ['/formula', '/timer', '/forum', '/profile']

// 触摸滑动状态
let touchStartX = 0
let touchStartY = 0
let touchStartTime = 0

function onTouchStart(e) {
  // 仅在主 Tab 页面启用滑动切换
  if (route.meta.noTabbar) return
  const touch = e.touches[0]
  touchStartX = touch.clientX
  touchStartY = touch.clientY
  touchStartTime = Date.now()
}

function onTouchEnd(e) {
  if (route.meta.noTabbar) return

  const touch = e.changedTouches[0]
  const deltaX = touch.clientX - touchStartX
  const deltaY = touch.clientY - touchStartY
  const elapsed = Date.now() - touchStartTime

  // 阈值：水平位移 > 80px，水平位移 > 1.5x 垂直位移，时间 < 500ms
  if (Math.abs(deltaX) < 80) return
  if (Math.abs(deltaX) < Math.abs(deltaY) * 1.5) return
  if (elapsed > 500) return

  // 排除 swipe-cell 内的触摸（避免与列表项左滑删除冲突）
  if (e.target.closest('.van-swipe-cell')) return

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
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-content {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}
</style>
