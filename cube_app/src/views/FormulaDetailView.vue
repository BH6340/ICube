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
          <van-cell title="记号" :value="detail.notation" />
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

        <!-- 收藏按钮 -->
        <div class="action-section">
          <van-button
            block
            :type="isCollected ? 'danger' : 'primary'"
            :icon="isCollected ? 'like' : 'like-o'"
            :loading="collectLoading"
            @click="toggleCollect"
          >
            {{ isCollected ? '取消收藏' : '收藏公式' }}
          </van-button>
        </div>
      </div>
    </template>

    <van-empty v-else description="公式不存在或已删除" />
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
import { getFormulaDetail, getMyCollections, addCollection, removeCollection } from '@/api/formula'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const detail = ref(null)
const isCollected = ref(false)
const collectLoading = ref(false)

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
</style>
