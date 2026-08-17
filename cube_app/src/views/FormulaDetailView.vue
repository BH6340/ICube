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
import CubeDemo from '@/components/formula/CubeDemo.vue'
import NotationKeyboard from '@/components/formula/NotationKeyboard.vue'
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
    await updateFormula(detail.value.id, formData)
    showToast({ type: 'success', message: '修改成功' })
    editShow.value = false
    await loadDetail(route.params.id)
  } catch {} finally {
    editLoading.value = false
  }
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
</style>
