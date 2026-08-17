<script setup>
/**
 * SplashView.vue — 启动加载页
 *
 * 深色背景 + 3D 魔方线框旋转动画 + ICube 标题
 * 加载完成后跳转登录页
 */
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const progress = ref(0)
const show = ref(true)

let progressTimer = null

const loadingTasks = [
  '初始化引擎...',
  '加载公式库...',
  '同步资源...',
]

const currentTask = ref(loadingTasks[0])

onMounted(() => {
  let taskIdx = 0
  progressTimer = setInterval(() => {
    progress.value = Math.min(100, progress.value + 2 + Math.random() * 2)

    const expectedTask = Math.floor((progress.value / 100) * loadingTasks.length)
    if (expectedTask !== taskIdx && expectedTask < loadingTasks.length) {
      taskIdx = expectedTask
      currentTask.value = loadingTasks[taskIdx]
    }

    if (progress.value >= 100) {
      clearInterval(progressTimer)
      setTimeout(() => {
        show.value = false
        setTimeout(() => {
          const token = localStorage.getItem('token')
          router.replace(token ? '/formula' : '/login')
        }, 200)
      }, 100)
    }
  }, 50)
})

onBeforeUnmount(() => {
  if (progressTimer) clearInterval(progressTimer)
})
</script>

<template>
  <Transition name="splash-fade">
    <div v-if="show" class="splash">
      <!-- 3D 魔方线框 -->
      <div class="cube-stage">
        <div class="cube">
          <div class="cube-face cube-front"></div>
          <div class="cube-face cube-back"></div>
          <div class="cube-face cube-left"></div>
          <div class="cube-face cube-right"></div>
          <div class="cube-face cube-top"></div>
          <div class="cube-face cube-bottom"></div>
        </div>
      </div>

      <!-- ICube 标题 -->
      <div class="splash-title">
        <h1>ICube</h1>
        <p>魔方学习平台</p>
      </div>

      <!-- 加载进度 -->
      <div class="splash-loading">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progress + '%' }"></div>
        </div>
        <div class="progress-info">
          <span class="progress-text">{{ currentTask }}</span>
          <span class="progress-num">{{ Math.round(progress) }}%</span>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.splash {
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #0a0e1a;
  z-index: 9999;
  overflow: hidden;
}

.splash::before {
  content: '';
  position: absolute;
  width: 200%;
  height: 200%;
  background: radial-gradient(ellipse at center, rgba(37, 99, 235, 0.15) 0%, transparent 50%);
  animation: glow-pulse 4s ease-in-out infinite;
}

@keyframes glow-pulse {
  0%, 100% { transform: scale(0.8); opacity: 0.5; }
  50% { transform: scale(1); opacity: 1; }
}

/* ── 3D 魔方线框 ──────────────────────── */
.cube-stage {
  perspective: 800px;
  margin-bottom: 2.5rem;
}

.cube {
  width: 80px;
  height: 80px;
  position: relative;
  transform-style: preserve-3d;
  animation: cube-rotate 4s linear infinite;
}

@keyframes cube-rotate {
  from { transform: rotateX(-20deg) rotateY(0deg); }
  to { transform: rotateX(-20deg) rotateY(360deg); }
}

.cube-face {
  position: absolute;
  width: 80px;
  height: 80px;
  border: 1.5px solid rgba(96, 165, 250, 0.7);
  background: rgba(37, 99, 235, 0.08);
  box-shadow: 0 0 20px rgba(96, 165, 250, 0.15);
}

.cube-face::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(to right, transparent calc(33.33% - 0.5px), rgba(96, 165, 250, 0.4) calc(33.33% - 0.5px), rgba(96, 165, 250, 0.4) 33.33%, transparent 33.33%),
    linear-gradient(to right, transparent calc(66.66% - 0.5px), rgba(96, 165, 250, 0.4) calc(66.66% - 0.5px), rgba(96, 165, 250, 0.4) 66.66%, transparent 66.66%),
    linear-gradient(to bottom, transparent calc(33.33% - 0.5px), rgba(96, 165, 250, 0.4) calc(33.33% - 0.5px), rgba(96, 165, 250, 0.4) 33.33%, transparent 33.33%),
    linear-gradient(to bottom, transparent calc(66.66% - 0.5px), rgba(96, 165, 250, 0.4) calc(66.66% - 0.5px), rgba(96, 165, 250, 0.4) 66.66%, transparent 66.66%);
}

.cube-front  { transform: translateZ(40px); }
.cube-back   { transform: rotateY(180deg) translateZ(40px); }
.cube-left   { transform: rotateY(-90deg) translateZ(40px); }
.cube-right  { transform: rotateY(90deg) translateZ(40px); }
.cube-top    { transform: rotateX(90deg) translateZ(40px); }
.cube-bottom { transform: rotateX(-90deg) translateZ(40px); }

/* ── 标题 ──────────────────────────────── */
.splash-title {
  text-align: center;
  margin-bottom: 2rem;
  z-index: 1;
}

.splash-title h1 {
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: 0.15em;
  color: #fff;
  text-shadow: 0 0 30px rgba(96, 165, 250, 0.5);
  animation: title-fade-in 0.8s ease-out;
}

.splash-title p {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 0.3em;
  margin-top: 0.4rem;
  animation: title-fade-in 0.8s ease-out 0.2s both;
}

@keyframes title-fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ── 加载进度 ────────────────────────────── */
.splash-loading {
  width: 200px;
  z-index: 1;
  animation: title-fade-in 0.6s ease-out 0.4s both;
}

.progress-bar {
  width: 100%;
  height: 3px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
  border-radius: 2px;
  transition: width 0.1s ease;
  box-shadow: 0 0 10px rgba(96, 165, 250, 0.6);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
}

.progress-text {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
  letter-spacing: 0.05em;
}

.progress-num {
  font-size: 0.7rem;
  color: rgba(96, 165, 250, 0.8);
  font-family: 'Cascadia Code', 'Consolas', monospace;
}

/* ── 退出动画 ────────────────────────────── */
.splash-fade-leave-active {
  transition: opacity 0.3s ease;
}

.splash-fade-leave-to {
  opacity: 0;
}
</style>
