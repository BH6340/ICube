<script setup>
/**
 * UserProfileView.vue — 用户主页
 *
 * 展示用户资料、关注按钮，以及帖子/收藏/公式/关注/粉丝五个 Tab。
 */
import { showToast } from 'vant'
import { useUserStore } from '@/stores/user'
import {
  getProfileApi,
  followUserApi,
  unfollowUserApi,
  getFollowingListApi,
  getFollowersListApi,
} from '@/api/user'
import { getPosts } from '@/api/forum'
import {
  getUserCustomFormulas,
  getUserFormulaCollections,
} from '@/api/formula'
import { buildMediaUrl } from '@/utils/media-url'
import UserCard from '@/components/user/UserCard.vue'
import PostCard from '@/components/forum/PostCard.vue'
import FormulaCard from '@/components/formula/FormulaCard.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const username = computed(() => route.params.username)
const profile = ref(null)
const loading = ref(false)
const followLoading = ref(false)
const activeTab = ref('posts')

const avatarUrl = computed(() => {
  if (!profile.value) return ''
  return buildMediaUrl(profile.value.image)
})

const isSelf = computed(() => username.value === userStore.username)
const isFollowing = computed(() => !!profile.value?.following)

// ─── Tab 状态 ──────────────────────────────
const tabs = [
  { name: 'posts', label: '帖子' },
  { name: 'collections', label: '收藏' },
  { name: 'formulas', label: '公式' },
  { name: 'following', label: '关注' },
  { name: 'followers', label: '粉丝' },
]

const tabData = reactive({
  posts: { list: [], page: 1, loading: false, finished: false },
  collections: { list: [], page: 1, loading: false, finished: false },
  formulas: { list: [], page: 1, loading: false, finished: false },
  following: { list: [], page: 1, loading: false, finished: false },
  followers: { list: [], page: 1, loading: false, finished: false },
})

const loadFns = {
  posts: (p) => getPosts({ author_username: username.value, page: p, page_size: 10 }),
  collections: (p) => getUserFormulaCollections(username.value, { page: p, page_size: 12 }),
  formulas: (p) => getUserCustomFormulas(username.value, { page: p, page_size: 12 }),
  following: (p) => getFollowingListApi(username.value, { page: p, page_size: 20 }),
  followers: (p) => getFollowersListApi(username.value, { page: p, page_size: 20 }),
}

async function loadTab(tabName) {
  const state = tabData[tabName]
  if (state.loading || state.finished) return
  state.loading = true
  try {
    const res = await loadFns[tabName](state.page)
    const data = res.data || res
    const results = data.results || data || []
    if (tabName === 'posts') {
      state.list.push(...results)
    } else if (tabName === 'collections' || tabName === 'formulas') {
      state.list.push(...results)
    } else {
      state.list.push(...results)
    }
    if (results.length < (tabName === 'posts' ? 10 : tabName === 'collections' || tabName === 'formulas' ? 12 : 20)) {
      state.finished = true
    } else {
      state.page++
    }
  } catch {
    state.finished = true
  } finally {
    state.loading = false
  }
}

function onTabChange(tab) {
  const tabName = tab.name
  if (tabData[tabName].list.length === 0 && !tabData[tabName].finished) {
    loadTab(tabName)
  }
}

function goToPostDetail(id) {
  router.push({ name: 'PostDetail', params: { id } })
}

function goToFormulaDetail(id) {
  router.push({ name: 'FormulaDetail', params: { id } })
}

function goToUserProfile(uname) {
  if (uname === username.value) return
  router.push({ name: 'UserProfile', params: { username: uname } })
}

async function onToggleFollow(user) {
  const state = activeTab.value === 'following' ? tabData.following : tabData.followers
  const u = state.list.find(x => x.username === user.username)
  if (!u) return
  if (user.following) {
    await unfollowUserApi(user.username)
    u.following = false
  } else {
    await followUserApi(user.username)
    u.following = true
  }
}

async function toggleFollow() {
  if (!userStore.token) {
    router.push({ name: 'login' })
    return
  }
  followLoading.value = true
  try {
    if (isFollowing.value) {
      await unfollowUserApi(username.value)
      profile.value.following = false
      if (profile.value.followers_count > 0) profile.value.followers_count--
    } else {
      await followUserApi(username.value)
      profile.value.following = true
      profile.value.followers_count++
    }
  } catch {
    showToast('操作失败')
  } finally {
    followLoading.value = false
  }
}

async function loadProfile() {
  loading.value = true
  try {
    const res = await getProfileApi(username.value)
    profile.value = res.data?.profiles || res.data || res
  } catch {
    showToast('用户不存在')
    router.back()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadProfile()
  loadTab('posts')
})
</script>

<template>
  <div class="page">
    <van-nav-bar :title="username" placeholder left-arrow @click-left="router.back()" />

    <div class="page-content">
      <!-- 用户资料卡片 -->
      <div v-if="profile" class="profile-card">
        <van-image round width="64" height="64" :src="avatarUrl" fit="cover">
          <template #error>
            <div class="avatar-fallback">{{ username?.[0] || '?' }}</div>
          </template>
        </van-image>
        <div class="profile-info">
          <div class="profile-name">{{ profile.username }}</div>
          <div class="profile-bio">{{ profile.bio || '这个人很懒，什么都没写' }}</div>
        </div>
        <van-button
          v-if="!isSelf"
          :type="isFollowing ? 'default' : 'primary'"
          size="small"
          round
          :loading="followLoading"
          @click="toggleFollow"
        >
          {{ isFollowing ? '已关注' : '关注' }}
        </van-button>
      </div>

      <!-- 统计数据 -->
      <div v-if="profile" class="stats-row">
        <div class="stat-item" @click="activeTab = 'posts'; onTabChange({ name: 'posts' })">
          <span class="stat-value">{{ profile.post_count || 0 }}</span>
          <span class="stat-label">帖子</span>
        </div>
        <div class="stat-item" @click="activeTab = 'collections'; onTabChange({ name: 'collections' })">
          <span class="stat-value">{{ profile.collection_count || 0 }}</span>
          <span class="stat-label">收藏</span>
        </div>
        <div class="stat-item" @click="activeTab = 'formulas'; onTabChange({ name: 'formulas' })">
          <span class="stat-value">{{ profile.custom_formula_count || 0 }}</span>
          <span class="stat-label">公式</span>
        </div>
        <div class="stat-item" @click="activeTab = 'following'; onTabChange({ name: 'following' })">
          <span class="stat-value">{{ profile.following_count || 0 }}</span>
          <span class="stat-label">关注</span>
        </div>
        <div class="stat-item" @click="activeTab = 'followers'; onTabChange({ name: 'followers' })">
          <span class="stat-value">{{ profile.followers_count || 0 }}</span>
          <span class="stat-label">粉丝</span>
        </div>
      </div>

      <!-- Tab 内容 -->
      <van-tabs v-model:active="activeTab" @change="onTabChange" sticky>
        <van-tab v-for="tab in tabs" :key="tab.name" :name="tab.name" :title="tab.label">
          <van-list
            v-model:loading="tabData[tab.name].loading"
            :finished="tabData[tab.name].finished"
            finished-text="没有更多了"
            @load="loadTab(tab.name)"
          >
            <!-- 帖子 -->
            <template v-if="tab.name === 'posts'">
              <PostCard
                v-for="post in tabData.posts.list"
                :key="post.id"
                :post="post"
                @click="goToPostDetail"
              />
            </template>

            <!-- 收藏 & 公式 -->
            <template v-else-if="tab.name === 'collections' || tab.name === 'formulas'">
              <FormulaCard
                v-for="formula in tabData[tab.name].list"
                :key="formula.id"
                :formula="formula"
                @click="goToFormulaDetail"
              />
            </template>

            <!-- 关注 & 粉丝 -->
            <template v-else>
              <UserCard
                v-for="u in tabData[tab.name].list"
                :key="u.username"
                :user="u"
                :current-username="userStore.username"
                @view="goToUserProfile"
                @toggle-follow="onToggleFollow"
              />
            </template>
          </van-list>

          <van-empty
            v-if="tabData[tab.name].finished && tabData[tab.name].list.length === 0"
            :description="`暂无${tab.label}`"
          />
        </van-tab>
      </van-tabs>
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
}

.avatar-fallback {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--van-primary-color);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 700;
}

.profile-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 16px;
  margin: 0;
  background: var(--van-background-2);
}

.profile-info {
  flex: 1;
  min-width: 0;
}

.profile-name {
  font-size: 1.15rem;
  font-weight: 700;
  margin-bottom: 4px;
}

.profile-bio {
  font-size: 0.85rem;
  color: var(--van-text-color-2);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.stats-row {
  display: flex;
  justify-content: space-around;
  padding: 12px 8px;
  background: var(--van-background-2);
  border-top: 1px solid var(--van-border-color);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 4px 8px;
}

.stat-item:active {
  opacity: 0.6;
}

.stat-value {
  font-size: 1.1rem;
  font-weight: 700;
}

.stat-label {
  font-size: 0.72rem;
  color: var(--van-text-color-2);
}
</style>
