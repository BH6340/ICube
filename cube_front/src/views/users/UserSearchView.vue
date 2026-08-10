<template>
  <main class="user-search-page">
    <header class="page-header">
      <div>
        <h1>魔友</h1>
        <p>按用户名找到一起交流魔方的伙伴</p>
      </div>
      <span v-if="keyword" class="result-count">找到 {{ total }} 位魔友</span>
    </header>

    <el-card class="search-panel" shadow="never">
      <el-input
        v-model="searchInput"
        size="large"
        clearable
        placeholder="输入用户名"
        aria-label="搜索用户名"
        @keyup.enter="submitSearch"
        @clear="submitSearch"
      >
        <template #append>
          <el-button type="primary" @click="submitSearch">搜索</el-button>
        </template>
      </el-input>
    </el-card>

    <section
      v-loading="loading"
      class="results-section"
      aria-live="polite"
    >
      <div v-if="errorMessage && !loading" class="state-card error-state">
        <h2>搜索没有完成</h2>
        <p>{{ errorMessage }}</p>
        <el-button type="primary" plain @click="loadUsers">重新搜索</el-button>
      </div>

      <el-empty
        v-else-if="!keyword && !loading"
        description="输入用户名开始搜索"
        :image-size="110"
      />

      <el-empty
        v-else-if="keyword && !users.length && !loading"
        description="没有找到匹配的魔友"
        :image-size="110"
      />

      <div v-else class="user-grid">
        <UserCard
          v-for="user in users"
          :key="user.username"
          :user="user"
          :current-username="userStore.username"
          :action-loading="actionLoading.has(user.username)"
          @view="viewProfile"
          @toggle-follow="toggleFollow"
        />
      </div>
    </section>

    <div v-if="total > pageSize" class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="changePage"
      />
    </div>
  </main>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  followUserApi,
  searchUsersApi,
  unfollowUserApi
} from '@/api/user'
import UserCard from '@/components/user/UserCard.vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const searchInput = ref('')
const keyword = ref('')
const users = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20
const loading = ref(false)
const errorMessage = ref('')
const actionLoading = reactive(new Set())
let requestVersion = 0

const loadUsers = async () => {
  if (!keyword.value) return

  const version = ++requestVersion
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await searchUsersApi({
      search: keyword.value,
      page: currentPage.value,
      page_size: pageSize
    })
    if (version !== requestVersion) return

    users.value = response.data?.results || []
    total.value = response.data?.count || 0
  } catch {
    if (version !== requestVersion) return
    users.value = []
    total.value = 0
    errorMessage.value = '请检查网络连接后重试'
  } finally {
    if (version === requestVersion) loading.value = false
  }
}

const submitSearch = () => {
  const query = searchInput.value.trim()
  const routeQuery = Array.isArray(route.query.q)
    ? route.query.q[0]
    : route.query.q

  if (query === (routeQuery || '').trim()) {
    currentPage.value = 1
    if (query) loadUsers()
    return
  }

  router.push({
    name: 'userSearch',
    query: query ? { q: query } : {}
  })
}

const changePage = () => {
  loadUsers()
}

const viewProfile = (username) => {
  router.push({
    name: 'userProfile',
    params: { username }
  })
}

const toggleFollow = async (user) => {
  if (!userStore.token) {
    router.push({
      name: 'login',
      query: { redirect: route.fullPath }
    })
    return
  }

  actionLoading.add(user.username)
  try {
    if (user.following) {
      await unfollowUserApi(user.username)
      user.following = false
      ElMessage.success(`已取消关注 ${user.username}`)
    } else {
      await followUserApi(user.username)
      user.following = true
      ElMessage.success(`已关注 ${user.username}`)
    }
  } finally {
    actionLoading.delete(user.username)
  }
}

watch(
  () => route.query.q,
  (query) => {
    const normalized = Array.isArray(query) ? query[0] : query
    keyword.value = (normalized || '').trim()
    searchInput.value = keyword.value
    currentPage.value = 1
    users.value = []
    total.value = 0
    errorMessage.value = ''

    if (keyword.value) {
      loadUsers()
    } else {
      requestVersion++
      loading.value = false
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.user-search-page {
  width: 100%;
  max-width: 1000px;
  min-height: 560px;
  margin: 0 auto;
  padding: 32px 20px 48px;
}

.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  color: #409eff;
  font-size: 30px;
  line-height: 1.2;
}

.page-header p {
  margin: 8px 0 0;
  color: #606266;
  font-size: 15px;
}

.result-count {
  color: #909399;
  font-size: 13px;
  white-space: nowrap;
}

.search-panel {
  margin-bottom: 24px;
  border-color: #e4e7ed;
  border-radius: 12px;
}

.search-panel :deep(.el-card__body) {
  padding: 20px;
}

.search-panel :deep(.el-input-group__append) {
  padding: 0;
  overflow: hidden;
  background: #409eff;
  border-color: #409eff;
}

.search-panel :deep(.el-input-group__append .el-button) {
  height: 100%;
  padding: 0 28px;
  color: #fff;
}

.results-section {
  min-height: 300px;
}

.user-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.state-card {
  display: flex;
  min-height: 260px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px;
  text-align: center;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
}

.state-card h2 {
  margin: 0;
  color: #303133;
  font-size: 18px;
}

.state-card p {
  margin: 10px 0 20px;
  color: #606266;
}

.error-state {
  border-color: #fab6b6;
  background: #fef0f0;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 28px;
}

@media (max-width: 720px) {
  .user-search-page {
    padding: 24px 14px 40px;
  }

  .page-header {
    align-items: flex-start;
  }

  .user-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 460px) {
  .page-header {
    flex-direction: column;
    gap: 8px;
  }

  .search-panel :deep(.el-input-group__append .el-button) {
    padding-inline: 18px;
  }
}
</style>
