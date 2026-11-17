<template>
  <div class="page">
    <van-pull-refresh v-model="pageRefreshing" @refresh="onPageRefresh">
    <div class="timer-tab">
      <van-nav-bar title="计时" placeholder />

      <!-- 模式切换 -->
      <van-tabs v-model:active="timingMode" line-width="20px" class="mode-tabs">
        <van-tab title="手动" name="manual" />
        <van-tab title="智能" name="smart" />
      </van-tabs>

      <!-- 智能模式：连接状态条 -->
      <div v-if="timingMode === 'smart'" class="connect-bar" @click="onConnectTap">
        <div class="connect-status">
          <span :class="['connect-dot', smartConnected ? 'dot-connected' : 'dot-disconnected']"></span>
          <span class="connect-text">{{ smartConnected ? smartDeviceName : '未连接' }}</span>
        </div>
        <div class="connect-right">
          <span v-if="smartConnected && smartBatteryLevel !== null" class="battery-info">
            <van-icon name="battery-o" size="14" color="#07c160" />
            <span class="battery-text">{{ smartBatteryLevel }}%</span>
          </span>
          <van-icon name="arrow" size="14" color="#c8c9cc" />
        </div>
      </div>

      <!-- 智能模式：3D 魔方 -->
      <div v-if="timingMode === 'smart'" class="cube-3d-wrap">
        <Cube3D ref="cube3dRef" :size="180" />
        <div class="cube-toolbar">
          <button v-if="smartConnected" class="cube-tool-btn" @click="resetCubeView" title="重置视角">
            <van-icon name="replay" size="14" />
          </button>
          <button
            v-if="smartConnected"
            class="cube-tool-btn"
            :class="{ active: gyroEnabled }"
            @click="toggleGyro"
            title="陀螺仪跟随"
          >
            <van-icon name="aim" size="14" />
          </button>
        </div>
      </div>

      <div class="scramble-nav">
        <button
          class="scramble-nav-btn"
          :class="{ disabled: !canPrevScramble }"
          @click="prevScramble"
          :disabled="!canPrevScramble"
        >
          <van-icon name="arrow-left" size="16" />
        </button>
        <ScrambleText :scramble="scramble" @refresh="generateScramble" />
        <button
          class="scramble-nav-btn"
          :class="{ disabled: !canNextScramble }"
          @click="nextScramble"
          :disabled="!canNextScramble"
        >
          <van-icon name="arrow" size="16" />
        </button>
      </div>

      <van-dropdown-menu class="type-selector">
        <van-dropdown-item v-model="cubeType" :options="cubeOptions" @change="onTypeChange" />
        <van-dropdown-item v-model="method" :options="methodOptions" />
      </van-dropdown-menu>

      <TimerDisplay
        v-if="timingMode === 'manual'"
        :state="timerState"
        :elapsed="elapsed"
        @touchstart="onTouchStart"
        @touchend="onTouchEnd"
      />

      <!-- 智能模式：计时显示 -->
      <div v-else class="smart-timer-display">
        <!-- DNF 标识 -->
        <div v-if="smartIsDNF" class="dnf-badge">DNF</div>

        <div :class="['smart-time', {
          'smart-time-scrambling': smartTimerState === 'scrambling',
          'smart-time-ready': smartTimerState === 'ready',
          'smart-time-observation': smartTimerState === 'observation',
          'smart-time-solving': smartTimerState === 'solving',
          'smart-time-solved': smartTimerState === 'solved',
          'smart-time-dnf': smartIsDNF,
        }]">
          <template v-if="smartTimerState === 'observation'">
            {{ formatObservationTime(smartObservationTime) }}
          </template>
          <template v-else-if="smartTimerState === 'idle' || smartTimerState === 'scrambling'">
            --:--:--
          </template>
          <template v-else-if="smartIsDNF">
            DNF
          </template>
          <template v-else>
            {{ formatTime(smartElapsed) }}
          </template>
        </div>

        <!-- 实时数据栏：步数 / TPS -->
        <div v-if="smartConnected && (smartTimerState === 'solving' || smartTimerState === 'solved' || smartTimerState === 'scrambling' || smartTimerState === 'observation')" class="smart-stats-row">
          <div class="smart-stat-item">
            <span class="smart-stat-value">{{ smartMoveCount }}</span>
            <span class="smart-stat-label">步</span>
          </div>
          <div v-if="(smartTimerState === 'solving' || smartTimerState === 'solved') && smartElapsed > 0" class="smart-stat-item">
            <span class="smart-stat-value">{{ smartTps }}</span>
            <span class="smart-stat-label">TPS</span>
          </div>
        </div>

        <div class="smart-timer-hint">
          <template v-if="!smartConnected">请先连接智能魔方</template>
          <template v-else-if="smartTimerState === 'idle'">转动魔方开始打乱</template>
          <template v-else-if="smartTimerState === 'scrambling'">打乱中... 完成后点下方按钮</template>
          <template v-else-if="smartTimerState === 'ready'">准备好了，点按钮进入观察期</template>
          <template v-else-if="smartTimerState === 'observation'">观察期... 转动即开始</template>
          <template v-else-if="smartTimerState === 'solving'">计时中...</template>
          <template v-else-if="smartIsDNF">未完成</template>
          <template v-else>🎉 完成！</template>
        </div>

        <!-- 打乱完成按钮 -->
        <van-button
          v-if="smartConnected && smartTimerState === 'scrambling'"
          type="success"
          round
          size="large"
          @click="smartMarkReady"
          style="margin-top: 16px;"
        >
          打乱完成
        </van-button>

        <!-- 开始观察按钮：ready 状态下点击进入观察期 -->
        <van-button
          v-if="smartConnected && smartTimerState === 'ready'"
          type="primary"
          round
          size="large"
          @click="smartStartObservation"
          style="margin-top: 16px;"
        >
          开始观察（15s）
        </van-button>

        <!-- 跳过观察按钮：observation 状态下可直接开始计时 -->
        <van-button
          v-if="smartConnected && smartTimerState === 'observation'"
          type="primary"
          plain
          round
          size="small"
          @click="smartStartSolving"
          style="margin-top: 12px;"
        >
          直接开始
        </van-button>

        <!-- 下一把按钮 -->
        <van-button
          v-if="smartConnected && (smartTimerState === 'solved' || smartTimerState === 'solved-dnf' || smartIsDNF)"
          type="primary"
          plain
          round
          size="small"
          @click="smartReset"
          style="margin-top: 12px;"
        >
          下一把
        </van-button>
      </div>

      <!-- 统计面板 -->
      <div class="stats-panel">
        <div class="stat-item">
          <span class="stat-value">{{ todayHistory.length }}</span>
          <span class="stat-label">次数</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ bestTime ? formatTime(bestTime) + 's' : '--' }}</span>
          <span class="stat-label">最快</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ ao5 !== null ? formatTime(ao5) + 's' : '--' }}</span>
          <span class="stat-label">Ao5</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ ao12 !== null ? formatTime(ao12) + 's' : '--' }}</span>
          <span class="stat-label">Ao12</span>
        </div>
      </div>

      <!-- 本地今日记录 -->
      <div class="history-section">
        <div class="history-header">
          <span class="history-title">今日记录</span>
          <van-button
            v-if="history.length > 0"
            size="mini"
            type="danger"
            plain
            @click="confirmClear"
          >清空</van-button>
        </div>
        <div class="history-list">
          <van-swipe-cell
            v-for="(record, index) in displayTodayHistory"
            :key="record.id"
          >
            <div class="history-item" @click="showDetail(record)">
              <span class="history-index">#{{ todayHistory.length - index }}</span>
              <span class="history-time" :class="{ 'dnf-time': record.penalty === 'dnf' || record.is_dnf }">
                {{ record.penalty === 'dnf' || record.is_dnf ? 'DNF' : formatTime(record.time_ms) }}
              </span>
              <span class="history-type">{{ record.cube_type }} · {{ methodLabel(record.method) }}</span>
              <van-icon name="arrow" size="12" color="#c8c9cc" />
            </div>
            <template #right>
              <van-button
                square
                type="danger"
                text="删除"
                class="delete-btn"
                @click="deleteRecord(index)"
              />
            </template>
          </van-swipe-cell>
          <van-empty v-if="todayHistory.length === 0" description="今日暂无记录" image-size="80" />
        </div>
      </div>

      <!-- 历史记录（后端 / 本地降级） -->
      <div ref="recordsSection" class="records-section">
        <div class="records-header">
          <span class="records-title">历史记录</span>
          <van-dropdown-menu class="records-filter">
            <van-dropdown-item v-model="recordCubeType" :options="recordCubeOptions" @change="onRecordFilterChange" />
          </van-dropdown-menu>
        </div>

        <van-list
          v-model:loading="recordLoading"
          :finished="recordFinished"
          finished-text="没有更多了"
          @load="loadRecords"
          :immediate-check="false"
        >
            <van-swipe-cell v-for="(record, index) in recordList" :key="record.id">
              <div class="record-item" @click="showDetail(record)">
                <span class="record-time" :class="{ 'dnf-time': record.is_dnf }">
                  {{ record.is_dnf ? 'DNF' : formatTime(record.time_ms) }}
                </span>
                <div class="record-meta">
                  <van-tag type="primary" size="mini">{{ record.cube_type }}</van-tag>
                  <van-tag v-if="record.timing_mode === 'smart'" type="success" size="mini">智能</van-tag>
                  <van-tag v-else plain size="mini">手动</van-tag>
                  <span class="record-method">{{ methodLabel(record.method) }}</span>
                  <span v-if="record.move_count" class="record-moves">{{ record.move_count }}步</span>
                  <span class="record-date">{{ formatDate(record.created_at) }}</span>
                </div>
              </div>
              <template #right>
                <van-button square type="danger" text="删除" class="delete-btn" @click="confirmDeleteRecord(record, index)" />
              </template>
            </van-swipe-cell>
            <van-empty v-if="!recordLoading && recordList.length === 0" description="暂无计时记录" image-size="80" />
          </van-list>
      </div>
    </div>
    </van-pull-refresh>

    <!-- 记录详情弹窗 -->
    <van-popup
      v-model:show="detailShow"
      position="bottom"
      round
      closeable
      :style="{ maxHeight: '70%' }"
    >
      <div v-if="detailRecord" class="detail-card">
        <div class="detail-header">
          <span class="detail-time" :class="{ 'dnf-time': detailRecord.is_dnf || detailRecord.penalty === 'dnf' }">
            {{ detailRecord.is_dnf || detailRecord.penalty === 'dnf' ? 'DNF' : formatTime(detailRecord.time_ms) }}
            <span v-if="detailRecord.penalty === 'plus2'" class="plus2-suffix">+2</span>
          </span>
          <van-tag type="primary" size="medium">{{ detailRecord.cube_type }}</van-tag>
          <van-tag plain type="primary" size="medium">{{ methodLabel(detailRecord.method) }}</van-tag>
          <van-tag v-if="detailRecord.timing_mode === 'smart'" type="success" size="medium">智能计时</van-tag>
        </div>
        <div class="detail-date">{{ formatDateTime(detailRecord.date || detailRecord.created_at) }}</div>
        <div v-if="detailRecord.move_count || detailRecord.observation_time_ms" class="detail-stats">
          <span v-if="detailRecord.move_count">步数: {{ detailRecord.move_count }}</span>
          <span v-if="detailRecord.observation_time_ms">观察: {{ formatTime(detailRecord.observation_time_ms) }}</span>
          <span v-if="detailRecord.move_count && detailRecord.time_ms">TPS: {{ (detailRecord.move_count / (detailRecord.time_ms / 1000)).toFixed(2) }}</span>
        </div>
        <div class="detail-section">
          <div class="detail-label">打乱公式</div>
          <div class="detail-chips">
            <span
              v-for="(move, i) in detailScrambleChips"
              :key="'s' + i"
              class="detail-chip"
            >{{ move }}</span>
            <span v-if="detailScrambleChips.length === 0" class="detail-empty">未记录</span>
          </div>
        </div>
        <div v-if="detailSolveChips.length > 0" class="detail-section">
          <div class="detail-label">复原步骤</div>
          <div class="detail-chips">
            <span
              v-for="(move, i) in detailSolveChips"
              :key="'v' + i"
              class="detail-chip solve-chip"
            >{{ move }}</span>
          </div>
        </div>

        <!-- 判罚操作 -->
        <div class="detail-penalty-actions">
          <van-button
            size="small"
            :type="detailRecord?.penalty === 'plus2' ? 'warning' : 'default'"
            plain
            @click="togglePlus2"
          >
            {{ detailRecord?.penalty === 'plus2' ? '取消 +2' : '+2 判罚' }}
          </van-button>
          <van-button
            size="small"
            :type="(detailRecord?.penalty === 'dnf' || detailRecord?.is_dnf) ? 'danger' : 'default'"
            plain
            @click="toggleDNF"
          >
            {{ detailRecord?.penalty === 'dnf' || detailRecord?.is_dnf ? '取消 DNF' : 'DNF' }}
          </van-button>
        </div>
      </div>
    </van-popup>

    <!-- 通用确认弹窗 -->
    <ConfirmDialog
      v-model:show="confirmShow"
      :title="confirmTitle"
      :message="confirmMessage"
      :confirm-text="confirmText"
      :confirm-color="confirmColor"
      :icon="confirmIcon"
      @confirm="onConfirm"
    />
  </div>
</template>

<script setup>
/**
 * TimerView.vue — 移动端计时器页面
 *
 * 单页：计时器 + 本地历史 + 数据记录（合并）
 * 触屏状态机：idle → holding → ready → running → idle
 */
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { showToast, showDialog } from 'vant'
import ScrambleText from '@/components/timer/ScrambleText.vue'
import TimerDisplay from '@/components/timer/TimerDisplay.vue'
import Cube3D from '@/components/cube/Cube3D.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { createTimerRecord, getTimerRecords, deleteTimerRecord } from '@/api/timer'
import { requestGanDevice, connectGanCube, startNotifications, disconnect } from '@/utils/ble'
import { Gen4ProtocolDriver } from '@/utils/gan-ble'

const route = useRoute()

// ─── 通用确认弹窗 ────────────────────────────────────
const confirmShow = ref(false)
const confirmTitle = ref('')
const confirmMessage = ref('')
const confirmText = ref('确认')
const confirmColor = ref('#ee0a24')
const confirmIcon = ref('warning-o')
let confirmCallback = null

function showConfirm(options) {
  confirmTitle.value = options.title || '确认操作'
  confirmMessage.value = options.message || ''
  confirmText.value = options.confirmText || '确认'
  confirmColor.value = options.confirmColor || '#ee0a24'
  confirmIcon.value = options.icon || 'warning-o'
  confirmCallback = options.onConfirm || null
  confirmShow.value = true
}

function onConfirm() {
  confirmShow.value = false
  confirmCallback?.()
}

// ─── 数据记录区域 ref ────────────────────────────────
const recordsSection = ref()

// ─── 常量 ────────────────────────────────────────────
const STORAGE_KEY = 'icube_timer_history'
const HOLD_THRESHOLD = 500

const cubeOptions = [
  { text: '2x2', value: '2x2' },
  { text: '3x3', value: '3x3' },
  { text: '4x4', value: '4x4' },
]
const methodOptions = [
  { text: '层先法', value: 'layer' },
  { text: 'CFOP', value: 'cfop' },
  { text: 'Roux', value: 'roux' },
  { text: 'ZZ', value: 'zz' },
]

// ─── 计时器状态 ──────────────────────────────────────
const timerState = ref('idle')
const elapsed = ref(0)
const scramble = ref('')
const scrambleHistory = ref([]) // 打乱历史
const scrambleIndex = ref(-1) // 当前打乱在历史中的索引
const MAX_SCRAMBLE_HISTORY = 20
const cubeType = ref('3x3')
const method = ref('cfop')
const history = ref([])

// ─── 智能模式状态 ────────────────────────────────────
const timingMode = ref('manual') // manual / smart
const smartConnected = ref(false)
const smartDeviceName = ref('')
const smartTimerState = ref('idle') // idle / scrambling / ready / observation / solving / solved
const smartObservationTime = ref(0) // 观察时间剩余（毫秒）
const smartIsDNF = ref(false) // 是否 DNF

let smartObservationInterval = null
const OBSERVATION_DURATION = 15000 // 15 秒观察期
const smartElapsed = ref(0)
const cube3dRef = ref(null)
const smartIsSolved = ref(true) // 魔方当前是否复原
const smartMoveCount = ref(0) // 实时步数
const smartBatteryLevel = ref(null) // 电量
const gyroEnabled = ref(false) // 陀螺仪跟随

let smartConnectionInfo = null
let smartProtocolDriver = null
let smartStartTime = 0
let smartTimerInterval = null
let smartSolveMoves = []

const detailShow = ref(false)
const detailRecord = ref(null)

// 详情弹窗的步骤拆分
const detailScrambleChips = computed(() => {
  if (!detailRecord.value?.scramble) return []
  return detailRecord.value.scramble.split(' ').filter(Boolean)
})
const detailSolveChips = computed(() => {
  const seq = detailRecord.value?.solve_sequence || detailRecord.value?.solveSequence
  if (!seq) return []
  return seq.split(' ').filter(Boolean)
})

let startTime = 0
let timerInterval = null
let holdTimer = null

// ─── 数据记录状态 ────────────────────────────────────
const recordList = ref([])
const recordLoading = ref(false)
const recordFinished = ref(false)
const recordRefreshing = ref(false)
const pageRefreshing = ref(false)
const recordPage = ref(1)
const recordPageSize = 20
const recordCubeType = ref('')
const recordCubeOptions = [
  { text: '全部类型', value: '' },
  { text: '2x2', value: '2x2' },
  { text: '3x3', value: '3x3' },
  { text: '4x4', value: '4x4' },
]
let recordsLoaded = false

// ─── 打乱公式生成 ────────────────────────────────────
const SCRAMBLE_MOVES = {
  '2x2': { moves: ['U', 'D', 'R', 'L', 'F', 'B'], variants: ['', "'", '2'], length: 11 },
  '3x3': { moves: ['U', 'D', 'R', 'L', 'F', 'B'], variants: ['', "'", '2'], length: 21 },
  '4x4': { moves: ['U', 'D', 'R', 'L', 'F', 'B', 'Uw', 'Rw', 'Fw'], variants: ['', "'", '2'], length: 40 },
}

function generateScramble() {
  const config = SCRAMBLE_MOVES[cubeType.value] || SCRAMBLE_MOVES['3x3']
  const result = []
  let lastFace = ''
  for (let i = 0; i < config.length; i++) {
    let move
    do {
      move = config.moves[Math.floor(Math.random() * config.moves.length)]
    } while (move[0] === lastFace)
    lastFace = move[0]
    const variant = config.variants[Math.floor(Math.random() * config.variants.length)]
    result.push(move + variant)
  }
  const newScramble = result.join(' ')
  scramble.value = newScramble

  // 加入历史（如果不在看历史记录的话）
  if (scrambleIndex.value === scrambleHistory.value.length - 1 || scrambleHistory.value.length === 0) {
    scrambleHistory.value.push(newScramble)
    if (scrambleHistory.value.length > MAX_SCRAMBLE_HISTORY) {
      scrambleHistory.value.shift()
    }
    scrambleIndex.value = scrambleHistory.value.length - 1
  } else {
    // 当前在看历史，新加的追加到末尾
    scrambleHistory.value.push(newScramble)
    scrambleIndex.value = scrambleHistory.value.length - 1
  }
}

// 上一把打乱
function prevScramble() {
  if (scrambleIndex.value > 0) {
    scrambleIndex.value--
    scramble.value = scrambleHistory.value[scrambleIndex.value]
  }
}

// 下一把打乱
function nextScramble() {
  if (scrambleIndex.value < scrambleHistory.value.length - 1) {
    scrambleIndex.value++
    scramble.value = scrambleHistory.value[scrambleIndex.value]
  }
}

const canPrevScramble = computed(() => scrambleIndex.value > 0)
const canNextScramble = computed(() => scrambleIndex.value < scrambleHistory.value.length - 1)

// ─── 智能模式：连接管理 ────────────────────────────────────
async function onConnectTap() {
    if (smartConnected.value) {
        // 已连接：显示设备信息，确认断开
        showDialog({
            title: '已连接',
            message: smartDeviceName.value + '\n确定要断开连接吗？',
            showCancelButton: true,
            confirmButtonText: '断开',
            cancelButtonText: '取消',
        }).then(() => {
            smartDisconnect()
        }).catch(() => {})
        return
    }

    // 未连接：弹出设备选择器
    try {
        const device = await requestGanDevice()
        await smartConnect(device)
    } catch (err) {
        const msg = err?.message || String(err)
        if (!msg.includes('cancel') && !msg.includes('取消')) {
            showToast('连接失败：' + msg)
        }
    }
}

async function smartConnect(device) {
    // 建立连接
    smartConnectionInfo = await connectGanCube(device.deviceId, {
        onDisconnect: smartHandleDisconnect,
    })

    // 初始化协议解析器
    smartProtocolDriver = new Gen4ProtocolDriver(device.deviceId)
    smartProtocolDriver.onMove = smartHandleMove
    smartProtocolDriver.onFacelets = smartHandleFacelets
    smartProtocolDriver.onBattery = (event) => {
        smartBatteryLevel.value = event.batteryLevel
    }
    smartProtocolDriver.onHardware = () => {}

    // 启动通知监听
    await startNotifications(
        smartConnectionInfo.deviceId,
        smartConnectionInfo.serviceUuid,
        smartConnectionInfo.stateUuid,
        (data) => {
            smartProtocolDriver.handleStateNotification(data)
        },
    )

    smartConnected.value = true
    smartDeviceName.value = device.name
    showToast('连接成功')

    // 保存 MAC 方便下次重连
    localStorage.setItem('gan_cube_mac', device.deviceId)

    // 重置 3D 魔方到复原状态
    if (cube3dRef.value) {
        cube3dRef.value.reset()
    }
}

async function smartDisconnect() {
    if (smartConnectionInfo) {
        try {
            await disconnect(smartConnectionInfo.deviceId)
        } catch (e) {}
    }
    smartHandleDisconnect()
}

function smartHandleDisconnect() {
    smartConnected.value = false
    smartDeviceName.value = ''
    smartBatteryLevel.value = null
    smartConnectionInfo = null
    smartProtocolDriver = null
    // 如果正在计时/观察中，重置状态
    if (smartTimerState.value === 'solving' || smartTimerState.value === 'observation') {
        clearInterval(smartTimerInterval)
        clearInterval(smartObservationInterval)
        smartTimerInterval = null
        smartObservationInterval = null
        smartTimerState.value = 'idle'
        smartElapsed.value = 0
        smartIsDNF.value = false
    }
    showToast('已断开连接')
}

// ─── 智能模式：转动处理 & 计时状态机 ────────────────────────────────────
function smartHandleMove(moveInfo) {
    // 同步 3D 魔方
    if (cube3dRef.value) {
        cube3dRef.value.rotate(moveInfo.move)
    }

    // 状态机逻辑
    switch (smartTimerState.value) {
        case 'idle':
            // 第一次转动 → 进入打乱状态
            smartTimerState.value = 'scrambling'
            break

        case 'observation':
            // 观察期内转动 → 开始计时
            clearInterval(smartObservationInterval)
            smartObservationInterval = null
            smartStartSolving()
            smartSolveMoves = [moveInfo.move]
            smartMoveCount.value = 1
            break

        case 'solving':
            // 计时中，记录步骤
            smartSolveMoves.push(moveInfo.move)
            smartMoveCount.value++
            break
    }
}

// 面块状态回调（检测是否复原）
function smartHandleFacelets(event) {
    smartIsSolved.value = event.isSolved

    // 复原中 & 魔方复原 → 停止计时
    if (smartTimerState.value === 'solving' && event.isSolved) {
        smartStopTimer()
    }
}

// 用户确认打乱完成
function smartMarkReady() {
    smartTimerState.value = 'ready'
}

// 开始观察期
function smartStartObservation() {
    smartTimerState.value = 'observation'
    smartObservationTime.value = OBSERVATION_DURATION
    smartMoveCount.value = 0

    const startTime = performance.now()
    smartObservationInterval = setInterval(() => {
        const elapsed = performance.now() - startTime
        const remaining = OBSERVATION_DURATION - elapsed

        if (remaining <= 0) {
            // 观察超时 → DNF
            clearInterval(smartObservationInterval)
            smartObservationInterval = null
            smartMarkDNF()
        } else {
            smartObservationTime.value = remaining
        }
    }, 10)
}

// 开始复原计时
function smartStartSolving() {
    smartTimerState.value = 'solving'
    smartStartTime = performance.now()
    smartElapsed.value = 0
    smartTimerInterval = setInterval(() => {
        smartElapsed.value = performance.now() - smartStartTime
    }, 10)
}

// 标记 DNF
function smartMarkDNF() {
    smartIsDNF.value = true
    smartTimerState.value = 'solved'
    smartElapsed.value = 0

    const record = {
        id: Date.now(),
        time_ms: 0,
        scramble: scramble.value,
        cube_type: cubeType.value,
        method: method.value,
        timing_mode: 'smart',
        move_count: smartMoveCount.value,
        solve_sequence: smartSolveMoves.join(' '),
        penalty: 'dnf',
        date: new Date().toISOString(),
    }

    history.value.unshift(record)
    saveToStorage()

    if (localStorage.getItem('token')) {
        createTimerRecord({
            cube_type: record.cube_type,
            method: record.method,
            time_ms: 0,
            scramble: record.scramble,
            timing_mode: 'smart',
            move_count: record.move_count,
            solve_sequence: record.solve_sequence,
            penalty: 'dnf',
        }).then(() => {
            if (recordsLoaded) loadRecords(true)
        }).catch(() => {})
    } else {
        if (recordsLoaded) loadRecords(true)
    }

    generateScramble()
}

function smartStopTimer() {
    clearInterval(smartTimerInterval)
    smartTimerInterval = null
    smartTimerState.value = 'solved'

    // 3D 魔方复位 + 高亮闪烁
    if (cube3dRef.value) {
        cube3dRef.value.reset()
        cube3dRef.value.flashHighlight?.()
    }

    const record = {
        id: Date.now(),
        time_ms: Math.round(smartElapsed.value),
        scramble: scramble.value,
        cube_type: cubeType.value,
        method: method.value,
        timing_mode: 'smart',
        move_count: smartMoveCount.value,
        solve_sequence: smartSolveMoves.join(' '),
        date: new Date().toISOString(),
    }

    history.value.unshift(record)
    saveToStorage()

    // 同步后端
    if (localStorage.getItem('token')) {
        createTimerRecord({
            cube_type: record.cube_type,
            method: record.method,
            time_ms: record.time_ms,
            scramble: record.scramble,
            timing_mode: 'smart',
            move_count: record.move_count,
            solve_sequence: record.solve_sequence,
        }).then(() => {
            if (recordsLoaded) loadRecords(true)
        }).catch(() => {})
    } else {
        if (recordsLoaded) loadRecords(true)
    }

    // 生成新打乱
    generateScramble()
}

// 重置到下一把
function smartReset() {
    clearInterval(smartObservationInterval)
    smartObservationInterval = null
    smartTimerState.value = 'idle'
    smartElapsed.value = 0
    smartIsDNF.value = false
    smartObservationTime.value = 0
    smartSolveMoves = []
    smartMoveCount.value = 0
    if (cube3dRef.value) {
        cube3dRef.value.reset()
    }
}

// 观察时间格式化
function formatObservationTime(ms) {
    const totalSeconds = Math.ceil(ms / 1000)
    return totalSeconds.toString().padStart(2, '0') + '.00'
}

// 重置 3D 魔方视角
function resetCubeView() {
    cube3dRef.value?.resetView?.()
}

// 切换陀螺仪跟随
async function toggleGyro() {
    if (!cube3dRef.value) return
    if (gyroEnabled.value) {
        await cube3dRef.value.setGyroEnabled(false)
        gyroEnabled.value = false
        showToast('陀螺仪已关闭')
    } else {
        const ok = await cube3dRef.value.setGyroEnabled(true)
        if (ok) {
            gyroEnabled.value = true
            showToast('陀螺仪已开启')
        } else {
            showToast('陀螺仪不可用')
        }
    }
}

function onTypeChange() {
  generateScramble()
}

// ─── 触屏事件处理 ────────────────────────────────────
function onTouchStart() {
  if (timerState.value === 'idle') {
    timerState.value = 'holding'
    elapsed.value = 0
    holdTimer = setTimeout(() => {
      timerState.value = 'ready'
    }, HOLD_THRESHOLD)
  } else if (timerState.value === 'running') {
    stopTimer()
  }
}

function onTouchEnd() {
  if (timerState.value === 'holding') {
    clearTimeout(holdTimer)
    timerState.value = 'idle'
  } else if (timerState.value === 'ready') {
    startTimer()
  }
}

// ─── 计时逻辑 ────────────────────────────────────────
function startTimer() {
  timerState.value = 'running'
  startTime = performance.now()
  timerInterval = setInterval(() => {
    elapsed.value = performance.now() - startTime
  }, 10)
}

function stopTimer() {
  clearInterval(timerInterval)
  timerInterval = null
  elapsed.value = performance.now() - startTime
  timerState.value = 'idle'

  const record = {
    id: Date.now(),
    time_ms: Math.round(elapsed.value),
    scramble: scramble.value,
    cube_type: cubeType.value,
    method: method.value,
    timing_mode: 'manual',
    date: new Date().toISOString(),
  }

  history.value.unshift(record)
  saveToStorage()

  // 仅登录时同步后端，离线模式纯本地
  if (localStorage.getItem('token')) {
    createTimerRecord({
      cube_type: record.cube_type,
      method: record.method,
      time_ms: record.time_ms,
      scramble: record.scramble,
      timing_mode: 'manual',
    }).then(() => {
      if (recordsLoaded) loadRecords(true)
    }).catch(() => {})
  } else {
    if (recordsLoaded) loadRecords(true)
  }

  generateScramble()
}

// ─── 智能模式计算属性 ────────────────────────────────────
const smartTps = computed(() => {
    if (smartElapsed.value <= 0 || smartMoveCount.value <= 0) return '0.00'
    const tps = smartMoveCount.value / (smartElapsed.value / 1000)
    return tps.toFixed(2)
})

// ─── 统计计算（基于今日记录，排除 DNF）──────────────────────────
const validTodayRecords = computed(() =>
  todayHistory.value.filter(r => r.penalty !== 'dnf' && !r.is_dnf && r.time_ms > 0)
)

const bestTime = computed(() => {
  if (validTodayRecords.value.length === 0) return null
  return Math.min(...validTodayRecords.value.map(r => r.time_ms))
})

const ao5 = computed(() => calculateAoN(5))
const ao12 = computed(() => calculateAoN(12))

function calculateAoN(n) {
  if (validTodayRecords.value.length < n) return null
  const recent = validTodayRecords.value.slice(0, n).map(r => r.time_ms)
  if (recent.length < 3) return null
  recent.sort((a, b) => a - b)
  const trimmed = recent.slice(1, -1)
  return Math.round(trimmed.reduce((a, b) => a + b, 0) / trimmed.length)
}

// ─── 今日记录过滤 ────────────────────────────────────
function isToday(record) {
  const dateStr = record.date || record.created_at
  if (!dateStr) return true
  const today = new Date()
  const d = new Date(dateStr)
  return d.getFullYear() === today.getFullYear()
    && d.getMonth() === today.getMonth()
    && d.getDate() === today.getDate()
}

const todayHistory = computed(() => history.value.filter(r => isToday(r)))
const displayTodayHistory = computed(() => todayHistory.value.slice(0, 50))

function showDetail(record) {
  detailRecord.value = record
  detailShow.value = true
}

// 切换 +2 判罚
function togglePlus2() {
  if (!detailRecord.value) return
  const r = detailRecord.value
  const isPlus2 = r.penalty === 'plus2'

  if (isPlus2) {
    // 取消 +2
    r.penalty = null
    r.time_ms -= 2000
    if (r.time_ms < 0) r.time_ms = 0
  } else {
    // 加 +2（先取消 DNF 如果有的话）
    if (r.penalty === 'dnf' || r.is_dnf) {
      r.penalty = 'plus2'
      r.is_dnf = false
      if (r.time_ms === 0) r.time_ms = 2000
      else r.time_ms += 2000
    } else {
      r.penalty = 'plus2'
      r.time_ms += 2000
    }
  }

  saveToStorage()
  // 同步后端
  if (r.server_id) {
    // TODO: 后端更新判罚接口
  }
  // 强制触发响应式更新
  detailRecord.value = { ...r }
}

// 切换 DNF 判罚
function toggleDNF() {
  if (!detailRecord.value) return
  const r = detailRecord.value
  const isDNF = r.penalty === 'dnf' || r.is_dnf

  if (isDNF) {
    // 取消 DNF，恢复时间
    r.penalty = null
    r.is_dnf = false
    // 从 solve_sequence 估算时间？暂时保留原 time_ms（如果之前存了的话）
    if (!r.original_time_ms) r.original_time_ms = r.time_ms
    r.time_ms = r.original_time_ms || r.time_ms
  } else {
    // 标记 DNF
    r.original_time_ms = r.time_ms
    r.penalty = 'dnf'
    r.is_dnf = true
  }

  saveToStorage()
  detailRecord.value = { ...r }
}

function deleteRecord(index) {
  const record = history.value[index]
  showConfirm({
    title: '删除记录',
    message: `确认删除 ${formatTime(record.time_ms)} 的记录？`,
    confirmText: '删除',
    icon: 'delete-o',
    onConfirm: () => {
      history.value.splice(index, 1)
      saveToStorage()
      if (record.server_id) {
        deleteTimerRecord(record.server_id).catch(() => {})
      }
      showToast({ type: 'success', message: '已删除' })
    },
  })
}

function confirmClear() {
  showConfirm({
    title: '清空本地记录',
    message: `确认清空全部 ${history.value.length} 条本地记录？仅清除本机保存的数据，不影响已同步到服务器的记录。此操作不可撤销。`,
    confirmText: '清空',
    icon: 'delete',
    onConfirm: () => {
      history.value = []
      saveToStorage()
      showToast({ type: 'success', message: '已清空' })
    },
  })
}

// ─── 数据记录（后端 / 本地降级） ──────────────────────
async function loadRecords(reset = false) {
  // 无 Token 时使用本地记录
  if (!localStorage.getItem('token')) {
    recordList.value = history.value.slice()
    recordFinished.value = true
    recordLoading.value = false
    return
  }

  if (reset) {
    recordPage.value = 1
    recordFinished.value = false
    recordLoading.value = true
  }

  try {
    const params = { page: recordPage.value, page_size: recordPageSize }
    if (recordCubeType.value) params.cube_type = recordCubeType.value

    const res = await getTimerRecords(params)
    const results = res.data?.results || res.data || []

    if (reset) {
      recordList.value = results
    } else {
      recordList.value.push(...results)
    }

    const count = res.data?.count || results.length
    if (recordList.value.length >= count || results.length < recordPageSize) {
      recordFinished.value = true
    } else {
      recordPage.value++
    }
  } catch {
    // 后端请求失败时降级到本地记录
    recordList.value = history.value.slice()
    recordFinished.value = true
  } finally {
    recordLoading.value = false
  }
}

function onRecordFilterChange() {
  loadRecords(true)
}

function onRecordRefresh() {
  loadRecords(true)
  recordRefreshing.value = false
}

async function onPageRefresh() {
  generateScramble()
  if (recordsLoaded) {
    await loadRecords(true)
  }
  pageRefreshing.value = false
}

function confirmDeleteRecord(record, index) {
  showConfirm({
    title: '删除记录',
    message: `确认删除 ${formatTime(record.time_ms)} 的记录？`,
    confirmText: '删除',
    icon: 'delete-o',
    onConfirm: async () => {
      try {
        await deleteTimerRecord(record.id)
        recordList.value.splice(index, 1)
        showToast({ type: 'success', message: '已删除' })
      } catch {}
    },
  })
}

function onTabChange() {
  // 兼容旧调用，空实现
}

function scrollToRecords() {
  if (!recordsLoaded) {
    recordsLoaded = true
    loadRecords(true)
  }
  nextTick(() => {
    recordsSection.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

// ─── localStorage 持久化 ────────────────────────────
function saveToStorage() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history.value))
  } catch {}
}

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) history.value = JSON.parse(raw)
  } catch {
    history.value = []
  }
}

// ─── 工具函数 ────────────────────────────────────────
function formatTime(ms) {
  if (ms == null) return '--'
  const totalSeconds = ms / 1000
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = Math.floor(totalSeconds % 60)
  const millis = Math.floor(ms % 1000)
  if (minutes > 0) {
    return `${minutes}:${String(seconds).padStart(2, '0')}.${String(millis).padStart(3, '0')}`
  }
  return `${seconds}.${String(millis).padStart(3, '0')}`
}

function formatDateTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${h}:${m}`
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${month}-${day}`
}

function methodLabel(m) {
  const found = methodOptions.find(o => o.value === m)
  return found ? found.text : m
}

// ─── 监听 route.query.tab ───────────────────────────
watch(() => route.query.tab, (tab) => {
  if (tab === 'records') {
    scrollToRecords()
  }
}, { immediate: true })

// ─── 生命周期 ────────────────────────────────────────
onMounted(() => {
  loadFromStorage()
  generateScramble()
})

// 智能模式：打乱公式变化时，3D 魔方执行打乱动画
watch(scramble, (newScramble) => {
    if (timingMode.value === 'smart' && cube3dRef.value && newScramble) {
        // 先重置到复原状态，再执行打乱动画
        cube3dRef.value.reset()
        nextTick(() => {
            cube3dRef.value.rotateSequence(newScramble)
        })
    }
})

onBeforeUnmount(() => {
  if (timerInterval) clearInterval(timerInterval)
  if (holdTimer) clearTimeout(holdTimer)
  if (smartTimerInterval) clearInterval(smartTimerInterval)
  if (smartObservationInterval) clearInterval(smartObservationInterval)
})
</script>

<style scoped>
.page {
  min-height: 100%;
}

/* 页面容器 */
.timer-tab {
  display: flex;
  flex-direction: column;
  padding-bottom: 16px;
}

/* 模式切换 */
.mode-tabs {
  margin: 0 12px;
}

/* 打乱导航 */
.scramble-nav {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 8px;
}

.scramble-nav-btn {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: var(--van-background-2);
  color: var(--van-text-color);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.scramble-nav-btn:active {
  background: var(--van-active-color);
}

.scramble-nav-btn.disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* 连接状态条 */
.connect-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  margin: 8px 12px;
  background: var(--van-background-2);
  border-radius: 8px;
}

.connect-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.connect-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot-connected {
  background: #07c160;
  box-shadow: 0 0 6px #07c160;
}

.dot-disconnected {
  background: #c8c9cc;
}

.connect-text {
  font-size: 0.85rem;
  color: var(--van-text-color);
}

.connect-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.battery-info {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.8rem;
  color: var(--van-text-color-2);
}

.battery-text {
  font-variant-numeric: tabular-nums;
}

/* 3D 魔方容器 */
.cube-3d-wrap {
  display: flex;
  justify-content: center;
  padding: 8px 0 4px;
  position: relative;
}

.cube-toolbar {
  position: absolute;
  top: 12px;
  right: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 10;
}

.cube-tool-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.cube-tool-btn:active {
  background: rgba(0, 0, 0, 0.7);
}

.cube-tool-btn.active {
  background: #1989fa;
}

/* 智能模式计时显示 */
.smart-timer-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 16px 28px;
}

.smart-time {
  font-size: 3rem;
  font-weight: 300;
  font-variant-numeric: tabular-nums;
  letter-spacing: 2px;
  color: var(--van-text-color);
  transition: color 0.3s;
}

.smart-time-scrambling {
  color: #ff976a;
}

.smart-time-ready {
  color: #07c160;
}

.smart-time-observation {
  color: #ff976a;
  font-size: 2.5rem;
}

.smart-time-solving {
  color: #1989fa;
}

.smart-time-solved {
  color: #07c160;
  font-weight: 500;
}

.smart-time-dnf {
  color: #ee0a24;
  font-size: 2.5rem;
}

/* DNF 徽章 */
.dnf-badge {
  display: inline-block;
  padding: 2px 10px;
  background: #ee0a24;
  color: #fff;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 4px;
  margin-bottom: 8px;
}

.smart-timer-hint {
  font-size: 0.85rem;
  color: var(--van-text-color-2);
  margin-top: 8px;
}

/* 智能模式实时数据栏 */
.smart-stats-row {
  display: flex;
  gap: 24px;
  margin-top: 12px;
}

.smart-stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.smart-stat-value {
  font-size: 1.3rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--van-text-color);
}

.smart-stat-label {
  font-size: 0.7rem;
  color: var(--van-text-color-2);
  margin-top: 2px;
}

.type-selector {
  margin: 0 12px 8px;
  border-radius: 8px;
  overflow: hidden;
}

/* 统计面板 */
.stats-panel {
  display: flex;
  justify-content: space-around;
  padding: 12px 16px;
  margin: 8px 12px;
  background: var(--van-background-2);
  border-radius: 8px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-value {
  font-size: 1.3rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--van-text-color);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--van-text-color-2);
}

/* 本地历史记录 */
.history-section {
  margin: 8px 12px 16px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding: 0 4px;
}

.history-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--van-text-color);
}

.history-list {
  max-height: 30vh;
  overflow-y: auto;
  border-radius: 8px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: var(--van-background-2);
  border-bottom: 1px solid var(--van-border-color);
  cursor: pointer;
}

.history-index {
  font-size: 0.8rem;
  color: var(--van-text-color-2);
  min-width: 36px;
}

.history-time {
  font-size: 1rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--van-text-color);
}

.dnf-time {
  color: #ee0a24 !important;
}

.history-type {
  font-size: 0.75rem;
  color: var(--van-text-color-2);
  margin-left: auto;
}

.delete-btn {
  height: 100%;
}

/* 数据记录区域 */
.records-section {
  margin: 8px 12px 16px;
  scroll-margin-top: 10px;
}

.records-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.records-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--van-text-color);
}

.records-filter {
  flex: 0 0 auto;
  box-shadow: none;
}
.records-filter :deep(.van-dropdown-menu__bar) {
  box-shadow: none;
  background: transparent;
}

.record-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  background: var(--van-background-2);
  border-bottom: 1px solid var(--van-border-color);
  cursor: pointer;
}

.record-time {
  font-size: 1rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--van-text-color);
  min-width: 64px;
  flex-shrink: 0;
}

.record-meta {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.7rem;
  color: var(--van-text-color-2);
  flex-wrap: nowrap;
  overflow: hidden;
}

.record-method {
  margin-left: 2px;
  flex-shrink: 0;
}

.record-moves {
  color: var(--van-primary-color);
  font-weight: 500;
  flex-shrink: 0;
}

.record-date {
  margin-left: auto;
  flex-shrink: 0;
  font-size: 0.7rem;
  color: var(--van-text-color-3);
}

/* 详情弹窗 */
.detail-card {
  padding: 20px 16px;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.detail-time {
  font-size: 1.8rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--van-text-color);
}

.plus2-suffix {
  font-size: 1rem;
  color: #ff976a;
  margin-left: 4px;
}

.detail-penalty-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  padding: 12px 0 4px;
}

.detail-date {
  font-size: 0.8rem;
  color: var(--van-text-color-3);
  margin-bottom: 16px;
}

.detail-section {
  background: var(--van-background);
  border-radius: 8px;
  padding: 12px 16px;
}

.detail-label {
  font-size: 0.75rem;
  color: var(--van-text-color-2);
  margin-bottom: 6px;
}

.detail-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.detail-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 26px;
  padding: 0 6px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
  font-family: "Cascadia Code", "Consolas", monospace;
  color: #fff;
  background: #909399;
}

.solve-chip {
  background: #409eff;
}

.detail-empty {
  font-size: 0.85rem;
  color: var(--van-text-color-3);
}

.dnf-time {
  color: var(--van-danger-color) !important;
}

.detail-stats {
  display: flex;
  gap: 16px;
  padding: 8px 0;
  font-size: 0.85rem;
  color: var(--van-text-color-2);
  font-variant-numeric: tabular-nums;
}

.record-moves {
  color: var(--van-primary-color);
  font-weight: 500;
}
</style>
