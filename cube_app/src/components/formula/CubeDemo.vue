<template>
  <div class="cube-demo-container">
    <div ref="canvasContainer" class="canvas-wrapper"></div>

    <div class="demo-controls">
      <div class="steps-display">
        <span
          v-for="(step, idx) in parsedSteps"
          :key="idx"
          class="step-tag"
          :class="{
            'active': idx === currentStepIdx - 1,
            'pending': idx >= currentStepIdx
          }"
        >
          {{ step }}
        </span>
      </div>

      <div class="progress-info">
        {{ currentStepIdx }} / {{ parsedSteps.length }}
      </div>

      <div class="action-buttons">
        <van-button
          size="small"
          :disabled="isAnimating || currentStepIdx === 0"
          @click="stepBackward"
        >
          上一步
        </van-button>
        <van-button
          size="small"
          type="primary"
          :disabled="isAnimating || currentStepIdx >= parsedSteps.length"
          @click="stepForward"
        >
          下一步
        </van-button>
        <van-button
          size="small"
          :type="isAutoPlaying ? 'warning' : 'success'"
          :disabled="parsedSteps.length === 0"
          @click="toggleAutoPlay"
        >
          {{ isAutoPlaying ? '暂停' : '播放' }}
        </van-button>
        <van-button size="small" @click="resetToFormulaState">
          重置
        </van-button>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * CubeDemo.vue - 魔方 3D 动画演示组件（移动端版）
 *
 * 基于 cube_front 版本复制，修复 4 个问题：
 * 1. onBeforeUnmount 清理不完整 → 完整释放 geometry/material/cancelAnimationFrame/tweenGroup
 * 2. 双重初始化 → 移除 onMounted 的 initThree，仅靠 watch immediate + nextTick
 * 3. 触摸交互 → canvas-wrapper 添加 touch-action: none
 * 4. 响应式高度 → 320px 改为 50vh
 */

import { ref, computed, onBeforeUnmount, watch, nextTick } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { Tween, Group, Easing } from '@tweenjs/tween.js'

const props = defineProps({
  formula: {
    type: Object,
    required: true
  }
})

// 响应式状态
const canvasContainer = ref(null)
const currentStepIdx = ref(0)
const isAnimating = ref(false)
const isAutoPlaying = ref(false)
let autoPlayTimer = null
let animFrameId = null  // 修复1：跟踪 requestAnimationFrame ID

const parsedSteps = computed(() => {
  if (!props.formula || !props.formula.notation) return []
  return props.formula.notation.split(/\s+/).filter(Boolean)
})

const COLOR_MAP = {
  yellow: 0xffd700,
  white: 0xf5f5f5,
  blue: 0x1e90ff,
  green: 0x32cd32,
  orange: 0xff8c00,
  red: 0xdc143c,
  gray: 0x808080,
  INTERNAL: 0x111111
}

let scene, camera, renderer, controls
let cubeGroup
let cubes = []
const tweenGroup = new Group()

const initThree = () => {
  if (!canvasContainer.value) return

  const width = canvasContainer.value.clientWidth || 300
  const height = canvasContainer.value.clientHeight || 300

  scene = new THREE.Scene()
  scene.background = new THREE.Color('#f5f5f5')

  const ambientLight = new THREE.AmbientLight(0xffffff, 0.9)
  scene.add(ambientLight)

  const pointLight1 = new THREE.PointLight(0xffffff, 1.5)
  pointLight1.position.set(5, 5, 5)
  scene.add(pointLight1)

  const pointLight2 = new THREE.PointLight(0xffffff, 0.8)
  pointLight2.position.set(-3, -3, -3)
  scene.add(pointLight2)

  const cameraLight = new THREE.PointLight(0xffffff, 0.6)
  cameraLight.position.set(4, 4, 6)
  scene.add(cameraLight)

  camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100)
  camera.position.set(5, 5, 7)

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))

  canvasContainer.value.innerHTML = ''
  canvasContainer.value.appendChild(renderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.minDistance = 3
  controls.maxDistance = 10

  buildCubeGeometry()

  const renderLoop = (time) => {
    animFrameId = requestAnimationFrame(renderLoop)  // 修复1：跟踪 ID
    const currentTime = time !== undefined ? time : performance.now()
    tweenGroup.update(currentTime)
    controls.update()
    renderer.render(scene, camera)
  }
  renderLoop()
}

const getFaceColor = (faceName, x, y, z, stateDefinition, defaultColors) => {
  if (!stateDefinition || !stateDefinition.faces || !stateDefinition.faces[faceName]) {
    return defaultColors[faceName] || 'INTERNAL'
  }

  const face = stateDefinition.faces[faceName]
  let row, col

  switch (faceName) {
    case 'F':
      row = 1 - y
      col = x + 1
      break
    case 'B':
      row = 1 - y
      col = 1 - x
      break
    case 'U':
      row = z + 1
      col = x + 1
      break
    case 'D':
      row = 1 - z
      col = 1 - x
      break
    case 'R':
      row = 1 - y
      col = 1 - z
      break
    case 'L':
      row = 1 - y
      col = z + 1
      break
    default:
      return defaultColors[faceName] || 'INTERNAL'
  }

  row = Math.max(0, Math.min(2, Math.floor(row)))
  col = Math.max(0, Math.min(2, Math.floor(col)))

  return face[row] && face[row][col] ? face[row][col] : defaultColors[faceName] || 'INTERNAL'
}

const buildCubeGeometry = (stateDefinition = null) => {
  if (cubeGroup) scene.remove(cubeGroup)
  cubeGroup = new THREE.Group()
  scene.add(cubeGroup)
  cubes = []

  const defaultColors = {
    U: 'yellow', D: 'white', F: 'blue', B: 'green', L: 'orange', R: 'red'
  }

  const edgeMaterial = new THREE.LineBasicMaterial({ color: 0x000000 })

  for (let x = -1; x <= 1; x++) {
    for (let y = -1; y <= 1; y++) {
      for (let z = -1; z <= 1; z++) {
        const geometry = new THREE.BoxGeometry(0.92, 0.92, 0.92)

        const rColor = x === 1 ? getFaceColor('R', x, y, z, stateDefinition, defaultColors) : 'INTERNAL'
        const lColor = x === -1 ? getFaceColor('L', x, y, z, stateDefinition, defaultColors) : 'INTERNAL'
        const uColor = y === 1 ? getFaceColor('U', x, y, z, stateDefinition, defaultColors) : 'INTERNAL'
        const dColor = y === -1 ? getFaceColor('D', x, y, z, stateDefinition, defaultColors) : 'INTERNAL'
        const fColor = z === 1 ? getFaceColor('F', x, y, z, stateDefinition, defaultColors) : 'INTERNAL'
        const bColor = z === -1 ? getFaceColor('B', x, y, z, stateDefinition, defaultColors) : 'INTERNAL'

        const materials = [
          new THREE.MeshBasicMaterial({ color: COLOR_MAP[rColor] || COLOR_MAP.INTERNAL }),
          new THREE.MeshBasicMaterial({ color: COLOR_MAP[lColor] || COLOR_MAP.INTERNAL }),
          new THREE.MeshBasicMaterial({ color: COLOR_MAP[uColor] || COLOR_MAP.INTERNAL }),
          new THREE.MeshBasicMaterial({ color: COLOR_MAP[dColor] || COLOR_MAP.INTERNAL }),
          new THREE.MeshBasicMaterial({ color: COLOR_MAP[fColor] || COLOR_MAP.INTERNAL }),
          new THREE.MeshBasicMaterial({ color: COLOR_MAP[bColor] || COLOR_MAP.INTERNAL })
        ]

        const mesh = new THREE.Mesh(geometry, materials)
        mesh.position.set(x, y, z)

        const edgesGeometry = new THREE.EdgesGeometry(geometry)
        const edges = new THREE.LineSegments(edgesGeometry, edgeMaterial)
        mesh.add(edges)

        cubeGroup.add(mesh)
        cubes.push(mesh)
      }
    }
  }
}

const parseNotationToAxis = (notation) => {
  const base = notation.replace("'", "").replace("2", "")
  let axis = 'x'
  let conditions = []
  let angle = -Math.PI / 2
  let isWholeCube = false

  switch (base) {
    case 'R': axis = 'x'; conditions = [{ op: '>', value: 0.5 }]; angle = -Math.PI / 2; break
    case 'L': axis = 'x'; conditions = [{ op: '<', value: -0.5 }]; angle = Math.PI / 2; break
    case 'U': axis = 'y'; conditions = [{ op: '>', value: 0.5 }]; angle = -Math.PI / 2; break
    case 'D': axis = 'y'; conditions = [{ op: '<', value: -0.5 }]; angle = Math.PI / 2; break
    case 'F': axis = 'z'; conditions = [{ op: '>', value: 0.5 }]; angle = -Math.PI / 2; break
    case 'B': axis = 'z'; conditions = [{ op: '<', value: -0.5 }]; angle = Math.PI / 2; break
    case 'r': axis = 'x'; conditions = [{ op: '>', value: -0.5 }]; angle = -Math.PI / 2; break
    case 'l': axis = 'x'; conditions = [{ op: '<', value: 0.5 }]; angle = Math.PI / 2; break
    case 'u': axis = 'y'; conditions = [{ op: '>', value: -0.5 }]; angle = -Math.PI / 2; break
    case 'd': axis = 'y'; conditions = [{ op: '<', value: 0.5 }]; angle = Math.PI / 2; break
    case 'f': axis = 'z'; conditions = [{ op: '>', value: -0.5 }]; angle = -Math.PI / 2; break
    case 'b': axis = 'z'; conditions = [{ op: '<', value: 0.5 }]; angle = Math.PI / 2; break
    case 'M': axis = 'x'; conditions = [{ op: '==', value: 0 }]; angle = -Math.PI / 2; break
    case 'E': axis = 'y'; conditions = [{ op: '==', value: 0 }]; angle = -Math.PI / 2; break
    case 'S': axis = 'z'; conditions = [{ op: '==', value: 0 }]; angle = -Math.PI / 2; break
    case 'x': axis = 'x'; conditions = []; angle = -Math.PI / 2; isWholeCube = true; break
    case 'y': axis = 'y'; conditions = []; angle = -Math.PI / 2; isWholeCube = true; break
    case 'z': axis = 'z'; conditions = []; angle = -Math.PI / 2; isWholeCube = true; break
    case "x'": axis = 'x'; conditions = []; angle = Math.PI / 2; isWholeCube = true; break
    case "y'": axis = 'y'; conditions = []; angle = Math.PI / 2; isWholeCube = true; break
    case "z'": axis = 'z'; conditions = []; angle = Math.PI / 2; isWholeCube = true; break
    default: return null
  }

  if (notation.includes("'") && !base.includes("'")) {
    angle = -angle
  }
  if (notation.includes("2")) {
    angle = angle * 2
  }

  return { axis, conditions, angle, isWholeCube }
}

const executeLayerRotation = (stepStr, duration = 180) => {
  return new Promise((resolve) => {
    if (!stepStr) return resolve()

    const result = parseNotationToAxis(stepStr)
    if (!result) return resolve()

    const { axis, conditions, angle, isWholeCube } = result
    const EPSILON = 0.05

    const movingCubes = isWholeCube ? cubes : cubes.filter(mesh => {
      const worldPos = new THREE.Vector3()
      mesh.getWorldPosition(worldPos)

      return conditions.every(cond => {
        const pos = worldPos[axis]
        switch (cond.op) {
          case '>': return pos > (cond.value - EPSILON)
          case '<': return pos < (cond.value + EPSILON)
          case '==': return Math.abs(pos) < 0.5
          default: return true
        }
      })
    })

    if (movingCubes.length === 0) return resolve()

    if (duration === 0) {
      movingCubes.forEach(mesh => {
        rotateMeshAroundWorldAxis(mesh, axis, angle)
      })
      return resolve()
    }

    isAnimating.value = true
    const animState = { currentAngle: 0 }
    let lastAngle = 0

    new Tween(animState, tweenGroup)
      .to({ currentAngle: angle }, duration)
      .easing(Easing.Quadratic.Out)
      .onUpdate(() => {
        const delta = animState.currentAngle - lastAngle
        lastAngle = animState.currentAngle

        movingCubes.forEach(mesh => {
          rotateMeshAroundWorldAxis(mesh, axis, delta)
        })
      })
      .onComplete(() => {
        isAnimating.value = false
        resolve()
      })
      .start()
  })
}

const rotateMeshAroundWorldAxis = (mesh, axisStr, radians) => {
  const uX = axisStr === 'x' ? 1 : 0
  const uY = axisStr === 'y' ? 1 : 0
  const uZ = axisStr === 'z' ? 1 : 0

  const rotWorldMatrix = new THREE.Matrix4()
  rotWorldMatrix.makeRotationAxis(new THREE.Vector3(uX, uY, uZ), radians)

  mesh.position.applyMatrix4(rotWorldMatrix)
  mesh.quaternion.premultiply(new THREE.Quaternion().setFromRotationMatrix(rotWorldMatrix))
  mesh.updateMatrixWorld(true)
}

const resetToFormulaState = async () => {
  stopAutoPlay()
  currentStepIdx.value = 0

  const targetState = props.formula.target_state
  let stateDefinition = null

  if (targetState && targetState.state_definition) {
    stateDefinition = targetState.state_definition
  }

  buildCubeGeometry(stateDefinition)

  if (stateDefinition && props.formula.inverse_notation) {
    const inverseSteps = props.formula.inverse_notation.split(/\s+/).filter(Boolean)
    for (const step of inverseSteps) {
      await executeLayerRotation(step, 0)
    }
  }

  if (controls && camera) {
    new Tween(camera.position, tweenGroup)
      .to({ x: 5, y: 5, z: 7 }, 300)
      .easing(Easing.Quadratic.Out)
      .start()

    new Tween(controls.target, tweenGroup)
      .to({ x: 0, y: 0, z: 0 }, 300)
      .easing(Easing.Quadratic.Out)
      .start()
  }
}

const stepForward = async () => {
  if (isAnimating.value || currentStepIdx.value >= parsedSteps.value.length) return
  const nextStepStr = parsedSteps.value[currentStepIdx.value]
  currentStepIdx.value++
  await executeLayerRotation(nextStepStr, 180)
}

const stepBackward = async () => {
  if (isAnimating.value || currentStepIdx.value <= 0) return

  const targetStep = currentStepIdx.value - 1
  isAnimating.value = true

  await resetToFormulaState()

  for (let i = 0; i < targetStep; i++) {
    await executeLayerRotation(parsedSteps.value[i], 0)
  }

  currentStepIdx.value = targetStep
  isAnimating.value = false
}

const toggleAutoPlay = () => {
  if (isAutoPlaying.value) {
    stopAutoPlay()
  } else {
    if (currentStepIdx.value >= parsedSteps.value.length) {
      currentStepIdx.value = 0
      resetToFormulaState().then(() => {
        startAutoPlayLoop()
      })
    } else {
      startAutoPlayLoop()
    }
  }
}

const startAutoPlayLoop = () => {
  isAutoPlaying.value = true
  const playNext = async () => {
    if (!isAutoPlaying.value) return
    if (currentStepIdx.value >= parsedSteps.value.length) {
      stopAutoPlay()
      return
    }
    await stepForward()
    autoPlayTimer = setTimeout(playNext, 400)
  }
  playNext()
}

const stopAutoPlay = () => {
  isAutoPlaying.value = false
  if (autoPlayTimer) {
    clearTimeout(autoPlayTimer)
    autoPlayTimer = null
  }
}

// 修复2：移除 onMounted，仅靠 watch immediate + nextTick 处理初始化
// 原代码 watch immediate 和 onMounted 都调用 initThree，导致首次挂载执行两次
watch(() => props.formula, () => {
  nextTick(() => {
    initThree()
    setTimeout(() => {
      resetToFormulaState()
    }, 100)
  })
}, { immediate: true })

// 修复1：完整的清理逻辑，防止内存泄漏
onBeforeUnmount(() => {
  stopAutoPlay()
  if (animFrameId) cancelAnimationFrame(animFrameId)

  // 释放所有 mesh 的 geometry 和 material
  scene?.traverse((child) => {
    if (child.isMesh) {
      child.geometry?.dispose()
      if (Array.isArray(child.material)) {
        child.material.forEach(m => m.dispose())
      } else {
        child.material?.dispose()
      }
    }
  })

  tweenGroup?.removeAll()
  renderer?.dispose()
  if (canvasContainer.value && renderer?.domElement) {
    canvasContainer.value.removeChild(renderer.domElement)
  }
})
</script>

<style scoped>
.cube-demo-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 修复3：touch-action: none 防止触摸旋转魔方时页面误滚动 */
/* 修复4：高度从 320px 改为 50vh，适配不同手机屏幕 */
.canvas-wrapper {
  width: 100%;
  height: 50vh;
  min-height: 280px;
  max-height: 400px;
  background-color: #f5f5f5;
  border-radius: 8px;
  overflow: hidden;
  touch-action: none;
}

.demo-controls {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.steps-display {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  max-height: 60px;
  overflow-y: auto;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 6px;
}

.step-tag {
  font-family: 'Consolas', monospace;
  font-size: 13px;
  font-weight: bold;
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
}

.step-tag.active {
  background-color: #07c160;
  color: white;
  border-color: #07c160;
}

.step-tag.pending {
  background-color: #f4f4f5;
  color: #909399;
}

.progress-info {
  text-align: center;
  font-size: 14px;
  color: #606266;
}

.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
  flex-wrap: wrap;
}

.action-buttons .van-button {
  min-width: 68px;
}
</style>
