<script setup>
/**
 * PostDetailView.vue — 帖子详情页
 *
 * Markdown 渲染（marked）、点赞/收藏互动、评论区。
 * 监听 route.params.id 变化，切换帖子时重新加载。
 */
defineOptions({ name: 'PostDetailView' })

import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import { marked } from 'marked'
import CommentSection from '@/components/forum/CommentSection.vue'
import { getPost, likePost, collectPost } from '@/api/forum'
import { buildMediaUrl } from '@/utils/media-url'

const router = useRouter()
const route = useRoute()

// ─── 响应式状态 ──────────────────────────────────────
const detail = ref(null)
const loading = ref(true)
const likeLoading = ref(false)
const collectLoading = ref(false)

// ─── Markdown 渲染 ───────────────────────────────────
// 配置 marked：GitHub 风味，换行转 <br>
marked.setOptions({
  breaks: true,
  gfm: true,
})

const renderedContent = computed(() => {
  if (!detail.value) return ''
  const md = detail.value.content_md || detail.value.content || ''
  if (!md) return ''
  try {
    // 将图片相对路径转为完整 URL
    const processedMd = md.replace(
      /!\[([^\]]*)\]\(([^)]+)\)/g,
      (match, alt, url) => {
        if (url.startsWith('http')) return match
        return `![${alt}](${buildMediaUrl(url)})`
      }
    )
    return marked.parse(processedMd)
  } catch {
    return md
  }
})

// ─── 数据加载 ────────────────────────────────────────
async function loadDetail(id) {
  loading.value = true
  detail.value = null
  try {
    const res = await getPost(id)
    // 后端返回 { post: {...} } 或直接返回
    detail.value = res.data?.post || res.data || res.post || res
  } catch {
    showToast('加载失败')
  } finally {
    loading.value = false
  }
}

// ─── 互动操作 ────────────────────────────────────────
async function toggleLike() {
  if (!localStorage.getItem('token')) {
    showToast('请先登录')
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  if (likeLoading.value) return

  likeLoading.value = true
  try {
    const res = await likePost(route.params.id)
    const data = res.data || {}
    detail.value.is_liked = data.liked ?? !detail.value.is_liked
    detail.value.like_count = data.like_count ?? detail.value.like_count
  } catch {
    // 静默失败
  } finally {
    likeLoading.value = false
  }
}

async function toggleCollect() {
  if (!localStorage.getItem('token')) {
    showToast('请先登录')
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  if (collectLoading.value) return

  collectLoading.value = true
  try {
    const res = await collectPost(route.params.id)
    const data = res.data || {}
    detail.value.is_collected = data.collected ?? !detail.value.is_collected
    detail.value.collect_count = data.collect_count ?? detail.value.collect_count
  } catch {
    // 静默失败
  } finally {
    collectLoading.value = false
  }
}

// ─── 工具函数 ────────────────────────────────────────
const authorAvatar = computed(() => buildMediaUrl(detail.value?.author?.image))
const tagNames = computed(() => {
  const tags = detail.value?.tags || []
  return tags.map(t => (typeof t === 'object' ? t.name : t))
})

function relativeTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}

// ─── watch 路由参数变化 ──────────────────────────────
watch(
  () => route.params.id,
  (newId) => {
    if (newId) loadDetail(newId)
  },
  { immediate: true }
)
</script>

<template>
  <div class="page">
    <van-nav-bar title="帖子详情" left-arrow @click-left="router.back()" placeholder />

    <div v-if="loading" class="loading-wrap">
      <van-loading size="36px">加载中...</van-loading>
    </div>

    <template v-else-if="detail">
      <div class="page-content">
        <!-- 帖子标题 -->
        <div class="post-header">
          <h1 class="post-title">
            <van-tag v-if="detail.is_pinned" type="danger" size="mini">置顶</van-tag>
            <van-tag v-if="detail.is_essence" type="warning" size="mini">精华</van-tag>
            {{ detail.title }}
          </h1>
          <!-- 作者信息 -->
          <div class="author-row">
            <van-image
              round
              width="32"
              height="32"
              :src="authorAvatar"
              fit="cover"
            >
              <template #error>
                <div class="avatar-mini">{{ detail.author?.username?.[0] || '?' }}</div>
              </template>
            </van-image>
            <div class="author-info">
              <span class="author-name">{{ detail.author?.username || '匿名' }}</span>
              <span class="post-time">{{ relativeTime(detail.created_at) }}</span>
            </div>
          </div>
        </div>

        <!-- Markdown 正文 -->
        <div class="markdown-body" v-html="renderedContent"></div>

        <!-- 标签 -->
        <div v-if="tagNames.length" class="tag-row">
          <van-tag v-for="tag in tagNames" :key="tag" plain size="medium" class="post-tag">
            {{ tag }}
          </van-tag>
        </div>

        <!-- 互动栏 -->
        <div class="interaction-bar">
          <div class="interaction-item" @click="toggleLike">
            <van-icon
              :name="detail.is_liked ? 'good-job' : 'good-job-o'"
              :color="detail.is_liked ? '#ef4444' : ''"
              size="18"
            />
            <span :class="{ active: detail.is_liked }">{{ detail.like_count || 0 }}</span>
          </div>
          <div class="interaction-item" @click="toggleCollect">
            <van-icon
              :name="detail.is_collected ? 'star' : 'star-o'"
              :color="detail.is_collected ? '#f59e0b' : ''"
              size="18"
            />
            <span :class="{ active: detail.is_collected }">{{ detail.collect_count || 0 }}</span>
          </div>
          <div class="interaction-item">
            <van-icon name="eye-o" size="18" />
            <span>{{ detail.view_count || 0 }}</span>
          </div>
        </div>

        <!-- 评论区 -->
        <CommentSection :post-id="route.params.id" />
      </div>
    </template>

    <van-empty v-else description="帖子不存在或已删除" />
  </div>
</template>

<style scoped>
.page {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-content {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 60px;
}

.loading-wrap {
  display: flex;
  justify-content: center;
  padding: 4rem 0;
}

/* 帖子头部 */
.post-header {
  padding: 16px;
  border-bottom: 1px solid var(--van-border-color);
}

.post-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--van-text-color);
  line-height: 1.5;
  margin-bottom: 12px;
}

.author-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.avatar-mini {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--van-primary-color);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  font-weight: 600;
}

.author-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.author-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--van-text-color);
}

.post-time {
  font-size: 0.72rem;
  color: var(--van-text-color-3);
}

/* Markdown 正文 */
.markdown-body {
  padding: 16px;
  font-size: 0.92rem;
  line-height: 1.7;
  color: var(--van-text-color);
  word-break: break-word;
}

.markdown-body :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 6px;
  margin: 8px 0;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  font-weight: 700;
  margin: 16px 0 8px;
}

.markdown-body :deep(h1) { font-size: 1.3rem; }
.markdown-body :deep(h2) { font-size: 1.15rem; }
.markdown-body :deep(h3) { font-size: 1rem; }

.markdown-body :deep(p) {
  margin: 8px 0;
}

.markdown-body :deep(blockquote) {
  border-left: 3px solid var(--van-primary-color);
  padding: 4px 12px;
  margin: 8px 0;
  background: var(--van-background);
  color: var(--van-text-color-2);
  border-radius: 0 4px 4px 0;
}

.markdown-body :deep(code) {
  background: var(--van-background);
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 0.85em;
  font-family: "Cascadia Code", "Fira Code", monospace;
}

.markdown-body :deep(pre) {
  background: var(--van-background);
  border: 1px solid var(--van-border-color);
  border-radius: 6px;
  padding: 12px;
  overflow-x: auto;
  margin: 8px 0;
}

.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 1.5rem;
  margin: 8px 0;
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 8px 0;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid var(--van-border-color);
  padding: 6px 10px;
  text-align: left;
}

/* 标签 */
.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 0 16px 12px;
}

.post-tag {
  margin-right: 4px;
}

/* 互动栏 */
.interaction-bar {
  display: flex;
  justify-content: space-around;
  padding: 12px 16px;
  border-top: 1px solid var(--van-border-color);
  border-bottom: 1px solid var(--van-border-color);
  margin-bottom: 8px;
}

.interaction-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.85rem;
  color: var(--van-text-color-2);
  cursor: pointer;
}

.interaction-item .active {
  color: #ef4444;
}

.interaction-item:nth-child(2) .active {
  color: #f59e0b;
}
</style>
