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
        <el-button
            :disabled="isAnimating || currentStepIdx === 0"
            @click="stepBackward"
            size="small"
        >
          上一步
        </el-button>
        <el-button
            type="primary"
            :disabled="isAnimating || currentStepIdx >= parsedSteps.length"
            @click="stepForward"
            size="small"
        >
          下一步
        </el-button>
        <el-button
            :type="isAutoPlaying ? 'warning' : 'success'"
            :disabled="parsedSteps.length === 0"
            @click="toggleAutoPlay"
            size="small"
        >
          {{ isAutoPlaying ? '暂停' : '播放' }}
        </el-button>
        <el-button @click="resetToFormulaState" size="small">
          重置
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * CubeDemo.vue - 魔方 3D 动画演示组件
 * 
 * 核心职责：
 * 1. 使用 Three.js 渲染三阶魔方的 3D 模型
 * 2. 根据公式记号（notation）逐步骤播放魔方转动动画
 * 3. 支持手动单步播放（上一步/下一步）和自动播放
 * 4. 根据公式的 target_state 初始化魔方状态
 * 5. 支持鼠标拖拽旋转视角和滚轮缩放
 * 
 * 技术栈：
 * - Three.js：3D 渲染引擎
 * - OrbitControls：相机轨道控制
 * - Tween.js：动画缓动库
 * 
 * 设计要点：
 * - 将魔方拆分为 27 个小方块（3x3x3），每个方块独立渲染
 * - 使用世界坐标系旋转，而非局部坐标系，确保旋转正确性
 * - 公式记号解析支持标准魔方符号（R/L/U/D/F/B/r/l/u/d/f/b/M/E/S/x/y/z）
 * - 动画状态管理防止重复触发
 */

import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as THREE from 'three'                                          // Three.js 3D 渲染引擎
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'  // 相机轨道控制
import { Tween, Group, Easing } from '@tweenjs/tween.js'               // 动画缓动库

// 组件属性定义
const props = defineProps({
  formula: {
    type: Object,
    required: true,
    description: '公式对象，包含 notation（公式记号）和 target_state（目标状态）'
  }
})

// 响应式状态
const canvasContainer = ref(null)    // 3D 画布容器引用
const currentStepIdx = ref(0)        // 当前播放步骤索引（0 表示初始状态）
const isAnimating = ref(false)       // 是否正在播放动画（防止重复触发）
const isAutoPlaying = ref(false)     // 是否自动播放模式
let autoPlayTimer = null             // 自动播放定时器

/**
 * 解析公式记号为步骤数组
 * 
 * @returns {Array} - 步骤字符串数组
 * 
 * 逻辑：
 * 1. 将公式记号按空格分割
 * 2. 过滤空字符串
 * 3. 例如："R U R'" → ["R", "U", "R'"]
 */
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
  scene.background = new THREE.Color('#1a1a2e')

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
  camera.position.set(4, 4, 6)

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
    requestAnimationFrame(renderLoop)
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

watch(() => props.formula, () => {
  nextTick(() => {
    initThree()
    setTimeout(() => {
      resetToFormulaState()
    }, 100)
  })
}, { immediate: true })

onMounted(() => {
  initThree()
  setTimeout(() => {
    resetToFormulaState()
  }, 100)
})

onBeforeUnmount(() => {
  stopAutoPlay()
  if (renderer) renderer.dispose()
})
</script>

<style scoped>
.cube-demo-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.canvas-wrapper {
  width: 100%;
  height: 320px;
  background-color: #1a1a2e;
  border-radius: 8px;
  overflow: hidden;
}

.demo-controls {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.steps-display {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
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
  background-color: #67c23a;
  color: white;
  border-color: #67c23a;
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
}

.action-buttons .el-button {
  min-width: 70px;
}
</style>