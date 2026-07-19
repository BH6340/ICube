<template>
  <div class="my-posts-container">
    <div class="page-header">
      <h1>我的帖子</h1>
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
            <span v-if="post.is_pinned" class="pin-badge">置顶</span>
            <span v-if="post.is_essence" class="essence-badge">精华</span>
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

        <div class="post-stats">
          <span><el-icon><View /></el-icon> {{ post.view_count }}</span>
          <span><el-icon><Star /></el-icon> {{ post.like_count }}</span>
          <span><el-icon><ChatLineRound /></el-icon> {{ post.comment_count }}</span>
          <span class="time">{{ formatTime(post.created_at) }}</span>
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
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #303133;
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
  gap: 10px;
}

.post-title h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.pin-badge {
  background-color: #f56c6c;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.essence-badge {
  background-color: #e6a23c;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
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

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>