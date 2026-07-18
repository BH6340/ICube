<template>
  <div class="timer-container" ref="timerPage" tabindex="0" @keydown="handleKeyDown" @keyup="handleKeyUp">
    <div class="scramble-section">
      <div class="scramble-header">
        <el-select v-model="cubeType" placeholder="选择魔方类型" style="width: 120px" @change="generateScramble">
          <el-option label="三阶魔方" value="3x3" />
          <el-option label="二阶魔方" value="2x2" />
          <el-option label="四阶魔方" value="4x4" />
        </el-select>
        <el-button type="primary" link @click="generateScramble">刷新打乱</el-button>
      </div>
      <div class="scramble-text">{{ currentScramble }}</div>
    </div>

    <el-row :gutter="30" class="main-layout">
      <el-col :xs="24" :sm="8" class="stats-panel">
        <el-card shadow="never" class="box-card">
          <template #header>
            <div class="card-header">
              <span>数据统计 </span>
              <el-button type="danger" link size="small" @click="clearHistory">清空列表</el-button>
            </div>
          </template>

          <div class="summary-stats">
            <p>还原次数: <strong>{{ history.length }}</strong></p>
            <p>当前单次最快: <span class="best-time">{{ bestTime }}</span></p>
            <p>当前 Ao5 (5次平均): <strong>{{ currentAo5 }}</strong></p>
            <p>当前 Ao12 (12次平均): <strong>{{ currentAo12 }}</strong></p>
          </div>

          <el-divider style="margin: 12px 0;" />

          <div class="history-list">
            <div v-for="(item, index) in history" :key="item.id" class="history-item">
              <span class="index">#{{ history.length - index }}</span>
              <span class="time">{{ formatTime(item.time) }}</span>
              <span class="scramble-tip" :title="item.scramble">打乱公式</span>
              <el-button type="danger" icon="Delete" circle size="small" link @click="deleteTime(index)" />
            </div>
            <div v-if="history.length === 0" class="empty-tip">暂无成绩，轻按空格开始</div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="16" class="timer-display-section">
        <div class="status-hint" :class="{ 'ready': timerState === 'ready', 'running': timerState === 'running' }">
          {{ statusText }}
        </div>

        <div class="time-banner" :class="timerState">
          {{ timeDisplay }}
        </div>

        <div class="instruction">
          PC端：长按【空格键】变绿后松开开始计时，再次轻按【空格键】停止。<br />
          移动端：直接点击上方大数字区域进行长按/松开操作。
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'

// --- 状态定义 ---
const timerPage = ref(null)
const cubeType = ref('3x3')
const currentScramble = ref('')
const history = ref(JSON.parse(localStorage.getItem('icube_timer_history') || '[]'))

// 计时器状态机: 'idle'(空闲), 'holding'(长按准备中), 'ready'(变绿准备就绪), 'running'(正在计时)
const timerState = ref('idle')
const startTime = ref(0)
const elapsedTime = ref(0)
const timerInterval = ref(null)
const holdTimer = ref(null)

// --- 核心：打乱公式生成器 (简易专业版) ---
const generateScramble = () => {
  const moves = {
    '2x2': ['U', "U'", 'U2', 'R', "R'", 'R2', 'F', "F'", 'F2'],
    '3x3': ['U', "U'", 'U2', 'D', "D'", 'D2', 'R', "R'", 'R2', 'L', "L'", 'L2', 'F', "F'", 'F2', 'B', "B'", 'B2'],
    '4x4': ['U', "U'", 'U2', 'D', "D'", 'D2', 'R', "R'", 'R2', 'L', "L'", 'L2', 'F', "F'", 'F2', 'B', "B'", 'B2', 'Uw', 'Rw', 'Fw']
  }

  const currentMoves = moves[cubeType.value]
  const length = cubeType.value === '2x2' ? 11 : cubeType.value === '4x4' ? 40 : 21 // 对应WCA标准步数
  let scramble = []
  let lastAxis = ''

  for (let i = 0; i < length; i++) {
    let move = currentMoves[Math.floor(Math.random() * currentMoves.length)]
    // 简单防重机制：防止连续出现同方向的面（如 R R' 或 R R2）
    while (move[0] === lastAxis) {
      move = currentMoves[Math.floor(Math.random() * currentMoves.length)]
    }
    scramble.push(move)
    lastAxis = move[0]
  }
  currentScramble.value = scramble.join(' ')
}

// --- 时间格式化工具 ---
const formatTime = (ms) => {
  if (ms === 0) return '0.00'
  const totalSeconds = ms / 1000
  if (totalSeconds < 60) {
    return totalSeconds.toFixed(2)
  }
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = (totalSeconds % 60).toFixed(2)
  return `${minutes}:${seconds.padStart(5, '0')}`
}

const timeDisplay = computed(() => formatTime(elapsedTime.value))

const statusText = computed(() => {
  if (timerState.value === 'holding') return '请按住...'
  if (timerState.value === 'ready') return '松开开始！'
  if (timerState.value === 'running') return '正在竞速...'
  return '准备就绪'
})

// --- 键盘事件监听（仿 csTimer 核心逻辑） ---
const handleKeyDown = (e) => {
  if (e.code !== 'Space') return
  e.preventDefault() // 阻止空格键网页滚动

  if (timerState.value === 'running') {
    // 1. 如果正在运行，敲击任意键/空格立刻停止
    stopTimer()
  } else if (timerState.value === 'idle') {
    // 2. 如果处于空闲，进入准备阶段
    timerState.value = 'holding'
    elapsedTime.value = 0

    // 必须长按超过 0.5 秒（红变绿），才算作有效准备，防止误触
    clearTimeout(holdTimer.value)
    holdTimer.value = setTimeout(() => {
      timerState.value = 'ready'
    }, 500)
  }
}

const handleKeyUp = (e) => {
  if (e.code !== 'Space') return
  e.preventDefault()

  if (timerState.value === 'ready') {
    // 长按时间足够，变绿后松开，开始计时
    startTimer()
  } else if (timerState.value === 'holding') {
    // 长按时间不足 0.5s 就松开了，视作无效，退回空闲
    clearTimeout(holdTimer.value)
    timerState.value = 'idle'
  }
}

// --- 计时器引擎 ---
const startTimer = () => {
  timerState.value = 'running'
  startTime.value = performance.now()
  timerInterval.value = setInterval(() => {
    elapsedTime.value = performance.now() - startTime.value
  }, 10) // 10ms 级高频刷新
}

const stopTimer = () => {
  clearInterval(timerInterval.value)
  timerState.value = 'idle'

  // 记录本次成绩
  const newRecord = {
    id: Date.now(),
    time: elapsedTime.value,
    scramble: currentScramble.value,
    date: new Date().toLocaleDateString()
  }
  // csTimer 新成绩压入到最前面
  history.value.unshift(newRecord)
  saveToLocalStorage()

  // 自动刷新下一把打乱
  generateScramble()
}

// --- WCA 成绩统计逻辑 (Ao5 / Ao12) ---
// WCA 规则：去一个最快，去一个最慢，剩下的取平均值
const calculateAoN = (n) => {
  if (history.value.length < n) return '-'
  // 取最近的 N 次成绩
  const recentTimes = history.value.slice(0, n).map(item => item.time)
  // 升序排列
  recentTimes.sort((a, b) => a - b)
  // 去头去尾
  const middleTimes = recentTimes.slice(1, n - 1)
  // 算平均数
  const sum = middleTimes.reduce((acc, curr) => acc + curr, 0)
  return formatTime(sum / (n - 2))
}

const currentAo5 = computed(() => calculateAoN(5))
const currentAo12 = computed(() => calculateAoN(12))

const bestTime = computed(() => {
  if (history.value.length === 0) return '-'
  const min = Math.min(...history.value.map(item => item.time))
  return formatTime(min)
})

// --- 数据管理 ---
const deleteTime = (index) => {
  history.value.splice(index, 1)
  saveToLocalStorage()
}

const clearHistory = () => {
  ElMessageBox.confirm('确定要清空所有计时历史记录吗？数据不可恢复！', '警告', {
    confirmButtonText: '确定清空',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    history.value = []
    saveToLocalStorage()
    ElMessage.success('已清空历史记录')
  }).catch(() => {})
}

const saveToLocalStorage = () => {
  localStorage.setItem('icube_timer_history', JSON.stringify(history.value))
}

// --- 生命周期钩子 ---
onMounted(() => {
  generateScramble()
  // 页面加载后自动让容器获得焦点，这样空格键能立刻生效
  if (timerPage.value) {
    timerPage.value.focus()
  }
})

onBeforeUnmount(() => {
  clearInterval(timerInterval.value)
  clearTimeout(holdTimer.value)
})
</script>

<style scoped>
/* 全局大容器 */
.timer-container {
  outline: none; /* 去除选中边框 */
  padding: 10px;
  min-height: 75vh;
}

/* 顶部打乱样式 */
.scramble-section {
  background-color: #f4f4f5;
  border-radius: 8px;
  padding: 15px;
  text-align: center;
  margin-bottom: 25px;
}
.scramble-header {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-bottom: 10px;
}
.scramble-text {
  font-family: 'Courier New', Courier, monospace;
  font-size: 20px;
  font-weight: bold;
  letter-spacing: 2px;
  color: #303133;
  line-height: 1.5;
}

/* 主主体布局 */
.main-layout {
  height: 100%;
}

/* 左侧数据栏 */
.stats-panel .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.summary-stats p {
  margin: 8px 0;
  font-size: 14px;
  color: #606266;
}
.best-time {
  color: #67c23a;
  font-weight: bold;
}
.history-list {
  max-height: 300px;
  overflow-y: auto;
}
.history-item {
  display: flex;
  align-items: center;
  padding: 6px 4px;
  border-bottom: 1px dashed #e4e7ed;
  font-size: 14px;
}
.history-item .index {
  color: #909399;
  width: 40px;
}
.history-item .time {
  font-weight: bold;
  flex-grow: 1;
}
.scramble-tip {
  font-size: 12px;
  color: #409eff;
  background-color: #ecf5ff;
  padding: 2px 6px;
  border-radius: 4px;
  cursor: help;
  margin-right: 10px;
}
.empty-tip {
  text-align: center;
  color: #909399;
  font-size: 13px;
  margin-top: 30px;
}

/* 右侧巨型时间面板 */
.timer-display-section {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  background-color: #fafafa;
  border-radius: 12px;
  border: 1px solid #eee;
}

.status-hint {
  font-size: 16px;
  color: #909399;
  margin-bottom: 10px;
  letter-spacing: 1px;
}
.status-hint.ready {
  color: #67c23a;
  font-weight: bold;
}
.status-hint.running {
  color: #f56c6c;
}

/* 仿 csTimer 时间红绿变色交互 */
.time-banner {
  font-family: 'Impact', 'Arial Black', sans-serif;
  font-size: 90px;
  letter-spacing: 2px;
  color: #303133;
  transition: color 0.1s ease;
  user-select: none;
}
/* 长按准备中变为红色 */
.time-banner.holding {
  color: #f56c6c;
}
/* 长按满0.5秒就绪变为绿色 */
.time-banner.ready {
  color: #67c23a;
}
/* 正在跑表时的时间颜色 */
.time-banner.running {
  color: #409eff;
}

.instruction {
  margin-top: 40px;
  font-size: 13px;
  color: #909399;
  text-align: center;
  line-height: 1.8;
}
</style>