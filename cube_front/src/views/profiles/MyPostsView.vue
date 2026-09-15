<template>
  <div class="my-posts-container">
    <div class="page-header">
      <el-button type="primary" @click="goToCreate">
        <el-icon><Edit /></el-icon>
        发布新帖
      </el-button>
    </div>

    <div class="posts-list" v-loading="loading">
      <el-card
        v-for="post in posts"
        :key="post.id"
        class="post-card"
        shadow="hover"
        @click="goToDetail(post.id)"
      >
        <div class="post-header">
          <div class="post-title">
            <div class="badges">
              <span v-if="post.is_pinned" class="pin-badge">置顶</span>
              <span v-if="post.is_essence" class="essence-badge">精华</span>
            </div>
            <h3>{{ post.title }}</h3>
          </div>
        </div>

        <div class="post-tags">
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

        <div class="post-content-preview" v-if="post.content_preview">
          {{ post.content_preview }}
        </div>

        <div class="post-stats">
          <span><el-icon><View /></el-icon> {{ post.view_count }}</span>
          <span><el-icon><Star /></el-icon> {{ post.like_count }}</span>
          <span><el-icon><ChatLineRound /></el-icon> {{ post.comment_count }}</span>
          <span class="time">{{ formatTime(post.created_at) }}</span>
        </div>

        <div class="post-comment-link" v-if="post.comment_count > 0" @click.stop="goToDetail(post.id)">
          查看 {{ post.comment_count }} 条评论
        </div>
      </el-card>

      <el-empty v-if="!loading && posts.length === 0" description="还没有发布过帖子" :image-size="80">
        <el-button type="primary" @click="goToCreate">去发布</el-button>
      </el-empty>
    </div>

    <div class="pagination" v-if="total > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadPosts"
        @current-change="loadPosts"
      />
    </div>
  </div>
</template>

<script setup>
/**
 * MyPostsView.vue - 我的帖子页面
 *
 * 核心职责：
 * 1. 展示当前用户发布的所有帖子列表
 * 2. 支持搜索、查看、编辑、删除帖子
 * 3. 显示帖子统计数据（浏览、评论、点赞）
 *
 * 功能特性：
 *   - 相对时间格式化：分钟前、小时前、天前
 *   - 分页加载，每页 20 条
 *   - 点击编辑跳转到帖子编辑器
 *
 * 设计要点：
 *   - 使用 getMyPosts API 加载当前用户帖子
 *   - 支持路由跳转到 PostEditorView 进行编辑
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, View, Star, ChatLineRound, Edit } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getMyPosts } from '@/api/posts'

const router = useRouter()

const posts = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const formatTime = (time) => {
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    const hours = Math.floor(diff / (1000 * 60 * 60))
    if (hours === 0) {
      const minutes = Math.floor(diff / (1000 * 60))
      return `${minutes}分钟前`
    }
    return `${hours}小时前`
  } else if (days < 7) {
    return `${days}天前`
  }
  return date.toLocaleDateString()
}

const loadPosts = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }

    const res = await getMyPosts(params)
    if (res.code === 100) {
      posts.value = res.data.results || []
      total.value = res.data.count || 0
    }
  } catch (error) {
    ElMessage.error('加载帖子失败')
  } finally {
    loading.value = false
  }
}

const goToDetail = (id) => {
  router.push(`/forum/post/${id}`)
}

const goToCreate = () => {
  router.push('/forum/create')
}

onMounted(() => {
  loadPosts()
})
</script>

<style scoped>
.my-posts-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 20px;
}

.posts-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.post-card {
  cursor: pointer;
  transition: all 0.3s;
  border-radius: 12px;
}

.post-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.post-header {
  margin-bottom: 12px;
}

.post-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.post-title .badges {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.post-title h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pin-badge {
  background-color: #f56c6c;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  flex-shrink: 0;
}

.essence-badge {
  background-color: #e6a23c;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  flex-shrink: 0;
}

.post-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.post-stats {
  display: flex;
  gap: 20px;
  color: #909399;
  font-size: 13px;
}

.post-stats span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.post-stats .time {
  margin-left: auto;
}

.post-content-preview {
  color: #909399;
  font-size: 14px;
  line-height: 1.5;
  margin: 8px 0 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.post-comment-link {
  margin-top: 8px;
  padding: 6px 10px;
  background-color: #f5f7fa;
  border-radius: 6px;
  font-size: 13px;
  color: #909399;
  cursor: pointer;
  transition: color 0.2s;
}

.post-comment-link:hover {
  color: #409eff;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .my-posts-container {
    padding: 12px 8px;
  }

  .page-header {
    margin-bottom: 12px;
    padding-top: 2px;
  }

  .post-card {
    padding: 12px;
  }

  .post-title h3 {
    font-size: 16px;
  }

  .post-stats {
    flex-wrap: wrap;
    gap: 12px;
    font-size: 12px;
  }

  .post-stats .time {
    margin-left: 0;
    width: 100%;
  }

  .post-content-preview {
    font-size: 13px;
    margin: 6px 0 10px;
  }

  .post-comment-link {
    font-size: 12px;
    padding: 5px 8px;
  }

  .pagination :deep(.el-pagination) {
    font-size: 12px;
  }
}

@media (max-width: 480px) {
  .my-posts-container {
    padding: 8px 4px;
  }

  .post-title h3 {
    font-size: 15px;
  }

  .post-tags {
    gap: 6px;
  }

  .post-stats {
    gap: 10px;
    font-size: 11px;
  }
}
</style>