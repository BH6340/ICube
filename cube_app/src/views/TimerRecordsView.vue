<script setup>
/**
 * TimerRecordsView.vue — 我的计时记录页
 *
 * 从后端加载计时记录，支持分页、筛选、查看详情。
 */
defineOptions({ name: 'TimerRecordsView' })

import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { getTimerRecords, deleteTimerRecord } from '@/api/timer'

const router = useRouter()

const recordList = ref([])
const loading = ref(false)
const finished = ref(false)
const page = ref(1)
const pageSize = 20

// 筛选
const cubeType = ref('')
const cubeOptions = [
  { text: '全部类型', value: '' },
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

// 详情弹窗
const detailShow = ref(false)
const detailRecord = ref(null)

// ─── 数据加载 ────────────────────────────────────────
async function loadRecords(reset = false) {
  if (reset) {
    page.value = 1
    finished.value = false
    loading.value = true
  }

  try {
    const params = { page: page.value, page_size: pageSize }
    if (cubeType.value) params.cube_type = cubeType.value

    const res = await getTimerRecords(params)
    const results = res.data?.results || res.data || []

    if (reset) {
      recordList.value = results
    } else {
      recordList.value.push(...results)
    }

    const count = res.data?.count || results.length
    if (recordList.value.length >= count || results.length < pageSize) {
      finished.value = true
    }
  } catch {
    finished.value = true
  } finally {
    loading.value = false
  }
}

function onLoad() {
  if (finished.value) return
  page.value++
  loadRecords()
}

function onFilterChange() {
  loadRecords(true)
}

// ─── 事件处理 ────────────────────────────────────────
function showDetail(record) {
  detailRecord.value = record
  detailShow.value = true
}

function confirmDelete(record, index) {
  showConfirmDialog({
    title: '删除记录',
    message: '确认删除这条计时记录？',
  }).then(async () => {
    try {
      await deleteTimerRecord(record.id)
      recordList.value.splice(index, 1)
      showToast({ type: 'success', message: '已删除' })
    } catch {
      // request.js 已统一处理
    }
  }).catch(() => {})
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

// ─── 生命周期 ────────────────────────────────────────
onMounted(() => {
  if (!localStorage.getItem('token')) {
    showToast('请先登录')
    router.push({ name: 'login', query: { redirect: '/timer-records' } })
    return
  }
  loadRecords(true)
})
</script>

<template>
  <div class="page">
    <van-nav-bar title="我的记录" left-arrow @click-left="router.back()" placeholder />

    <!-- 筛选 -->
    <van-dropdown-menu>
      <van-dropdown-item v-model="cubeType" :options="cubeOptions" @change="onFilterChange" />
    </van-dropdown-menu>

    <!-- 记录列表 -->
    <div class="list-container">
      <van-list
        v-model:loading="loading"
        :finished="finished"
        finished-text="没有更多了"
        @load="onLoad"
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
            <van-button square type="danger" text="删除" class="delete-btn" @click="confirmDelete(record, index)" />
          </template>
        </van-swipe-cell>
        <van-empty v-if="!loading && recordList.length === 0" description="暂无计时记录" />
      </van-list>
    </div>

    <!-- 详情弹窗 -->
    <van-popup v-model:show="detailShow" position="bottom" round closeable :style="{ maxHeight: '70%' }">
      <div v-if="detailRecord" class="detail-card">
        <div class="detail-header">
          <span class="detail-time">{{ formatTime(detailRecord.time_ms) }}</span>
          <van-tag type="primary" size="medium">{{ detailRecord.cube_type }}</van-tag>
          <van-tag plain type="primary" size="medium">{{ methodLabel(detailRecord.method) }}</van-tag>
        </div>
        <div class="detail-date">{{ formatDateTime(detailRecord.created_at) }}</div>
        <div class="detail-section">
          <div class="detail-label">打乱公式</div>
          <div class="detail-scramble">{{ detailRecord.scramble || '未记录' }}</div>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<style scoped>
.page {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.list-container {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
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

.delete-btn {
  height: 100%;
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
