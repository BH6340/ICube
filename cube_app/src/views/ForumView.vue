<script setup>
/**
 * ForumView.vue — 论坛列表页
 *
 * 四栏排序（最新/最热/精华/我的帖子）、搜索、下拉刷新、上拉加载。
 * 匿名用户可浏览，"我的帖子"需登录。
 */
defineOptions({ name: 'ForumView' })

import { ref, watch, onMounted, onActivated } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import PostCard from '@/components/forum/PostCard.vue'
import { getPosts, getHotPosts, getMyPosts } from '@/api/forum'

const router = useRouter()
const route = useRoute()

// ─── 响应式状态 ──────────────────────────────────────
const searchKeyword = ref('')
const activeTab = ref(0)  // 0=最新 1=最热 2=精华 3=我的帖子
const postList = ref([])
const loading = ref(false)
const finished = ref(false)
const refreshing = ref(false)
const page = ref(1)
const pageSize = 20

// ─── 数据加载 ────────────────────────────────────────
async function loadPosts(reset = false) {
  if (reset) {
    page.value = 1
    finished.value = false
    loading.value = true
  }

  // "我的帖子"需登录
  if (activeTab.value === 3 && !localStorage.getItem('token')) {
    showToast('请先登录')
    router.push({ name: 'login', query: { redirect: '/forum' } })
    loading.value = false
    return
  }

  try {
    let res
    const params = { page: page.value, page_size: pageSize }

    if (activeTab.value === 3) {
      // 我的帖子
      res = await getMyPosts(params)
    } else if (activeTab.value === 1) {
      // 最热
      res = await getHotPosts({ days: 30, limit: 50 })
    } else {
      // 最新 / 精华
      if (searchKeyword.value) params.search = searchKeyword.value
      if (activeTab.value === 2) params.is_essence = true
      params.ordering = '-created_at'
      res = await getPosts(params)
    }

    // 兼容分页格式 {results:[]} 和非分页格式 {posts:[]}
    const results = res.data?.results || res.posts || res.data || []
    if (Array.isArray(results)) {
      if (reset) {
        postList.value = results
      } else {
        postList.value.push(...results)
      }
      const count = res.data?.count || results.length
      if (postList.value.length >= count || results.length < pageSize) {
        finished.value = true
      }
    } else {
      finished.value = true
    }
  } catch {
    finished.value = true
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

// ─── 事件处理 ────────────────────────────────────────
function onLoad() {
  if (finished.value) return
  page.value++
  loadPosts()
}

function onRefresh() {
  loadPosts(true)
}

function onSearch() {
  if (activeTab.value === 1 || activeTab.value === 3) {
    activeTab.value = 0
  }
  loadPosts(true)
}

function onTabChange() {
  searchKeyword.value = ''
  loadPosts(true)
}

function goToDetail(id) {
  router.push({ name: 'PostDetail', params: { id } })
}

// ─── 从个人中心跳转时，根据 query.filter 切换 Tab ────
watch(() => route.query.filter, (filter) => {
  if (filter === 'my_posts') {
    activeTab.value = 3
    loadPosts(true)
  }
}, { immediate: true })

// 首次挂载时加载数据（无 filter 参数时也加载）
onMounted(() => {
  if (postList.value.length === 0) {
    loadPosts(true)
  }
})

// keep-alive 重新激活时，如果 filter 变化则重新加载
onActivated(() => {
  if (route.query.filter === 'my_posts' && activeTab.value !== 3) {
    activeTab.value = 3
    loadPosts(true)
  }
})
</script>

<template>
  <div class="page">
    <van-nav-bar title="论坛" placeholder />

    <!-- 搜索栏 -->
    <van-search
      v-model="searchKeyword"
      placeholder="搜索帖子"
      shape="round"
      @search="onSearch"
      @clear="onSearch"
    />

    <!-- 排序栏 -->
    <van-tabs v-model:active="activeTab" @change="onTabChange" shrink swipeable>
      <van-tab title="最新" />
      <van-tab title="最热" />
      <van-tab title="精华" />
      <van-tab title="我的" />
    </van-tabs>

    <!-- 帖子列表 -->
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh" class="list-container">
      <van-list
        v-model:loading="loading"
        :finished="finished"
        finished-text="没有更多了"
        @load="onLoad"
        :immediate-check="false"
      >
        <PostCard
          v-for="post in postList"
          :key="post.id"
          :post="post"
          @click="goToDetail"
        />
        <van-empty v-if="!loading && postList.length === 0" description="暂无帖子" />
      </van-list>
    </van-pull-refresh>
  </div>
</template>

<style scoped>
.page {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.list-container {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 8px;
}
</style>
