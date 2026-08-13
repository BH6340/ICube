<script setup>
/**
 * CommentSection.vue — 评论区组件
 *
 * 功能：评论列表（一级评论 + 扁平化子评论）、发表评论、回复、点赞、删除。
 * 未登录时输入框显示"登录后评论"。
 */
defineOptions({ name: 'CommentSection' })

import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { buildMediaUrl } from '@/utils/media-url'
import { getComments, createComment, deleteComment, likeComment } from '@/api/forum'

const props = defineProps({
  postId: {
    type: [String, Number],
    required: true,
  },
})

const router = useRouter()
const isLoggedIn = computed(() => !!localStorage.getItem('token'))
const currentUsername = computed(() => localStorage.getItem('username') || '')

// ─── 响应式状态 ──────────────────────────────────────
const comments = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const finished = ref(false)
const page = ref(1)
const pageSize = 10

// 输入框
const inputText = ref('')
const submitting = ref(false)
const replyTarget = ref(null)  // { id, username } 回复目标

// ─── 数据加载 ────────────────────────────────────────
async function loadComments(reset = false) {
  if (reset) {
    page.value = 1
    finished.value = false
  }

  const isLoadingMore = !reset
  if (isLoadingMore) {
    loadingMore.value = true
  } else {
    loading.value = true
  }

  try {
    const res = await getComments(props.postId, { page: page.value, page_size: pageSize })
    const results = res.data?.results || res.data || []

    if (reset) {
      comments.value = results
    } else {
      comments.value.push(...results)
    }

    const count = res.data?.count || results.length
    if (comments.value.length >= count || results.length < pageSize) {
      finished.value = true
    }
  } catch {
    finished.value = true
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// ─── 发表评论 ────────────────────────────────────────
function setReply(comment) {
  replyTarget.value = { id: comment.id, username: comment.author?.username || '用户' }
}

function cancelReply() {
  replyTarget.value = null
}

async function submitComment() {
  if (!isLoggedIn.value) {
    showToast('请先登录')
    router.push({ name: 'login', query: { redirect: `/forum/${props.postId}` } })
    return
  }
  if (!inputText.value.trim()) return

  submitting.value = true
  try {
    const data = {
      post: props.postId,
      content: inputText.value.trim(),
    }
    if (replyTarget.value) {
      data.parent = replyTarget.value.id
    }

    await createComment(data)
    inputText.value = ''
    replyTarget.value = null
    showToast({ type: 'success', message: '评论成功' })
    // 重新加载评论列表
    loadComments(true)
  } catch {
    // request.js 已统一处理错误提示
  } finally {
    submitting.value = false
  }
}

// ─── 点赞评论 ────────────────────────────────────────
const likeLoading = ref(new Set())

async function toggleLike(comment) {
  if (!isLoggedIn.value) {
    showToast('请先登录')
    return
  }
  if (likeLoading.value.has(comment.id)) return

  likeLoading.value.add(comment.id)
  try {
    const res = await likeComment(comment.id)
    const data = res.data || {}
    comment.liked = data.liked ?? !comment.liked
    comment.like_count = data.like_count ?? comment.like_count
  } catch {
    // 静默失败
  } finally {
    likeLoading.value.delete(comment.id)
  }
}

// ─── 删除评论 ────────────────────────────────────────
function confirmDelete(comment, isReply = false, parent = null) {
  showConfirmDialog({
    title: '删除评论',
    message: '确认删除这条评论吗？',
  }).then(async () => {
    try {
      await deleteComment(comment.id)
      if (isReply && parent) {
        // 从父评论的 replies 中移除
        const idx = parent.replies.findIndex(r => r.id === comment.id)
        if (idx !== -1) parent.replies.splice(idx, 1)
      } else {
        // 从一级评论列表中移除
        const idx = comments.value.findIndex(c => c.id === comment.id)
        if (idx !== -1) comments.value.splice(idx, 1)
      }
      showToast({ type: 'success', message: '已删除' })
    } catch {
      // request.js 已统一处理
    }
  }).catch(() => {})
}

// ─── 工具函数 ────────────────────────────────────────
function avatarUrl(author) {
  return buildMediaUrl(author?.image)
}

function relativeTime(dateStr) {
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

// ─── 生命周期 ────────────────────────────────────────
onMounted(() => {
  loadComments(true)
})

// 暴露给父组件重新加载
defineExpose({ reload: () => loadComments(true) })
</script>

<template>
  <div class="comment-section">
    <div class="section-title">评论 ({{ comments.length }})</div>

    <!-- 评论列表 -->
    <div v-if="loading" class="loading-wrap">
      <van-loading size="24px">加载中...</van-loading>
    </div>

    <template v-else>
      <!-- 一级评论 -->
      <div v-for="comment in comments" :key="comment.id" class="comment-item">
        <van-image
          round
          width="32"
          height="32"
          :src="avatarUrl(comment.author)"
          fit="cover"
        >
          <template #error>
            <div class="avatar-mini">{{ comment.author?.username?.[0] || '?' }}</div>
          </template>
        </van-image>

        <div class="comment-body">
          <div class="comment-header">
            <span class="comment-author">{{ comment.author?.username || '匿名' }}</span>
            <span class="comment-time">{{ relativeTime(comment.created_at) }}</span>
          </div>
          <div class="comment-content">{{ comment.content }}</div>
          <div class="comment-actions">
            <span class="action-btn" @click="setReply(comment)">回复</span>
            <span class="action-btn" @click="toggleLike(comment)">
              <van-icon :name="comment.liked ? 'good-job' : 'good-job-o'" size="13" />
              {{ comment.like_count || 0 }}
            </span>
            <span
              v-if="isLoggedIn && comment.author?.username === currentUsername"
              class="action-btn danger"
              @click="confirmDelete(comment)"
            >删除</span>
          </div>

          <!-- 子评论（扁平化） -->
          <div v-if="comment.replies?.length" class="replies">
            <div v-for="reply in comment.replies" :key="reply.id" class="reply-item">
              <van-image
                round
                width="24"
                height="24"
                :src="avatarUrl(reply.author)"
                fit="cover"
              >
                <template #error>
                  <div class="avatar-mini-sm">{{ reply.author?.username?.[0] || '?' }}</div>
                </template>
              </van-image>
              <div class="reply-body">
                <div class="comment-header">
                  <span class="comment-author">{{ reply.author?.username || '匿名' }}</span>
                  <span v-if="reply.reply_to_name" class="reply-to">回复 @{{ reply.reply_to_name }}</span>
                  <span class="comment-time">{{ relativeTime(reply.created_at) }}</span>
                </div>
                <div class="comment-content">{{ reply.content }}</div>
                <div class="comment-actions">
                  <span class="action-btn" @click="setReply(reply)">回复</span>
                  <span class="action-btn" @click="toggleLike(reply)">
                    <van-icon :name="reply.liked ? 'good-job' : 'good-job-o'" size="12" />
                    {{ reply.like_count || 0 }}
                  </span>
                  <span
                    v-if="isLoggedIn && reply.author?.username === currentUsername"
                    class="action-btn danger"
                    @click="confirmDelete(reply, true, comment)"
                  >删除</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 加载更多 -->
      <div v-if="!finished" class="load-more" @click="page++; loadComments()">
        {{ loadingMore ? '加载中...' : '加载更多' }}
      </div>

      <van-empty v-if="comments.length === 0" description="暂无评论" image-size="60" />
    </template>

    <!-- 底部输入框 -->
    <div class="comment-input-bar">
      <template v-if="replyTarget">
        <div class="reply-banner">
          回复 @{{ replyTarget.username }}
          <van-icon name="cross" size="14" @click="cancelReply" />
        </div>
      </template>
      <div class="input-row">
        <van-field
          v-model="inputText"
          :placeholder="isLoggedIn ? '写评论...' : '登录后评论'"
          rows="1"
          autosize
          class="comment-field"
          @focus="!isLoggedIn && router.push({ name: 'login', query: { redirect: `/forum/${postId}` } })"
        />
        <van-button
          size="small"
          type="primary"
          :loading="submitting"
          :disabled="!inputText.trim()"
          @click="submitComment"
        >发送</van-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.comment-section {
  padding: 0 12px 60px;
}

.section-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--van-text-color);
  padding: 12px 0 8px;
}

.loading-wrap {
  display: flex;
  justify-content: center;
  padding: 2rem 0;
}

.comment-item {
  display: flex;
  gap: 10px;
  padding: 12px 0;
  border-bottom: 1px solid var(--van-border-color);
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

.avatar-mini-sm {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--van-gray-5);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  font-weight: 600;
}

.comment-body {
  flex: 1;
  min-width: 0;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.comment-author {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--van-text-color);
}

.reply-to {
  font-size: 0.72rem;
  color: var(--van-primary-color);
}

.comment-time {
  font-size: 0.7rem;
  color: var(--van-text-color-3);
}

.comment-content {
  font-size: 0.88rem;
  color: var(--van-text-color);
  line-height: 1.5;
  word-break: break-word;
}

.comment-actions {
  display: flex;
  gap: 16px;
  margin-top: 4px;
}

.action-btn {
  font-size: 0.72rem;
  color: var(--van-text-color-2);
  display: flex;
  align-items: center;
  gap: 3px;
  cursor: pointer;
}

.action-btn.danger {
  color: #ef4444;
}

/* 子评论 */
.replies {
  margin-top: 8px;
  padding-left: 8px;
  border-left: 2px solid var(--van-border-color);
}

.reply-item {
  display: flex;
  gap: 8px;
  padding: 8px 0;
}

.reply-body {
  flex: 1;
  min-width: 0;
}

.load-more {
  text-align: center;
  padding: 12px;
  font-size: 0.8rem;
  color: var(--van-primary-color);
  cursor: pointer;
}

/* 底部输入 */
.comment-input-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--van-background-2);
  border-top: 1px solid var(--van-border-color);
  padding: 8px 12px;
  z-index: 10;
}

.reply-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  color: var(--van-text-color-2);
  padding: 2px 0 6px;
}

.input-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.comment-field {
  flex: 1;
  background: var(--van-background);
  border-radius: 6px;
  padding: 4px 12px;
}
</style>
