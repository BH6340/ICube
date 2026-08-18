<script setup>
/**
 * FormulaView.vue - 移动端公式列表页
 *
 * 筛选：范围（全部/我的收藏/我的下载）、分类、难度、排序。
 * 支持下拉刷新、上拉加载、搜索、长按多选、创建公式。
 */
import { ref, computed, onMounted, watch, onActivated, onDeactivated, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera'
import FormulaCard from '@/components/formula/FormulaCard.vue'
import NotationKeyboard from '@/components/formula/NotationKeyboard.vue'
import ImageCropper from '@/components/ImageCropper.vue'
import FreeCropper from '@/components/FreeCropper.vue'
import { cropAndCompress } from '@/utils/image-compress'
import { preprocessImage, multiPassOCR } from '@/utils/ocr-helper'
import { buildMediaUrl } from '@/utils/media-url'
import { getFormulaList, getFormulaCategories, getMyCollections, getMyCustomFormulas, addCollection, removeCollection, createFormula } from '@/api/formula'
import { getDownloadedFormulas, getDownloadedIds, batchDownload, isDownloaded } from '@/utils/formula-download'
import { useTabReset } from '@/composables/useTabReset'

const router = useRouter()
const route = useRoute()

const { resetTrigger } = useTabReset()
const savedScrollTop = ref(0)

// ─── 筛选状态 ────────────────────────────────────────
const searchKeyword = ref('')
const selectedRange = ref('all')        // all / created / collected / downloaded
const selectedCategory = ref('')
const selectedDifficulty = ref('')
const sortBy = ref('default')

const createdOnly = computed(() => selectedRange.value === 'created')
const collectedOnly = computed(() => selectedRange.value === 'collected')
const downloadedOnly = computed(() => selectedRange.value === 'downloaded')

// 下拉选项
const rangeOptions = [
  { text: '全部公式', value: 'all' },
  { text: '已创建', value: 'created' },
  { text: '已收藏', value: 'collected' },
  { text: '已下载', value: 'downloaded' },
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
  { text: '难度降序', value: 'difficulty_desc' },
  { text: '浏览量排序', value: 'view_count' },
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

// 下载状态
const downloadedIds = ref(new Set())

// 多选模式
const multiSelectMode = ref(false)
const selectedIds = ref(new Set())

onMounted(() => {
  applyQueryFilter()
  loadCategories()
  loadCollections()
  downloadedIds.value = getDownloadedIds()
})

onActivated(() => {
  downloadedIds.value = getDownloadedIds()
  setTimeout(() => {
    const el = document.querySelector('.list-container')
    if (el) el.scrollTop = savedScrollTop.value
  }, 100)
})

onDeactivated(() => {
  const el = document.querySelector('.list-container')
  if (el) savedScrollTop.value = el.scrollTop
})

function resetFilters() {
  searchKeyword.value = ''
  selectedRange.value = 'all'
  selectedCategory.value = ''
  selectedDifficulty.value = ''
  sortBy.value = 'default'
  resetList()
}

watch(resetTrigger, () => {
  resetFilters()
})

function applyQueryFilter() {
  const filter = route.query.filter
  if (filter === 'created' || filter === 'collected' || filter === 'downloaded') {
    selectedRange.value = filter
  } else {
    selectedRange.value = 'all'
  }
}

// 构建查询参数
function buildParams(page) {
  const params = { page, page_size: pageSize }
  if (selectedCategory.value) params.category = selectedCategory.value
  if (selectedDifficulty.value) params.difficulty = selectedDifficulty.value
  if (searchKeyword.value.trim()) params.search = searchKeyword.value.trim()
  if (sortBy.value !== 'default') {
    if (sortBy.value === 'difficulty_asc') params.ordering = 'difficulty'
    else if (sortBy.value === 'difficulty_desc') params.ordering = '-difficulty'
    else if (sortBy.value === 'view_count') params.ordering = '-view_count'
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
  } catch {}
}

async function loadCollections() {
  if (!localStorage.getItem('token')) return
  try {
    const res = await getMyCollections()
    const items = res.data.results || res.data || []
    collectedIds.value = new Set(items.map(c => c.id))
  } catch {}
}

// van-list @load
async function loadMore() {
  if ((collectedOnly.value || createdOnly.value) && !localStorage.getItem('token')) {
    showToast('请先登录')
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    finished.value = true
    listLoading.value = false
    return
  }

  // 我的下载：从 localStorage 加载
  if (downloadedOnly.value) {
    let allDownloads = getDownloadedFormulas()
    // 搜索过滤
    if (searchKeyword.value.trim()) {
      const kw = searchKeyword.value.trim().toLowerCase()
      allDownloads = allDownloads.filter(f =>
        f.name?.toLowerCase().includes(kw) ||
        f.notation?.toLowerCase().includes(kw) ||
        f.author_name?.toLowerCase().includes(kw) ||
        f.category_name?.toLowerCase().includes(kw)
      )
    }
    // 分类过滤
    if (selectedCategory.value) {
      allDownloads = allDownloads.filter(f => f.category_id === selectedCategory.value)
    }
    // 难度过滤
    if (selectedDifficulty.value) {
      allDownloads = allDownloads.filter(f => Number(f.difficulty) === Number(selectedDifficulty.value))
    }
    // 排序
    if (sortBy.value === 'difficulty_asc') {
      allDownloads.sort((a, b) => a.difficulty - b.difficulty)
    } else if (sortBy.value === 'difficulty_desc') {
      allDownloads.sort((a, b) => b.difficulty - a.difficulty)
    } else if (sortBy.value === 'view_count') {
      allDownloads.sort((a, b) => (b.view_count || 0) - (a.view_count || 0))
    }
    formulaList.value = allDownloads
    finished.value = true
    listLoading.value = false
    return
  }

  try {
    const params = buildParams(currentPage.value)
    const res = collectedOnly.value
      ? await getMyCollections(params)
      : createdOnly.value
        ? await getMyCustomFormulas(params)
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
  downloadedIds.value = getDownloadedIds()
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
  if (multiSelectMode.value) {
    toggleSelect(formula)
    return
  }
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
  } catch {} finally {
    collectLoadingIds.value.delete(formula.id)
  }
}

// ─── 多选模式 ────────────────────────────────────────
function onCardLongPress(formula) {
  if (downloadedOnly.value) return // 我的下载页面不支持多选
  multiSelectMode.value = true
  selectedIds.value = new Set([formula.id])
}

function toggleSelect(formula) {
  const ids = new Set(selectedIds.value)
  if (ids.has(formula.id)) {
    ids.delete(formula.id)
  } else {
    ids.add(formula.id)
  }
  selectedIds.value = ids
  if (selectedIds.value.size === 0) {
    exitMultiSelect()
  }
}

function exitMultiSelect() {
  multiSelectMode.value = false
  selectedIds.value = new Set()
}

function selectAll() {
  selectedIds.value = new Set(formulaList.value.map(f => f.id))
}

async function batchDownloadSelected() {
  const selected = formulaList.value.filter(f => selectedIds.value.has(f.id))
  const added = batchDownload(selected)
  downloadedIds.value = getDownloadedIds()
  showToast({ type: 'success', message: `已下载 ${added} 个公式` })
  exitMultiSelect()
}

async function batchCollectSelected() {
  if (!localStorage.getItem('token')) {
    showToast('请先登录')
    router.push({ name: 'login', query: { redirect: '/formula' } })
    return
  }
  const selected = formulaList.value.filter(f => selectedIds.value.has(f.id))
  let success = 0
  for (const f of selected) {
    if (!collectedIds.value.has(f.id)) {
      try {
        await addCollection(f.id)
        success++
      } catch {}
    }
  }
  await loadCollections()
  showToast({ type: 'success', message: `收藏成功 ${success} 个` })
  exitMultiSelect()
}

// 监听 route.query.filter 变化（从个人中心跳转）
watch(() => route.query.filter, () => {
  applyQueryFilter()
  resetList()
})

// ─── 创建公式 ────────────────────────────────────────
const addShow = ref(false)
const addLoading = ref(false)
const addForm = ref({
  name: '',
  notation: '',
  category_id: '',
  difficulty: 1,
  description: '',
})
const thumbnailFile = ref(null)
const thumbnailPath = ref('')
const thumbnailPreview = ref('')

const notationCursor = ref(-1)
const notationInputRef = ref()

function trackNotationCursor() {
  const el = notationInputRef.value?.$el?.querySelector('textarea')
  if (el) {
    notationCursor.value = el.selectionStart
  }
}

function onNotationCursorChange(pos) {
  notationCursor.value = pos
  nextTick(() => {
    const el = notationInputRef.value?.$el?.querySelector('textarea')
    if (el) {
      el.focus()
      el.setSelectionRange(pos, pos)
    }
  })
}

const showImageSheet = ref(false)
const showCropper = ref(false)
const cropperSrc = ref('')
const ocrLoading = ref(false)
const imageActions = [
  { name: '拍照', action: 'camera' },
  { name: '从相册选择', action: 'gallery' },
  { name: '从公式库选择', action: 'library' },
]

const showFormulaPicker = ref(false)
const pickerList = ref([])
const pickerLoading = ref(false)

// OCR 图片选择
const showOcrSheet = ref(false)
const showOcrCropper = ref(false)
const ocrCropSrc = ref('')
const ocrActions = [
  { name: '拍照识别', action: 'camera' },
  { name: '从相册识别', action: 'gallery' },
]

function openAdd() {
  if (!localStorage.getItem('token')) {
    showToast('请先登录')
    router.push({ name: 'login', query: { redirect: '/formula' } })
    return
  }
  addForm.value = { name: '', notation: '', category_id: '', difficulty: 1, description: '' }
  thumbnailFile.value = null
  thumbnailPath.value = ''
  thumbnailPreview.value = ''
  addShow.value = true
}

function onImageAction(item) {
  if (item.action === 'camera') selectFromCamera()
  else if (item.action === 'gallery') selectFromGallery()
  else if (item.action === 'library') openFormulaPicker()
}

async function selectFromCamera() {
  showImageSheet.value = false
  try {
    const photo = await Camera.getPhoto({
      quality: 90,
      resultType: CameraResultType.DataUrl,
      source: CameraSource.Camera,
    })
    cropperSrc.value = photo.dataUrl
    showCropper.value = true
  } catch {}
}

async function selectFromGallery() {
  showImageSheet.value = false
  try {
    const photo = await Camera.getPhoto({
      quality: 90,
      resultType: CameraResultType.DataUrl,
      source: CameraSource.Photos,
    })
    cropperSrc.value = photo.dataUrl
    showCropper.value = true
  } catch {}
}

async function onCropConfirm(crop) {
  showCropper.value = false
  try {
    thumbnailFile.value = await cropAndCompress(cropperSrc.value, crop, {
      outputSize: 512,
      quality: 0.85,
    })
    thumbnailPath.value = ''
    thumbnailPreview.value = URL.createObjectURL(thumbnailFile.value)
  } catch {
    showToast('图片处理失败')
  }
}

function onCropCancel() {
  showCropper.value = false
}

// ─── OCR 识别 ────────────────────────────────────────
function onOcrAction(item) {
  showOcrSheet.value = false
  if (item.action === 'camera') selectOcrFromSource(CameraSource.Camera)
  else if (item.action === 'gallery') selectOcrFromSource(CameraSource.Photos)
}

async function selectOcrFromSource(source) {
  try {
    const photo = await Camera.getPhoto({
      quality: 90,
      resultType: CameraResultType.DataUrl,
      source,
    })
    ocrCropSrc.value = photo.dataUrl
    showOcrCropper.value = true
  } catch {}
}

async function onOcrCropConfirm(cropRegion) {
  showOcrCropper.value = false
  ocrLoading.value = true
  try {
    const img = new Image()
    img.src = ocrCropSrc.value
    await new Promise((resolve) => { img.onload = resolve })
    const canvas = document.createElement('canvas')
    canvas.width = cropRegion.width
    canvas.height = cropRegion.height
    canvas.getContext('2d').drawImage(img, cropRegion.x, cropRegion.y, cropRegion.width, cropRegion.height, 0, 0, cropRegion.width, cropRegion.height)

    const procCanvas = preprocessImage(canvas)
    const dataUrl = procCanvas.toDataURL('image/png')

    const best = await multiPassOCR(dataUrl, procCanvas)
    if (best.cleaned) {
      addForm.value.notation = best.cleaned
      updateDifficulty(best.cleaned)
      showToast({ type: 'success', message: '识别成功' })
    } else {
      showToast('未识别到有效公式')
    }
  } catch {
    showToast('识别失败')
  } finally {
    ocrLoading.value = false
  }
}

function onOcrCropCancel() {
  showOcrCropper.value = false
}

function cleanNotation(text) {
  let cleaned = text.replace(/[′ʼ`´]/g, "'")
  cleaned = cleaned.replace(/[（［【]/g, ' ').replace(/[）］】]/g, ' ')
  const tokens = cleaned.split(/[\s,]+/).filter(Boolean)
  const validPattern = /^[RLUDFBMESxyzrludfb]['2]?$/
  return tokens.filter(t => validPattern.test(t)).join(' ')
}

function updateDifficulty(notation) {
  const count = notation.trim().split(/\s+/).filter(Boolean).length
  if (count <= 6) addForm.value.difficulty = 1
  else if (count <= 10) addForm.value.difficulty = 2
  else addForm.value.difficulty = 3
}

watch(() => addForm.value.notation, (val) => {
  if (val) updateDifficulty(val)
})

async function openFormulaPicker() {
  showImageSheet.value = false
  showFormulaPicker.value = true
  if (pickerList.value.length === 0) {
    pickerLoading.value = true
    try {
      const res = await getFormulaList({ page: 1, page_size: 50 })
      pickerList.value = res.data?.results || res.data || []
    } catch {} finally {
      pickerLoading.value = false
    }
  }
}

function pickFormulaImage(formula) {
  const thumb = formula.thumbnail || ''
  if (thumb) {
    thumbnailPath.value = thumb
    thumbnailFile.value = null
    thumbnailPreview.value = buildMediaUrl(thumb)
  }
  showFormulaPicker.value = false
}

async function submitAdd() {
  if (!addForm.value.name.trim()) {
    showToast('请输入公式名')
    return
  }
  if (!addForm.value.notation.trim()) {
    showToast('请输入公式')
    return
  }
  if (!thumbnailFile.value && !thumbnailPath.value) {
    showToast('请选择公式图片')
    return
  }

  addLoading.value = true
  try {
    const formData = new FormData()
    formData.append('name', addForm.value.name.trim())
    formData.append('notation', addForm.value.notation.trim())
    if (addForm.value.category_id) {
      formData.append('category_id', addForm.value.category_id)
    }
    formData.append('difficulty', addForm.value.difficulty)
    if (addForm.value.description.trim()) {
      formData.append('description', addForm.value.description.trim())
    }
    if (thumbnailFile.value) {
      formData.append('thumbnail_file', thumbnailFile.value)
    } else if (thumbnailPath.value) {
      const cleanPath = thumbnailPath.value.replace(/^\/media\//, '')
      formData.append('thumbnail_path', cleanPath)
    }

    await createFormula(formData)
    showToast({ type: 'success', message: '创建成功' })
    addShow.value = false
    resetList()
  } catch {} finally {
    addLoading.value = false
  }
}
</script>

<template>
  <div class="formula-page">
    <van-nav-bar :title="createdOnly ? '我的公式' : collectedOnly ? '公式收藏' : downloadedOnly ? '公式下载' : '公式库'" placeholder>
      <template #right>
        <van-icon name="plus" size="20" @click="openAdd" />
      </template>
    </van-nav-bar>

    <!-- 搜索栏 -->
    <van-search
      v-model="searchKeyword"
      :placeholder="createdOnly ? '搜索我创建的公式' : collectedOnly ? '搜索收藏的公式' : downloadedOnly ? '搜索下载的公式' : '搜索公式、作者或分类'"
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

    <!-- 多选操作栏 -->
    <div v-if="multiSelectMode" class="multi-select-bar">
      <span class="select-count">已选 {{ selectedIds.size }} 项</span>
      <div class="select-actions">
        <van-button size="small" plain @click="selectAll">全选</van-button>
        <van-button size="small" type="primary" @click="batchCollectSelected">收藏</van-button>
        <van-button size="small" type="success" @click="batchDownloadSelected">下载</van-button>
        <van-button size="small" plain @click="exitMultiSelect">取消</van-button>
      </div>
    </div>

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
            :downloaded="downloadedIds.has(formula.id)"
            :multi-select="multiSelectMode"
            :selected="selectedIds.has(formula.id)"
            @click="goDetail"
            @collect="toggleCollect"
            @longpress="onCardLongPress"
          />
        </div>
        <van-empty v-if="!listLoading && formulaList.length === 0" :description="createdOnly ? '暂无创建的公式' : collectedOnly ? '暂无收藏公式' : downloadedOnly ? '暂无下载公式' : '暂无公式数据'" image-size="80" />
      </van-list>
    </van-pull-refresh>

    <!-- 创建公式弹窗 -->
    <van-popup v-model:show="addShow" position="bottom" round :style="{ maxHeight: '90%' }">
      <div class="add-form">
        <div class="add-title">添加公式</div>

        <!-- 图片选择 -->
        <div class="add-image" @click="showImageSheet = true">
          <div class="image-upload">
            <van-image
              v-if="thumbnailPreview"
              width="100"
              height="100"
              :src="thumbnailPreview"
              fit="cover"
              radius="8"
            />
            <van-icon v-else name="photo-o" size="40" color="#9ca3af" />
          </div>
          <span class="image-hint">点击选择公式图片</span>
        </div>

        <!-- 公式名 -->
        <van-field
          v-model="addForm.name"
          label="公式名"
          placeholder="请输入公式名"
          maxlength="200"
        />

        <!-- 公式输入（可编辑 + 键盘） -->
        <van-field
          v-model="addForm.notation"
          ref="notationInputRef"
          label="公式"
          placeholder="点击输入或使用下方键盘"
          type="textarea"
          rows="1"
          autosize
          inputmode="none"
          @click="trackNotationCursor"
          @keyup="trackNotationCursor"
        >
          <template #button>
            <van-tag v-if="addForm.notation" type="primary" size="medium">
              {{ addForm.notation.trim().split(/\s+/).length }} 步
            </van-tag>
          </template>
        </van-field>

        <!-- OCR 识别按钮 -->
        <div class="ocr-section">
          <van-button size="small" plain type="primary" icon="scan" :loading="ocrLoading" @click="showOcrSheet = true">
            从图片识别
          </van-button>
        </div>

        <!-- 公式键盘 -->
        <NotationKeyboard
          v-model="addForm.notation"
          :cursor-pos="notationCursor"
          @update:cursor-pos="onNotationCursorChange"
        />

        <!-- 分类 -->
        <div class="add-field-row">
          <span class="add-field-label">分类</span>
          <select v-model="addForm.category_id" class="add-select">
            <option value="">不指定</option>
            <option v-for="opt in categoryOptions.slice(1)" :key="opt.value" :value="opt.value">
              {{ opt.text }}
            </option>
          </select>
        </div>

        <!-- 难度 -->
        <div class="add-field-row">
          <span class="add-field-label">难度</span>
          <div class="add-difficulty">
            <van-radio-group v-model="addForm.difficulty" direction="horizontal">
              <van-radio :name="1">基础</van-radio>
              <van-radio :name="2">进阶</van-radio>
              <van-radio :name="3">困难</van-radio>
            </van-radio-group>
          </div>
        </div>

        <!-- 描述 -->
        <van-field
          v-model="addForm.description"
          label="描述"
          type="textarea"
          placeholder="公式描述（选填）"
          rows="2"
          maxlength="500"
          show-word-limit
          autosize
        />

        <div class="add-actions">
          <van-button block type="primary" :loading="addLoading" @click="submitAdd">
            创建公式
          </van-button>
        </div>
      </div>
    </van-popup>

    <!-- 图片选择 ActionSheet -->
    <van-action-sheet
      v-model:show="showImageSheet"
      :actions="imageActions"
      cancel-text="取消"
      close-on-click-action
      @select="onImageAction"
    />

    <!-- OCR 图片选择 ActionSheet -->
    <van-action-sheet
      v-model:show="showOcrSheet"
      :actions="ocrActions"
      cancel-text="取消"
      close-on-click-action
      @select="onOcrAction"
    />

    <!-- 图片裁剪 -->
    <ImageCropper
      v-if="showCropper"
      :src="cropperSrc"
      @confirm="onCropConfirm"
      @cancel="onCropCancel"
    />

    <!-- OCR 自由裁剪 -->
    <FreeCropper
      v-if="showOcrCropper"
      :src="ocrCropSrc"
      @confirm="onOcrCropConfirm"
      @cancel="onOcrCropCancel"
    />

    <!-- 公式库选图弹窗 -->
    <van-popup v-model:show="showFormulaPicker" position="bottom" round :style="{ maxHeight: '70%' }">
      <div class="picker-container">
        <div class="picker-title">选择公式图片</div>
        <div v-if="pickerLoading" class="picker-loading">
          <van-loading>加载中...</van-loading>
        </div>
        <div v-else class="picker-grid">
          <div
            v-for="formula in pickerList"
            :key="formula.id"
            class="picker-item"
            @click="pickFormulaImage(formula)"
          >
            <van-image
              v-if="formula.thumbnail"
              width="80"
              height="80"
              :src="buildMediaUrl(formula.thumbnail)"
              fit="cover"
              radius="6"
            />
            <div class="picker-item-name">{{ formula.name }}</div>
          </div>
        </div>
      </div>
    </van-popup>
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

/* 多选操作栏 */
.multi-select-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #fff;
  border-bottom: 1px solid #ebedf0;
  flex-wrap: wrap;
  gap: 4px;
}

.select-count {
  font-size: 0.85rem;
  color: #323233;
  font-weight: 500;
}

.select-actions {
  display: flex;
  gap: 6px;
}

/* 创建公式弹窗 */
.add-form {
  padding: 20px 16px;
  max-height: 90vh;
  overflow-y: auto;
}

.add-title {
  font-size: 1.1rem;
  font-weight: 600;
  text-align: center;
  margin-bottom: 16px;
}

.add-image {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 16px;
  cursor: pointer;
}

.add-image:active {
  opacity: 0.7;
}

.image-upload {
  width: 100px;
  height: 100px;
  border: 1px dashed var(--van-border-color);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.image-hint {
  font-size: 0.8rem;
  color: var(--van-text-color-2);
  margin-top: 8px;
}

.ocr-section {
  display: flex;
  justify-content: flex-end;
  padding: 4px 16px 8px;
}

.add-field-row {
  display: flex;
  align-items: center;
  padding: 10px 16px;
}

.add-field-label {
  width: 65px;
  font-size: 14px;
  color: var(--van-text-color);
  flex-shrink: 0;
}

.add-select {
  flex: 1;
  border: none;
  font-size: 14px;
  color: var(--van-text-color);
  background: transparent;
  appearance: none;
  -webkit-appearance: none;
}

.add-actions {
  margin-top: 20px;
}

/* 公式库选图 */
.picker-container {
  padding: 20px 16px;
}

.picker-title {
  font-size: 1.1rem;
  font-weight: 600;
  text-align: center;
  margin-bottom: 16px;
}

.picker-loading {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

.picker-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  max-height: 50vh;
  overflow-y: auto;
}

.picker-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
}

.picker-item:active {
  opacity: 0.7;
}

.picker-item-name {
  font-size: 0.75rem;
  color: var(--van-text-color-2);
  margin-top: 4px;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 80px;
}
</style>
