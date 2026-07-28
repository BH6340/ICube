<template>
  <div class="my-data-container">
    <div class="filter-section">
      <el-card shadow="never">
        <el-form :model="filterForm" inline>
          <el-form-item label="魔方类型">
            <el-select v-model="filterForm.cube_type" placeholder="全部" clearable>
              <el-option label="二阶魔方" value="2x2" />
              <el-option label="三阶魔方" value="3x3" />
              <el-option label="四阶魔方" value="4x4" />
              <el-option label="五阶魔方" value="5x5" />
            </el-select>
          </el-form-item>
          <el-form-item label="还原方法">
            <el-select v-model="filterForm.method" placeholder="全部" clearable>
              <el-option label="层先法" value="layer" />
              <el-option label="CFOP" value="cfop" />
              <el-option label="桥式" value="roux" />
              <el-option label="ZBLL" value="zbll" />
            </el-select>
          </el-form-item>
          <el-form-item label="日期范围">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadData">查询</el-button>
            <el-button @click="resetFilter">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <div class="stats-section">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="6">
          <el-card shadow="never" class="stat-card">
            <div class="stat-num">{{ stats.total_count }}</div>
            <div class="stat-label">总还原次数</div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="6">
          <el-card shadow="never" class="stat-card">
            <div class="stat-num best">{{ formatTime(stats.best_time) }}</div>
            <div class="stat-label">最快成绩</div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="6">
          <el-card shadow="never" class="stat-card">
            <div class="stat-num">{{ formatTime(stats.avg_time) }}</div>
            <div class="stat-label">平均成绩</div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="6">
          <el-card shadow="never" class="stat-card">
            <div class="stat-num">{{ groupStats.length }}</div>
            <div class="stat-label">分组数量</div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <div class="chart-section">
      <el-card shadow="never">
        <template #header>
          <span>成绩趋势（最近30天）</span>
        </template>
        <div ref="chartRef" class="chart-container"></div>
      </el-card>
    </div>

    <div class="group-section">
      <el-card shadow="never">
        <template #header>
          <span>分组统计</span>
        </template>
        <el-table :data="groupStats" border>
          <el-table-column prop="cube_type_label" label="魔方类型" />
          <el-table-column prop="method_label" label="还原方法" />
          <el-table-column prop="total_count" label="次数" />
          <el-table-column prop="best_time" label="最快(秒)">
            <template #default="scope">
              {{ formatTime(scope.row.best_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="avg_time" label="平均(秒)">
            <template #default="scope">
              {{ formatTime(scope.row.avg_time) }}
            </template>
          </el-table-column>
        </el-table>
        <div v-if="groupStats.length === 0" class="empty-tip">暂无分组数据</div>
      </el-card>
    </div>

    <div class="records-section">
      <el-card shadow="never">
        <template #header>
          <span>成绩记录</span>
        </template>
        <el-table :data="records" border>
          <el-table-column prop="created_at" label="日期">
            <template #default="scope">
              {{ formatDate(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="cube_type" label="魔方类型">
            <template #default="scope">
              {{ getCubeTypeLabel(scope.row.cube_type) }}
            </template>
          </el-table-column>
          <el-table-column prop="method" label="还原方法">
            <template #default="scope">
              {{ getMethodLabel(scope.row.method) }}
            </template>
          </el-table-column>
          <el-table-column prop="time_ms" label="成绩(秒)">
            <template #default="scope">
              {{ formatTime(scope.row.time_ms) }}
            </template>
          </el-table-column>
          <el-table-column prop="scramble" label="打乱公式" show-overflow-tooltip />
          <el-table-column label="操作">
            <template #default="scope">
              <el-button type="danger" size="small" link @click="deleteRecord(scope.row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div v-if="records.length === 0" class="empty-tip">暂无成绩记录</div>
        <el-pagination
          v-if="pagination.total > 0"
          :current-page="pagination.page"
          :page-size="pagination.page_size"
          :total="pagination.total"
          layout="prev, pager, next, jumper, ->, total"
          @current-change="handlePageChange"
        />
      </el-card>
    </div>
  </div>
</template>

<script setup>
/**
 * MyDataView.vue - 我的数据统计页面
 *
 * 核心职责：
 * 1. 展示用户计时记录列表和统计数据
 * 2. 使用 ECharts 可视化展示成绩趋势图
 * 3. 支持按魔方类型、方法、日期范围筛选
 * 4. 支持删除错误的计时记录
 *
 * 功能特性：
 *   - 统计卡片：总次数、最佳成绩、平均成绩
 *   - 趋势折线图：展示成绩变化
 *   - 筛选条件联动刷新图表和列表
 *
 * 设计要点：
 *   - 使用 echarts 渲染趋势图，组件卸载时销毁实例
 *   - chartInstance 保存图表引用，避免重复初始化
 */
import { ref, reactive, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import { getTimerRecords, getTimerStats, getTimerTrend, deleteTimerRecord } from '@/api/timer'

const chartRef = ref(null)
let chartInstance = null

const filterForm = reactive({
  cube_type: '',
  method: ''
})

const dateRange = ref([])

const stats = reactive({
  total_count: 0,
  best_time: 0,
  avg_time: 0
})

const groupStats = ref([])
const records = ref([])
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const CUBE_TYPE_MAP = {
  '2x2': '二阶魔方',
  '3x3': '三阶魔方',
  '4x4': '四阶魔方',
  '5x5': '五阶魔方',
  'other': '其他'
}

const METHOD_MAP = {
  'layer': '层先法',
  'cfop': 'CFOP',
  'roux': '桥式',
  'zbll': 'ZBLL',
  'other': '其他'
}

const formatTime = (ms) => {
  if (!ms || ms === 0) return '-'
  const totalSeconds = ms / 1000
  if (totalSeconds < 60) {
    return totalSeconds.toFixed(2)
  }
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = (totalSeconds % 60).toFixed(2)
  return `${minutes}:${seconds.padStart(5, '0')}`
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const getCubeTypeLabel = (type) => CUBE_TYPE_MAP[type] || type
const getMethodLabel = (method) => METHOD_MAP[method] || method

const loadData = () => {
  loadStats()
  loadRecords()
  loadTrend()
}

const loadStats = async () => {
  const params = { ...filterForm }
  if (dateRange.value.length === 2) {
    params.start_date = dateRange.value[0]
    params.end_date = dateRange.value[1]
  }
  try {
    const res = await getTimerStats(params)
    stats.total_count = res.data.overall_stats.total_count
    stats.best_time = res.data.overall_stats.best_time
    stats.avg_time = res.data.overall_stats.avg_time
    groupStats.value = res.data.group_stats
  } catch (error) {
    console.error('加载统计数据失败', error)
  }
}

const loadRecords = async () => {
  const params = {
    ...filterForm,
    page: pagination.page,
    page_size: pagination.page_size
  }
  if (dateRange.value.length === 2) {
    params.start_date = dateRange.value[0]
    params.end_date = dateRange.value[1]
  }
  try {
    const res = await getTimerRecords(params)
    records.value = res.data.results || res.data
    pagination.total = res.data.count || 0
  } catch (error) {
    console.error('加载记录失败', error)
  }
}

const loadTrend = async () => {
  const params = { ...filterForm, days: 30 }
  if (dateRange.value.length === 2) {
    params.start_date = dateRange.value[0]
    params.end_date = dateRange.value[1]
  }
  try {
    const res = await getTimerTrend(params)
    renderChart(res.data)
  } catch (error) {
    console.error('加载趋势数据失败', error)
  }
}

const renderChart = (data) => {
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const xAxisData = data.map(item => {
    const date = new Date(item.date)
    return `${date.getMonth() + 1}/${date.getDate()}`
  })

  const bestTimes = data.map(item => (item.best_time / 1000).toFixed(2))
  const avgTimes = data.map(item => (item.avg_time / 1000).toFixed(2))

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        let result = `<div style="font-weight:bold;margin-bottom:8px;">${params[0].axisValue}</div>`
        params.forEach(param => {
          result += `<div>${param.marker} ${param.seriesName}: ${param.value}秒</div>`
        })
        return result
      }
    },
    legend: {
      data: ['最快成绩', '平均成绩'],
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      axisLabel: {
        rotate: 45,
        fontSize: 11
      }
    },
    yAxis: {
      type: 'value',
      name: '时间(秒)',
      axisLabel: {
        formatter: '{value}'
      }
    },
    series: [
      {
        name: '最快成绩',
        type: 'line',
        data: bestTimes,
        smooth: true,
        lineStyle: {
          color: '#67c23a',
          width: 2
        },
        itemStyle: {
          color: '#67c23a'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
            { offset: 1, color: 'rgba(103, 194, 58, 0.05)' }
          ])
        }
      },
      {
        name: '平均成绩',
        type: 'line',
        data: avgTimes,
        smooth: true,
        lineStyle: {
          color: '#409eff',
          width: 2
        },
        itemStyle: {
          color: '#409eff'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
          ])
        }
      }
    ]
  }

  chartInstance.setOption(option)
}

const handlePageChange = (page) => {
  pagination.page = page
  loadRecords()
}

const deleteRecord = (id) => {
  ElMessageBox.confirm('确定要删除这条记录吗？', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteTimerRecord(id)
      ElMessage.success('删除成功')
      loadData()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const resetFilter = () => {
  filterForm.cube_type = ''
  filterForm.method = ''
  dateRange.value = []
  pagination.page = 1
  loadData()
}

const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
  }
})

watch([() => filterForm.cube_type, () => filterForm.method, dateRange], () => {
  pagination.page = 1
})
</script>

<style scoped>
.my-data-container {
  padding: 20px 10px;
  max-width: 1200px;
  margin: 0 auto;
}

.filter-section {
  margin-bottom: 20px;
}

.stats-section {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-num {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 5px;
}

.stat-num.best {
  color: #67c23a;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.chart-section {
  margin-bottom: 20px;
}

.chart-container {
  height: 400px;
}

.group-section {
  margin-bottom: 20px;
}

.records-section {
  margin-bottom: 20px;
}

.empty-tip {
  text-align: center;
  color: #909399;
  padding: 40px;
}
</style>