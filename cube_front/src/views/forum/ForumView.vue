<template>
  <div class="forum-container">
    <div class="forum-header">
      <h1>魔方论坛</h1>
      <el-button type="primary" @click="goToCreate" v-if="token">
        <el-icon><Edit /></el-icon>
        发布帖子
      </el-button>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-row :gutter="16">
        <el-col :xs="24" :sm="12" :md="8">
          <el-input
            v-model="searchParams.search"
            placeholder="搜索帖子标题"
            clearable
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          >
            <template #append>
              <el-button @click="handleSearch">
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
        </el-col>

        <el-col :xs="12" :sm="6" :md="4">
          <el-select v-model="searchParams.ordering" placeholder="排序" clearable @change="loadPosts">
            <el-option label="最新发布" value="-created_at" />
            <el-option label="最热" value="hot" />
            <el-option label="最多点赞" value="-like_count" />
            <el-option label="最多浏览" value="-view_count" />
          </el-select>
        </el-col>

        <el-col :xs="6" :sm="3" :md="2">
          <el-switch v-model="searchParams.is_pinned" active-text="置顶" @change="loadPosts" />
        </el-col>

        <el-col :xs="6" :sm="3" :md="2">
          <el-switch v-model="searchParams.is_essence" active-text="精华" @change="loadPosts" />
        </el-col>
      </el-row>
    </el-card>

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

        <div class="post-info">
          <span class="author">
            <el-avatar :size="24" :src="post.author?.image || defaultAvatar" />
            {{ post.author?.username }}
          </span>
          <span class="time">{{ formatTime(post.created_at) }}</span>
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
        </div>
      </el-card>
    </div>

    <div class="pagination">
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
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Search, View, Star, ChatLineRound, Edit } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getPosts } from '@/api/posts'
// 💡 标注修改：引入本地的默认头像 SVG 静态资源，保持和评论组件的逻辑同步
import defaultAvatar from '@/assets/default_avatar.svg'

const router = useRouter()
const token = computed(() => localStorage.getItem('token'))

const posts = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const searchParams = reactive({
  search: '',
  ordering: '-created_at',
  is_pinned: false,
  is_essence: false
})

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
      page_size: pageSize.value,
      search: searchParams.search || undefined,
      is_pinned: searchParams.is_pinned || undefined,
      is_essence: searchParams.is_essence || undefined
    }

    if (searchParams.ordering === 'hot') {
      const res = await getPosts({ ...params, hot: true })
      if (res.code === 100) {
        posts.value = res.data.results || []
        total.value = res.data.count || 0
      }
    } else {
      params.ordering = searchParams.ordering
      const res = await getPosts(params)
      if (res.code === 100) {
        posts.value = res.data.results || []
        total.value = res.data.count || 0
      }
    }
  } catch (error) {
    ElMessage.error('加载帖子失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadPosts()
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
.forum-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.forum-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.forum-header h1 {
  margin: 0;
  font-size: 28px;
  color: #409eff;
}

.filter-card {
  margin-bottom: 20px;
  border-radius: 12px;
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

.post-info {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
  color: #909399;
  font-size: 13px;
}

.author {
  display: flex;
  align-items: center;
  gap: 8px;
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

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>