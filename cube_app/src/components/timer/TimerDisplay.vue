<script setup>
/**
 * TimerDisplay.vue — 大字号时间显示 + 触屏交互区
 *
 * 状态机驱动背景色变化：
 *   idle(灰) → holding(黄) → ready(绿) → running(蓝)
 *
 * 触屏事件透传给父组件处理状态流转。
 */
defineOptions({ name: 'TimerDisplay' })

const props = defineProps({
  state: {
    type: String,
    default: 'idle'
  },
  elapsed: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['touchstart', 'touchend'])

// 毫秒 → MM:SS.mmm 格式
function formatTime(ms) {
  const totalSeconds = ms / 1000
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = Math.floor(totalSeconds % 60)
  const millis = Math.floor(ms % 1000)
  if (minutes > 0) {
    return `${minutes}:${String(seconds).padStart(2, '0')}.${String(millis).padStart(3, '0')}`
  }
  return `${seconds}.${String(millis).padStart(3, '0')}`
}

const hintText = {
  idle: '长按准备',
  holding: '保持按下...',
  ready: '松手开始！',
  running: ''
}
</script>

<template>
  <div
    class="timer-display"
    :class="`state-${state}`"
    @touchstart.prevent="emit('touchstart')"
    @touchend.prevent="emit('touchend')"
  >
    <div class="time-value">
      {{ elapsed > 0 ? formatTime(elapsed) : '00.000' }}<span class="time-unit">s</span>
    </div>
    <div class="hint-text">{{ hintText[state] }}</div>
  </div>
</template>

<style scoped>
.timer-display {
  height: 55vh;
  min-height: 280px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border-radius: 12px;
  margin: 8px 12px;
  transition: background-color 0.15s ease;
  touch-action: none;
  user-select: none;
  -webkit-user-select: none;
}

/* 状态色 */
.state-idle {
  background: #f3f4f6;
  color: #6b7280;
}
.state-holding {
  background: #fef3c7;
  color: #92400e;
}
.state-ready {
  background: #d1fae5;
  color: #065f46;
}
.state-running {
  background: #dbeafe;
  color: #1e40af;
}

.time-value {
  font-size: 3.5rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.02em;
  line-height: 1;
  margin-bottom: 0.5rem;
}

.time-unit {
  font-size: 1.5rem;
  font-weight: 500;
  opacity: 0.7;
  margin-left: 4px;
}

.hint-text {
  font-size: 1.1rem;
  font-weight: 500;
  opacity: 0.8;
}
</style>
