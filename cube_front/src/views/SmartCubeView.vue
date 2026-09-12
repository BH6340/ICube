<template>
  <div class="smart-cube-container">
    <!-- 左侧：3D 魔方 -->
    <div class="cube-panel">
      <div class="cube-wrapper">
        <Cube3D ref="cube3dRef" :animation-speed="120" />
      </div>
      <div class="cube-status-bar">
        <el-tag :type="statusTagType" size="small">{{ statusText }}</el-tag>
        <span v-if="isSolved" class="solved-badge">✓ 已复原</span>
      </div>
    </div>

    <!-- 右侧：控制面板 -->
    <div class="control-panel">
      <!-- 连接区 -->
      <el-card class="connection-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>智能魔方连接</span>
          </div>
        </template>

        <div class="connection-controls">
          <el-button type="primary" @click="handleConnect" :loading="connecting" :disabled="connected">
            连接魔方
          </el-button>
          <el-button @click="handleDisconnect" :disabled="!connected">断开</el-button>
          <el-button @click="handleReset" :disabled="!connected" type="warning">复位</el-button>
          <el-tooltip placement="right" effect="light">
            <template #content>
              <div class="mac-tooltip">
                <p>无法自动获取 MAC 地址时，可通过以下方式查看：</p>
                <p>1. 在地址栏输入 <code>edge://bluetooth-internals/#devices</code>（Chrome 同理）</p>
                <p>2. 找到你的 GAN 魔方设备，复制其 MAC 地址</p>
                <p>3. 回到本页面点击「连接魔方」，在弹窗中粘贴 MAC 地址</p>
              </div>
            </template>
            <el-icon class="mac-hint-icon"><WarningFilled /></el-icon>
          </el-tooltip>
        </div>

        <div v-if="deviceInfo.name || deviceInfo.mac" class="device-info">
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="设备名称">{{ deviceInfo.name }}</el-descriptions-item>
            <el-descriptions-item label="MAC 地址">{{ deviceInfo.mac }}</el-descriptions-item>
            <el-descriptions-item label="电量">
              <span v-if="deviceInfo.battery !== null">{{ deviceInfo.battery }}%</span>
              <span v-else class="text-muted">—</span>
              <el-button
                link
                type="primary"
                size="small"
                :disabled="!connected"
                @click="refreshBattery"
                style="margin-left: 4px"
              >刷新</el-button>
            </el-descriptions-item>
            <el-descriptions-item label="复原状态">
              <el-tag v-if="faceletsReceived" :type="isSolved ? 'success' : 'warning'" size="small">
                {{ isSolved ? '已复原' : '未复原' }}
              </el-tag>
              <span v-else class="text-muted">—</span>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-card>

      <!-- 计时器区 -->
      <el-card class="timer-card" shadow="never" v-if="connected">
        <template #header>
          <div class="card-header">
            <span>计时器</span>
            <div class="timer-mode-switch">
              <el-radio-group v-model="timerMode" size="small" @change="onTimerModeChange">
                <el-radio-button value="practice">标准</el-radio-button>
                <el-radio-button value="unlimited">不计时</el-radio-button>
              </el-radio-group>
              <el-tooltip placement="bottom" effect="light">
                <template #content>
                  <div class="mode-tooltip">
                    <p><strong>标准模式</strong>：15 秒观察倒计时，超时判 DNF</p>
                    <p><strong>不计时模式</strong>：观察时间不限，15 秒后从 0 开始正计时，直至首次转动</p>
                  </div>
                </template>
                <el-icon class="mode-hint-icon"><QuestionFilled /></el-icon>
              </el-tooltip>
            </div>
          </div>
        </template>

        <div class="timer-display-area">
          <div class="timer-main" :style="{ color: timerColor }">
            {{ timerDisplay }}
          </div>
          <div class="timer-sub" :style="{ color: timerColor }">
            {{ timerStateText }} · {{ timerSubText }}
          </div>
        </div>

        <!-- 打乱序列 -->
        <div class="scramble-section" v-if="scrambleSequence.length > 0">
          <div class="scramble-header">打乱序列（{{ scrambleCurrentStep }}/{{ scrambleTotalStep }}）</div>
          <div class="scramble-sequence">
            <span
              v-for="(move, i) in scrambleSequence"
              :key="i"
              class="scramble-chip"
              :class="{
                'scramble-done': i < scrambleCurrentStep,
                'scramble-current': i === scrambleCurrentStep,
                'scramble-pending': i > scrambleCurrentStep
              }"
            >{{ move }}</span>
          </div>
          <div class="scramble-next" v-if="scrambleNextMove && timerState === TimerStates.SCRAMBLING">
            下一步：<strong>{{ scrambleNextMove }}</strong>
          </div>
        </div>

        <!-- 复原结果 -->
        <div class="result-section" v-if="solveResult">
          <div class="result-header" :class="{ 'result-dnf': solveResult.dnf }">
            {{ solveResult.dnf ? 'DNF' : '✓ 复原成功' }}
          </div>
          <div class="result-body" v-if="!solveResult.dnf">
            <span>用时：<strong>{{ solveResult.solveTimeFormatted }}</strong></span>
            <span>步数：<strong>{{ solveResult.moveCount }}</strong></span>
            <span>观察：<strong>{{ solveResult.observationTimeFormatted }}</strong></span>
          </div>
          <div class="result-scramble" v-if="solveResult.scramble?.length">
            <div class="result-label">打乱</div>
            <div class="result-sequence">{{ solveResult.scramble.join(' ') }}</div>
          </div>
          <div class="result-solve" v-if="solveResult.solve?.length">
            <div class="result-label">复原</div>
            <div class="result-sequence">{{ solveResult.solve.join(' ') }}</div>
          </div>
        </div>

        <!-- 停止按钮 -->
        <div class="timer-stop" v-if="timerState !== TimerStates.IDLE">
          <el-button type="danger" size="small" @click="handleStopTimer">停止</el-button>
        </div>
      </el-card>

      <!-- 持握方向区 -->
      <el-card class="orientation-card" shadow="never" v-if="connected">
        <template #header>
          <div class="card-header">
            <span>持握方向</span>
            <div class="orientation-mode-switch">
              <el-tag :type="gyroMode ? 'success' : 'info'" size="small" effect="plain">
                {{ gyroMode ? '陀螺仪模式' : '经典模式' }}
              </el-tag>
              <el-switch
                v-if="gyroSupported !== null"
                v-model="forceGyroOff"
                :disabled="!gyroSupported"
                active-text="手动"
                inactive-text="自动"
                inline-prompt
                style="margin-left: 8px"
                @change="onModeSwitch"
              />
            </div>
          </div>
        </template>

        <!-- 陀螺仪模式：自动识别 + 初始映射锁定 -->
        <div v-if="gyroMode" class="orientation-gyro">
          <template v-if="initialMapSet">
            <div class="orientation-row">
              <span class="orientation-label">初始持握</span>
              <el-tag type="success" size="large">{{ initialOrientation }}</el-tag>
            </div>
            <!-- 当前持握暂不显示（转体检测在快速衔接时可能漏检，显示会不准）
            <div class="orientation-row">
              <span class="orientation-label">当前持握</span>
              <el-tag type="warning" size="large">{{ orientationLabel }}</el-tag>
            </div>
            -->
            <span class="orientation-detail">初始映射不变，转体不影响转动记号</span>
          </template>
          <el-tag v-else-if="detectedTopFace" type="warning" size="large">
            检测到{{ faceColorName(detectedTopFace) }}面朝顶，请选择朝前面
          </el-tag>
          <el-tag v-else type="info" size="large">识别中…</el-tag>
        </div>

        <!-- 经典模式：手动选择 -->
        <div v-else class="orientation-manual">
          <el-select v-model="manualPreset" placeholder="选择持握方向" style="width: 200px" @change="onManualPresetChange">
            <el-option
              v-for="preset in PRESET_ORIENTATIONS"
              :key="preset.key"
              :label="preset.label"
              :value="preset.key"
            />
          </el-select>
          <span class="orientation-detail">
            手动模式无法检测转体（x/y/z），如魔方支持陀螺仪请切换到自动模式
          </span>
        </div>
      </el-card>

      <!-- 转动序列区 -->
      <el-card class="moves-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>转动序列（{{ moves.length }} 步）</span>
            <el-button type="danger" link size="small" @click="clearMoves" :disabled="moves.length === 0">
              清空
            </el-button>
          </div>
        </template>

        <div class="moves-list" v-if="moves.length > 0">
          <span
            v-for="(move, i) in moves"
            :key="i"
            class="move-chip"
            :class="getMoveChipClass(move)"
          >{{ move }}</span>
        </div>
        <el-empty v-else description="转动魔方以显示动作序列" :image-size="60" />
      </el-card>

      <!-- 调试日志区 -->
      <el-card class="debug-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>调试日志</span>
            <el-button type="info" link size="small" @click="logs = []" :disabled="logs.length === 0">
              清空
            </el-button>
          </div>
        </template>

        <div class="debug-log" v-if="logs.length > 0">
          <div v-for="(log, i) in logs" :key="i" class="log-item">
            <span class="log-time">{{ log.time }}</span>
            <el-tag :type="logTagType(log.type)" size="small" effect="plain">{{ log.type }}</el-tag>
            <span class="log-detail">{{ log.detail }}</span>
          </div>
        </div>
        <el-empty v-else description="暂无日志" :image-size="60" />
      </el-card>
    </div>

    <!-- MAC 地址手动输入对话框 -->
    <el-dialog v-model="macDialogVisible" title="输入魔方 MAC 地址" width="420px" @close="onMacDialogClose">
      <p class="mac-hint">无法自动获取 MAC 地址，请手动输入。</p>
      <p class="mac-hint">格式：XX:XX:XX:XX:XX:XX（不区分大小写）</p>
      <el-input v-model="macInput" placeholder="例如：A4:CF:12:34:56:78" />
      <template #footer>
        <el-button @click="macDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitMac">确定</el-button>
      </template>
    </el-dialog>

    <!-- 朝前面选择对话框 -->
    <el-dialog v-model="frontFaceDialogVisible" title="选择朝前的面" width="420px" :close-on-click-modal="false">
      <p class="mac-hint">陀螺仪检测到 <strong>{{ faceColorName(detectedTopFace) }}</strong> 面朝顶。</p>
      <p class="mac-hint">请选择当前朝向你的面（单击选中，双击确认）：</p>
      <div class="front-face-blocks">
        <div
          v-for="face in frontFaceOptions"
          :key="face"
          class="face-block"
          :class="['face-block-' + face.toLowerCase(), { 'face-block-selected': frontFaceInput === face }]"
          @click="frontFaceInput = face"
          @dblclick="frontFaceInput = face; submitFrontFace()"
        >
          <span class="face-block-color">{{ faceColorName(face) }}</span>
          <span class="face-block-letter">{{ face }}</span>
        </div>
      </div>
      <template #footer>
        <el-button @click="frontFaceDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitFrontFace" :disabled="!frontFaceInput">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { getCubeClient, tryAutoReconnect, saveDeviceInfo, clearSavedDevice } from '@/utils/gan-ble'
import Cube3D from '@/components/cube/Cube3D.vue'
import {
  CubeOrientationTracker,
  StaticOrientation,
  PRESET_ORIENTATIONS,
  remapMove,
  FACES,
  FACE_NORMALS
} from '@/utils/cube-orientation'
import { ElMessage } from 'element-plus'
import { WarningFilled, QuestionFilled } from '@element-plus/icons-vue'
import { CubeTimer, TimerStates } from '@/utils/cube-timer'

const client = getCubeClient()
const tracker = new CubeOrientationTracker()
const staticOrientation = new StaticOrientation()
const cube3dRef = ref(null)

// ===== 计时器 =====
const timer = new CubeTimer({
  mode: 'practice',
  onStateChange: (state) => {
    timerState.value = state
  },
  onTimeUpdate: ({ state, display }) => {
    timerDisplay.value = display
  },
  onScrambleGenerated: (seq) => {
    scrambleSequence.value = seq
    scrambleCurrentStep.value = 0
  },
  onScrambleProgress: (current, total, next) => {
    scrambleCurrentStep.value = current
    scrambleTotalStep.value = total
    scrambleNextMove.value = next
  },
  onCorrection: (move) => {
    ElMessage.info(`已撤销 ${move}`)
  },
  onWarning: (msg) => {
    ElMessage.warning(msg)
  },
  onSolveComplete: (result) => {
    solveResult.value = result
  },
})
const timerState = ref(TimerStates.IDLE)
const timerDisplay = ref('0.00')
const scrambleSequence = ref([])
const scrambleCurrentStep = ref(0)
const scrambleTotalStep = ref(0)
const scrambleNextMove = ref(null)
const solveResult = ref(null)
const timerMode = ref('practice')

const timerStateText = computed(() => {
  const texts = {
    [TimerStates.IDLE]: '等待开始',
    [TimerStates.SCRAMBLING]: '打乱中',
    [TimerStates.OBSERVATION]: '观察中',
    [TimerStates.SOLVING]: '计时中',
    [TimerStates.SOLVED]: '已复原',
  }
  return texts[timerState.value] || ''
})

const timerColor = computed(() => {
  const colors = {
    [TimerStates.IDLE]: '#909399',
    [TimerStates.SCRAMBLING]: '#e6a23c',
    [TimerStates.OBSERVATION]: '#e6a23c',
    [TimerStates.SOLVING]: '#67c23a',
    [TimerStates.SOLVED]: '#409eff',
  }
  return colors[timerState.value] || '#909399'
})

const timerSubText = computed(() => {
  switch (timerState.value) {
    case TimerStates.IDLE:
      return '请回到初始持握开始打乱'
    case TimerStates.SCRAMBLING:
      return `${scrambleCurrentStep.value}/${scrambleTotalStep.value} 步`
    case TimerStates.OBSERVATION:
      return timerMode.value === 'practice' ? '15s 倒计时' : '不限时观察'
    case TimerStates.SOLVING:
      return '复原中…'
    case TimerStates.SOLVED:
      return solveResult.value?.dnf ? '观察超时' : `${solveResult.value?.moveCount || 0} 步`
    default:
      return ''
  }
})

function onTimerModeChange(val) {
  timerMode.value = val
  timer.setMode(val)
}

function handleStopTimer() {
  timer.stop()
  solveResult.value = null
  scrambleSequence.value = []
  scrambleCurrentStep.value = 0
}

// 固定事件回调引用，不在每次连接时重新注册
const handleEvent = (event) => {
  switch (event.type) {
    case 'MOVE': {
      const raw = event.move
      const map = currentMap()
      const remapped = map ? remapMove(raw, map) : raw
      moves.value.push(remapped)
      addLog('MOVE', `${raw} → ${remapped}（serial: ${event.serial}）`)
      // 驱动 3D 魔方转动
      if (cube3dRef.value && initialMapSet.value) {
        cube3dRef.value.rotate(remapped)
      }
      // 驱动计时器
      if (initialMapSet.value && connected.value) {
        timer.onMove(remapped, isSolved.value)
      }
      break
    }
    case 'GYRO':
      if (gyroSupported.value === null) {
        gyroSupported.value = true
        if (!forceGyroOff.value) enterGyroMode()
      }
      if (gyroMode.value) {
        tracker.handleGyro(event)
      }
      // 陀螺仪跟随：通过 rAF 合并同帧多次 GYRO 为一次姿态更新
      if (initialMapSet.value && tracker.currentQuaternion) {
        pendingGyroQuat = { ...tracker.currentQuaternion }
        if (!gyroRafId) {
          gyroRafId = requestAnimationFrame(() => {
            gyroRafId = null
            if (pendingGyroQuat) {
              updateCubeAttitude(pendingGyroQuat)
              pendingGyroQuat = null
            }
          })
        }
      }
      break
    case 'FACELETS':
      isSolved.value = event.isSolved
      faceletsReceived.value = true
      addLog('FACELETS', `serial: ${event.serial}，复原: ${event.isSolved}`)
      // FACELETS 事件中检查复原状态，触发计时停止
      if (initialMapSet.value && connected.value) {
        timer.onFacelets(event.isSolved)
      }
      break
    case 'BATTERY':
      deviceInfo.battery = event.batteryLevel
      addLog('BATTERY', `${event.batteryLevel}%（dataLen=${event.dataLength}, raw=[${event.raw?.join(',')}]）`)
      break
    case 'HARDWARE':
      if (event.hardwareName) deviceInfo.name = event.hardwareName
      addLog('HARDWARE', `name: ${event.hardwareName || '-'}，sw: ${event.softwareVersion || '-'}，hw: ${event.hardwareVersion || '-'}`)
      break
    case 'DISCONNECT':
      connected.value = false
      isSolved.value = false
      timer.stop()
      timerState.value = TimerStates.IDLE
      timerDisplay.value = '0.00'
      solveResult.value = null
      scrambleSequence.value = []
      scrambleCurrentStep.value = 0
      faceletsReceived.value = false
      gyroMode.value = false
      gyroSupported.value = null
      initialMapSet.value = false
      detectedTopFace.value = null
      orientationLabel.value = '识别中…'
      orientationDetail.value = ''
      initialOrientation.value = ''
      gyroBaseQuat.value = null
      if (gyroRafId) { cancelAnimationFrame(gyroRafId); gyroRafId = null }
      pendingGyroQuat = null
      deviceInfo.battery = null
      if (cube3dRef.value) {
        cube3dRef.value.resetAttitude()
      }
      addLog('DISCONNECT', '设备已断开')
      break
  }
}
client.onEvent(handleEvent)

const connecting = ref(false)
const connected = ref(false)
const isSolved = ref(false)
const faceletsReceived = ref(false)
const moves = ref([])
const logs = ref([])
const macDialogVisible = ref(false)
const macInput = ref('')
const deviceInfo = reactive({ name: '', mac: '', battery: null })

// 模式管理
const gyroSupported = ref(null)
const forceGyroOff = ref(false)
const gyroMode = ref(false)
const manualPreset = ref('white-top-green-front')
const orientationLabel = ref('识别中…')
const initialOrientation = ref('')
const gyroBaseQuat = ref(null) // 陀螺仪基准四元数（初始映射确认时记录）
let gyroRafId = null           // GYRO 事件 rAF 节流
let pendingGyroQuat = null     // 待应用的陀螺仪四元数
const orientationDetail = ref('')
const initialMapSet = ref(false)
const detectedTopFace = ref(null)

// 朝前面选择
const frontFaceDialogVisible = ref(false)
const frontFaceInput = ref('')
const frontFaceOptions = ref([])

let macResolve = null
let gyroTimer = null
let batteryTimer = null  // 电量定时查询

const FACE_COLOR_NAMES = { U: '白', D: '黄', R: '红', L: '橙', F: '绿', B: '蓝' }

function faceColorName(face) {
  return FACE_COLOR_NAMES[face] || face
}

const statusText = computed(() => {
  if (connecting.value) return '连接中…'
  if (connected.value) return '已连接'
  return '未连接'
})

const statusTagType = computed(() => {
  if (connecting.value) return 'warning'
  if (connected.value) return 'success'
  return 'info'
})

function logTagType(type) {
  const types = { MOVE: 'primary', GYRO: 'info', FACELETS: 'success', BATTERY: 'warning', DISCONNECT: 'danger', HARDWARE: 'info', CONNECT: 'info', ROTATION: 'warning', ERROR: 'danger' }
  return types[type] ?? 'info'
}

function addLog(type, detail) {
  const time = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  logs.value.unshift({ time, type, detail })
  if (logs.value.length > 100) logs.value.pop()
}

function getMoveChipClass(move) {
  const c = move[0].toLowerCase()
  if (['x', 'y', 'z'].includes(c)) return 'move-rotation'
  return 'face-' + c
}

function currentMap() {
  if (gyroMode.value) return tracker.currentMap
  return staticOrientation.currentMap
}

function clearMoves() {
  moves.value = []
  if (cube3dRef.value) {
    cube3dRef.value.clearQueue()
  }
}

// ===== 3D 魔方姿态更新（陀螺仪跟随）=====
// 四元数工具：共轭
function quatConj(q) {
  return { w: q.w, x: -q.x, y: -q.y, z: -q.z }
}
// 四元数乘法：a * b
function quatMul(a, b) {
  return {
    w: a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z,
    x: a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
    y: a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
    z: a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w
  }
}

/**
 * 更新 3D 魔方整体姿态
 * 计算 relQuat = currentQuat × baseQuat⁻¹（相对初始姿态的旋转）
 * 然后应用到 outerGroup
 */
function updateCubeAttitude(currentQuat) {
  if (!cube3dRef.value || !gyroBaseQuat.value) return
  const base = gyroBaseQuat.value
  // rel = current * base^-1
  const baseInv = quatConj(base)
  const rel = quatMul(currentQuat, baseInv)
  // 归一化
  const len = Math.sqrt(rel.w*rel.w + rel.x*rel.x + rel.y*rel.y + rel.z*rel.z)
  if (len > 0) {
    rel.w /= len; rel.x /= len; rel.y /= len; rel.z /= len
  }
  cube3dRef.value.setAttitude(rel)
}

function enterGyroMode() {
  gyroMode.value = true
  tracker.reset()
  initialMapSet.value = false
  detectedTopFace.value = null
  orientationLabel.value = '识别中…'
  orientationDetail.value = ''

  // 转体检测 → 插入 x/y/z（暂不记录到序列，判定逻辑保留供朝向显示使用）
  tracker.onRotation(({ rotation, angle }) => {
    // moves.value.push(rotation)
    addLog('ROTATION', `${rotation}（${angle.toFixed(0)}°）`)
  })

  // 顶面检测 → 弹出朝前面选择器
  tracker.onTopFaceDetected((topFace) => {
    detectedTopFace.value = topFace
    // 计算排除顶面和底面的 4 个候选面
    const topOpposite = FACES.find(f =>
      Math.abs(
        FACE_NORMALS[f].reduce((sum, v, i) => sum + v * FACE_NORMALS[topFace][i], 0)
      ) + 1 < 0.01
    )
    frontFaceOptions.value = FACES.filter(f => f !== topFace && f !== topOpposite)
    frontFaceInput.value = ''
    frontFaceDialogVisible.value = true
    addLog('GYRO', `检测到顶面: ${faceColorName(topFace)}（${topFace}）`)
  })

  // 朝向变化（暂不使用，当前持握不显示）
  // tracker.onOrientationChange(({ topFace, frontFace }) => {
  //   if (initialMapSet.value) {
  //     orientationLabel.value = `${faceColorName(topFace)}顶${faceColorName(frontFace)}前`
  //   }
  // })
}

function enterStaticMode() {
  gyroMode.value = false
  staticOrientation.setPreset(manualPreset.value)
  initialMapSet.value = true
  const preset = PRESET_ORIENTATIONS.find(p => p.key === manualPreset.value)
  orientationLabel.value = preset?.label || '手动'
  orientationDetail.value = ''
}

function onModeSwitch(val) {
  if (val) {
    gyroMode.value = false
    enterStaticMode()
    addLog('GYRO', '切换到经典模式（手动持握方向）')
  } else if (gyroSupported.value) {
    enterGyroMode()
    addLog('GYRO', '切换到陀螺仪模式（自动持握方向）')
  }
}

function onManualPresetChange(key) {
  staticOrientation.setPreset(key)
  const preset = PRESET_ORIENTATIONS.find(p => p.key === key)
  if (preset) {
    orientationLabel.value = preset.label
    initialOrientation.value = preset.label
    addLog('GYRO', `手动持握方向: ${preset.label}`)
    // 经典模式：设置静态姿态和颜色
    if (cube3dRef.value) {
      cube3dRef.value.setInitialPose(preset.top, preset.front)
      cube3dRef.value.setColorScheme(preset.top, preset.front)
    }
  }
}

function submitFrontFace() {
  if (!frontFaceInput.value) {
    ElMessage.warning('请选择朝前的面')
    return
  }
  frontFaceDialogVisible.value = false
  const top = detectedTopFace.value
  const front = frontFaceInput.value
  tracker.setInitialMap(top, front)
  initialMapSet.value = true
  const label = `${faceColorName(top)}顶${faceColorName(front)}前`
  initialOrientation.value = label
  orientationLabel.value = label
  orientationDetail.value = `初始映射已锁定`
  addLog('GYRO', `初始映射锁定: ${label}`)

  // 校准陀螺仪：记录当前四元数为基准，后续相对旋转控制 3D 姿态
  const q = tracker.currentQuaternion
  if (q && cube3dRef.value) {
    gyroBaseQuat.value = { ...q }
    updateCubeAttitude(q)
  }

  // 根据持握方向更新 3D 魔方颜色
  if (cube3dRef.value) {
    cube3dRef.value.setColorScheme(top, front)
  }
}

async function handleConnect() {
  // 单例已连接，直接恢复 UI 状态
  if (client.connected) {
    connected.value = true
    deviceInfo.name = client.deviceName
    deviceInfo.mac = client.deviceMAC
    addLog('CONNECT', `已连接：${deviceInfo.name}（${deviceInfo.mac}）`)
    return
  }

  if (!client.constructor.isSupported) {
    ElMessage.error('当前浏览器不支持 Web Bluetooth API，请使用 Chrome 或 Edge 浏览器')
    return
  }

  connecting.value = true
  gyroSupported.value = null
  forceGyroOff.value = false
  gyroMode.value = false
  initialMapSet.value = false

  try {
    await client.connect({
      onMacAddressRequired: async () => {
        return new Promise(resolve => {
          macResolve = resolve
          macInput.value = ''
          macDialogVisible.value = true
        })
      }
    })
    connected.value = true
    deviceInfo.name = client.deviceName
    deviceInfo.mac = client.deviceMAC
    saveDeviceInfo(deviceInfo.name, deviceInfo.mac)
    ElMessage.success('魔方连接成功')
    addLog('CONNECT', `${deviceInfo.name}（${deviceInfo.mac}）`)

    // 3 秒内无 GYRO 事件 → 经典模式
    gyroTimer = setTimeout(() => {
      if (gyroSupported.value === null) {
        gyroSupported.value = false
        enterStaticMode()
        addLog('GYRO', '未检测到陀螺仪数据，切换到经典模式')
      }
    }, 3000)

    // 定时查询电量（每 30 秒），连接后立即查一次
    if (batteryTimer) clearInterval(batteryTimer)
    batteryTimer = setInterval(() => {
      if (client.connected) client.requestBattery().catch(() => {})
    }, 30000)
  } catch (err) {
    if (err.name === 'NotFoundError') {
      ElMessage.info('已取消设备选择')
    } else {
      ElMessage.error(err.message)
      addLog('ERROR', err.message)
    }
  } finally {
    connecting.value = false
  }
}

function refreshBattery() {
  if (!client.connected) return
  addLog('BATTERY', '手动请求电量…')
  client.requestBattery().catch(err => addLog('ERROR', '电量请求失败: ' + err.message))
}

async function handleReset() {
  try {
    await client.resetCube()
    moves.value = []
    isSolved.value = true
    faceletsReceived.value = true
    timer.stop()
    timerState.value = TimerStates.IDLE
    timerDisplay.value = '0.00'
    solveResult.value = null
    scrambleSequence.value = []
    scrambleCurrentStep.value = 0
    tracker.reset()
    initialMapSet.value = false
    detectedTopFace.value = null
    orientationLabel.value = '识别中…'
    orientationDetail.value = ''
    initialOrientation.value = ''
    gyroBaseQuat.value = null
    if (gyroRafId) { cancelAnimationFrame(gyroRafId); gyroRafId = null }
    pendingGyroQuat = null
    // 3D 魔方复位 + 姿态复位
    if (cube3dRef.value) {
      cube3dRef.value.reset()
      cube3dRef.value.resetAttitude()
    }
    addLog('CONNECT', '魔方已复位，重新识别朝向…')
    // 等待 GYRO 数据稳定后重新检测顶面
    if (gyroMode.value) {
      tracker.reset()
    }
  } catch (err) {
    ElMessage.error('复位失败: ' + err.message)
    addLog('ERROR', '复位失败: ' + err.message)
  }
}

async function handleDisconnect() {
  if (gyroTimer) { clearTimeout(gyroTimer); gyroTimer = null }
  await client.disconnect()
  clearSavedDevice()
  connected.value = false
  deviceInfo.name = ''
  deviceInfo.mac = ''
  deviceInfo.battery = null
  isSolved.value = false
  gyroMode.value = false
  gyroSupported.value = null
  initialMapSet.value = false
  detectedTopFace.value = null
  orientationLabel.value = '识别中…'
  orientationDetail.value = ''
  initialOrientation.value = ''
  tracker.reset()
  if (batteryTimer) { clearInterval(batteryTimer); batteryTimer = null }
}

function submitMac() {
  const mac = macInput.value.trim().toUpperCase()
  if (!/^([0-9A-F]{2}:){5}[0-9A-F]{2}$/.test(mac)) {
    ElMessage.warning('MAC 地址格式不正确，应为 XX:XX:XX:XX:XX:XX')
    return
  }
  macDialogVisible.value = false
  if (macResolve) {
    macResolve(mac)
    macResolve = null
  }
}

function onMacDialogClose() {
  if (macResolve) {
    macResolve(null)
    macResolve = null
  }
}

function beforeUnloadHandler() {
  if (connected.value) {
    client.disconnectSync()
  }
}

onMounted(async () => {
  window.addEventListener('beforeunload', beforeUnloadHandler)
  // 尝试自动重连（刷新页面后静默恢复连接）
  const ok = await tryAutoReconnect()
  if (ok) {
    connected.value = true
    deviceInfo.name = client.deviceName
    deviceInfo.mac = client.deviceMAC
    addLog('CONNECT', `自动重连成功：${deviceInfo.name}`)
    // 启动陀螺仪检测计时
    gyroTimer = setTimeout(() => {
      if (gyroSupported.value === null) {
        gyroSupported.value = false
        enterStaticMode()
        addLog('GYRO', '未检测到陀螺仪数据，切换到经典模式')
      }
    }, 3000)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', beforeUnloadHandler)
  if (gyroTimer) clearTimeout(gyroTimer)
  if (gyroRafId) cancelAnimationFrame(gyroRafId)
  if (batteryTimer) { clearInterval(batteryTimer); batteryTimer = null }
  // 单例模式：组件销毁不主动断开 BLE 连接，保持连接到其他页面
})
</script>

<style scoped>
.smart-cube-container {
  display: flex;
  gap: 24px;
  align-items: flex-start;
  max-width: 1200px;
  margin: 0 auto;
}

.cube-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: sticky;
  top: 20px;
}

.cube-wrapper {
  width: 100%;
  aspect-ratio: 1 / 1;
  max-height: 500px;
  background: #f5f5f5;
  border-radius: 12px;
  overflow: hidden;
}

.cube-status-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 4px;
}

.solved-badge {
  color: #67c23a;
  font-size: 14px;
  font-weight: 500;
}

.control-panel {
  width: 420px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.connection-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.timer-card .timer-display-area {
  text-align: center;
  padding: 12px 0;
}

.timer-main {
  font-size: 48px;
  font-weight: 800;
  font-family: 'Courier New', monospace;
  line-height: 1.2;
  letter-spacing: 2px;
}

.timer-sub {
  font-size: 14px;
  margin-top: 4px;
}

.timer-mode-switch {
  display: flex;
  align-items: center;
}

.mode-hint-icon {
  font-size: 16px;
  color: var(--el-text-color-secondary);
  cursor: help;
  margin-left: 4px;
}

.mode-tooltip {
  max-width: 280px;
}

.mode-tooltip p {
  margin: 4px 0;
  font-size: 13px;
  line-height: 1.6;
}

.scramble-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.scramble-header {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}

.scramble-sequence {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.scramble-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  height: 28px;
  padding: 0 6px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 700;
  font-family: 'Courier New', monospace;
  color: #fff;
}

.scramble-done {
  background: #67c23a;
  opacity: 0.5;
}

.scramble-current {
  background: #e6a23c;
  box-shadow: 0 0 0 2px rgba(230, 162, 60, 0.3);
}

.scramble-pending {
  background: #909399;
}

.scramble-next {
  margin-top: 8px;
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.result-section {
  margin-top: 12px;
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}

.result-header {
  font-size: 18px;
  font-weight: 700;
  color: #409eff;
}

.result-header.result-dnf {
  color: #f56c6c;
}

.result-body {
  margin-top: 8px;
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.result-scramble,
.result-solve {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.result-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.result-sequence {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.6;
  word-break: break-all;
}

.timer-stop {
  margin-top: 12px;
  text-align: center;
}

.device-info {
  margin-top: 16px;
}

.text-muted {
  color: var(--el-text-color-secondary);
}

.orientation-card :deep(.el-card__body) {
  padding: 16px 20px;
}

.orientation-mode-switch {
  display: flex;
  align-items: center;
}

.orientation-gyro {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.orientation-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.orientation-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  min-width: 60px;
}

.orientation-manual {
  display: flex;
  align-items: center;
  gap: 12px;
}

.orientation-detail {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.front-face-radio {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 12px;
}

.moves-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
  padding: 4px;
}

.move-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  height: 36px;
  padding: 0 10px;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 700;
  font-family: 'Courier New', monospace;
  color: #fff;
  background: #909399;
}

.face-u { background: #e6a700; }
.face-r { background: #f56c6c; }
.face-f { background: #67c23a; }
.face-d { background: #e6e6e6; color: #303030; }
.face-l { background: #e8923c; }
.face-b { background: #409eff; }
.move-rotation { background: #722ed1; }

.debug-log {
  max-height: 300px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.log-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.log-time {
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.log-detail {
  color: var(--el-text-color-primary);
}

.mac-hint {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  margin-bottom: 8px;
}

.mac-hint-icon {
  font-size: 18px;
  color: var(--el-color-warning);
  cursor: help;
  margin-left: 4px;
}

.mac-tooltip {
  max-width: 360px;
}

.mac-tooltip p {
  margin: 4px 0;
  font-size: 13px;
  line-height: 1.6;
}

.mac-tooltip code {
  background: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.front-face-blocks {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-top: 20px;
}

.face-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  border-radius: 12px;
  cursor: pointer;
  border: 4px solid transparent;
  transition: border-color 0.2s, transform 0.15s;
  user-select: none;
}

.face-block:hover {
  transform: scale(1.05);
}

.face-block-selected {
  border-color: #303030;
  transform: scale(1.05);
}

.face-block-color {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
}

.face-block-letter {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 2px;
}

.face-block-u { background: #e6a700; }
.face-block-r { background: #f56c6c; }
.face-block-f { background: #67c23a; }
.face-block-d { background: #e6e6e6; }
.face-block-d .face-block-color,
.face-block-d .face-block-letter { color: #303030; }
.face-block-l { background: #e8923c; }
.face-block-b { background: #409eff; }
</style>
