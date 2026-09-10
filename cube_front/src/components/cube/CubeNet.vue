<template>
  <div class="cube-net" :style="{ '--cell-size': cellSize + 'px' }">
    <!-- 布局：
          U
       L  F  R  B
          D
    -->
    <div class="net-row net-row-u">
      <div class="net-face net-u">
        <div class="face-label">U</div>
        <div class="face-grid">
          <div
            v-for="(color, i) in uFace"
            :key="'u-' + i"
            class="face-cell"
            :style="{ backgroundColor: colorMap[color] || '#333' }"
          ></div>
        </div>
      </div>
    </div>

    <div class="net-row net-row-mid">
      <div class="net-face net-l">
        <div class="face-label">L</div>
        <div class="face-grid">
          <div
            v-for="(color, i) in lFace"
            :key="'l-' + i"
            class="face-cell"
            :style="{ backgroundColor: colorMap[color] || '#333' }"
          ></div>
        </div>
      </div>
      <div class="net-face net-f">
        <div class="face-label">F</div>
        <div class="face-grid">
          <div
            v-for="(color, i) in fFace"
            :key="'f-' + i"
            class="face-cell"
            :style="{ backgroundColor: colorMap[color] || '#333' }"
          ></div>
        </div>
      </div>
      <div class="net-face net-r">
        <div class="face-label">R</div>
        <div class="face-grid">
          <div
            v-for="(color, i) in rFace"
            :key="'r-' + i"
            class="face-cell"
            :style="{ backgroundColor: colorMap[color] || '#333' }"
          ></div>
        </div>
      </div>
      <div class="net-face net-b">
        <div class="face-label">B</div>
        <div class="face-grid">
          <div
            v-for="(color, i) in bFace"
            :key="'b-' + i"
            class="face-cell"
            :style="{ backgroundColor: colorMap[color] || '#333' }"
          ></div>
        </div>
      </div>
    </div>

    <div class="net-row net-row-d">
      <div class="net-face net-d">
        <div class="face-label">D</div>
        <div class="face-grid">
          <div
            v-for="(color, i) in dFace"
            :key="'d-' + i"
            class="face-cell"
            :style="{ backgroundColor: colorMap[color] || '#333' }"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { createSolvedState, applyScramble, getFace } from '@/utils/cube-state'

const props = defineProps({
  // 打乱序列，如 ['R', "U'", 'F2']
  scramble: {
    type: Array,
    default: () => []
  },
  // 单格尺寸（px）
  cellSize: {
    type: Number,
    default: 18
  }
})

const colorMap = {
  white: '#f5f5f5',
  yellow: '#ffd700',
  green: '#32cd32',
  blue: '#1e90ff',
  red: '#dc143c',
  orange: '#ff8c00',
}

const state = computed(() => {
  if (!props.scramble || props.scramble.length === 0) {
    return createSolvedState()
  }
  return applyScramble(props.scramble)
})

const uFace = computed(() => getFace(state.value, 'U'))
const dFace = computed(() => getFace(state.value, 'D'))
const fFace = computed(() => getFace(state.value, 'F'))
const bFace = computed(() => getFace(state.value, 'B'))
const lFace = computed(() => getFace(state.value, 'L'))
const rFace = computed(() => getFace(state.value, 'R'))
</script>

<style scoped>
.cube-net {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  --cell-size: 18px;
}

.net-row {
  display: flex;
  gap: 2px;
}

.net-face {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.face-label {
  font-size: 10px;
  color: #999;
  font-weight: 500;
  line-height: 1;
}

.face-grid {
  display: grid;
  grid-template-columns: repeat(3, var(--cell-size));
  grid-template-rows: repeat(3, var(--cell-size));
  gap: 1px;
  background: #222;
  padding: 1px;
  border-radius: 2px;
}

.face-cell {
  border-radius: 1px;
}
</style>
