<template>
  <div class="timer-container" ref="timerPage" tabindex="0" @keydown="handleKeyDown" @keyup="handleKeyUp">
    <!-- 顶部工具栏 -->
    <div class="top-bar">
      <div class="top-bar-center">
        <el-radio-group v-model="timingMode" size="small" @change="onTimingModeChange">
          <el-radio-button value="manual">手动</el-radio-button>
          <el-radio-button value="smart">智能</el-radio-button>
        </el-radio-group>
        <el-select v-model="cubeType" size="small" style="width: 100px" @change="generateScramble">
          <el-option label="三阶" value="3x3" />
          <el-option label="二阶" value="2x2" />
          <el-option label="四阶" value="4x4" />
        </el-select>
        <el-select v-model="method" size="small" style="width: 100px">
          <el-option label="层先法" value="layer" />
          <el-option label="CFOP" value="cfop" />
          <el-option label="桥式" value="roux" />
          <el-option label="ZBLL" value="zbll" />
        </el-select>
        <el-button size="small" type="primary" link @click="generateScramble">刷新打乱</el-button>
        <!-- 紧凑连接区 -->
        <div class="connect-mini" v-if="timingMode === 'smart'">
          <template v-if="!connected">
            <el-button size="small" type="primary" @click="handleConnect" :loading="connecting">连接</el-button>
            <el-tooltip placement="bottom" effect="light">
              <template #content>
                <div class="mac-tooltip">
                  <p>无法自动获取 MAC 地址时：</p>
                  <p>1. 地址栏输入 <code>edge://bluetooth-internals/#devices</code></p>
                  <p>2. 找到 GAN 魔方，复制 MAC 地址</p>
                  <p>3. 点击「连接」，在弹窗中粘贴</p>
                </div>
              </template>
              <el-icon class="mac-hint-icon"><WarningFilled /></el-icon>
            </el-tooltip>
          </template>
          <template v-else>
            <el-tag type="success" size="small" effect="plain">{{ deviceInfo.name || '已连接' }}</el-tag>
            <el-tag v-if="deviceInfo.battery !== null" size="small" type="info" effect="plain">{{ deviceInfo.battery }}%</el-tag>
            <el-dropdown @command="onDeviceCmd" trigger="click">
              <el-icon class="device-menu-icon"><ArrowDown /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="reset">复位</el-dropdown-item>
                  <el-dropdown-item command="disconnect" divided>断开</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </div>
      </div>
    </div>

    <!-- 主体：左右布局 -->
    <el-row :gutter="16" class="main-layout">
      <!-- 左列：统计 + 历史 -->
      <el-col :xs="24" :sm="8" class="left-col">
        <el-card shadow="never" class="stats-card">
          <template #header>
            <div class="card-header">
              <span>数据统计</span>
              <el-button v-if="timingMode === 'manual'" type="danger" link size="small" @click="clearHistory">清空</el-button>
            </div>
          </template>
          <div class="summary-stats">
            <p>次数: <strong>{{ allHistory.length }}</strong></p>
            <p>最佳: <span class="best-time">{{ bestTimeDisplay }}</span></p>
            <p>Ao5: <strong>{{ ao5Display }}</strong></p>
            <p>Ao12: <strong>{{ ao12Display }}</strong></p>
          </div>
        </el-card>

        <el-card shadow="never" class="history-card">
          <template #header><span>历史记录</span></template>
          <div class="history-list">
            <div v-for="(item, index) in allHistory" :key="item.id" class="history-item" :class="{ 'is-dnf': item.isDnf }">
              <span class="hi-index">#{{ allHistory.length - index }}</span>
              <span class="hi-time">{{ formatTime(item.time) }}</span>
              <template v-if="timingMode === 'smart'">
                <span v-if="item.isDnf" class="hi-dnf">DNF</span>
                <template v-else>
                  <span class="hi-moves" v-if="item.moveCount">{{ item.moveCount }}步</span>
                  <span class="hi-tps" v-if="item.tps">TPS {{ item.tps }}</span>
                </template>
              </template>
              <el-button type="danger" icon="Delete" circle size="small" link @click="deleteRecord(index)" />
            </div>
            <div v-if="allHistory.length === 0" class="empty-tip">暂无成绩</div>
          </div>
        </el-card>
      </el-col>

      <!-- 右列：打乱chip + 计时器/3D + 操作提示 + 平面图 -->
      <el-col :xs="24" :sm="16" class="right-col">
        <el-card shadow="never" class="main-card">
          <!-- 打乱序列 chip（两种模式共用） -->
          <div class="scramble-chips" v-if="scrambleChips.length > 0">
            <span
              v-for="(move, i) in scrambleChips"
              :key="i"
              class="scramble-chip"
              :class="scrambleChipClass(i)"
            >{{ move }}</span>
          </div>
          <div class="scramble-empty" v-else>
            <span v-if="timingMode === 'manual'">点击「刷新打乱」生成</span>
            <span v-else>连接魔方后，来回拨动任意面开始打乱</span>
          </div>

          <!-- 中间区域：计时器/3D（居中） -->
          <div class="center-area">
            <div class="center-left">
              <!-- 手动模式：大计时器 -->
              <template v-if="timingMode === 'manual'">
                <div class="status-hint" :class="{ 'ready': manualTimerState === 'ready', 'running': manualTimerState === 'running' }">
                  {{ manualStatusText }}
                </div>
                <div class="time-banner" :class="manualTimerState"
                     @mousedown="handleManualTouchStart" @mouseup="handleManualTouchEnd"
                     @mouseleave="handleManualTouchEnd" @touchstart.prevent="handleManualTouchStart" @touchend.prevent="handleManualTouchEnd">
                  {{ manualTimeDisplay }}
                </div>
                <div class="manual-hint">长按空格键开始 / 轻按停止</div>
              </template>
              <!-- 智能模式：3D + 计时器 -->
              <template v-else>
                <div class="smart-center">
                  <div class="cube-mini" v-if="connected">
                    <Cube3D ref="cube3dRef" :animation-speed="120" />
                  </div>
                  <div class="smart-timer-block" v-if="connected">
                    <div class="timer-main" :style="{ color: smartTimerColor }">{{ smartTimerDisplay }}</div>
                    <div class="timer-sub" :style="{ color: smartTimerColor }">{{ smartTimerStateText }} · {{ smartTimerSubText }}</div>
                    <div class="smart-controls" v-if="cubeTimerState !== TimerStates.IDLE || true">
                      <el-radio-group v-model="cubeTimerMode" size="small" @change="onCubeTimerModeChange">
                        <el-radio-button value="practice">标准</el-radio-button>
                        <el-radio-button value="unlimited">不限</el-radio-button>
                      </el-radio-group>
                      <el-button v-if="cubeTimerState !== TimerStates.IDLE" type="danger" size="small" @click="handleStopTimer">停止</el-button>
                    </div>
                  </div>
                  <div class="smart-placeholder" v-if="!connected">
                    <span class="placeholder-text">请先连接智能魔方</span>
                  </div>
                </div>
              </template>
            </div>
          </div>

          <!-- 平面图：右下角绝对定位 -->
          <div class="net-block">
            <CubeNet :scramble="scrambleChips" :cell-size="10" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- MAC 地址输入对话框 -->
    <el-dialog v-model="macDialogVisible" title="输入 MAC 地址" width="400px" @close="onMacDialogClose">
      <p class="mac-hint">格式：XX:XX:XX:XX:XX:XX（不区分大小写）</p>
      <el-input v-model="macInput" placeholder="例如：A4:CF:12:34:56:78" />
      <template #footer>
        <el-button @click="macDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitMac">确定</el-button>
      </template>
    </el-dialog>

    <!-- 朝前面选择对话框 -->
    <el-dialog v-model="frontFaceDialogVisible" title="选择朝前的面" width="400px" :close-on-click-modal="false">
      <p class="mac-hint">检测到 <strong>{{ faceColorName(detectedTopFace) }}</strong> 面朝顶。请选择朝向你的面：</p>
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
/**
 * TimerView.vue - 统一计时器页面（手动 + 智能）
 */
import { ref, computed, reactive, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { WarningFilled, ArrowDown } from '@element-plus/icons-vue'
import { createTimerRecord, getSmartCubeDevices, registerSmartCubeDevice } from '@/api/timer'
import CubeNet from '@/components/cube/CubeNet.vue'
import Cube3D from '@/components/cube/Cube3D.vue'
import { getCubeClient, tryAutoReconnect, saveDeviceInfo, clearSavedDevice } from '@/utils/gan-ble'
import {
  CubeOrientationTracker,
  StaticOrientation,
  PRESET_ORIENTATIONS,
  remapMove,
  FACES,
  FACE_NORMALS
} from '@/utils/cube-orientation'
import { CubeTimer, TimerStates } from '@/utils/cube-timer'

// ===== 通用 =====
const route = useRoute()
const timerPage = ref(null)
const timingMode = ref('manual')
const cubeType = ref('3x3')
const method = ref('layer')
const currentScramble = ref('')

if (route.query.mode === 'smart') timingMode.value = 'smart'
watch(() => route.query.mode, (val) => {
  if (val === 'smart' || val === 'manual') timingMode.value = val
})

// ===== 统一历史记录 =====
const allHistory = ref([])
// 从 localStorage 加载手动记录
function loadManualHistory() {
  const raw = JSON.parse(localStorage.getItem('icube_timer_history') || '[]')
  return raw.map(r => ({ ...r, timingMode: 'manual', isDnf: false }))
}
allHistory.value = loadManualHistory()

function formatTime(ms) {
  if (!ms || ms === 0) return '0.00'
  const s = ms / 1000
  if (s < 60) return s.toFixed(2)
  const m = Math.floor(s / 60)
  return `${m}:${(s % 60).toFixed(2).padStart(5, '0')}`
}

function calcTPS(moves, ms) {
  if (!moves || !ms || ms === 0) return null
  return (moves / (ms / 1000)).toFixed(2)
}

const bestTimeDisplay = computed(() => {
  const valid = allHistory.value.filter(r => !r.isDnf)
  if (valid.length === 0) return '-'
  return formatTime(Math.min(...valid.map(r => r.time)))
})

function calcAoN(n) {
  const valid = allHistory.value.filter(r => !r.isDnf)
  if (valid.length < n) return '-'
  const recent = valid.slice(0, n).map(r => r.time)
  recent.sort((a, b) => a - b)
  const mid = recent.slice(1, n - 1)
  return formatTime(mid.reduce((a, b) => a + b, 0) / (n - 2))
}
const ao5Display = computed(() => calcAoN(5))
const ao12Display = computed(() => calcAoN(12))

function deleteRecord(index) {
  allHistory.value.splice(index, 1)
  if (timingMode.value === 'manual') {
    localStorage.setItem('icube_timer_history', JSON.stringify(
      allHistory.value.map(({ timingMode, isDnf, ...rest }) => rest)
    ))
  }
}

// ===== 打乱 chip 展示 =====
const scrambleChips = computed(() => {
  if (timingMode.value === 'manual') {
    return currentScramble.value ? currentScramble.value.split(' ').filter(Boolean) : []
  }
  return scrambleSequence.value
})

function scrambleChipClass(i) {
  if (timingMode.value !== 'smart') return ''
  if (i < scrambleCurrentStep.value) return 'chip-done'
  if (i === scrambleCurrentStep.value && cubeTimerState.value === TimerStates.SCRAMBLING) return 'chip-current'
  return 'chip-pending'
}

// ===== 顶部工具栏 =====
function onTimingModeChange(val) {
  if (val === 'manual') {
    if (cubeTimer) cubeTimer.stop()
    allHistory.value = loadManualHistory()
    if (timerPage.value) timerPage.value.focus()
  } else {
    stopManualTimer()
    manualTimerState.value = 'idle'
    elapsedTime.value = 0
    allHistory.value = [] // 智能模式从后端/新记录开始
    loadSavedDevices()
  }
}

// ============================================================
// 手动计时
// ============================================================
const manualTimerState = ref('idle')
const startTime = ref(0)
const elapsedTime = ref(0)
const timerInterval = ref(null)
const holdTimer = ref(null)

const generateScramble = () => {
  const moves = {
    '2x2': ['U', "U'", 'U2', 'R', "R'", 'R2', 'F', "F'", 'F2'],
    '3x3': ['U', "U'", 'U2', 'D', "D'", 'D2', 'R', "R'", 'R2', 'L', "L'", 'L2', 'F', "F'", 'F2', 'B', "B'", 'B2'],
    '4x4': ['U', "U'", 'U2', 'D', "D'", 'D2', 'R', "R'", 'R2', 'L', "L'", 'L2', 'F', "F'", 'F2', 'B', "B'", 'B2', 'Uw', 'Rw', 'Fw']
  }
  const currentMoves = moves[cubeType.value]
  const length = cubeType.value === '2x2' ? 11 : cubeType.value === '4x4' ? 40 : 21
  let scramble = []
  let lastAxis = ''
  for (let i = 0; i < length; i++) {
    let move = currentMoves[Math.floor(Math.random() * currentMoves.length)]
    while (move[0] === lastAxis) {
      move = currentMoves[Math.floor(Math.random() * currentMoves.length)]
    }
    scramble.push(move)
    lastAxis = move[0]
  }
  currentScramble.value = scramble.join(' ')
}

const manualTimeDisplay = computed(() => formatTime(elapsedTime.value))
const manualStatusText = computed(() => {
  if (manualTimerState.value === 'holding') return '请按住…'
  if (manualTimerState.value === 'ready') return '松开开始！'
  if (manualTimerState.value === 'running') return '计时中…'
  return '准备就绪'
})

const handleKeyDown = (e) => {
  if (timingMode.value !== 'manual') return
  if (e.code !== 'Space') return
  e.preventDefault()
  if (manualTimerState.value === 'running') {
    stopManualTimer()
  } else if (manualTimerState.value === 'idle') {
    manualTimerState.value = 'holding'
    elapsedTime.value = 0
    clearTimeout(holdTimer.value)
    holdTimer.value = setTimeout(() => { manualTimerState.value = 'ready' }, 500)
  }
}

const handleKeyUp = (e) => {
  if (timingMode.value !== 'manual') return
  if (e.code !== 'Space') return
  e.preventDefault()
  if (manualTimerState.value === 'ready') {
    startManualTimer()
  } else if (manualTimerState.value === 'holding') {
    clearTimeout(holdTimer.value)
    manualTimerState.value = 'idle'
  }
}

const handleManualTouchStart = () => {
  if (timingMode.value !== 'manual') return
  if (manualTimerState.value === 'running') { stopManualTimer(); return }
  if (manualTimerState.value === 'idle') {
    manualTimerState.value = 'holding'
    elapsedTime.value = 0
    clearTimeout(holdTimer.value)
    holdTimer.value = setTimeout(() => { manualTimerState.value = 'ready' }, 500)
  }
}
const handleManualTouchEnd = () => {
  if (timingMode.value !== 'manual') return
  if (manualTimerState.value === 'ready') startManualTimer()
  else if (manualTimerState.value === 'holding') {
    clearTimeout(holdTimer.value)
    manualTimerState.value = 'idle'
  }
}

function startManualTimer() {
  manualTimerState.value = 'running'
  startTime.value = performance.now()
  timerInterval.value = setInterval(() => {
    elapsedTime.value = performance.now() - startTime.value
  }, 10)
}

function stopManualTimer() {
  if (timerInterval.value) clearInterval(timerInterval.value)
  if (elapsedTime.value === 0) { manualTimerState.value = 'idle'; return }
  const wasRunning = manualTimerState.value === 'running'
  manualTimerState.value = 'idle'
  if (!wasRunning) return

  const record = {
    id: Date.now(),
    time: elapsedTime.value,
    scramble: currentScramble.value,
    date: new Date().toLocaleDateString(),
    timingMode: 'manual',
    isDnf: false
  }
  allHistory.value.unshift(record)
  localStorage.setItem('icube_timer_history', JSON.stringify(
    allHistory.value.map(({ timingMode, isDnf, ...rest }) => rest)
  ))

  createTimerRecord({
    cube_type: cubeType.value, method: method.value,
    time_ms: Math.round(elapsedTime.value), scramble: currentScramble.value,
    timing_mode: 'manual'
  }).catch(() => {})

  generateScramble()
}

function clearHistory() {
  ElMessageBox.confirm('确定清空所有历史记录？', '警告', {
    confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'
  }).then(() => {
    allHistory.value = []
    localStorage.removeItem('icube_timer_history')
    ElMessage.success('已清空')
  }).catch(() => {})
}

// ============================================================
// 智能魔方
// ============================================================
const client = getCubeClient()
const tracker = new CubeOrientationTracker()
const staticOrientation = new StaticOrientation()
const cube3dRef = ref(null)

const connecting = ref(false)
const connected = ref(false)
const isSolved = ref(false)
const faceletsReceived = ref(false)
const deviceInfo = reactive({ name: '', mac: '', battery: null })
const macDialogVisible = ref(false)
const macInput = ref('')
let macResolve = null
const savedDevices = ref([])
const currentDeviceId = ref(null)

const cubeTimer = new CubeTimer({
  mode: 'practice',
  onStateChange: (state) => { cubeTimerState.value = state },
  onTimeUpdate: ({ display }) => { smartTimerDisplay.value = display },
  onScrambleGenerated: (seq) => {
    scrambleSequence.value = seq
    scrambleCurrentStep.value = 0
  },
  onScrambleProgress: (current, total, next) => {
    scrambleCurrentStep.value = current
    scrambleTotalStep.value = total
    scrambleNextMove.value = next
  },
  onCorrection: (move) => ElMessage.info(`已撤销 ${move}`),
  onWarning: (msg) => ElMessage.warning(msg),
  onSolveComplete: (result) => { onSmartSolveComplete(result) },
})
const cubeTimerState = ref(TimerStates.IDLE)
const smartTimerDisplay = ref('0.00')
const scrambleSequence = ref([])
const scrambleCurrentStep = ref(0)
const scrambleTotalStep = ref(0)
const scrambleNextMove = ref(null)
const cubeTimerMode = ref('practice')

const smartTimerStateText = computed(() => {
  const texts = {
    [TimerStates.IDLE]: '等待开始', [TimerStates.SCRAMBLING]: '打乱中',
    [TimerStates.OBSERVATION]: '观察中', [TimerStates.SOLVING]: '计时中',
    [TimerStates.SOLVED]: '已复原',
  }
  return texts[cubeTimerState.value] || ''
})
const smartTimerColor = computed(() => {
  const colors = {
    [TimerStates.IDLE]: '#909399', [TimerStates.SCRAMBLING]: '#e6a23c',
    [TimerStates.OBSERVATION]: '#e6a23c', [TimerStates.SOLVING]: '#67c23a',
    [TimerStates.SOLVED]: '#409eff',
  }
  return colors[cubeTimerState.value] || '#909399'
})
const smartTimerSubText = computed(() => {
  switch (cubeTimerState.value) {
    case TimerStates.IDLE: return '请回到初始持握开始打乱'
    case TimerStates.SCRAMBLING: return `${scrambleCurrentStep.value}/${scrambleTotalStep.value} 步`
    case TimerStates.OBSERVATION: return cubeTimerMode.value === 'practice' ? '15s 倒计时' : '不限时观察'
    case TimerStates.SOLVING: return '复原中…'
    case TimerStates.SOLVED: return solveResult.value?.dnf ? '观察超时' : `${solveResult.value?.moveCount || 0} 步`
    default: return ''
  }
})

function onCubeTimerModeChange(val) {
  cubeTimerMode.value = val
  cubeTimer.setMode(val)
}
function handleStopTimer() {
  cubeTimer.stop()
  solveResult.value = null
  scrambleSequence.value = []
  scrambleCurrentStep.value = 0
}

// 陀螺仪 / 朝向
const gyroSupported = ref(null)
const forceGyroOff = ref(false)
const gyroMode = ref(false)
const initialMapSet = ref(false)
const detectedTopFace = ref(null)
const initialOrientation = ref('')
const gyroBaseQuat = ref(null)
let gyroRafId = null
let pendingGyroQuat = null
let gyroTimer = null
const frontFaceDialogVisible = ref(false)
const frontFaceInput = ref('')
const frontFaceOptions = ref([])
const solveResult = ref(null)

const FACE_COLOR_NAMES = { U: '白', D: '黄', R: '红', L: '橙', F: '绿', B: '蓝' }
function faceColorName(face) { return FACE_COLOR_NAMES[face] || face }

function currentMap() {
  return gyroMode.value ? tracker.currentMap : staticOrientation.currentMap
}

function quatConj(q) { return { w: q.w, x: -q.x, y: -q.y, z: -q.z } }
function quatMul(a, b) {
  return {
    w: a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z,
    x: a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
    y: a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
    z: a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w
  }
}
function updateCubeAttitude(currentQuat) {
  if (!cube3dRef.value || !gyroBaseQuat.value) return
  const baseInv = quatConj(gyroBaseQuat.value)
  const rel = quatMul(currentQuat, baseInv)
  const len = Math.sqrt(rel.w*rel.w + rel.x*rel.x + rel.y*rel.y + rel.z*rel.z)
  if (len > 0) { rel.w /= len; rel.x /= len; rel.y /= len; rel.z /= len }
  cube3dRef.value.setAttitude(rel)
}

function enterGyroMode() {
  gyroMode.value = true
  tracker.reset()
  initialMapSet.value = false
  detectedTopFace.value = null
  tracker.onTopFaceDetected((topFace) => {
    detectedTopFace.value = topFace
    const topOpposite = FACES.find(f =>
      Math.abs(FACE_NORMALS[f].reduce((s, v, i) => s + v * FACE_NORMALS[topFace][i], 0)) + 1 < 0.01
    )
    frontFaceOptions.value = FACES.filter(f => f !== topFace && f !== topOpposite)
    frontFaceInput.value = ''
    frontFaceDialogVisible.value = true
  })
}
function enterStaticMode() {
  gyroMode.value = false
  staticOrientation.setPreset('white-top-green-front')
  initialMapSet.value = true
  initialOrientation.value = '白顶绿前'
}
function onModeSwitch(val) {
  if (val) { enterStaticMode() } else if (gyroSupported.value) { enterGyroMode() }
}
function submitFrontFace() {
  if (!frontFaceInput.value) { ElMessage.warning('请选择'); return }
  frontFaceDialogVisible.value = false
  const top = detectedTopFace.value
  const front = frontFaceInput.value
  tracker.setInitialMap(top, front)
  initialMapSet.value = true
  initialOrientation.value = `${faceColorName(top)}顶${faceColorName(front)}前`
  const q = tracker.currentQuaternion
  if (q && cube3dRef.value) {
    gyroBaseQuat.value = { ...q }
    updateCubeAttitude(q)
  }
  if (cube3dRef.value) cube3dRef.value.setColorScheme(top, front)
}

const handleEvent = (event) => {
  switch (event.type) {
    case 'MOVE': {
      const raw = event.move
      const map = currentMap()
      const remapped = map ? remapMove(raw, map) : raw
      if (cube3dRef.value && initialMapSet.value) cube3dRef.value.rotate(remapped)
      if (initialMapSet.value && connected.value) cubeTimer.onMove(remapped, isSolved.value)
      break
    }
    case 'GYRO':
      if (gyroSupported.value === null) {
        gyroSupported.value = true
        if (!forceGyroOff.value) enterGyroMode()
      }
      if (gyroMode.value) tracker.handleGyro(event)
      if (initialMapSet.value && tracker.currentQuaternion) {
        pendingGyroQuat = { ...tracker.currentQuaternion }
        if (!gyroRafId) {
          gyroRafId = requestAnimationFrame(() => {
            gyroRafId = null
            if (pendingGyroQuat) { updateCubeAttitude(pendingGyroQuat); pendingGyroQuat = null }
          })
        }
      }
      break
    case 'FACELETS':
      isSolved.value = event.isSolved
      faceletsReceived.value = true
      if (initialMapSet.value && connected.value) cubeTimer.onFacelets(event.isSolved)
      break
    case 'BATTERY':
      deviceInfo.battery = event.batteryLevel
      break
    case 'HARDWARE':
      if (event.hardwareName) deviceInfo.name = event.hardwareName
      break
    case 'DISCONNECT':
      connected.value = false
      isSolved.value = false
      cubeTimer.stop()
      cubeTimerState.value = TimerStates.IDLE
      smartTimerDisplay.value = '0.00'
      solveResult.value = null
      scrambleSequence.value = []
      scrambleCurrentStep.value = 0
      faceletsReceived.value = false
      gyroMode.value = false
      gyroSupported.value = null
      initialMapSet.value = false
      detectedTopFace.value = null
      initialOrientation.value = ''
      gyroBaseQuat.value = null
      if (gyroRafId) { cancelAnimationFrame(gyroRafId); gyroRafId = null }
      pendingGyroQuat = null
      deviceInfo.battery = null
      if (cube3dRef.value) cube3dRef.value.resetAttitude()
      break
  }
}
client.onEvent(handleEvent)

// --- 智能模式自动保存 ---
function onSmartSolveComplete(result) {
  solveResult.value = result
  const isDnf = result.dnf
  const record = {
    id: Date.now(),
    time: isDnf ? 0 : (result.solveTime || 0),
    scramble: result.scramble ? result.scramble.join(' ') : '',
    solveSequence: result.solve ? result.solve.join(' ') : '',
    moveCount: result.moveCount || 0,
    tps: isDnf ? null : calcTPS(result.moveCount, result.solveTime),
    isDnf,
    timingMode: 'smart'
  }
  allHistory.value.unshift(record)

  createTimerRecord({
    cube_type: cubeType.value,
    method: method.value,
    time_ms: isDnf ? 0 : Math.round(result.solveTime || 0),
    scramble: result.scramble ? result.scramble.join(' ') : '',
    solve_sequence: result.solve ? result.solve.join(' ') : '',
    observation_time_ms: result.observationTime || 0,
    move_count: result.moveCount || 0,
    is_dnf: isDnf,
    timing_mode: 'smart',
    device_id: currentDeviceId.value || undefined
  }).then(() => {
    ElMessage.success(isDnf ? 'DNF 记录已保存' : '记录已保存')
  }).catch(() => {
    ElMessage.error('保存失败')
  })
}

// --- 连接 ---
async function loadSavedDevices() {
  try {
    const res = await getSmartCubeDevices()
    if (res.code === 100 && res.data && res.data.length > 0) {
      savedDevices.value = res.data
      currentDeviceId.value = res.data[0].id
      // 从后端设备列表预设 MAC 到 client，刷新后连接时复用
      const client = getCubeClient()
      if (!client._mac && res.data[0].mac_address) {
        client._mac = res.data[0].mac_address
        client._name = res.data[0].name || 'GAN-XXXX'
      }
    }
  } catch {}
}

async function handleConnect() {
  if (client.connected) {
    connected.value = true
    deviceInfo.name = client.deviceName
    deviceInfo.mac = client.deviceMAC
    return
  }
  if (!client.constructor.isSupported) {
    ElMessage.error('请使用 Chrome 或 Edge 浏览器')
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
    ElMessage.success('连接成功')
    try {
      const res = await registerSmartCubeDevice({ mac_address: deviceInfo.mac, name: deviceInfo.name })
      if (res.code === 100 && res.data) currentDeviceId.value = res.data.id
    } catch {}
    gyroTimer = setTimeout(() => {
      if (gyroSupported.value === null) {
        gyroSupported.value = false
        enterStaticMode()
      }
    }, 3000)
  } catch (err) {
    if (err.name === 'NotFoundError') ElMessage.info('已取消选择')
    else ElMessage.error(err.message)
  } finally {
    connecting.value = false
  }
}

function onDeviceCmd(cmd) {
  if (cmd === 'reset') handleReset()
  else if (cmd === 'disconnect') handleDisconnect()
}

async function handleReset() {
  try {
    await client.resetCube()
    isSolved.value = true
    faceletsReceived.value = true
    cubeTimer.stop()
    cubeTimerState.value = TimerStates.IDLE
    smartTimerDisplay.value = '0.00'
    solveResult.value = null
    scrambleSequence.value = []
    scrambleCurrentStep.value = 0
    tracker.reset()
    initialMapSet.value = false
    detectedTopFace.value = null
    initialOrientation.value = ''
    gyroBaseQuat.value = null
    if (gyroRafId) { cancelAnimationFrame(gyroRafId); gyroRafId = null }
    pendingGyroQuat = null
    if (cube3dRef.value) { cube3dRef.value.reset(); cube3dRef.value.resetAttitude() }
    if (gyroMode.value) tracker.reset()
  } catch (err) {
    ElMessage.error('复位失败: ' + err.message)
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
  tracker.reset()
}

function submitMac() {
  const mac = macInput.value.trim().toUpperCase()
  if (!/^([0-9A-F]{2}:){5}[0-9A-F]{2}$/.test(mac)) {
    ElMessage.warning('格式不正确')
    return
  }
  macDialogVisible.value = false
  if (macResolve) { macResolve(mac); macResolve = null }
}
function onMacDialogClose() {
  if (macResolve) { macResolve(null); macResolve = null }
}

// ===== 生命周期 =====
function beforeUnloadHandler() {
  if (connected.value) client.disconnectSync()
}
onMounted(() => {
  generateScramble()
  if (timerPage.value) timerPage.value.focus()
  window.addEventListener('beforeunload', beforeUnloadHandler)
  if (timingMode.value === 'smart') loadSavedDevices()
})
onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', beforeUnloadHandler)
  clearInterval(timerInterval.value)
  clearTimeout(holdTimer.value)
  if (gyroTimer) clearTimeout(gyroTimer)
  if (gyroRafId) cancelAnimationFrame(gyroRafId)
})
</script>

<style scoped>
.timer-container {
  outline: none;
  padding: 10px;
  min-height: 75vh;
}

/* 顶部工具栏 */
.top-bar {
  display: flex;
  justify-content: center;
  margin-bottom: 12px;
}
.top-bar-center {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}
.connect-mini {
  display: flex;
  align-items: center;
  gap: 6px;
}
.device-menu-icon {
  cursor: pointer;
  font-size: 16px;
  color: #909399;
  padding: 2px;
}
.mac-hint-icon {
  font-size: 16px;
  color: var(--el-color-warning);
  cursor: help;
}

/* 左列 */
.left-col {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.stats-card .card-header,
.history-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.summary-stats p {
  margin: 6px 0;
  font-size: 13px;
  color: #606266;
}
.best-time {
  color: #67c23a;
  font-weight: bold;
}
.history-list {
  max-height: 400px;
  overflow-y: auto;
}
.history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 4px;
  border-bottom: 1px dashed #e4e7ed;
  font-size: 13px;
}
.history-item.is-dnf .hi-time {
  color: #f56c6c;
}
.hi-index { color: #909399; width: 30px; }
.hi-time { font-weight: bold; flex-grow: 1; }
.hi-moves { color: #409eff; font-size: 12px; }
.hi-tps { color: #e6a23c; font-size: 12px; }
.hi-dnf { color: #f56c6c; font-weight: bold; }
.empty-tip {
  text-align: center;
  color: #909399;
  font-size: 13px;
  padding: 30px 0;
}

/* 右列主卡片 */
.main-card {
  min-height: 500px;
  position: relative;
  overflow: hidden;
  background: #f5f5f5;
}
.main-card :deep(.el-card__body) {
  background: #f5f5f5;
  height: 100%;
  min-height: 500px;
}

/* 打乱 chip */
.scramble-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: center;
  margin-bottom: 12px;
}
.scramble-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 24px;
  padding: 0 5px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
  font-family: 'Courier New', monospace;
  color: #fff;
  background: #909399;
}
.chip-done { background: #67c23a; opacity: 0.5; }
.chip-current { background: #e6a23c; box-shadow: 0 0 0 2px rgba(230,162,60,0.3); }
.scramble-empty {
  text-align: center;
  color: #c0c4cc;
  font-size: 13px;
  padding: 8px 0;
  margin-bottom: 12px;
}

/* 中间区域：居中布局 */
.center-area {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  padding: 16px;
}
.center-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.status-hint {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}
.status-hint.ready { color: #67c23a; font-weight: bold; }
.status-hint.running { color: #f56c6c; }
.time-banner {
  font-family: 'Impact', 'Arial Black', sans-serif;
  font-size: 64px;
  letter-spacing: 2px;
  color: #303133;
  cursor: pointer;
  user-select: none;
  transition: color 0.1s ease;
}
.time-banner.holding { color: #f56c6c; }
.time-banner.ready { color: #67c23a; }
.time-banner.running { color: #409eff; }
.manual-hint {
  font-size: 13px;
  color: #909399;
  margin-top: 8px;
}

/* 智能模式中间区域 */
.smart-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
.cube-mini {
  width: 260px;
  height: 260px;
  background: transparent;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
}
.smart-timer-block {
  text-align: center;
}
.timer-main {
  font-size: 36px;
  font-weight: 800;
  font-family: 'Courier New', monospace;
  line-height: 1.2;
}
.timer-sub {
  font-size: 13px;
  margin-top: 2px;
}
.smart-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
  margin-top: 8px;
}
.smart-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}
.placeholder-text {
  color: #c0c4cc;
  font-size: 16px;
}
.net-block {
  position: absolute;
  bottom: 8px;
  right: 8px;
  z-index: 1;
}

/* 对话框 */
.mac-hint {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  margin-bottom: 8px;
}
.mac-tooltip {
  max-width: 340px;
}
.mac-tooltip p { margin: 4px 0; font-size: 13px; }
.mac-tooltip code {
  background: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}
.front-face-blocks {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-top: 16px;
}
.face-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 10px;
  cursor: pointer;
  border: 3px solid transparent;
  transition: border-color 0.2s, transform 0.15s;
  user-select: none;
}
.face-block:hover { transform: scale(1.05); }
.face-block-selected { border-color: #303030; transform: scale(1.05); }
.face-block-color { font-size: 18px; font-weight: 700; color: #fff; }
.face-block-letter { font-size: 12px; color: rgba(255,255,255,0.8); }
.face-block-u { background: #e6a700; }
.face-block-r { background: #f56c6c; }
.face-block-f { background: #67c23a; }
.face-block-d { background: #e6e6e6; }
.face-block-d .face-block-color, .face-block-d .face-block-letter { color: #303030; }
.face-block-l { background: #e8923c; }
.face-block-b { background: #409eff; }

/* 响应式 */
@media (max-width: 768px) {
  .center-area { flex-direction: column; }
  .cube-mini { width: 220px; height: 220px; }
  .time-banner { font-size: 48px; }
}
</style>
