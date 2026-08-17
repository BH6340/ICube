<template>
  <div class="page">
    <div class="timer-tab">
      <van-nav-bar title="计时" placeholder />
      <ScrambleText :scramble="scramble" @refresh="generateScramble" />

      <van-dropdown-menu class="type-selector">
        <van-dropdown-item v-model="cubeType" :options="cubeOptions" @change="onTypeChange" />
        <van-dropdown-item v-model="method" :options="methodOptions" />
      </van-dropdown-menu>

      <TimerDisplay
        :state="timerState"
        :elapsed="elapsed"
        @touchstart="onTouchStart"
        @touchend="onTouchEnd"
      />

      <!-- 统计面板 -->
      <div class="stats-panel">
        <div class="stat-item">
          <span class="stat-value">{{ history.length }}</span>
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
      </div>

      <!-- 本地历史记录 -->
      <div class="history-section">
        <div class="history-header">
          <span class="history-title">历史记录</span>
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
            v-for="(record, index) in displayHistory"
            :key="record.id"
          >
            <div class="history-item" @click="showDetail(record)">
              <span class="history-index">#{{ history.length - index }}</span>
              <span class="history-time">{{ formatTime(record.time_ms) }}</span>
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
          <van-empty v-if="history.length === 0" description="暂无记录" image-size="60" />
        </div>
      </div>

      <!-- 数据记录（合并到历史记录下方） -->
      <div ref="recordsSection" class="records-section">
        <div class="records-header">
          <span class="records-title">数据记录</span>
          <van-dropdown-menu class="records-filter">
            <van-dropdown-item v-model="recordCubeType" :options="recordCubeOptions" @change="onRecordFilterChange" />
          </van-dropdown-menu>
        </div>

        <van-pull-refresh v-model="recordRefreshing" @refresh="onRecordRefresh">
          <van-list
            v-model:loading="recordLoading"
            :finished="recordFinished"
            finished-text="没有更多了"
            @load="loadRecords"
            :immediate-check="false"
          >
            <van-swipe-cell v-for="(record, index) in recordList" :key="record.id">
              <div class="record-item" @click="showDetail(record)">
                <span class="record-time">{{ formatTime(record.time_ms) }}</span>
                <div class="record-meta">
                  <van-tag type="primary" size="mini">{{ record.cube_type }}</van-tag>
                  <span class="record-method">{{ methodLabel(record.method) }}</span>
                  <span class="record-date">{{ formatDateTime(record.created_at) }}</span>
                </div>
                <van-icon name="arrow" size="12" color="#c8c9cc" />
              </div>
              <template #right>
                <van-button square type="danger" text="删除" class="delete-btn" @click="confirmDeleteRecord(record, index)" />
              </template>
            </van-swipe-cell>
            <van-empty v-if="!recordLoading && recordList.length === 0" description="暂无计时记录" />
          </van-list>
        </van-pull-refresh>
      </div>
    </div>

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
          <span class="detail-time">{{ formatTime(detailRecord.time_ms) }}</span>
          <van-tag type="primary" size="medium">{{ detailRecord.cube_type }}</van-tag>
          <van-tag plain type="primary" size="medium">{{ methodLabel(detailRecord.method) }}</van-tag>
        </div>
        <div class="detail-date">{{ formatDateTime(detailRecord.date || detailRecord.created_at) }}</div>
        <div class="detail-section">
          <div class="detail-label">打乱公式</div>
          <div class="detail-scramble">{{ detailRecord.scramble || '未记录' }}</div>
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
import { showToast } from 'vant'
import ScrambleText from '@/components/timer/ScrambleText.vue'
import TimerDisplay from '@/components/timer/TimerDisplay.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { createTimerRecord, getTimerRecords, deleteTimerRecord } from '@/api/timer'

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
const cubeType = ref('3x3')
const method = ref('cfop')
const history = ref([])

const detailShow = ref(false)
const detailRecord = ref(null)

let startTime = 0
let timerInterval = null
let holdTimer = null

// ─── 数据记录状态 ────────────────────────────────────
const recordList = ref([])
const recordLoading = ref(false)
const recordFinished = ref(false)
const recordRefreshing = ref(false)
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
  scramble.value = result.join(' ')
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
    }).catch(() => {})
  }

  generateScramble()
}

// ─── 统计计算 ────────────────────────────────────────
const bestTime = computed(() => {
  if (history.value.length === 0) return null
  return Math.min(...history.value.map(r => r.time_ms))
})

const ao5 = computed(() => calculateAoN(5))

function calculateAoN(n) {
  if (history.value.length < n) return null
  const recent = history.value.slice(0, n).map(r => r.time_ms)
  recent.sort((a, b) => a - b)
  const trimmed = recent.slice(1, -1)
  return Math.round(trimmed.reduce((a, b) => a + b, 0) / trimmed.length)
}

// ─── 本地历史记录管理 ────────────────────────────────
const displayHistory = computed(() => history.value.slice(0, 50))

function showDetail(record) {
  detailRecord.value = record
  detailShow.value = true
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
    title: '清空记录',
    message: `确认清空全部 ${history.value.length} 条本地记录？此操作不可撤销。`,
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

onBeforeUnmount(() => {
  if (timerInterval) clearInterval(timerInterval)
  if (holdTimer) clearTimeout(holdTimer)
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
}

.record-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--van-background-2);
  border-bottom: 1px solid var(--van-border-color);
  cursor: pointer;
}

.record-time {
  font-size: 1.1rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--van-text-color);
  min-width: 80px;
}

.record-meta {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  color: var(--van-text-color-2);
}

.record-method {
  margin-left: 4px;
}

.record-date {
  margin-left: auto;
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

.detail-scramble {
  font-size: 0.9rem;
  font-family: "Cascadia Code", "Consolas", monospace;
  line-height: 1.6;
  color: var(--van-text-color);
  word-break: break-all;
}
</style>
