<script setup>
/**
 * ConfirmDialog.vue — 通用确认弹窗
 * 居中卡片式，带渐变图标和竖向按钮
 */
defineOptions({ name: 'ConfirmDialog' })

defineProps({
  show: { type: Boolean, default: false },
  title: { type: String, default: '确认操作' },
  message: { type: String, default: '' },
  confirmText: { type: String, default: '确认' },
  cancelText: { type: String, default: '取消' },
  confirmColor: { type: String, default: '#ee0a24' },
  icon: { type: String, default: 'warning-o' },
})

const emit = defineEmits(['confirm', 'cancel', 'update:show'])

function onConfirm() {
  emit('confirm')
}

function onCancel() {
  emit('cancel')
  emit('update:show', false)
}
</script>

<template>
  <van-popup
    :show="show"
    @update:show="emit('update:show', $event)"
    position="center"
    :close-on-click-overlay="true"
    class="confirm-popup"
    :style="{ '--c': confirmColor }"
  >
    <div class="confirm-dialog">
      <div class="confirm-icon-wrap">
        <van-icon :name="icon" color="#fff" size="30" />
      </div>
      <div v-if="title" class="confirm-title">{{ title }}</div>
      <div v-if="message" class="confirm-message">{{ message }}</div>
      <div class="confirm-actions">
        <button class="confirm-ok" @click="onConfirm">{{ confirmText }}</button>
        <button class="confirm-cancel" @click="onCancel">{{ cancelText }}</button>
      </div>
    </div>
  </van-popup>
</template>

<style scoped>
.confirm-popup {
  width: 300px;
  max-width: 90vw;
  border-radius: 20px;
  overflow: hidden;
  background: #fff;
}

.confirm-dialog {
  padding: 28px 24px 18px;
  text-align: center;
}

.confirm-icon-wrap {
  width: 56px;
  height: 56px;
  margin: 0 auto 14px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--c), color-mix(in srgb, var(--c) 75%, #000 25%));
  box-shadow: 0 8px 20px -6px var(--c);
}

.confirm-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--van-text-color);
  margin-bottom: 6px;
  line-height: 1.4;
}

.confirm-message {
  font-size: 0.88rem;
  color: var(--van-text-color-2);
  line-height: 1.6;
  margin-bottom: 22px;
  padding: 0 4px;
}

.confirm-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.confirm-ok {
  height: 44px;
  border: none;
  border-radius: 12px;
  font-size: 0.95rem;
  font-weight: 500;
  color: #fff;
  background: linear-gradient(135deg, var(--c), color-mix(in srgb, var(--c) 75%, #000 25%));
  box-shadow: 0 4px 12px -4px var(--c);
  transition: transform 0.15s, box-shadow 0.15s;
}

.confirm-ok:active {
  transform: scale(0.97);
  box-shadow: 0 2px 6px -2px var(--c);
}

.confirm-cancel {
  height: 40px;
  border: none;
  background: transparent;
  font-size: 0.9rem;
  color: var(--van-text-color-3);
  transition: opacity 0.15s;
}

.confirm-cancel:active {
  opacity: 0.6;
}
</style>
