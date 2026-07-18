<!-- src/views/forum/PostDetail.vue -->
<template>
  <div class="post-detail-container" v-loading="loading">
    <div v-if="post">
      <!-- 帖子内容卡片 -->
      <el-card class="post-card" shadow="never">
        <div class="post-header">
          <div class="title-section">
            <div class="badges">
              <el-tag v-if="post.is_pinned" type="danger" size="small" effect="dark">置顶</el-tag>
              <el-tag v-if="post.is_essence" type="warning" size="small" effect="dark">精华</el-tag>
              <el-tag v-if="post.is_closed" type="info" size="small">已关闭评论</el-tag>
            </div>
            <h1 class="post-title">{{ post.title }}</h1>
          </div>

          <div class="author-section">
            <div class="author-info" @click="goToProfile(post.author?.username)">
              <el-avatar :size="48" :src="post.author?.image" />
              <div class="author-details">
                <div class="author-name">{{ post.author?.username }}</div>
                <div class="post-time">
                  发布于 {{ formatDateTime(post.created_at) }}
                  <span v-if="post.updated_at !== post.created_at">
                    · 最后编辑于 {{ formatDateTime(post.updated_at) }}
                  </span>
                </div>
              </div>
            </div>

            <div class="post-actions" v-if="isLoggedIn">
              <el-button
                :type="post.is_liked ? 'primary' : 'default'"
                @click="handleLike"
              >
               👍{{post.is_liked? '已点赞' : '点赞'}}{{ post.like_count }}
              </el-button>

              <el-button
                :type="post.is_collected ? 'warning' : 'default'"
                @click="handleCollect"
              >
                <el-icon><FolderChecked v-if="post.is_collected" /><Folder v-else /></el-icon>
                {{ post.is_collected ? '已收藏' : '收藏' }}
              </el-button>

              <el-button
                v-if="isOwner"
                @click="goToEdit"
                :icon="Edit"
              >
                编辑
              </el-button>

              <el-button
                v-if="isOwner || isAdmin"
                type="danger"
                @click="handleDelete"
                :icon="Delete"
              >
                删除
              </el-button>
            </div>
          </div>
        </div>

        <div class="post-stats">
          <span><el-icon><View /></el-icon> {{ post.view_count }} 次浏览</span>
          <span><el-icon><ChatLineRound /></el-icon> {{ post.comment_count }} 条评论</span>
          <span><el-icon><Star /></el-icon> {{ post.like_count }} 人点赞</span>
        </div>

        <div class="post-tags" v-if="post.tags && post.tags.length">
          <span class="tags-label">标签：</span>
          <el-tag
            v-for="tag in post.tags"
            :key="tag.id"
            :color="tag.color"
            size="small"
            effect="plain"
            style="color: white"
          >
            {{ tag.name }}
          </el-tag>
        </div>

        <!-- Markdown 内容 -->
        <div class="post-content markdown-body" v-html="renderedContent"></div>
      </el-card>

      <!-- 评论区 -->
      <el-card class="comments-card" shadow="never">
        <template #header>
          <div class="comments-header">
            <h3>评论 <span class="comment-count">({{ post.comment_count }})</span></h3>
          </div>
        </template>

        <CommentSection
          :post-id="post.id"
          @comment-added="onCommentAdded"
          @comment-count-updated="updateCommentCount"
        />
      </el-card>
    </div>

    <!-- 加载失败显示 -->
    <div v-else-if="!loading && error" class="error-container">
      <el-result
        icon="error"
        title="加载失败"
        :sub-title="error"
      >
        <template #extra>
          <el-button type="primary" @click="loadPost">重新加载</el-button>
          <el-button @click="goBack">返回首页</el-button>
        </template>
      </el-result>
    </div>

    <el-backtop :right="40" :bottom="40" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { View, Star, StarFilled, Folder, FolderChecked, Delete, ChatLineRound } from '@element-plus/icons-vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import 'github-markdown-css/github-markdown.css'

import { getPost, likePost, collectPost, deletePost } from '@/api/posts'
import CommentSection from '@/components/forum/CommentSection.vue'

const router = useRouter()
const route = useRoute()

const post = ref(null)
const loading = ref(false)
const error = ref('')

// 用户状态
const isLoggedIn = computed(() => !!localStorage.getItem('token'))
const currentUsername = computed(() => localStorage.getItem('username') || '')
const isOwner = computed(() => post.value?.author?.username === currentUsername.value)
const isAdmin = computed(() => false)

// 配置 marked
marked.setOptions({
  highlight: function(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,
  gfm: true
})

const renderedContent = computed(() => {
  if (post.value?.content) {
    return marked(post.value.content)
  }
  return '<p>暂无内容</p>'
})

const formatDateTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const loadPost = async () => {
  const id = route.params.id
  if (!id) {
    error.value = '帖子不存在'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const res = await getPost(id)
    console.log('Post Detail Response:', res)

    if (res.code === 100) {
      // 数据在 res.post 中
      post.value = res.post
      document.title = `${post.value.title} - 魔方论坛`
    } else if (res.code === 404) {
      error.value = '帖子不存在或已被删除'
    } else {
      error.value = res.msg || '加载失败'
    }
  } catch (err) {
    console.error('加载帖子失败:', err)
    error.value = err.message || '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}

const handleLike = async () => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    await router.push('/login')
    return
  }

  try {
    const res = await likePost(post.value.id)
    if (res.code === 100) {
      post.value.is_liked = res.liked
      post.value.like_count = res.like_count
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleCollect = async () => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    await router.push('/login')
    return
  }

  try {
    const res = await collectPost(post.value.id)
    if (res.code === 100) {
      post.value.is_collected = res.collected
      post.value.collect_count = res.collect_count
      ElMessage.success(res.collected ? '收藏成功' : '已取消收藏')
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const goToEdit = () => {
  router.push(`/forum/edit/${post.value.id}`)
}

const handleDelete = async () => {
  ElMessageBox.confirm('确定要删除这个帖子吗？删除后无法恢复！', '警告', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await deletePost(post.value.id)
      if (res.code === 100) {
        ElMessage.success('删除成功')
        router.push('/forum')
      } else {
        ElMessage.error(res.msg || '删除失败')
      }
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const goToProfile = (username) => {
  if (username) {
    router.push(`/profiles/info?username=${username}`)
  }
}

const goBack = () => {
  router.back()
}

const onCommentAdded = () => {
  loadPost()
}

const updateCommentCount = () => {
  if (post.value) {
    post.value.comment_count++
  }
}

onUnmounted(() => {
  document.title = '魔方学习平台'
})

onMounted(() => {
  loadPost()
})
</script>

<style scoped>
.post-detail-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.post-card {
  border-radius: 12px;
  margin-bottom: 20px;
}

.post-header {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.title-section {
  margin-bottom: 20px;
}

.badges {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.post-title {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  line-height: 1.4;
}

.author-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.author-info:hover .author-name {
  color: #409eff;
}

.author-details {
  display: flex;
  flex-direction: column;
}

.author-name {
  font-weight: 500;
  font-size: 16px;
  color: #303133;
  transition: color 0.2s;
}

.post-time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.post-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.post-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
  color: #909399;
  font-size: 14px;
}

.post-stats span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.post-tags {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.tags-label {
  font-size: 14px;
  color: #606266;
}

.post-content {
  padding: 20px 0;
  min-height: 300px;
  font-size: 16px;
  line-height: 1.8;
}

.comments-card {
  border-radius: 12px;
}

.comments-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
}

.comment-count {
  color: #909399;
  font-size: 14px;
  font-weight: normal;
}

.error-container {
  padding: 60px 20px;
  text-align: center;
}

@media (max-width: 768px) {
  .post-detail-container {
    padding: 12px;
  }

  .post-title {
    font-size: 22px;
  }

  .author-section {
    flex-direction: column;
    align-items: flex-start;
  }

  .post-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>