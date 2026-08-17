<template>
  <div class="formula-detail">
    <van-nav-bar title="公式详情" left-arrow @click-left="router.back()" />

    <div v-if="loading" class="loading-wrap">
      <van-loading size="36px">加载中...</van-loading>
    </div>

    <template v-else-if="detail">
      <!-- 3D 演示区 -->
      <div class="demo-section">
        <CubeDemo :formula="detail" />
      </div>

      <!-- 公式信息区 -->
      <div class="info-section">
        <van-cell-group inset>
          <van-cell title="公式名" :value="detail.name" />
          <van-cell title="公式" :value="detail.notation" />
          <van-cell v-if="detail.inverse_notation" title="逆公式" :value="detail.inverse_notation" />
          <van-cell title="分类" :value="categoryName" />
          <van-cell title="难度">
            <template #value>
              <van-tag :type="difficultyType">{{ difficultyText }}</van-tag>
            </template>
          </van-cell>
          <van-cell title="作者" :value="authorName" />
          <van-cell v-if="detail.description" title="描述">
            <template #value>
              <span class="desc-text">{{ detail.description }}</span>
            </template>
          </van-cell>
        </van-cell-group>

        <!-- 收藏 + 下载按钮 -->
        <div class="action-section">
          <van-button
            v-if="canEdit"
            block
            plain
            type="primary"
            icon="edit"
            @click="openEdit"
            style="margin-bottom: 12px;"
          >
            编辑公式
          </van-button>
          <div class="action-row">
            <van-button
              class="action-btn"
              :type="isCollected ? 'danger' : 'primary'"
              :icon="isCollected ? 'like' : 'like-o'"
              :loading="collectLoading"
              @click="toggleCollect"
            >
              {{ isCollected ? '取消收藏' : '收藏' }}
            </van-button>
            <van-button
              class="action-btn"
              :type="isDownloaded ? 'success' : 'default'"
              :icon="isDownloaded ? 'success' : 'down'"
              @click="toggleDownload"
            >
              {{ isDownloaded ? '已下载' : '下载' }}
            </van-button>
          </div>
        </div>
      </div>
    </template>

    <van-empty v-else description="公式不存在或已删除" />

    <!-- 编辑公式弹窗 -->
    <van-popup v-model:show="editShow" position="bottom" round :style="{ maxHeight: '90%' }">
      <div class="edit-form">
        <div class="edit-title">编辑公式</div>

        <!-- 图片选择 -->
        <div class="edit-image" @click="showEditImageSheet = true">
          <div class="image-upload">
            <van-image
              v-if="editThumbnailPreview"
              width="100"
              height="100"
              :src="editThumbnailPreview"
              fit="cover"
              radius="8"
            />
            <van-icon v-else name="photo-o" size="40" color="#9ca3af" />
          </div>
          <span class="image-hint">点击选择公式图片</span>
        </div>

        <van-field
          v-model="editForm.name"
          label="公式名"
          placeholder="请输入公式名"
          maxlength="200"
        />

        <van-field
          v-model="editForm.notation"
          label="公式"
          placeholder="点击下方键盘输入"
          readonly
          type="textarea"
          rows="1"
          autosize
        >
          <template #button>
            <van-tag v-if="editForm.notation" type="primary" size="medium">
              {{ editForm.notation.trim().split(/\s+/).length }} 步
            </van-tag>
          </template>
        </van-field>

        <!-- OCR 识别按钮 -->
        <div class="edit-ocr-section">
          <van-button size="small" plain type="primary" icon="scan" :loading="editOcrLoading" @click="showEditOcrSheet = true">
            从图片识别
          </van-button>
        </div>

        <NotationKeyboard v-model="editForm.notation" />

        <div class="edit-field-row">
          <span class="edit-field-label">分类</span>
          <select v-model="editForm.category_id" class="edit-select">
            <option value="">不指定</option>
            <option v-for="opt in categoryOptions" :key="opt.value" :value="opt.value">
              {{ opt.text }}
            </option>
          </select>
        </div>

        <div class="edit-field-row">
          <span class="edit-field-label">难度</span>
          <van-radio-group v-model="editForm.difficulty" direction="horizontal">
            <van-radio :name="1">基础</van-radio>
            <van-radio :name="2">进阶</van-radio>
            <van-radio :name="3">困难</van-radio>
          </van-radio-group>
        </div>

        <van-field
          v-model="editForm.description"
          label="描述"
          type="textarea"
          placeholder="公式描述（选填）"
          rows="2"
          maxlength="500"
          show-word-limit
          autosize
        />

        <div class="edit-actions">
          <van-button block type="primary" :loading="editLoading" @click="submitEdit">
            保存修改
          </van-button>
        </div>
      </div>
    </van-popup>

    <!-- 编辑图片选择 ActionSheet -->
    <van-action-sheet
      v-model:show="showEditImageSheet"
      :actions="editImageActions"
      cancel-text="取消"
      close-on-click-action
      @select="onEditImageAction"
    />

    <!-- 编辑 OCR ActionSheet -->
    <van-action-sheet
      v-model:show="showEditOcrSheet"
      :actions="editOcrActions"
      cancel-text="取消"
      close-on-click-action
      @select="onEditOcrAction"
    />

    <!-- 编辑图片裁剪 -->
    <ImageCropper
      v-if="showEditCropper"
      :src="editCropperSrc"
      @confirm="onEditCropConfirm"
      @cancel="onEditCropCancel"
    />

    <!-- 编辑 OCR 自由裁剪 -->
    <FreeCropper
      v-if="showEditOcrCropper"
      :src="editOcrCropSrc"
      @confirm="onEditOcrCropConfirm"
      @cancel="onEditOcrCropCancel"
    />
  </div>
</template>

<script setup>
/**
 * FormulaDetailView.vue - 公式详情页（移动端）
 *
 * 桌面端用 el-dialog 弹窗，移动端改为独立路由页面（上下垂直布局）
 */
defineOptions({ name: 'FormulaDetailView' })

import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera'
import CubeDemo from '@/components/formula/CubeDemo.vue'
import NotationKeyboard from '@/components/formula/NotationKeyboard.vue'
import ImageCropper from '@/components/ImageCropper.vue'
import FreeCropper from '@/components/FreeCropper.vue'
import { cropAndCompress } from '@/utils/image-compress'
import { preprocessImage, multiPassOCR } from '@/utils/ocr-helper'
import { buildMediaUrl } from '@/utils/media-url'
import { getFormulaDetail, getMyCollections, addCollection, removeCollection, updateFormula, getFormulaCategories } from '@/api/formula'
import { useUserStore } from '@/stores/user'
import { isDownloaded as checkDownloaded, downloadFormula, removeDownload } from '@/utils/formula-download'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loading = ref(true)
const detail = ref(null)
const isCollected = ref(false)
const collectLoading = ref(false)
const isDownloaded = ref(false)

// 编辑状态
const editShow = ref(false)
const editLoading = ref(false)
const editForm = ref({ name: '', notation: '', category_id: '', difficulty: 1, description: '' })
const categoryOptions = ref([])

// 编辑图片上传
const editThumbnailFile = ref(null)
const editThumbnailPreview = ref('')
const showEditImageSheet = ref(false)
const showEditCropper = ref(false)
const editCropperSrc = ref('')
const editImageActions = [
  { name: '拍照', action: 'camera' },
  { name: '从相册选择', action: 'gallery' },
]

// 编辑 OCR
const showEditOcrSheet = ref(false)
const showEditOcrCropper = ref(false)
const editOcrCropSrc = ref('')
const editOcrLoading = ref(false)
const editOcrActions = [
  { name: '拍照识别', action: 'camera' },
  { name: '从相册识别', action: 'gallery' },
]

const canEdit = computed(() => {
  const d = detail.value
  if (!d) return false
  return d.is_custom && (d.created_by?.username === userStore.username || d.author?.username === userStore.username)
})

// 难度映射：后端 difficulty 为 IntegerField（1=基础 2=进阶 3+=困难）
const diffKey = computed(() => Number(detail.value?.difficulty))
const difficultyText = computed(() => {
  const d = diffKey.value
  if (d === 1) return '基础'
  if (d === 2) return '进阶'
  return '困难'
})
const difficultyType = computed(() => {
  const d = diffKey.value
  if (d === 1) return 'primary'
  if (d === 2) return 'warning'
  return 'danger'
})

const categoryName = computed(() => {
  const d = detail.value
  return d?.category?.name || d?.category_name || '未分类'
})
const authorName = computed(() => {
  const d = detail.value
  return d?.author?.username || d?.author_username || '匿名'
})

// 加载公式详情 + 收藏状态
async function loadDetail(id) {
  loading.value = true
  detail.value = null
  isCollected.value = false
  isDownloaded.value = checkDownloaded(Number(id))

  try {
    const res = await getFormulaDetail(id)
    detail.value = res.data

    // 检查收藏状态：后端 list 返回 Formula 对象列表，c.id 即为 formula ID
    if (localStorage.getItem('token')) {
      const colRes = await getMyCollections()
      const items = colRes.data.results || colRes.data || []
      const found = items.find(c => c.id === Number(id))
      if (found) {
        isCollected.value = true
      }
    }
  } catch {
    // request.js 已统一处理错误提示
  } finally {
    loading.value = false
  }
}

// 修复问题5：watch route.params.id，切换公式时重新加载
watch(() => route.params.id, (newId) => {
  if (newId) loadDetail(newId)
}, { immediate: true })

async function toggleCollect() {
  if (!localStorage.getItem('token')) {
    showToast('请先登录')
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }

  collectLoading.value = true
  try {
    if (isCollected.value) {
      // 取消收藏：后端 destroy 按 formula_id 删除
      await removeCollection(detail.value.id)
      isCollected.value = false
      showToast({ type: 'success', message: '已取消收藏' })
    } else {
      // 添加收藏
      await addCollection(detail.value.id)
      isCollected.value = true
      showToast({ type: 'success', message: '收藏成功' })
    }
  } catch {
    // request.js 已统一处理错误提示
  } finally {
    collectLoading.value = false
  }
}

function toggleDownload() {
  if (!detail.value) return
  if (isDownloaded.value) {
    removeDownload(detail.value.id)
    isDownloaded.value = false
    showToast({ type: 'success', message: '已删除下载' })
  } else {
    downloadFormula(detail.value)
    isDownloaded.value = true
    showToast({ type: 'success', message: '已下载到本地' })
  }
}

// ─── 编辑公式 ────────────────────────────────────────
async function openEdit() {
  const d = detail.value
  editForm.value = {
    name: d.name || '',
    notation: d.notation || '',
    category_id: d.category?.id || d.category_id || '',
    difficulty: Number(d.difficulty) || 1,
    description: d.description || '',
  }
  editThumbnailFile.value = null
  editThumbnailPreview.value = d.thumbnail ? buildMediaUrl(d.thumbnail) : ''
  // 加载分类选项
  if (categoryOptions.value.length === 0) {
    try {
      const res = await getFormulaCategories()
      const cats = res.data.results || res.data || []
      categoryOptions.value = cats.map(c => ({ text: c.name, value: c.id }))
    } catch {}
  }
  editShow.value = true
}

function updateDifficulty(notation) {
  const count = notation.trim().split(/\s+/).filter(Boolean).length
  if (count <= 6) editForm.value.difficulty = 1
  else if (count <= 10) editForm.value.difficulty = 2
  else editForm.value.difficulty = 3
}

watch(() => editForm.value.notation, (val) => {
  if (val) updateDifficulty(val)
})

async function submitEdit() {
  if (!editForm.value.name.trim()) {
    showToast('请输入公式名')
    return
  }
  if (!editForm.value.notation.trim()) {
    showToast('请输入公式')
    return
  }
  editLoading.value = true
  try {
    const formData = new FormData()
    formData.append('name', editForm.value.name.trim())
    formData.append('notation', editForm.value.notation.trim())
    if (editForm.value.category_id) {
      formData.append('category_id', editForm.value.category_id)
    }
    formData.append('difficulty', editForm.value.difficulty)
    if (editForm.value.description.trim()) {
      formData.append('description', editForm.value.description.trim())
    }
    if (editThumbnailFile.value) {
      formData.append('thumbnail_file', editThumbnailFile.value)
    }
    await updateFormula(detail.value.id, formData)
    showToast({ type: 'success', message: '修改成功' })
    editShow.value = false
    await loadDetail(route.params.id)
  } catch {} finally {
    editLoading.value = false
  }
}

// ─── 编辑图片上传 ────────────────────────────────────
function onEditImageAction(item) {
  if (item.action === 'camera') selectEditFromCamera()
  else if (item.action === 'gallery') selectEditFromGallery()
}

async function selectEditFromCamera() {
  showEditImageSheet.value = false
  try {
    const photo = await Camera.getPhoto({
      quality: 90,
      resultType: CameraResultType.DataUrl,
      source: CameraSource.Camera,
    })
    editCropperSrc.value = photo.dataUrl
    showEditCropper.value = true
  } catch {}
}

async function selectEditFromGallery() {
  showEditImageSheet.value = false
  try {
    const photo = await Camera.getPhoto({
      quality: 90,
      resultType: CameraResultType.DataUrl,
      source: CameraSource.Photos,
    })
    editCropperSrc.value = photo.dataUrl
    showEditCropper.value = true
  } catch {}
}

async function onEditCropConfirm(crop) {
  showEditCropper.value = false
  try {
    editThumbnailFile.value = await cropAndCompress(editCropperSrc.value, crop, {
      outputSize: 512,
      quality: 0.85,
    })
    editThumbnailPreview.value = URL.createObjectURL(editThumbnailFile.value)
  } catch {
    showToast('图片处理失败')
  }
}

function onEditCropCancel() {
  showEditCropper.value = false
}

// ─── 编辑 OCR 识别 ────────────────────────────────────
function onEditOcrAction(item) {
  showEditOcrSheet.value = false
  if (item.action === 'camera') selectEditOcrFromSource(CameraSource.Camera)
  else if (item.action === 'gallery') selectEditOcrFromSource(CameraSource.Photos)
}

async function selectEditOcrFromSource(source) {
  try {
    const photo = await Camera.getPhoto({
      quality: 90,
      resultType: CameraResultType.DataUrl,
      source,
    })
    editOcrCropSrc.value = photo.dataUrl
    showEditOcrCropper.value = true
  } catch {}
}

async function onEditOcrCropConfirm(cropRegion) {
  showEditOcrCropper.value = false
  editOcrLoading.value = true
  try {
    const img = new Image()
    img.src = editOcrCropSrc.value
    await new Promise((resolve) => { img.onload = resolve })
    const canvas = document.createElement('canvas')
    canvas.width = cropRegion.width
    canvas.height = cropRegion.height
    canvas.getContext('2d').drawImage(img, cropRegion.x, cropRegion.y, cropRegion.width, cropRegion.height, 0, 0, cropRegion.width, cropRegion.height)

    const procCanvas = preprocessImage(canvas)
    const dataUrl = procCanvas.toDataURL('image/png')

    const best = await multiPassOCR(dataUrl, procCanvas)
    if (best.cleaned) {
      editForm.value.notation = best.cleaned
      updateDifficulty(best.cleaned)
      showToast({ type: 'success', message: '识别成功' })
    } else {
      showToast('未识别到有效公式')
    }
  } catch {
    showToast('识别失败')
  } finally {
    editOcrLoading.value = false
  }
}

function onEditOcrCropCancel() {
  showEditOcrCropper.value = false
}

function cleanNotation(text) {
  let cleaned = text.replace(/[′ʼ`´]/g, "'")
  cleaned = cleaned.replace(/[（［【]/g, ' ').replace(/[）］】]/g, ' ')
  const tokens = cleaned.split(/[\s,]+/).filter(Boolean)
  const validPattern = /^[RLUDFBMESxyzrludfb]['2]?$/
  return tokens.filter(t => validPattern.test(t)).join(' ')
}
</script>

<style scoped>
.formula-detail {
  min-height: 100vh;
  background: #f7f8fa;
}

.loading-wrap {
  display: flex;
  justify-content: center;
  padding-top: 120px;
}

.demo-section {
  padding: 12px;
  background: #fff;
  margin-bottom: 8px;
}

.info-section {
  padding-bottom: 24px;
}

.desc-text {
  white-space: pre-wrap;
  word-break: break-all;
}

.action-section {
  padding: 16px;
}

.action-row {
  display: flex;
  gap: 12px;
}

.action-btn {
  flex: 1;
}

.edit-form {
  padding: 20px 16px;
  max-height: 90vh;
  overflow-y: auto;
}

.edit-title {
  font-size: 1.1rem;
  font-weight: 600;
  text-align: center;
  margin-bottom: 16px;
}

.edit-field-row {
  display: flex;
  align-items: center;
  padding: 10px 16px;
}

.edit-field-label {
  width: 65px;
  font-size: 14px;
  flex-shrink: 0;
}

.edit-select {
  flex: 1;
  border: none;
  font-size: 14px;
  background: transparent;
  appearance: none;
  -webkit-appearance: none;
}

.edit-actions {
  margin-top: 20px;
}

.edit-image {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 16px;
  cursor: pointer;
}

.edit-image:active {
  opacity: 0.7;
}

.edit-ocr-section {
  display: flex;
  justify-content: flex-end;
  padding: 4px 16px 8px;
}
</style>
