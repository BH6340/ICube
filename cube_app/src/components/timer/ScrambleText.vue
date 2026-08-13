<script setup>
/**
 * ScrambleText.vue — 打乱公式展示组件
 *
 * 等宽字体展示打乱公式，支持点击刷新按钮重新生成。
 */
defineOptions({ name: 'ScrambleText' })

defineProps({
  scramble: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['refresh'])
</script>

<template>
  <div class="scramble-section">
    <div class="scramble-header">
      <span class="scramble-label">打乱公式</span>
      <van-icon name="replay" size="18" class="refresh-icon" @click="emit('refresh')" />
    </div>
    <div class="scramble-text">{{ scramble || '点击刷新生成打乱' }}</div>
  </div>
</template>

<style scoped>
.scramble-section {
  background: var(--van-background-2);
  border-radius: 8px;
  padding: 12px 16px;
  margin: 8px 12px;
}

.scramble-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.scramble-label {
  font-size: 0.8rem;
  color: var(--van-text-color-2);
}

.refresh-icon {
  color: var(--van-primary-color);
  cursor: pointer;
  padding: 4px;
}

.scramble-text {
  font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
  font-size: 1.05rem;
  font-weight: 600;
  line-height: 1.6;
  word-break: break-all;
  letter-spacing: 0.02em;
  color: var(--van-text-color);
  min-height: 2.2rem;
}
</style>
