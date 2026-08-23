<script setup>
/**
 * ProfileView.vue — 个人中心页
 *
 * 未登录显示登录入口；已登录显示用户卡片、统计、快捷入口、编辑资料、退出登录。
 */
defineOptions({ name: 'ProfileView' })

import { ref, computed, onMounted, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast } from 'vant'
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera'
import { useUserStore } from '@/stores/user'
import { getProfileApi, updateProfileApi, logoutApi } from '@/api/user'
import { getLatestVersion } from '@/api/home'
import { buildMediaUrl } from '@/utils/media-url'
import { version as appVersion } from '../../package.json'
import ImageCropper from '@/components/ImageCropper.vue'
import { cropAndCompress } from '@/utils/image-compress'
import { getDownloadCount } from '@/utils/formula-download'

const router = useRouter()
const userStore = useUserStore()

const isLoggedIn = computed(() => !!userStore.token)
const avatarUrl = computed(() => buildMediaUrl(userStore.image))

// 统计数据
const stats = ref({
  post_count: 0,
  formula_count: 0,
  collection_count: 0,
  download_count: 0,
})

// 编辑弹窗
const editShow = ref(false)
const editForm = ref({ username: '', bio: '' })
const editLoading = ref(false)
const avatarFile = ref(null)
const avatarPreview = ref('')

// 头像选择
const showAvatarSheet = ref(false)
const showCropper = ref(false)
const cropperSrc = ref('')
const refreshing = ref(false)
const avatarActions = [
  { name: '拍照', action: 'camera' },
  { name: '从相册选择', action: 'gallery' },
]

// ─── 数据加载 ────────────────────────────────────────
async function loadStats() {
  if (!isLoggedIn.value || !userStore.username) return
  try {
    const res = await getProfileApi(userStore.username)
    const profile = res.data?.profiles || res.data || res.profiles || {}
    stats.value = {
      post_count: profile.post_count || 0,
      formula_count: profile.custom_formula_count || 0,
      collection_count: profile.collection_count || 0,
      download_count: getDownloadCount(),
    }
  } catch {
    // 静默失败
  }
}

// ─── 事件处理 ────────────────────────────────────────
function goToLogin() {
  router.push({ name: 'login', query: { redirect: '/profile' } })
}

function goToMyPosts() {
  router.push({ path: '/forum', query: { filter: 'my_posts' } })
}

function goToCollected() {
  router.push({ path: '/formula', query: { filter: 'collected' } })
}

function goToMyFormulas() {
  router.push({ path: '/formula', query: { filter: 'created' } })
}

function goToDownloads() {
  router.push({ path: '/formula', query: { filter: 'downloaded' } })
}

function goToTimerRecords() {
  router.push('/timer?tab=records')
}

function openEdit() {
  editForm.value = {
    username: userStore.username,
    bio: userStore.bio || '',
  }
  avatarFile.value = null
  avatarPreview.value = ''
  editShow.value = true
}

function selectAvatar() {
  showAvatarSheet.value = true
}

function onAvatarAction(item) {
  if (item.action === 'camera') selectFromCamera()
  else if (item.action === 'gallery') selectFromGallery()
}

async function selectFromCamera() {
  showAvatarSheet.value = false
  try {
    const photo = await Camera.getPhoto({
      quality: 90,
      resultType: CameraResultType.DataUrl,
      source: CameraSource.Camera,
    })
    cropperSrc.value = photo.dataUrl
    showCropper.value = true
  } catch {
    // 用户取消
  }
}

async function selectFromGallery() {
  showAvatarSheet.value = false
  try {
    const photo = await Camera.getPhoto({
      quality: 90,
      resultType: CameraResultType.DataUrl,
      source: CameraSource.Photos,
    })
    cropperSrc.value = photo.dataUrl
    showCropper.value = true
  } catch {
    // 用户取消
  }
}

async function onCropConfirm(crop) {
  showCropper.value = false
  showLoadingToast({ message: '正在上传头像...', forbidClick: true, duration: 0 })
  try {
    const file = await cropAndCompress(cropperSrc.value, crop, {
      outputSize: 512,
      quality: 0.85,
    })
    const formData = new FormData()
    formData.append('avatar', file)
    const res = await updateProfileApi(formData)
    const userInfo = res.data?.user || res.user || {}
    userStore.updateInfo({
      image: userInfo.image || undefined,
    })
    if (editShow.value) {
      avatarFile.value = file
      avatarPreview.value = URL.createObjectURL(file)
    }
    closeToast()
    showToast({ type: 'success', message: '头像更新成功' })
  } catch {
    closeToast()
    showToast('头像上传失败')
  }
}

function onCropCancel() {
  showCropper.value = false
}

async function saveEdit() {
  if (!editForm.value.username.trim()) {
    showToast('用户名不能为空')
    return
  }

  editLoading.value = true
  try {
    const formData = new FormData()
    // 仅 username 变化时才传（避免 unique 冲突）
    if (editForm.value.username !== userStore.username) {
      formData.append('username', editForm.value.username)
    }
    formData.append('bio', editForm.value.bio)
    if (avatarFile.value) {
      formData.append('avatar', avatarFile.value)
    }

    const res = await updateProfileApi(formData)
    const userInfo = res.data?.user || res.user || {}
    userStore.updateInfo({
      username: userInfo.username || editForm.value.username,
      bio: userInfo.bio ?? editForm.value.bio,
      image: userInfo.image || undefined,
    })

    showToast({ type: 'success', message: '保存成功' })
    editShow.value = false
    loadStats()
  } catch {
    // request.js 已统一处理错误提示
  } finally {
    editLoading.value = false
  }
}

const logoutShow = ref(false)
const logoutLoading = ref(false)

function confirmLogout() {
  logoutShow.value = true
}

async function doLogout() {
  logoutLoading.value = true
  try {
    await logoutApi()
  } catch {
    // 即使后端失败也清除本地状态
  }
  userStore.clearInfo()
  logoutShow.value = false
  logoutLoading.value = false
  showToast({ type: 'success', message: '已退出登录' })
  router.push({ name: 'login' })
}

// ─── 检查更新 ────────────────────────────────────────
const updateInfo = ref(null)
const updateShow = ref(false)
const checking = ref(false)

function compareVersion(v1, v2) {
  const a = v1.split('.').map(Number)
  const b = v2.split('.').map(Number)
  for (let i = 0; i < 3; i++) {
    if ((a[i] || 0) !== (b[i] || 0)) return (a[i] || 0) - (b[i] || 0)
  }
  return 0
}

async function checkUpdate() {
  if (checking.value) return
  checking.value = true
  try {
    const res = await getLatestVersion()
    const data = res.data || res
    if (compareVersion(data.version, appVersion) > 0) {
      updateInfo.value = data
      updateShow.value = true
    } else {
      showToast({ type: 'success', message: `已是最新版本 v${appVersion}` })
    }
  } catch {
    showToast('检查更新失败')
  } finally {
    checking.value = false
  }
}

function downloadApk() {
  if (updateInfo.value?.download_url) {
    window.open(updateInfo.value.download_url, '_system')
  }
}

// ─── 生命周期 ────────────────────────────────────────
onMounted(() => {
  loadStats()
})

onActivated(() => {
  loadStats()
})

async function onRefresh() {
  await loadStats()
  refreshing.value = false
}
</script>

<template>
  <div class="page">
    <van-nav-bar title="个人中心" placeholder />

    <div class="page-content">
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <!-- 未登录状态 -->
      <div v-if="!isLoggedIn" class="login-prompt">
        <van-icon name="user-circle-o" size="64" color="#d1d5db" />
        <p class="prompt-text">登录后查看更多信息</p>
        <van-button type="primary" round size="small" @click="goToLogin">去登录</van-button>
      </div>

      <!-- 已登录状态 -->
      <template v-else>
        <!-- 用户卡片 -->
        <div class="user-card">
          <van-image
            round
            width="64"
            height="64"
            :src="avatarUrl"
            fit="cover"
            @click="selectAvatar"
          >
            <template #error>
              <div class="avatar-fallback">{{ userStore.username?.[0] || '?' }}</div>
            </template>
          </van-image>
          <div class="user-info" @click="openEdit">
            <div class="user-name">{{ userStore.username }}</div>
            <div class="user-bio">{{ userStore.bio || '这个人很懒，什么都没写' }}</div>
          </div>
        </div>

        <!-- 统计数据 -->
        <div class="stats-grid">
          <div class="stat-item clickable" @click="goToMyPosts">
            <span class="stat-value">{{ stats.post_count }}</span>
            <span class="stat-label">帖子</span>
          </div>
          <div class="stat-item clickable" @click="goToMyFormulas">
            <span class="stat-value">{{ stats.formula_count }}</span>
            <span class="stat-label">公式</span>
          </div>
          <div class="stat-item clickable" @click="goToCollected">
            <span class="stat-value">{{ stats.collection_count }}</span>
            <span class="stat-label">收藏</span>
          </div>
          <div class="stat-item clickable" @click="goToDownloads">
            <span class="stat-value">{{ stats.download_count }}</span>
            <span class="stat-label">下载</span>
          </div>
        </div>

        <!-- 快捷入口 -->
        <van-cell-group inset class="action-group">
          <van-cell title="我的帖子" icon="notes-o" is-link @click="goToMyPosts" />
          <van-cell title="我的公式" icon="records-o" is-link @click="goToMyFormulas" />
          <van-cell title="公式收藏" icon="star-o" is-link @click="goToCollected" />
          <van-cell title="公式下载" icon="down" is-link @click="goToDownloads" />
          <van-cell title="个人数据" icon="chart-trending-o" is-link @click="goToTimerRecords" />
          <van-cell title="编辑资料" icon="edit" is-link @click="openEdit" />
          <van-cell title="检查更新" icon="upgrade" is-link @click="checkUpdate" :value="`v${appVersion}`" />
          <van-cell title="退出登录" icon="cross" is-link @click="confirmLogout" class="logout-cell" />
        </van-cell-group>
      </template>
      </van-pull-refresh>
    </div>

    <!-- 编辑资料弹窗 -->
    <van-popup
      v-model:show="editShow"
      position="bottom"
      round
      :style="{ maxHeight: '80%' }"
    >
      <div class="edit-form">
        <div class="edit-title">编辑资料</div>

        <div class="edit-avatar" @click="selectAvatar">
          <div class="avatar-upload">
            <van-image
              v-if="avatarPreview || avatarUrl"
              round
              width="72"
              height="72"
              :src="avatarPreview || avatarUrl"
              fit="cover"
            />
            <van-icon v-else name="camera-o" size="32" color="#9ca3af" />
          </div>
        </div>

        <van-field
          v-model="editForm.username"
          label="用户名"
          placeholder="请输入用户名"
          maxlength="60"
        />
        <van-field
          v-model="editForm.bio"
          label="简介"
          type="textarea"
          placeholder="介绍一下自己吧"
          rows="3"
          maxlength="200"
          show-word-limit
          autosize
        />

        <div class="edit-actions">
          <van-button block type="primary" :loading="editLoading" @click="saveEdit">
            保存
          </van-button>
        </div>
      </div>
    </van-popup>

    <!-- 退出登录确认弹窗 -->
    <van-dialog
      v-model:show="logoutShow"
      title="退出登录"
      show-cancel-button
      :before-close="() => !logoutLoading"
      confirm-button-color="#ee0a24"
      @confirm="doLogout"
    >
      <div class="logout-content">
        <van-icon name="warning-o" size="40" color="#f59e0b" />
        <p>确认退出当前账号？</p>
        <p class="logout-hint">退出后需重新登录才能使用收藏、发帖等功能</p>
      </div>
    </van-dialog>

    <!-- 头像选择 ActionSheet -->
    <van-action-sheet
      v-model:show="showAvatarSheet"
      :actions="avatarActions"
      cancel-text="取消"
      close-on-click-action
      @select="onAvatarAction"
    />

    <!-- 图片裁剪 -->
    <ImageCropper
      v-if="showCropper"
      :src="cropperSrc"
      @confirm="onCropConfirm"
      @cancel="onCropCancel"
    />

    <!-- 更新弹窗 -->
    <van-dialog
      v-model:show="updateShow"
      title="发现新版本"
      show-cancel-button
      confirm-button-text="下载"
      cancel-button-text="稍后"
      @confirm="downloadApk"
    >
      <div class="update-content">
        <van-icon name="upgrade" size="40" color="var(--van-primary-color)" />
        <p class="update-version">v{{ updateInfo?.version }}</p>
        <p class="update-info">{{ updateInfo?.update_info }}</p>
      </div>
    </van-dialog>
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

/* 未登录 */
.login-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  gap: 12px;
}

.prompt-text {
  font-size: 0.9rem;
  color: var(--van-text-color-2);
}

/* 用户卡片 */
.user-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 16px;
  margin: 8px 12px;
  background: var(--van-background-2);
  border-radius: 12px;
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

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--van-text-color);
  margin-bottom: 4px;
}

.user-bio {
  font-size: 0.85rem;
  color: var(--van-text-color-2);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

/* 统计 */
.stats-grid {
  display: flex;
  justify-content: space-around;
  padding: 16px 12px;
  margin: 0 12px 8px;
  background: var(--van-background-2);
  border-radius: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-item.clickable {
  cursor: pointer;
}

.stat-item.clickable:active {
  opacity: 0.6;
}

.stat-value {
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--van-text-color);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--van-text-color-2);
}

/* 快捷入口 */
.action-group {
  margin-top: 8px;
}

.logout-cell {
  color: #ee0a24;
}

/* 编辑弹窗 */
.edit-form {
  padding: 20px 16px;
}

.edit-title {
  font-size: 1.1rem;
  font-weight: 600;
  text-align: center;
  margin-bottom: 20px;
}

.edit-avatar {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
  cursor: pointer;
}

.edit-avatar:active {
  opacity: 0.7;
}

.avatar-upload {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  border: 1px dashed var(--van-border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.edit-actions {
  margin-top: 20px;
}

/* 退出登录弹窗 */
.logout-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 24px 16px;
  text-align: center;
}

.logout-content p {
  margin: 0;
}

.logout-content p:first-of-type {
  font-size: 1rem;
  font-weight: 600;
  color: var(--van-text-color);
  margin-top: 12px;
}

.logout-hint {
  font-size: 0.78rem;
  color: var(--van-text-color-3);
  margin-top: 6px !important;
}

/* 更新弹窗 */
.update-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 24px 16px;
  text-align: center;
}

.update-version {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--van-text-color);
  margin: 12px 0 6px;
}

.update-info {
  font-size: 0.85rem;
  color: var(--van-text-color-2);
  white-space: pre-wrap;
  line-height: 1.6;
}
</style>
