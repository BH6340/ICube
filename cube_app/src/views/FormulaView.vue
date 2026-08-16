<script setup>
/**
 * FormulaView.vue - 移动端公式列表页
 *
 * 筛选：范围（全部/我的收藏）、分类、难度、排序。
 * 支持下拉刷新、上拉加载、搜索。
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import FormulaCard from '@/components/formula/FormulaCard.vue'
import { getFormulaList, getFormulaCategories, getMyCollections, addCollection, removeCollection } from '@/api/formula'

const router = useRouter()
const route = useRoute()

// ─── 筛选状态 ────────────────────────────────────────
const searchKeyword = ref('')
const selectedRange = ref('all')        // all / collected
const selectedCategory = ref('')
const selectedDifficulty = ref('')
const sortBy = ref('default')

const collectedOnly = computed(() => selectedRange.value === 'collected')

// 下拉选项
const rangeOptions = [
  { text: '全部公式', value: 'all' },
  { text: '我的收藏', value: 'collected' },
]
const categoryOptions = ref([{ text: '全部分类', value: '' }])
const difficultyOptions = [
  { text: '全部难度', value: '' },
  { text: '基础', value: 1 },
  { text: '进阶', value: 2 },
  { text: '困难', value: 3 }
]
const sortOptions = [
  { text: '默认排序', value: 'default' },
  { text: '难度升序', value: 'difficulty_asc' },
  { text: '难度降序', value: 'difficulty_desc' }
]

// ─── 列表状态 ────────────────────────────────────────
const formulaList = ref([])
const listLoading = ref(false)
const finished = ref(false)
const refreshing = ref(false)
const currentPage = ref(1)
const pageSize = 20

// 收藏状态
const collectedIds = ref(new Set())
const collectLoadingIds = ref(new Set())

onMounted(() => {
  // 从 ProfileView 跳转时带 filter=collected
  if (route.query.filter === 'collected') {
    selectedRange.value = 'collected'
  }
  loadCategories()
  loadCollections()
})

// 构建查询参数
function buildParams(page) {
  const params = { page, page_size: pageSize }
  if (selectedCategory.value) params.category = selectedCategory.value
  if (selectedDifficulty.value) params.difficulty = selectedDifficulty.value
  if (searchKeyword.value.trim()) params.search = searchKeyword.value.trim()
  if (sortBy.value !== 'default') {
    params.ordering = sortBy.value === 'difficulty_asc' ? 'difficulty' : '-difficulty'
  }
  return params
}

async function loadCategories() {
  try {
    const res = await getFormulaCategories()
    const cats = res.data.results || res.data || []
    categoryOptions.value = [
      { text: '全部分类', value: '' },
      ...cats.map(c => ({ text: c.name, value: c.id }))
    ]
  } catch {
    // request.js 已统一处理错误提示
  }
}

async function loadCollections() {
  if (!localStorage.getItem('token')) return
  try {
    const res = await getMyCollections()
    const items = res.data.results || res.data || []
    collectedIds.value = new Set(items.map(c => c.id))
  } catch {
    // 收藏加载失败不阻塞列表展示
  }
}

// van-list @load
async function loadMore() {
  if (collectedOnly.value && !localStorage.getItem('token')) {
    showToast('请先登录')
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    finished.value = true
    listLoading.value = false
    return
  }

  try {
    const params = buildParams(currentPage.value)
    const res = collectedOnly.value
      ? await getMyCollections(params)
      : await getFormulaList(params)
    const results = res.data?.results || res.data || []

    if (currentPage.value === 1) {
      formulaList.value = results
    } else {
      formulaList.value.push(...results)
    }

    const count = res.data?.count || results.length
    if (formulaList.value.length >= count || results.length < pageSize) {
      finished.value = true
    } else {
      currentPage.value++
    }
  } catch {
    finished.value = true
  } finally {
    listLoading.value = false
  }
}

// ─── 事件处理 ────────────────────────────────────────
function onSearch() {
  resetList()
}

function onFilterChange() {
  resetList()
}

function onRangeChange() {
  resetList()
}

function onRefresh() {
  resetList()
  refreshing.value = false
}

function resetList() {
  formulaList.value = []
  currentPage.value = 1
  finished.value = false
  listLoading.value = true
  loadMore()
}

function goDetail(formula) {
  router.push(`/formula/${formula.id}`)
}

async function toggleCollect(formula) {
  if (!localStorage.getItem('token')) {
    showToast('请先登录')
    router.push({ name: 'login', query: { redirect: '/formula' } })
    return
  }

  if (collectLoadingIds.value.has(formula.id)) return
  collectLoadingIds.value.add(formula.id)

  try {
    if (collectedIds.value.has(formula.id)) {
      await removeCollection(formula.id)
      collectedIds.value = new Set([...collectedIds.value].filter(id => id !== formula.id))
      if (collectedOnly.value) {
        formulaList.value = formulaList.value.filter(f => f.id !== formula.id)
      }
      showToast({ type: 'success', message: '已取消收藏' })
    } else {
      await addCollection(formula.id)
      await loadCollections()
      showToast({ type: 'success', message: '收藏成功' })
    }
  } catch {
    // request.js 已统一处理错误提示
  } finally {
    collectLoadingIds.value.delete(formula.id)
  }
}

// 监听 route.query.filter 变化（从个人中心跳转）
watch(() => route.query.filter, (filter) => {
  selectedRange.value = filter === 'collected' ? 'collected' : 'all'
  resetList()
})
</script>

<template>
  <div class="formula-page">
    <van-nav-bar :title="collectedOnly ? '我的收藏' : '公式库'" placeholder />

    <!-- 搜索栏 -->
    <van-search
      v-model="searchKeyword"
      :placeholder="collectedOnly ? '搜索收藏的公式' : '搜索公式、作者或分类'"
      shape="round"
      @search="onSearch"
      @clear="onSearch"
    />

    <!-- 筛选下拉菜单 -->
    <van-dropdown-menu>
      <van-dropdown-item v-model="selectedRange" :options="rangeOptions" @change="onRangeChange" />
      <van-dropdown-item v-model="selectedCategory" :options="categoryOptions" @change="onFilterChange" />
      <van-dropdown-item v-model="selectedDifficulty" :options="difficultyOptions" @change="onFilterChange" />
      <van-dropdown-item v-model="sortBy" :options="sortOptions" @change="onFilterChange" />
    </van-dropdown-menu>

    <!-- 公式列表（下拉刷新 + 上拉加载） -->
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh" class="list-container">
      <van-list
        v-model:loading="listLoading"
        :finished="finished"
        finished-text="没有更多了"
        @load="loadMore"
      >
        <div class="card-list">
          <FormulaCard
            v-for="formula in formulaList"
            :key="formula.id"
            :formula="formula"
            :collected="collectedIds.has(formula.id)"
            @click="goDetail"
            @collect="toggleCollect"
          />
        </div>
        <van-empty v-if="!listLoading && formulaList.length === 0" :description="collectedOnly ? '暂无收藏公式' : '暂无公式数据'" />
      </van-list>
    </van-pull-refresh>
  </div>
</template>

<style scoped>
.formula-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f7f8fa;
}

.list-container {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.card-list {
  padding: 8px 12px;
}
</style>
