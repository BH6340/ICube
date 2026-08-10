<template>
  <main class="public-profile-page">
    <div v-if="profileLoading" class="loading-shell" v-loading="true"></div>

    <section v-else-if="notFound" class="page-state">
      <h1>用户不存在或已停用</h1>
      <p>该主页当前无法访问。</p>
      <el-button type="primary" plain @click="router.push({ name: 'userSearch' })">
        返回魔友搜索
      </el-button>
    </section>

    <section v-else-if="profileError" class="page-state error-state">
      <h1>加载用户资料失败</h1>
      <p>请检查网络连接后重试。</p>
      <el-button type="primary" @click="loadProfile">重新加载</el-button>
    </section>

    <template v-else-if="profile">
      <section class="profile-card">
        <div class="profile-accent" aria-hidden="true">
          <span></span>
          <span></span>
          <span></span>
        </div>

        <div class="profile-main">
          <el-avatar
            class="profile-avatar"
            :size="88"
            :src="profile.image || defaultAvatar"
            :alt="`${profile.username} 的头像`"
          />
          <div class="profile-copy">
            <h1>{{ profile.username }}</h1>
            <p>{{ profile.bio || '暂无简介' }}</p>
          </div>
          <el-button
            v-if="isSelf"
            type="primary"
            plain
            @click="router.push('/profiles/info')"
          >
            进入个人中心
          </el-button>
          <el-button
            v-else
            :type="profile.following ? 'default' : 'primary'"
            :loading="profileFollowLoading"
            @click="toggleProfileFollow"
          >
            {{ profile.following ? '已关注' : '关注' }}
          </el-button>
        </div>

        <div class="stat-groups">
          <div class="stat-group">
            <span class="group-label">内容</span>
            <button type="button" class="stat-item" @click="activateTab('posts')">
              <strong>{{ profile.post_count }}</strong>
              <span>文章</span>
            </button>
          </div>
          <div class="stat-group">
            <span class="group-label">公式</span>
            <button type="button" class="stat-item" @click="activateTab('collections')">
              <strong>{{ profile.collection_count }}</strong>
              <span>收藏</span>
            </button>
            <button type="button" class="stat-item" @click="activateTab('customFormulas')">
              <strong>{{ profile.custom_formula_count }}</strong>
              <span>自创</span>
            </button>
          </div>
          <div class="stat-group">
            <span class="group-label">关系</span>
            <button type="button" class="stat-item" @click="activateTab('following')">
              <strong>{{ profile.following_count }}</strong>
              <span>关注</span>
            </button>
            <button type="button" class="stat-item" @click="activateTab('followers')">
              <strong>{{ profile.followers_count }}</strong>
              <span>粉丝</span>
            </button>
          </div>
        </div>
      </section>

      <section class="profile-content">
        <el-tabs v-model="activeTab" @tab-change="loadTab">
          <el-tab-pane label="文章" name="posts" />
          <el-tab-pane label="公式收藏" name="collections" />
          <el-tab-pane label="自创公式" name="customFormulas" />
          <el-tab-pane label="关注" name="following" />
          <el-tab-pane label="粉丝" name="followers" />
        </el-tabs>

        <div class="tab-content" v-loading="activeState.loading">
          <div v-if="activeState.error" class="tab-state error-state">
            <p>{{ activeState.error }}</p>
            <el-button type="primary" plain @click="retryActiveTab">重试</el-button>
          </div>

          <div
            v-else-if="activeTab === 'posts' && activeState.items.length"
            class="post-list"
          >
            <article
              v-for="post in activeState.items"
              :key="post.id"
              class="post-card"
              tabindex="0"
              @click="openPost(post.id)"
              @keydown.enter="openPost(post.id)"
            >
              <div class="post-main">
                <div class="post-title-row">
                  <el-tag v-if="post.is_pinned" size="small" type="danger">置顶</el-tag>
                  <el-tag v-if="post.is_essence" size="small" type="warning">精华</el-tag>
                  <h2>{{ post.title }}</h2>
                </div>
                <div class="post-meta">
                  <el-avatar
                    :size="24"
                    :src="post.author?.image || defaultAvatar"
                    :alt="`${post.author?.username || profile.username} 的头像`"
                  />
                  <span>{{ post.author?.username }}</span>
                  <time>{{ formatDate(post.created_at) }}</time>
                </div>
                <div v-if="post.tags?.length" class="post-tags">
                  <el-tag
                    v-for="tag in post.tags"
                    :key="tag.id"
                    size="small"
                    effect="plain"
                  >
                    {{ tag.name }}
                  </el-tag>
                </div>
                <div class="post-stats">
                  <span>浏览 {{ post.view_count }}</span>
                  <span>点赞 {{ post.like_count }}</span>
                  <span>评论 {{ post.comment_count }}</span>
                </div>
              </div>
              <div v-if="post.images?.length" class="post-image">
                <img
                  :src="post.images[0].image_url"
                  :alt="post.images[0].alt || post.title"
                />
              </div>
            </article>
          </div>

          <div
            v-else-if="isFormulaTab && activeState.items.length"
            class="formula-grid"
          >
            <article
              v-for="formula in activeState.items"
              :key="formula.id"
              class="formula-card"
            >
              <div class="formula-header">
                <h2>{{ formula.name }}</h2>
                <el-tag
                  :type="difficultyTagType(formula.difficulty)"
                  size="small"
                  effect="plain"
                >
                  {{ difficultyLabel(formula.difficulty) }}
                </el-tag>
              </div>
              <div class="formula-notation">{{ formula.notation }}</div>
              <div class="formula-thumbnail">
                <img
                  v-if="formula.thumbnail"
                  :src="formula.thumbnail"
                  :alt="`${formula.name} 缩略图`"
                />
                <span v-else>暂无缩略图</span>
              </div>
              <footer>
                {{ formula.category?.name || '未分类' }}&nbsp;&nbsp;by&nbsp;&nbsp;{{ formula.author?.username || '官方' }}
              </footer>
            </article>
          </div>

          <div
            v-else-if="isRelationTab && activeState.items.length"
            class="relation-grid"
          >
            <UserCard
              v-for="user in activeState.items"
              :key="user.username"
              :user="user"
              :current-username="userStore.username"
              :action-loading="relationActionLoading.has(user.username)"
              @view="openUser"
              @toggle-follow="toggleRelationFollow"
            />
          </div>

          <el-empty
            v-else-if="activeState.loaded && !activeState.loading"
            :description="emptyDescription"
            :image-size="100"
          />
        </div>

        <div v-if="activeState.total > activeState.pageSize" class="pagination">
          <el-pagination
            :current-page="activeState.page"
            :page-size="activeState.pageSize"
            :total="activeState.total"
            layout="total, prev, pager, next"
            @current-change="changePage"
          />
        </div>
      </section>
    </template>
  </main>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  followUserApi,
  getFollowersListApi,
  getFollowingListApi,
  getProfileApi,
  unfollowUserApi
} from '@/api/user'
import { getUserPosts } from '@/api/posts'
import {
  getUserCustomFormulas,
  getUserFormulaCollections
} from '@/api/formula'
import UserCard from '@/components/user/UserCard.vue'
import { useUserStore } from '@/stores/user'
import defaultAvatar from '@/assets/default_avatar.svg'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const createTabState = (pageSize) => ({
  loaded: false,
  loading: false,
  error: '',
  page: 1,
  pageSize,
  total: 0,
  items: [],
  requestVersion: 0
})

const tabStates = reactive({
  posts: createTabState(10),
  collections: createTabState(12),
  customFormulas: createTabState(12),
  following: createTabState(20),
  followers: createTabState(20)
})

const profile = ref(null)
const profileLoading = ref(true)
const profileError = ref(false)
const notFound = ref(false)
const profileFollowLoading = ref(false)
const activeTab = ref('posts')
const relationActionLoading = reactive(new Set())
let profileVersion = 0
let profileFollowVersion = 0

const activeState = computed(() => tabStates[activeTab.value])
const isFormulaTab = computed(
  () => activeTab.value === 'collections' || activeTab.value === 'customFormulas'
)
const isRelationTab = computed(
  () => activeTab.value === 'following' || activeTab.value === 'followers'
)
const isSelf = computed(
  () => Boolean(
    userStore.token &&
    profile.value?.username === userStore.username
  )
)

const emptyDescription = computed(() => ({
  posts: '还没有发布文章',
  collections: '还没有收藏公式',
  customFormulas: '还没有发布自创公式',
  following: '还没有关注其他魔友',
  followers: '还没有粉丝'
}[activeTab.value]))

const resetTabs = () => {
  tabStates.posts = createTabState(10)
  tabStates.collections = createTabState(12)
  tabStates.customFormulas = createTabState(12)
  tabStates.following = createTabState(20)
  tabStates.followers = createTabState(20)
}

const loadProfile = async () => {
  const username = String(route.params.username || '')
  const version = ++profileVersion
  profileFollowVersion++

  profile.value = null
  profileLoading.value = true
  profileFollowLoading.value = false
  profileError.value = false
  notFound.value = false
  activeTab.value = 'posts'
  resetTabs()

  try {
    const response = await getProfileApi(username)
    if (version !== profileVersion) return
    profile.value = response.profiles
    await loadTab('posts')
  } catch (error) {
    if (version !== profileVersion) return
    if (error.response?.status === 404) {
      notFound.value = true
    } else {
      profileError.value = true
    }
  } finally {
    if (version === profileVersion) profileLoading.value = false
  }
}

const loadTab = async (name, force = false) => {
  if (!profile.value || !tabStates[name]) return
  const state = tabStates[name]
  if ((state.loading || state.loaded) && !force) return

  const requestVersion = ++state.requestVersion
  const currentProfileVersion = profileVersion
  state.loading = true
  state.error = ''

  const params = {
    page: state.page,
    page_size: state.pageSize
  }
  const username = profile.value.username
  const requests = {
    posts: () => getUserPosts(username, {
      ...params,
      ordering: '-created_at'
    }),
    collections: () => getUserFormulaCollections(username, params),
    customFormulas: () => getUserCustomFormulas(username, params),
    following: () => getFollowingListApi(username, params),
    followers: () => getFollowersListApi(username, params)
  }

  try {
    const response = await requests[name]()
    if (
      requestVersion !== state.requestVersion ||
      currentProfileVersion !== profileVersion ||
      profile.value?.username !== username
    ) return

    state.items = response.data?.results || []
    state.total = response.data?.count || 0
    state.loaded = true
  } catch {
    if (
      requestVersion !== state.requestVersion ||
      currentProfileVersion !== profileVersion
    ) return
    state.error = '该内容加载失败，请重试'
  } finally {
    if (requestVersion === state.requestVersion) {
      state.loading = false
    }
  }
}

const activateTab = (name) => {
  activeTab.value = name
  loadTab(name)
}

const retryActiveTab = () => {
  loadTab(activeTab.value, true)
}

const changePage = (page) => {
  activeState.value.page = page
  loadTab(activeTab.value, true)
}

const requireLogin = () => {
  if (userStore.token) return true
  router.push({
    name: 'login',
    query: { redirect: route.fullPath }
  })
  return false
}

const toggleProfileFollow = async () => {
  if (!requireLogin() || !profile.value) return

  const targetProfile = profile.value
  const username = targetProfile.username
  const wasFollowing = targetProfile.following
  const currentProfileVersion = profileVersion
  const actionVersion = ++profileFollowVersion
  profileFollowLoading.value = true

  try {
    if (wasFollowing) {
      await unfollowUserApi(username)
    } else {
      await followUserApi(username)
    }

    if (
      actionVersion !== profileFollowVersion ||
      currentProfileVersion !== profileVersion ||
      profile.value !== targetProfile
    ) return

    if (wasFollowing) {
      targetProfile.following = false
      targetProfile.followers_count = Math.max(
        0,
        targetProfile.followers_count - 1
      )
      ElMessage.success('已取消关注')
    } else {
      targetProfile.following = true
      targetProfile.followers_count += 1
      ElMessage.success('关注成功')
    }

    tabStates.followers.loaded = false
    tabStates.followers.page = 1
    if (activeTab.value === 'followers') {
      await loadTab('followers', true)
    }
  } finally {
    if (actionVersion === profileFollowVersion) {
      profileFollowLoading.value = false
    }
  }
}

const toggleRelationFollow = async (user) => {
  if (!requireLogin()) return

  relationActionLoading.add(user.username)
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
    relationActionLoading.delete(user.username)
  }
}

const openPost = (id) => {
  router.push({ name: 'postDetail', params: { id } })
}

const openUser = (username) => {
  router.push({ name: 'userProfile', params: { username } })
}

const formatDate = (value) => new Date(value).toLocaleDateString('zh-CN')

const difficultyLabel = (level) => {
  if (level === 1) return '基础'
  if (level === 2) return '进阶'
  return '困难'
}

const difficultyTagType = (level) => {
  if (level === 1) return 'success'
  if (level === 2) return 'warning'
  return 'danger'
}

watch(
  () => route.params.username,
  loadProfile,
  { immediate: true }
)
</script>

<style scoped>
.public-profile-page {
  width: 100%;
  max-width: 1000px;
  min-height: 620px;
  margin: 0 auto;
  padding: 32px 20px 48px;
}

.loading-shell,
.page-state {
  min-height: 420px;
}

.page-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
}

.page-state h1 {
  margin: 0;
  color: #303133;
  font-size: 24px;
}

.page-state p {
  margin: 12px 0 22px;
  color: #606266;
}

.error-state {
  background: #fef0f0;
  border-color: #fab6b6;
}

.profile-card {
  position: relative;
  overflow: hidden;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 14px;
}

.profile-accent {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  height: 6px;
}

.profile-accent span:nth-child(1) {
  background: #409eff;
}

.profile-accent span:nth-child(2) {
  background: #e6a23c;
}

.profile-accent span:nth-child(3) {
  background: #f56c6c;
}

.profile-main {
  display: flex;
  align-items: center;
  gap: 22px;
  padding: 28px 30px 24px;
}

.profile-avatar {
  flex-shrink: 0;
  border: 4px solid #ecf5ff;
}

.profile-copy {
  flex: 1;
  min-width: 0;
}

.profile-copy h1 {
  margin: 0;
  overflow-wrap: anywhere;
  color: #303133;
  font-size: 28px;
}

.profile-copy p {
  margin: 8px 0 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.7;
}

.stat-groups {
  display: grid;
  grid-template-columns: 1fr 2fr 2fr;
  border-top: 1px solid #ebeef5;
}

.stat-group {
  position: relative;
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: 1fr;
  min-width: 0;
  border-right: 1px solid #ebeef5;
}

.stat-group:last-child {
  border-right: 0;
}

.group-label {
  position: absolute;
  top: 9px;
  left: 12px;
  color: #909399;
  font-size: 11px;
  letter-spacing: 0.08em;
}

.stat-item {
  min-width: 0;
  padding: 30px 10px 16px;
  background: transparent;
  border: 0;
  cursor: pointer;
}

.stat-item strong,
.stat-item span {
  display: block;
}

.stat-item strong {
  color: #303133;
  font-size: 21px;
}

.stat-item span {
  margin-top: 4px;
  color: #606266;
  font-size: 12px;
}

.stat-item:hover strong {
  color: #409eff;
}

.stat-item:focus-visible {
  outline: 3px solid rgba(64, 158, 255, 0.35);
  outline-offset: -3px;
}

.profile-content {
  margin-top: 22px;
  padding: 0 24px 24px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 14px;
}

.tab-content {
  min-height: 280px;
  padding-top: 8px;
}

.tab-state {
  display: flex;
  min-height: 260px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
}

.tab-state p {
  margin: 0 0 16px;
  color: #606266;
}

.post-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.post-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 10px;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.post-card:hover {
  border-color: #c6e2ff;
  box-shadow: 0 5px 16px rgba(48, 49, 51, 0.07);
}

.post-card:focus-visible {
  outline: 3px solid rgba(64, 158, 255, 0.35);
  outline-offset: 2px;
}

.post-main {
  flex: 1;
  min-width: 0;
}

.post-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.post-title-row h2 {
  margin: 0;
  overflow: hidden;
  color: #303133;
  font-size: 17px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.post-meta,
.post-stats,
.post-tags {
  display: flex;
  align-items: center;
  gap: 10px;
}

.post-meta {
  margin-top: 12px;
  color: #909399;
  font-size: 12px;
}

.post-meta time {
  margin-left: 4px;
}

.post-tags {
  flex-wrap: wrap;
  margin-top: 12px;
}

.post-stats {
  margin-top: 14px;
  color: #909399;
  font-size: 12px;
}

.post-image {
  flex: 0 0 120px;
  width: 120px;
  aspect-ratio: 1;
  overflow: hidden;
  background: #f5f7fa;
  border-radius: 8px;
}

.post-image img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.formula-grid,
.relation-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.formula-card {
  display: flex;
  min-width: 0;
  flex-direction: column;
  padding: 18px;
  border: 1px solid #ebeef5;
  border-radius: 10px;
}

.formula-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.formula-header h2 {
  margin: 0;
  overflow: hidden;
  color: #303133;
  font-size: 16px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.formula-notation {
  margin-top: 12px;
  padding: 8px 10px;
  overflow: hidden;
  color: #e6a23c;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
  background: #f5f7fa;
  border-radius: 6px;
}

.formula-thumbnail {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  margin-top: 14px;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  color: #909399;
  font-size: 13px;
  background: #f5f7fa;
  border-radius: 8px;
}

.formula-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.formula-card footer {
  margin-top: 14px;
  overflow: hidden;
  color: #606266;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 26px;
}

@media (max-width: 768px) {
  .public-profile-page {
    padding: 24px 14px 40px;
  }

  .profile-main {
    flex-direction: column;
    align-items: flex-start;
    padding: 24px 20px;
  }

  .profile-main :deep(.el-button) {
    width: 100%;
  }

  .stat-groups {
    grid-template-columns: 1fr 2fr;
  }

  .stat-group:first-child {
    border-bottom: 1px solid #ebeef5;
  }

  .stat-group:last-child {
    grid-column: 1 / -1;
    border-top: 1px solid #ebeef5;
  }

  .profile-content {
    padding-inline: 14px;
  }

  .formula-grid,
  .relation-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .post-card {
    align-items: flex-start;
    gap: 12px;
    padding: 16px;
  }

  .post-image {
    flex-basis: 88px;
    width: 88px;
  }

  .post-stats {
    flex-wrap: wrap;
  }

  .profile-content {
    overflow-x: hidden;
  }
}

@media (prefers-reduced-motion: reduce) {
  .post-card {
    transition: none;
  }
}
</style>
