<script setup>
/**
 * NotationKeyboard.vue — 公式记号键盘
 *
 * 4 行布局，与 web 端 FormulaEditor 一致：
 *   R L U D F B | r l u d f b | M E S x y z | ' 2
 * 点击插入字符，修饰符附加到上一步末尾。
 */
defineOptions({ name: 'NotationKeyboard' })

const props = defineProps({
  modelValue: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue'])

const topRow = ['R', 'L', 'U', 'D', 'F', 'B']
const middleRow = ['r', 'l', 'u', 'd', 'f', 'b']
const bottomRow = ['M', 'E', 'S', 'x', 'y', 'z']
const modifiers = ["'", '2']

function addNotation(key) {
  if (key === "'" || key === '2') {
    if (!props.modelValue.trim()) return
    const lastStep = props.modelValue.split(/\s+/).pop()
    const lastChar = lastStep.slice(-1)
    if (lastChar !== "'" && lastChar !== '2') {
      const steps = props.modelValue.trim().split(/\s+/)
      steps[steps.length - 1] = lastStep + key
      emit('update:modelValue', steps.join(' '))
    }
  } else {
    emit('update:modelValue', props.modelValue + (props.modelValue ? ' ' : '') + key)
  }
}

function addSpace() {
  if (!props.modelValue || props.modelValue.endsWith(' ')) return
  emit('update:modelValue', props.modelValue + ' ')
}

function backspace() {
  const trimmed = props.modelValue.trimEnd()
  if (!trimmed) return
  const lastChar = trimmed.slice(-1)
  if (lastChar === "'" || lastChar === '2') {
    emit('update:modelValue', trimmed.slice(0, -1))
  } else {
    const steps = trimmed.split(/\s+/)
    steps.pop()
    emit('update:modelValue', steps.join(' '))
  }
}

function clearAll() {
  emit('update:modelValue', '')
}
</script>

<template>
  <div class="notation-keyboard">
    <div class="keyboard-row">
      <button
        v-for="key in topRow"
        :key="key"
        class="key-btn"
        @click="addNotation(key)"
      >{{ key }}</button>
    </div>
    <div class="keyboard-row">
      <button
        v-for="key in middleRow"
        :key="key"
        class="key-btn"
        @click="addNotation(key)"
      >{{ key }}</button>
    </div>
    <div class="keyboard-row">
      <button
        v-for="key in bottomRow"
        :key="key"
        class="key-btn"
        @click="addNotation(key)"
      >{{ key }}</button>
    </div>
    <div class="keyboard-row">
      <button
        v-for="key in modifiers"
        :key="key"
        class="key-btn modifier"
        @click="addNotation(key)"
      >{{ key }}</button>
      <button class="key-btn action" @click="addSpace">空格</button>
      <button class="key-btn action" @click="backspace">删除</button>
      <button class="key-btn action danger" @click="clearAll">清空</button>
    </div>
  </div>
</template>

<style scoped>
.notation-keyboard {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: var(--van-background-2);
  border-radius: 8px;
}

.keyboard-row {
  display: flex;
  gap: 6px;
  justify-content: center;
}

.key-btn {
  flex: 1;
  min-width: 0;
  height: 44px;
  border: 1px solid var(--van-border-color);
  border-radius: 6px;
  background: var(--van-background);
  color: var(--van-text-color);
  font-size: 1rem;
  font-weight: 600;
  font-family: 'Cascadia Code', 'Consolas', monospace;
  cursor: pointer;
  user-select: none;
  -webkit-user-select: none;
  transition: background-color 0.1s;
}

.key-btn:active {
  background: var(--van-primary-color-light);
}

.key-btn.modifier {
  flex: 0 0 60px;
  color: var(--van-primary-color);
}

.key-btn.action {
  font-size: 0.85rem;
  font-weight: 500;
}

.key-btn.danger {
  color: var(--van-danger-color);
}
</style>
