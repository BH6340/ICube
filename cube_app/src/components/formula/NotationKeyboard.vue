<script setup>
/**
 * NotationKeyboard.vue — 公式记号键盘
 *
 * 4 行布局，与 web 端 FormulaEditor 一致：
 *   R L U D F B | r l u d f b | M E S x y z | ' 2
 * 支持在光标位置插入字符（中间编辑）。
 */
defineOptions({ name: 'NotationKeyboard' })

const props = defineProps({
  modelValue: { type: String, default: '' },
  cursorPos: { type: Number, default: -1 }
})
const emit = defineEmits(['update:modelValue', 'update:cursorPos'])

const topRow = ['R', 'L', 'U', 'D', 'F', 'B']
const middleRow = ['r', 'l', 'u', 'd', 'f', 'b']
const bottomRow = ['M', 'E', 'S', 'x', 'y', 'z']
const modifiers = ["'", '2']

function getPos() {
  const text = props.modelValue || ''
  return props.cursorPos >= 0 && props.cursorPos <= text.length ? props.cursorPos : text.length
}

function addNotation(key) {
  const text = props.modelValue || ''
  const pos = getPos()
  const before = text.slice(0, pos)
  const after = text.slice(pos)

  if (key === "'" || key === '2') {
    const lastChar = before.slice(-1)
    if (!lastChar || lastChar === ' ' || lastChar === "'" || lastChar === '2') return
    emit('update:modelValue', before + key + after)
    emit('update:cursorPos', pos + 1)
  } else {
    let prefix = before && !before.endsWith(' ') ? ' ' : ''
    let suffix = after && !after.startsWith(' ') ? ' ' : ''
    emit('update:modelValue', before + prefix + key + suffix + after)
    emit('update:cursorPos', pos + prefix.length + key.length)
  }
}

function addSpace() {
  const text = props.modelValue || ''
  const pos = getPos()
  const before = text.slice(0, pos)
  const after = text.slice(pos)
  if (before && !before.endsWith(' ')) {
    emit('update:modelValue', before + ' ' + after)
    emit('update:cursorPos', pos + 1)
  }
}

function backspace() {
  const text = props.modelValue || ''
  const pos = getPos()
  if (pos === 0) return

  const before = text.slice(0, pos)
  const after = text.slice(pos)
  const lastChar = before.slice(-1)

  if (lastChar === "'" || lastChar === '2' || lastChar === ' ') {
    emit('update:modelValue', before.slice(0, -1) + after)
    emit('update:cursorPos', pos - 1)
  } else {
    const tokenStart = before.lastIndexOf(' ') + 1
    emit('update:modelValue', text.slice(0, tokenStart) + after)
    emit('update:cursorPos', tokenStart)
  }
}

function clearAll() {
  emit('update:modelValue', '')
  emit('update:cursorPos', 0)
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
