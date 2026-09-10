/**
 * 魔方持握方向与转体检测模块
 *
 * 架构：初始朝向映射 + 转体标记
 *   - 连接后用陀螺仪识别初始朝向，生成一套静态映射
 *   - 所有 MOVE 事件走这套映射，不随转体变化
 *   - 陀螺仪只做两件事：检测转体插入 x/y/z、提供当前朝向（供 3D 展示）
 *
 * 双模式：
 *   - 陀螺仪模式：CubeOrientationTracker，自动识别顶面 + 用户确认朝前面
 *   - 经典模式：StaticOrientation，用户手动选择持握方向
 *
 * 统一接口：remapMove(internalMove, ctx)
 *
 * 坐标系约定（GAN 魔方内部）：
 *   +X = R（红），+Y = B（蓝），+Z = U（白）
 *   世界坐标系：+Z 朝上，+Y 朝前（屏幕方向）
 *
 * 标准魔方转体记号：
 *   x = 绕 R-L 轴旋转（前后翻）→ 世界 X 轴
 *   y = 绕 U-D 轴旋转（左右转）→ 世界 Z 轴
 *   z = 绕 F-B 轴旋转（侧翻）→ 世界 Y 轴
 */

// ===== 常量 =====

// 魔方内部 6 个面的法向量
const FACE_NORMALS = {
  U: [0, 0, 1],
  D: [0, 0, -1],
  R: [1, 0, 0],
  L: [-1, 0, 0],
  F: [0, -1, 0],
  B: [0, 1, 0]
}

const FACES = ['U', 'D', 'R', 'L', 'F', 'B']
const FACE_INDICES = { U: 0, D: 1, R: 2, L: 3, F: 4, B: 5 }

// 预设持握方向（经典模式）
const PRESET_ORIENTATIONS = [
  { key: 'white-top-green-front', label: '白顶绿前（标准）', top: 'U', front: 'F' },
  { key: 'white-bottom-green-front', label: '白底绿前', top: 'D', front: 'F' },
  { key: 'white-top-red-front', label: '白顶红前', top: 'U', front: 'R' },
  { key: 'white-bottom-red-front', label: '白底红前', top: 'D', front: 'R' },
  { key: 'white-top-blue-front', label: '白顶蓝前', top: 'U', front: 'B' },
  { key: 'white-top-orange-front', label: '白顶橙前', top: 'U', front: 'L' }
]

// 转体检测参数（稳定检测状态机）
const ROTATION_THRESHOLD = 40   // 度，累积角度超过此值才判定为有效转体
const MOTION_THRESHOLD = 5      // 度，帧间增量超过此值认为"还在动"
const SETTLE_TIME = 250         // ms，持续无大动作多久才判定为"停下来了"

// ===== 四元数运算 =====

function quatNormalize(q) {
  const len = Math.sqrt(q.w * q.w + q.x * q.x + q.y * q.y + q.z * q.z)
  if (len < 1e-8) return { w: 1, x: 0, y: 0, z: 0 }
  return { w: q.w / len, x: q.x / len, y: q.y / len, z: q.z / len }
}

function quatConjugate(q) {
  return { w: q.w, x: -q.x, y: -q.y, z: -q.z }
}

function quatMultiply(a, b) {
  return {
    w: a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z,
    x: a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
    y: a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
    z: a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w
  }
}

/** 用四元数旋转向量 */
function rotateVector(q, v) {
  const qv = { w: 0, x: v[0], y: v[1], z: v[2] }
  const result = quatMultiply(quatMultiply(q, qv), quatConjugate(q))
  return [result.x, result.y, result.z]
}

/** 两四元数的相对旋转 Δq = q₂ × q₁⁻¹ */
function quatDelta(q1, q2) {
  return quatMultiply(q2, quatConjugate(q1))
}

/** 四元数转轴角（角度单位：度） */
function quatToAxisAngle(q) {
  const w = Math.max(-1, Math.min(1, q.w))
  const angle = 2 * Math.acos(w) * 180 / Math.PI
  const s = Math.sqrt(1 - w * w)
  if (s < 1e-6) return { axis: [0, 0, 0], angle: 0 }
  return { axis: [q.x / s, q.y / s, q.z / s], angle }
}

function dot(a, b) {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
}

function cross(a, b) {
  return [
    a[1] * b[2] - a[2] * b[1],
    a[2] * b[0] - a[0] * b[2],
    a[0] * b[1] - a[1] * b[0]
  ]
}

// ===== 静态映射 =====

/**
 * 由顶面和前面推导完整 6 面映射表
 * @param {string} topFace 朝顶的内部面
 * @param {string} frontFace 朝前的内部面
 * @returns { 内部面 → { face: 用户面, invert: 是否反转 } }
 */
function buildStaticMap(topFace, frontFace) {
  const topVec = FACE_NORMALS[topFace]
  const frontVec = FACE_NORMALS[frontFace]
  // right = top × front（右手坐标系叉乘）
  const rightVec = cross(topVec, frontVec)

  const userAxes = {
    up: topVec,
    down: topVec.map(c => -c),
    front: frontVec,
    back: frontVec.map(c => -c),
    right: rightVec,
    left: rightVec.map(c => -c)
  }

  const userFaceNames = { up: 'U', down: 'D', front: 'F', back: 'B', right: 'R', left: 'L' }
  const map = {}

  for (const face of FACES) {
    const normal = FACE_NORMALS[face]
    let bestKey = null
    let bestDot = -2

    // 有符号比较：取最大点积，正数优先于负数（同绝对值时正轴胜出）
    for (const [key, axis] of Object.entries(userAxes)) {
      const d = dot(normal, axis)
      if (d > bestDot) {
        bestDot = d
        bestKey = key
      }
    }

    const userFace = userFaceNames[bestKey]
    const invert = bestDot < 0
    map[face] = { face: userFace, invert }
  }

  return map
}

// 预设映射表缓存
const PRESET_MAPS = {}
for (const preset of PRESET_ORIENTATIONS) {
  PRESET_MAPS[preset.key] = buildStaticMap(preset.top, preset.front)
}

// ===== 统一接口：remapMove =====

/**
 * 将魔方内部记号转换为用户视角记号
 * @param {string} move 内部记号，如 "R"、"U'"
 * @param {object|null} ctx 映射上下文
 *                         null = 标准持握，不转换
 * @returns {string} 用户视角记号
 */
export function remapMove(move, ctx) {
  if (!ctx) return move
  const face = move[0]
  const isPrime = move.includes("'")
  const entry = ctx[face]
  if (!entry) return move
  const dir = isPrime ? !entry.invert : entry.invert
  return entry.face + (dir ? "'" : '')
}

// ===== 陀螺仪模式：CubeOrientationTracker =====

export class CubeOrientationTracker {
  constructor() {
    this._currentQuat = null
    this._stableQuat = null        // 上次稳定位置的参考四元数（累积角度的基准）
    this._lastQuat = null          // 上一帧四元数（帧间增量角度的基准）
    this._moving = false           // 是否正在转动中
    this._lastMoveTime = 0         // 最后一次检测到大幅度移动的时间
    this._settlingSince = 0        // 开始接近稳定的时间戳
    this._currentMap = null        // 初始映射，设置后不变
    this._currentOrientation = null // 当前朝向（供 3D 展示）
    this._onRotation = null
    this._onOrientationChange = null
    this._onTopFaceDetected = null
  }

  /** 注册回调：转体检测到时调用 */
  onRotation(callback) { this._onRotation = callback }
  /** 注册回调：当前朝向变化时调用（仅展示，不影响映射） */
  onOrientationChange(callback) { this._onOrientationChange = callback }
  /** 注册回调：陀螺仪识别到顶面时调用 */
  onTopFaceDetected(callback) { this._onTopFaceDetected = callback }

  get currentMap() { return this._currentMap }
  get currentOrientation() { return this._currentOrientation }
  get currentQuaternion() { return this._currentQuat ? { ...this._currentQuat } : null }

  /** 重置状态（重连/复位时调用） */
  reset() {
    this._currentQuat = null
    this._stableQuat = null
    this._lastQuat = null
    this._moving = false
    this._lastMoveTime = 0
    this._settlingSince = 0
    this._currentMap = null
    this._currentOrientation = null
  }

  /**
   * 设置初始映射（用户确认朝前面后调用，只设一次）
   */
  setInitialMap(topFace, frontFace) {
    this._currentMap = buildStaticMap(topFace, frontFace)
  }

  /**
   * 处理 GYRO 事件 — 稳定检测状态机
   *
   * 用两种角度：
   *   - 增量角度（帧间变化）：_lastQuat → q，判断是否"还在动"
   *   - 累积角度（稳定基准到当前）：_stableQuat → q，判定转体类型和幅度
   *
   * 状态流转：
   *   IDLE → 增量角度 > MOTION_THRESHOLD → MOVING
   *   MOVING → 增量角度 < MOTION_THRESHOLD 且持续 SETTLE_TIME → 已稳定
   *          → 累积角度 > ROTATION_THRESHOLD → emit 转体 → IDLE
   *          → 累积角度 < ROTATION_THRESHOLD → 微调，IDLE
   */
  handleGyro(gyroEvent) {
    const q = quatNormalize(gyroEvent.quaternion)
    this._currentQuat = q
    const now = gyroEvent.timestamp || Date.now()

    // 首次收到数据
    if (!this._stableQuat) {
      this._stableQuat = q
      this._lastQuat = q
      this._detectTopFace(q)
      this._updateOrientation(q)
      return
    }

    // 增量角度（帧间变化）：判断是否还在动
    const incDelta = quatDelta(this._lastQuat, q)
    const { angle: incAngle } = quatToAxisAngle(incDelta)

    // 累积角度（稳定基准到当前）：判断转体幅度和方向
    const cumDelta = quatDelta(this._stableQuat, q)
    const { axis: cumAxis, angle: cumAngle } = quatToAxisAngle(cumDelta)

    if (incAngle > MOTION_THRESHOLD) {
      // 还在动
      this._moving = true
      this._lastMoveTime = now
      this._settlingSince = 0
    } else if (this._moving) {
      // 之前在移动，帧间增量小 → 接近稳定
      if (this._settlingSince === 0) {
        this._settlingSince = now
      }
      if (now - this._settlingSince >= SETTLE_TIME) {
        // 已稳定，用累积角度判定转体
        if (cumAngle > ROTATION_THRESHOLD) {
          this._emitRotation(cumAxis, cumAngle, now)
        }
        this._stableQuat = q
        this._moving = false
        this._settlingSince = 0
      }
    } else {
      // IDLE 状态，持续微调，更新基准
      this._stableQuat = q
    }

    // 更新上一帧
    this._lastQuat = q

    // 更新当前朝向（供展示）
    this._updateOrientation(q)
  }

  /**
   * 由四元数检测当前朝顶的面
   */
  _detectTopFace(q) {
    let topFace = null
    let topDot = -2
    for (const face of FACES) {
      const rotated = rotateVector(q, FACE_NORMALS[face])
      if (rotated[2] > topDot) {
        topDot = rotated[2]
        topFace = face
      }
    }
    this._onTopFaceDetected?.(topFace)
  }

  /**
   * 检测当前完整朝向（供 3D 展示，不改变映射）
   */
  _updateOrientation(q) {
    const rotatedNormals = {}
    for (const face of FACES) {
      rotatedNormals[face] = rotateVector(q, FACE_NORMALS[face])
    }

    let topFace = null, topDot = -2
    for (const face of FACES) {
      if (rotatedNormals[face][2] > topDot) {
        topDot = rotatedNormals[face][2]
        topFace = face
      }
    }

    const topOpposite = FACES.find(f => Math.abs(dot(FACE_NORMALS[f], FACE_NORMALS[topFace]) + 1) < 0.01)
    // GAN 坐标系 +Y = B（后），-Y = F（前），世界坐标系 +Y 朝前
    // 所以朝前的面 = 旋转后 y 分量最大的那个面
    let frontFace = null, frontDot = -2
    for (const face of FACES) {
      if (face === topFace || face === topOpposite) continue
      if (rotatedNormals[face][1] > frontDot) {
        frontDot = rotatedNormals[face][1]
        frontFace = face
      }
    }

    const newOrientation = { topFace, frontFace }
    const changed = !this._orientationEqual(this._currentOrientation, newOrientation)
    this._currentOrientation = newOrientation
    if (changed) {
      this._onOrientationChange?.(newOrientation)
    }
  }

  _orientationEqual(a, b) {
    if (!a || !b) return false
    return a.topFace === b.topFace && a.frontFace === b.frontFace
  }

  /**
   * 判定转体类型并触发回调
   * 世界 X 轴 → x（前后翻）
   * 世界 Z 轴 → y（左右转）
   * 世界 Y 轴 → z（侧翻）
   *
   * 方向规则（实测校准）：
   *   x: direction*quarters > 0 → prime
   *   y: direction*quarters > 0 → prime
   *   z: direction*quarters < 0 → prime
   */
  _emitRotation(axis, angle, timestamp) {
    const absAxis = axis.map(Math.abs)
    const maxIdx = absAxis.indexOf(Math.max(...absAxis))
    const axisName = ['x', 'z', 'y'][maxIdx]
    const direction = axis[maxIdx] > 0 ? 1 : -1

    const quarters = Math.round(angle / 90)
    if (quarters === 0) return

    const isPrime = axisName === 'z'
      ? (direction * quarters) < 0
      : (direction * quarters) > 0
    const rotation = axisName + (isPrime ? "'" : '')

    this._onRotation?.({ rotation, axisName, quarters, angle, timestamp })
  }
}

// ===== 经典模式：StaticOrientation =====

export class StaticOrientation {
  constructor(presetKey = null) {
    this._map = presetKey ? PRESET_MAPS[presetKey] : null
  }

  get currentMap() { return this._map }

  setPreset(key) {
    this._map = PRESET_MAPS[key] || null
  }
}

export { PRESET_ORIENTATIONS, buildStaticMap, FACE_NORMALS, FACES }
