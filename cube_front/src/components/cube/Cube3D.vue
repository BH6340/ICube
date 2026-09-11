<template>
  <div ref="containerRef" class="cube-3d-container"></div>
</template>

<script setup>
/**
 * Cube3D.vue - 3D 魔方组件（可复用）
 *
 * 功能：
 *   - Three.js 渲染 3x3 魔方
 *   - 接收标准记号字符串驱动转动（R/U/F/D/L/B 及其逆/双层/转体）
 *   - 转动队列：动画中自动排队，空闲即播
 *   - 支持复位、获取状态
 *
 * 使用方式：
 *   <Cube3D ref="cube3d" :animation-speed="120" />
 *   cube3d.rotate('R') → 转 R
 *   cube3d.reset() → 复原
 *
 * 移植性：不依赖 BLE、不依赖业务逻辑，纯 3D 渲染 + 转动动画
 */

import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { Tween, Group, Easing } from '@tweenjs/tween.js'

const props = defineProps({
  animationSpeed: {
    type: Number,
    default: 120
  },
  background: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['moveCompleted'])

const containerRef = ref(null)

// Three.js 内部变量
let scene, camera, renderer, controls
let outerGroup
let cubeGroup
let cubes = []
const tweenGroup = new Group()
let animationFrameId = null
let needsRender = true

// 共享资源
let sharedGeometry = null
let sharedEdgesGeometry = null
let sharedEdgeMaterial = null
let sharedMaterials = null

// 预分配临时对象（避免动画热路径中 GC）
const _rotAxis = new THREE.Vector3()
const _rotMatrix = new THREE.Matrix4()
const _rotQuat = new THREE.Quaternion()

// 转动队列
const moveQueue = []
let isAnimating = false

// 标准配色（用户视角：U=白 D=黄 F=绿 B=蓝 R=红 L=橙）
const COLOR_MAP = {
  white: 0xf0f0f0,
  yellow: 0xffc400,
  green: 0x1f9e1f,
  blue: 0x1c5ed4,
  red: 0xc40824,
  orange: 0xe67400,
  INTERNAL: 0x101010
}

// GAN 面字母 → 颜色名
const FACE_TO_COLOR = {
  U: 'white', D: 'yellow', F: 'green', B: 'blue', R: 'red', L: 'orange'
}

// 当前配色方案（面字母 → 颜色名）
let currentColorScheme = {
  U: 'white', D: 'yellow', F: 'green', B: 'blue', R: 'red', L: 'orange'
}

// ===== 记号 → 旋转参数 =====
// 坐标系：x=R/L, y=U/D, z=F/B
function parseNotation(notation) {
  const base = notation.replace("'", "").replace("2", "")
  let axis = 'x'
  let conditions = []
  let angle = -Math.PI / 2
  let isWholeCube = false

  switch (base) {
    case 'R': axis = 'x'; conditions = [{ op: '>', value: 0.5 }]; break
    case 'L': axis = 'x'; conditions = [{ op: '<', value: -0.5 }]; angle = Math.PI / 2; break
    case 'U': axis = 'y'; conditions = [{ op: '>', value: 0.5 }]; break
    case 'D': axis = 'y'; conditions = [{ op: '<', value: -0.5 }]; angle = Math.PI / 2; break
    case 'F': axis = 'z'; conditions = [{ op: '>', value: 0.5 }]; break
    case 'B': axis = 'z'; conditions = [{ op: '<', value: -0.5 }]; angle = Math.PI / 2; break
    case 'r': axis = 'x'; conditions = [{ op: '>', value: -0.5 }]; break
    case 'l': axis = 'x'; conditions = [{ op: '<', value: 0.5 }]; angle = Math.PI / 2; break
    case 'u': axis = 'y'; conditions = [{ op: '>', value: -0.5 }]; break
    case 'd': axis = 'y'; conditions = [{ op: '<', value: 0.5 }]; angle = Math.PI / 2; break
    case 'f': axis = 'z'; conditions = [{ op: '>', value: -0.5 }]; break
    case 'b': axis = 'z'; conditions = [{ op: '<', value: 0.5 }]; angle = Math.PI / 2; break
    case 'M': axis = 'x'; conditions = [{ op: '==', value: 0 }]; break
    case 'E': axis = 'y'; conditions = [{ op: '==', value: 0 }]; break
    case 'S': axis = 'z'; conditions = [{ op: '==', value: 0 }]; break
    case 'x': axis = 'x'; conditions = []; isWholeCube = true; break
    case 'y': axis = 'y'; conditions = []; isWholeCube = true; break
    case 'z': axis = 'z'; conditions = []; isWholeCube = true; break
    default: return null
  }

  // 逆 / 180°
  if (notation.includes("'")) {
    angle = -angle
  }
  if (notation.includes('2')) {
    angle = angle * 2
  }

  return { axis, conditions, angle, isWholeCube }
}

// ===== 初始化 Three.js =====
function initThree() {
  if (!containerRef.value) return

  const width = containerRef.value.clientWidth || 300
  const height = containerRef.value.clientHeight || 300

  scene = new THREE.Scene()

  if (props.background) {
    scene.background = new THREE.Color(props.background)
  }

  // 相机
  camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100)
  camera.position.set(5.5, 5.5, 8)

  // 渲染器
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  containerRef.value.appendChild(renderer.domElement)

  // 轨道控制
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.minDistance = 4
  controls.maxDistance = 15
  controls.addEventListener('change', () => { needsRender = true })

  // 构建魔方
  buildCube()

  // 渲染循环（按需渲染：无动画/无交互/无姿态更新时跳过 renderer.render）
  const renderLoop = (time) => {
    animationFrameId = requestAnimationFrame(renderLoop)
    const currentTime = time !== undefined ? time : performance.now()
    tweenGroup.update(currentTime)
    controls.update()

    if (tweenGroup.getAll().length > 0) needsRender = true
    if (needsRender) {
      renderer.render(scene, camera)
      needsRender = false
    }
  }
  renderLoop()

  // 窗口 resize
  window.addEventListener('resize', handleResize)
}

// ===== 构建魔方（复原状态，标准配色）=====
function buildCube() {
  // 外层整体姿态组（只创建一次）
  if (!outerGroup) {
    outerGroup = new THREE.Group()
    scene.add(outerGroup)
  }
  // 清理内层
  if (cubeGroup) {
    outerGroup.remove(cubeGroup)
  }
  cubeGroup = new THREE.Group()
  outerGroup.add(cubeGroup)
  cubes = []

  // 释放旧共享资源
  if (sharedGeometry) sharedGeometry.dispose()
  if (sharedEdgesGeometry) sharedEdgesGeometry.dispose()
  if (sharedEdgeMaterial) sharedEdgeMaterial.dispose()
  if (sharedMaterials) {
    Object.values(sharedMaterials).forEach(m => m.dispose())
  }

  // 创建共享资源（1 份 geometry + 1 份 edges + 7 个 material）
  sharedGeometry = new THREE.BoxGeometry(0.984, 0.984, 0.984)
  sharedEdgesGeometry = new THREE.EdgesGeometry(sharedGeometry)
  sharedEdgeMaterial = new THREE.LineBasicMaterial({ color: 0x222222 })
  sharedMaterials = {
    U: new THREE.MeshBasicMaterial({ color: COLOR_MAP[currentColorScheme.U] || COLOR_MAP.INTERNAL }),
    D: new THREE.MeshBasicMaterial({ color: COLOR_MAP[currentColorScheme.D] || COLOR_MAP.INTERNAL }),
    R: new THREE.MeshBasicMaterial({ color: COLOR_MAP[currentColorScheme.R] || COLOR_MAP.INTERNAL }),
    L: new THREE.MeshBasicMaterial({ color: COLOR_MAP[currentColorScheme.L] || COLOR_MAP.INTERNAL }),
    F: new THREE.MeshBasicMaterial({ color: COLOR_MAP[currentColorScheme.F] || COLOR_MAP.INTERNAL }),
    B: new THREE.MeshBasicMaterial({ color: COLOR_MAP[currentColorScheme.B] || COLOR_MAP.INTERNAL }),
    INTERNAL: new THREE.MeshBasicMaterial({ color: COLOR_MAP.INTERNAL }),
  }

  for (let x = -1; x <= 1; x++) {
    for (let y = -1; y <= 1; y++) {
      for (let z = -1; z <= 1; z++) {
        // BoxGeometry 材质顺序：[+x, -x, +y, -y, +z, -z]
        const materials = [
          x === 1 ? sharedMaterials.R : sharedMaterials.INTERNAL,
          x === -1 ? sharedMaterials.L : sharedMaterials.INTERNAL,
          y === 1 ? sharedMaterials.U : sharedMaterials.INTERNAL,
          y === -1 ? sharedMaterials.D : sharedMaterials.INTERNAL,
          z === 1 ? sharedMaterials.F : sharedMaterials.INTERNAL,
          z === -1 ? sharedMaterials.B : sharedMaterials.INTERNAL,
        ]

        const mesh = new THREE.Mesh(sharedGeometry, materials)
        mesh.position.set(x, y, z)

        const edges = new THREE.LineSegments(sharedEdgesGeometry, sharedEdgeMaterial)
        mesh.add(edges)

        cubeGroup.add(mesh)
        cubes.push(mesh)
      }
    }
  }

  needsRender = true
}

// ===== 执行单步转动 =====
function executeRotation(stepStr, duration) {
  return new Promise((resolve) => {
    if (!stepStr) return resolve()

    const result = parseNotation(stepStr)
    if (!result) return resolve()

    const { axis, conditions, angle, isWholeCube } = result
    const EPSILON = 0.05

    // 筛选参与旋转的小方块（用 cubeGroup 局部坐标，不受 outerGroup 旋转影响）
    const movingCubes = isWholeCube ? cubes : cubes.filter(mesh => {
      const pos = mesh.position[axis]
      return conditions.every(cond => {
        switch (cond.op) {
          case '>': return pos > (cond.value - EPSILON)
          case '<': return pos < (cond.value + EPSILON)
          case '==': return Math.abs(pos) < 0.5
          default: return true
        }
      })
    })

    if (movingCubes.length === 0) return resolve()

    // 0 时长 = 瞬切
    if (duration === 0) {
      movingCubes.forEach(mesh => {
        rotateMeshAroundLocalAxis(mesh, axis, angle)
      })
      needsRender = true
      return resolve()
    }

    // Tween 动画
    const animState = { currentAngle: 0 }
    let lastAngle = 0

    new Tween(animState, tweenGroup)
      .to({ currentAngle: angle }, duration)
      .easing(Easing.Quadratic.Out)
      .onUpdate(() => {
        const delta = animState.currentAngle - lastAngle
        lastAngle = animState.currentAngle
        movingCubes.forEach(mesh => {
          rotateMeshAroundLocalAxis(mesh, axis, delta)
        })
      })
      .onComplete(() => {
        resolve()
      })
      .start()
  })
}

// ===== cubeGroup 局部坐标系旋转（不受 outerGroup 姿态影响）=====
// 使用预分配对象，避免热路径中反复 new 导致 GC 压力
function rotateMeshAroundLocalAxis(mesh, axisStr, radians) {
  _rotAxis.set(
    axisStr === 'x' ? 1 : 0,
    axisStr === 'y' ? 1 : 0,
    axisStr === 'z' ? 1 : 0
  )
  _rotMatrix.makeRotationAxis(_rotAxis, radians)
  mesh.position.applyMatrix4(_rotMatrix)
  _rotQuat.setFromRotationMatrix(_rotMatrix)
  mesh.quaternion.premultiply(_rotQuat)
}

// ===== 转动队列处理 =====
function processQueue() {
  if (isAnimating) return
  if (moveQueue.length === 0) return

  isAnimating = true
  const next = moveQueue.shift()
  executeRotation(next, props.animationSpeed).then(() => {
    isAnimating = false
    emit('moveCompleted', next)
    processQueue()
  })
}

// ===== 暴露给父组件的方法 =====
defineExpose({
  /** 执行一步转动（入队） */
  rotate(notation) {
    moveQueue.push(notation)
    processQueue()
  },

  /** 执行一串转动（入队多个） */
  rotateSequence(notations) {
    if (Array.isArray(notations)) {
      moveQueue.push(...notations)
    } else {
      moveQueue.push(...notations.split(/\s+/).filter(Boolean))
    }
    processQueue()
  },

  /** 复位到复原状态 */
  reset() {
    moveQueue.length = 0
    isAnimating = false
    tweenGroup.getAll().forEach(t => t.stop())
    buildCube()
  },

  /** 是否有动画在进行 */
  get isAnimating() {
    return isAnimating || moveQueue.length > 0
  },

  /** 清空队列 */
  clearQueue() {
    moveQueue.length = 0
  },

  /**
   * 根据持握方向设置颜色方案并重建魔方
   * @param {string} topFace 朝顶的面（U/D/R/L/F/B）
   * @param {string} frontFace 朝前的面
   */
  setColorScheme(topFace, frontFace) {
    const OPPOSITE = { U: 'D', D: 'U', F: 'B', B: 'F', R: 'L', L: 'R' }
    const bottomFace = OPPOSITE[topFace]
    const backFace = OPPOSITE[frontFace]
    const FACE_NORMALS_VEC = {
      U: [0, 1, 0], D: [0, -1, 0],
      R: [1, 0, 0], L: [-1, 0, 0],
      F: [0, 0, 1], B: [0, 0, -1]
    }
    const tv = FACE_NORMALS_VEC[topFace]
    const fv = FACE_NORMALS_VEC[frontFace]
    const rightVec = [
      tv[1] * fv[2] - tv[2] * fv[1],
      tv[2] * fv[0] - tv[0] * fv[2],
      tv[0] * fv[1] - tv[1] * fv[0]
    ]
    let rightFace = null
    for (const [face, normal] of Object.entries(FACE_NORMALS_VEC)) {
      if (Math.abs(normal[0] - rightVec[0]) < 0.01 &&
          Math.abs(normal[1] - rightVec[1]) < 0.01 &&
          Math.abs(normal[2] - rightVec[2]) < 0.01) {
        rightFace = face
        break
      }
    }
    const leftFace = rightFace ? OPPOSITE[rightFace] : 'L'

    currentColorScheme = {
      U: FACE_TO_COLOR[topFace],
      D: FACE_TO_COLOR[bottomFace],
      F: FACE_TO_COLOR[frontFace],
      B: FACE_TO_COLOR[backFace],
      R: FACE_TO_COLOR[rightFace] || 'red',
      L: FACE_TO_COLOR[leftFace]
    }

    buildCube()
  },

  /**
   * 设置整体姿态四元数（陀螺仪跟随用）
   * GAN 坐标系 → Three.js 坐标系映射：
   *   GAN X（R-L 轴，前后翻转）→ Three X（同轴）
   *   GAN Z（U-D 轴，左右旋转）→ Three Y（同轴）
   *   GAN Y（F-B 轴，侧翻）   → -Three Z（方向取反：GAN +Y=B 而 Three +Z=F）
   * @param {{w:number, x:number, y:number, z:number}} quat 四元数（GAN 坐标系）
   */
  setAttitude(quat) {
    if (!outerGroup) return
    outerGroup.quaternion.set(quat.x, quat.z, -quat.y, quat.w)
    needsRender = true
  },

  /**
   * 设置初始静态姿态（经典模式用）
   * @param {string} topFace 朝顶的面（U/D/R/L/F/B）
   * @param {string} frontFace 朝前的面
   */
  setInitialPose(topFace, frontFace) {
    if (!outerGroup) return
    const FACE_NORMALS = {
      U: [0, 1, 0], D: [0, -1, 0],
      R: [1, 0, 0], L: [-1, 0, 0],
      F: [0, 0, 1], B: [0, 0, -1]
    }
    const topV = FACE_NORMALS[topFace]
    const frontV = FACE_NORMALS[frontFace]
    const rightV = [
      topV[1] * frontV[2] - topV[2] * frontV[1],
      topV[2] * frontV[0] - topV[0] * frontV[2],
      topV[0] * frontV[1] - topV[1] * frontV[0]
    ]
    const m = new THREE.Matrix4()
    m.set(
      rightV[0], topV[0], frontV[0], 0,
      rightV[1], topV[1], frontV[1], 0,
      rightV[2], topV[2], frontV[2], 0,
      0, 0, 0, 1
    )
    outerGroup.quaternion.setFromRotationMatrix(m)
    needsRender = true
  },

  /** 重置整体姿态为单位四元数 */
  resetAttitude() {
    if (outerGroup) {
      outerGroup.quaternion.identity()
      needsRender = true
    }
  }
})

// ===== 窗口尺寸变化 =====
function handleResize() {
  if (!containerRef.value || !camera || !renderer) return
  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight
  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
  needsRender = true
}

// ===== 生命周期 =====
onMounted(() => {
  initThree()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)

  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
    animationFrameId = null
  }

  tweenGroup.getAll().forEach(t => t.stop())
  moveQueue.length = 0
  isAnimating = false

  // 释放共享资源
  if (sharedGeometry) { sharedGeometry.dispose(); sharedGeometry = null }
  if (sharedEdgesGeometry) { sharedEdgesGeometry.dispose(); sharedEdgesGeometry = null }
  if (sharedEdgeMaterial) { sharedEdgeMaterial.dispose(); sharedEdgeMaterial = null }
  if (sharedMaterials) {
    Object.values(sharedMaterials).forEach(m => m.dispose())
    sharedMaterials = null
  }

  cubes = []

  if (controls) {
    controls.dispose()
    controls = null
  }

  if (renderer) {
    renderer.dispose()
    renderer = null
  }

  scene = null
  camera = null
  cubeGroup = null
  outerGroup = null
})
</script>

<style scoped>
.cube-3d-container {
  width: 100%;
  height: 100%;
  min-height: 300px;
  background: #f5f5f5;
}

.cube-3d-container :deep(canvas) {
  display: block;
  width: 100% !important;
  height: 100% !important;
}
</style>
