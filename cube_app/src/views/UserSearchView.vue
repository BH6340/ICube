<script setup>
/**
 * UserSearchView.vue — 魔友搜索页面
 *
 * 搜索用户并显示结果列表，支持关注/取消关注，点击跳转用户主页。
 */
import { showToast } from 'vant'
import { useUserStore } from '@/stores/user'
import {
  searchUsersApi,
  followUserApi,
  unfollowUserApi,
} from '@/api/user'
import UserCard from '@/components/user/UserCard.vue'

const router = useRouter()
const userStore = useUserStore()

const searchValue = ref('')
const userList = ref([])
const loading = ref(false)
const finished = ref(false)
const page = ref(1)
const searching = ref(false)
const hasSearched = ref(false)
const actionLoadingMap = ref({})

async function onSearch() {
  const q = searchValue.value.trim()
  if (!q) {
    showToast('请输入搜索关键词')
    return
  }
  hasSearched.value = true
  userList.value = []
  page.value = 1
  finished.value = false
  await loadUsers()
}

async function loadUsers() {
  if (loading.value || finished.value) return
  loading.value = true
  try {
    const res = await searchUsersApi({
      search: searchValue.value.trim(),
      page: page.value,
      page_size: 20,
    })
    const data = res.data || res
    const results = data.results || data || []
    userList.value.push(...results)
    if (results.length < 20) {
      finished.value = true
    } else {
      page.value++
    }
  } catch {
    finished.value = true
  } finally {
    loading.value = false
  }
}

function goToProfile(username) {
  router.push({ name: 'UserProfile', params: { username } })
}

async function onToggleFollow(user) {
  if (!userStore.token) {
    router.push({ name: 'login', query: { redirect: router.currentRoute.value.fullPath } })
    return
  }
  actionLoadingMap.value[user.username] = true
  try {
    if (user.following) {
      await unfollowUserApi(user.username)
      user.following = false
    } else {
      await followUserApi(user.username)
      user.following = true
    }
  } catch {
    showToast('操作失败')
  } finally {
    actionLoadingMap.value[user.username] = false
  }
}
</script>

<template>
  <div class="page">
    <van-nav-bar title="魔友搜索" placeholder left-arrow @click-left="router.back()" />

    <van-search
      v-model="searchValue"
      placeholder="搜索用户名"
      show-action
      @search="onSearch"
      @clear="hasSearched = false; userList = []"
    >
      <template #action>
        <div @click="onSearch">搜索</div>
      </template>
    </van-search>

    <div class="page-content">
      <van-list
        v-if="hasSearched"
        v-model:loading="loading"
        :finished="finished"
        finished-text="没有更多了"
        @load="loadUsers"
      >
        <UserCard
          v-for="user in userList"
          :key="user.username"
          :user="user"
          :current-username="userStore.username"
          :action-loading="!!actionLoadingMap[user.username]"
          @view="goToProfile"
          @toggle-follow="onToggleFollow"
        />
      </van-list>

      <van-empty
        v-else
        description="搜索魔友，发现更多精彩内容"
      />

      <van-empty
        v-if="hasSearched && userList.length === 0 && !loading"
        description="没有找到匹配的用户"
      />
    </div>
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
  padding-bottom: 16px;
}
</style>
