<template>
  <div class="profile-info-container">
    <div class="profile-layout-wrapper">

      <el-card class="profile-card" shadow="never">
        <el-skeleton :loading="loading" animated :rows="3">
          <template #default>
            <div class="profile-header">
              <el-avatar :size="85" :src="profileData.image || defaultAvatar" class="profile-avatar" />

              <div class="profile-meta">
                <div class="name-row">
                  <h2 class="username">{{ profileData.username || '未登录' }}</h2>
                  <el-tag v-if="isMe" size="small" type="success" effect="plain" class="identity-tag">本用户</el-tag>
                  <el-tag v-else size="small" type="warning" effect="plain" class="identity-tag">魔方达人</el-tag>
                </div>
                <p class="bio-text">{{ profileData.bio || '这个魔方大神很懒，还没有填写个人简介~' }}</p>
              </div>

              <div class="action-btn">
                <el-button v-if="isMe" type="primary" icon="Edit" plain @click="openEditDialog">
                  修改资料
                </el-button>

                <template v-else>
                  <el-button
                    v-if="profileData.following"
                    type="info"
                    icon="Check"
                    :loading="followLoading"
                    @click="handleMainToggleFollow"
                  >
                    已关注
                  </el-button>
                  <el-button
                    v-else
                    type="primary"
                    icon="Plus"
                    :loading="followLoading"
                    @click="handleMainToggleFollow"
                  >
                    关注
                  </el-button>
                </template>
              </div>
            </div>
          </template>
        </el-skeleton>

        <el-divider style="margin: 20px 0 15px 0;" />

        <div class="stats-row">
          <div class="stats-item" @click="activeTab = 'following'">
            <div class="stats-num" :class="{ 'active-num': activeTab === 'following' }">
              {{ profileData.following_count }}
            </div>
            <div class="stats-label">{{ isMe ? '我的关注' : '他的关注' }}</div>
          </div>
          <div class="stats-item" @click="activeTab = 'followers'">
            <div class="stats-num" :class="{ 'active-num': activeTab === 'followers' }">
              {{ profileData.followers_count }}
            </div>
            <div class="stats-label">{{ isMe ? '我的粉丝' : '他的粉丝' }}</div>
          </div>
          <div v-if="isMe" class="stats-item" @click="goToOrders">
            <div class="stats-num">
              {{ orderCount }}
            </div>
            <div class="stats-label">我的订单</div>
          </div>
          <div v-if="isMe" class="stats-item" @click="goToAddresses">
            <div class="stats-num">
              {{ addressCount }}
            </div>
            <div class="stats-label">收货地址</div>
          </div>
        </div>
      </el-card>

      <el-card v-if="isMe" class="quick-entry-card" shadow="never">
        <template #header>
          <span>快捷入口</span>
        </template>
        <div class="quick-entry-grid">
          <div class="quick-entry-item" @click="goToOrders">
            <div class="entry-icon order-icon">
              <el-icon size="24" color="#e6a23c">
                <ShoppingCart />
              </el-icon>
            </div>
            <span class="entry-label">我的订单</span>
            <el-tag v-if="orderCount > 0" size="small" type="danger">{{ orderCount }}</el-tag>
          </div>
          <div class="quick-entry-item" @click="goToAddresses">
            <div class="entry-icon address-icon">
              <el-icon size="24" color="#67c23a">
                <MapLocation />
              </el-icon>
            </div>
            <span class="entry-label">收货地址</span>
            <el-tag v-if="addressCount > 0" size="small" type="primary">{{ addressCount }}</el-tag>
          </div>
          <div class="quick-entry-item" @click="goToCollections">
            <div class="entry-icon collection-icon">
              <el-icon size="24" color="#f56c6c">
                <Star />
              </el-icon>
            </div>
            <span class="entry-label">我的收藏</span>
          </div>
          <div class="quick-entry-item" @click="goToPosts">
            <div class="entry-icon post-icon">
              <el-icon size="24" color="#909399">
                <Document />
              </el-icon>
            </div>
            <span class="entry-label">我的帖子</span>
          </div>
          <div class="quick-entry-item" @click="goToData">
            <div class="entry-icon data-icon">
              <el-icon size="24" color="#b37feb">
                <TrendCharts />
              </el-icon>
            </div>
            <span class="entry-label">数据统计</span>
          </div>
          <div class="quick-entry-item" @click="openEditDialog">
            <div class="entry-icon edit-icon">
              <el-icon size="24" color="#409EFF">
                <User />
              </el-icon>
            </div>
            <span class="entry-label">修改资料</span>
          </div>
        </div>
      </el-card>

      <el-card class="relation-card" shadow="never">
        <el-tabs v-model="activeTab" class="relation-tabs">
          <el-tab-pane :label="isMe ? '我的关注' : '他的关注'" name="following">
            <el-scrollbar max-height="320px">
              <div v-if="followingList.length > 0" class="user-list">
                <div v-for="user in followingList" :key="user.username" class="user-item" @click="viewOtherProfile(user.username)">
                  <el-avatar :size="40" :src="user.image || defaultAvatar" />
                  <div class="user-info-mini">
                    <span class="user-name-mini">{{ user.username }}</span>
                    <span class="user-bio-mini">{{ user.bio || '暂无简介' }}</span>
                  </div>

                  <div class="list-action-btn" @click.stop>
                    <el-tag size="small" v-if="user.username === userStore.username" type="success">我</el-tag>
                    <template v-else>
                      <el-button
                        v-if="user.following"
                        size="small"
                        type="info"
                        plain
                        @click="handleListToggleFollow(user)"
                      >
                        取消关注
                      </el-button>
                      <el-button
                        v-else
                        size="small"
                        type="primary"
                        plain
                        @click="handleListToggleFollow(user)"
                      >
                        关注
                      </el-button>
                    </template>
                  </div>
                </div>
              </div>
              <el-empty v-else description="暂无关注的用户" :image-size="80" />
            </el-scrollbar>
          </el-tab-pane>

          <el-tab-pane :label="isMe ? '我的粉丝' : '他的粉丝'" name="followers">
            <el-scrollbar max-height="320px">
              <div v-if="followersList.length > 0" class="user-list">
                <div v-for="user in followersList" :key="user.username" class="user-item" @click="viewOtherProfile(user.username)">
                  <el-avatar :size="40" :src="user.image || defaultAvatar" />
                  <div class="user-info-mini">
                    <span class="user-name-mini">{{ user.username }}</span>
                    <span class="user-bio-mini">{{ user.bio || '暂无简介' }}</span>
                  </div>

                  <div class="list-action-btn" @click.stop>
                    <el-tag size="small" v-if="user.username === userStore.username" type="success">我</el-tag>
                    <template v-else>
                      <el-button
                        v-if="user.following"
                        size="small"
                        type="info"
                        plain
                        @click="handleListToggleFollow(user)"
                      >
                        互关注 (取关)
                      </el-button>
                      <el-button
                        v-else
                        size="small"
                        type="primary"
                        plain
                        @click="handleListToggleFollow(user)"
                      >
                        回关
                      </el-button>
                    </template>
                  </div>
                </div>
              </div>
              <el-empty v-else description="还没有粉丝关注哦" :image-size="80" />
            </el-scrollbar>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>

    <el-dialog v-model="editDialogVisible" title="修改个人资料" width="380px" append-to-body>
      <el-form :model="editForm" label-position="top">
        <el-form-item label="个人头像">
          <el-upload
            class="avatar-uploader"
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleAvatarChange"
            :http-request="() => {}"
          >
            <img v-if="previewUrl" :src="previewUrl" class="edit-preview-avatar" />
            <el-avatar v-else :size="80" :src="editForm.image || defaultAvatar" />
            <div class="upload-tip">点击更换头像</div>
          </el-upload>
        </el-form-item>

        <el-form-item label="个性昵称">
          <el-input v-model="editForm.username" placeholder="修改您的昵称" maxlength="20" show-word-limit />
        </el-form-item>

        <el-form-item label="个人简介">
          <el-input
            v-model="editForm.bio"
            type="textarea"
            :rows="3"
            placeholder="介绍一下你自己吧..."
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false" :disabled="saveLoading">取消</el-button>
        <el-button type="primary" :loading="saveLoading" @click="submitEditProfile">保存修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useUserStore } from '@/stores/user'
import { useRoute, useRouter } from 'vue-router'
// 💡 一举打包引入你前期做好的全部业务关联接口（含修改、看别人、看自己、关注、取关）
import { getProfileApi,
  getFollowingListApi,
  getFollowersListApi,
  followUserApi,
  unfollowUserApi,
  updateProfileApi
} from '@/api/user'
import { getOrders, getAddresses } from '@/api/shop'

import { ElMessage } from 'element-plus'
import { ShoppingCart, MapLocation, Star, Document, TrendCharts, User } from '@element-plus/icons-vue'
import defaultAvatar from '@/assets/default_avatar.svg'

const userStore = useUserStore()
const route = useRoute()
const router = useRouter()

const loading = ref(true)
const followLoading = ref(false)
const saveLoading = ref(false)

const activeTab = ref('following')
const editDialogVisible = ref(false)

// 主卡片基础数据模型
const profileData = ref({
  username: '',
  bio: '',
  image: null,
  following: false,
  followers_count: 0,
  following_count: 0
})
const orderCount = ref(0)
const addressCount = ref(0)

// 关注、粉丝列表响应式存储
const followingList = ref([])
const followersList = ref([])

// 修改个人资料对应的临时表单变量
const editForm = ref({ username: '', bio: '', image: null })
const previewUrl = ref('')
const selectedFile = ref(null)

// 💡 核心计算属性：判断当前查看的是不是“登录用户自己”
const isMe = computed(() => {
  const queryUser = route.query.username
  // 如果 URL 没传参数，或者参数值和登录在 Pinia 里的用户名一样，就是在看自己
  return !queryUser || queryUser === userStore.username
})

// 💡 动态获取要查询的目标用户名
const getTargetUsername = () => {
  return route.query.username || userStore.username
}

// 核心加载链：拉取任意目标用户的资料及社交关系列表
const fetchUserProfileChain = async () => {
  const targetUser = getTargetUsername()
  if (!targetUser) {
    ElMessage.error('无法获取目标用户名')
    loading.value = false
    return
  }

  try {
    loading.value = true

    // 并发请求目标用户的信息、关注、粉丝列表数据
    const [profileRes, followingRes, followersRes] = await Promise.all([
      getProfileApi(targetUser),
      getFollowingListApi(targetUser).catch(() => ({ profiles: [] })),
      getFollowersListApi(targetUser).catch(() => ({ profiles: [] }))
    ])

    if (profileRes && profileRes.profiles) profileData.value = profileRes.profiles
    if (followingRes && followingRes.profiles) followingList.value = followingRes.profiles
    if (followersRes && followersRes.profiles) followersList.value = followersRes.profiles

  } catch (err) {
    console.error('拉取社交链数据故障:', err)
  } finally {
    loading.value = false
  }
}

// 💡 1. 顶部主卡片的关注/取关逻辑（联动更新主卡片数量统计）
const handleMainToggleFollow = async () => {
  const targetUser = profileData.value.username
  if (!targetUser) return

  try {
    followLoading.value = true
    if (profileData.value.following) {
      await unfollowUserApi(targetUser)
      ElMessage.success('已取消关注')
      profileData.value.following = false
      profileData.value.followers_count--
    } else {
      await followUserApi(targetUser)
      ElMessage.success('关注成功')
      profileData.value.following = true
      profileData.value.followers_count++
    }
  } catch (err) {
    console.error(err)
  } finally {
    followLoading.value = false
  }
}

// 💡 2. 下方列表内的独立关注/取关逻辑（通过 @click.stop 隔离了整行点击）
const handleListToggleFollow = async (user) => {
  const targetUser = user.username
  if (!targetUser) return

  try {
    if (user.following) {
      await unfollowUserApi(targetUser)
      ElMessage.success(`已取消关注 ${targetUser}`)
      user.following = false // 局部改变当前行状态

      if (isMe.value) {
        profileData.value.following_count = Math.max(0, profileData.value.following_count - 1)
      }
    } else {
      await followUserApi(targetUser)
      ElMessage.success(`成功关注 ${targetUser}`)
      user.following = true // 局部改变当前行状态

      if (isMe.value) {
        profileData.value.following_count++
      }
    }
  } catch (err) {
    console.error(err)
  }
}

// 💡 3. 修改资料：点击“修改资料”按钮时，将数据深拷贝灌入临时表单中
const openEditDialog = () => {
  editForm.value.username = profileData.value.username
  editForm.value.bio = profileData.value.bio
  editForm.value.image = profileData.value.image
  previewUrl.value = ''
  selectedFile.value = null
  editDialogVisible.value = true
}

// 💡 4. 头像捕获：预览选择头像并将原生二进制 File 对象存下
const handleAvatarChange = (file) => {
  selectedFile.value = file.raw
  previewUrl.value = URL.createObjectURL(file.raw)
}

// 💡 5. 真实数据保存：包装 FormData 交付给后端的 UserView
// 💡 ✅ 标注修改：重写资料提交保存函数
const submitEditProfile = async () => {
  try {
    saveLoading.value = true

    const formData = new FormData()

    // 🌟 核心防错 1：只有当用户“真的改了名字”时才往后端传 username 字段
    // 这样可以完美避开 Django 数据库对未变更用户名的“重复存在”校验冲突！
    if (editForm.value.username && editForm.value.username !== profileData.value.username) {
      formData.append('username', editForm.value.username)
    }

    // 简介直接传递
    formData.append('bio', editForm.value.bio || '')

    // 如果选择了新的本地头像文件，送入二进制数据
    if (selectedFile.value) {
      formData.append('image', selectedFile.value)
    }

    // 发送局部更新 PATCH 请求
    const res = await updateProfileApi(formData)

    // 🌟 核心防错 2：对齐你项目的全局通用响应结构（检查 res.code 或 res.data）
    if (res && (res.code === 100 || res.data)) {
      ElMessage.success('资料修改成功！')

      // ① 重新拉取当前页面所需的社交与 Profile 数据链，使页面内容刷新
      await fetchUserProfileChain()

      // 获取后端返回的更新后的真实数据（兼容你后端可能包裹在 data 内的结构）
      const updatedUser = res.data || res.user || {}

      // ② 🌟 临门一脚：调用我们上一步检查过的 Pinia 内部方法，派发给顶部 Header 更新
      userStore.updateInfo({
        username: updatedUser.username || editForm.value.username,
        bio: updatedUser.bio || editForm.value.bio,
        image: updatedUser.image || profileData.value.image // 拿到后端返回的最新图片 URL
      })

      // ③ 成功后关闭弹窗，重置清理预览缓存
      editDialogVisible.value = false
      previewUrl.value = ''
      selectedFile.value = null
    } else {
      ElMessage.error(res.msg || '保存失败，请检查输入')
    }
  } catch (err) {
    console.error('更新个人资料发生故障:', err)
    // 捕获可能由用户名冲突或文件过大引起的异常提示
    ElMessage.error(err.response?.data?.msg || '更新失败，请重试')
  } finally {
    saveLoading.value = false
  }
}

// 点击行跳转查看空间
const viewOtherProfile = (username) => {
  router.push(`/profiles/info?username=${username}`)
}

// 跳转到订单页面
const goToOrders = () => {
  router.push('/profiles/orders')
}

// 跳转到地址管理页面
const goToAddresses = () => {
  router.push('/profiles/addresses')
}

// 跳转到收藏页面
const goToCollections = () => {
  router.push('/profiles/collections')
}

// 跳转到帖子页面
const goToPosts = () => {
  router.push('/profiles/posts')
}

// 跳转到数据统计页面
const goToData = () => {
  router.push('/profiles/data')
}

const loadOrderCount = async () => {
  if (!isMe.value) return
  try {
    const res = await getOrders()
    if (res.code === 100) {
      orderCount.value = res.data.count || 0
    }
  } catch (error) {
    console.error('加载订单数量失败', error)
  }
}

const loadAddressCount = async () => {
  if (!isMe.value) return
  try {
    const res = await getAddresses()
    if (res.code === 100) {
      addressCount.value = res.data.length || 0
    }
  } catch (error) {
    console.error('加载地址数量失败', error)
  }
}

// 💡 侦听器关键：由于是同一个组件内切路由（比如从看自己切到看别人的列表），组件不会重新销毁挂载。
// 必须通过监听 query.username 的变化，来重新触发数据抓取。
watch(() => route.query.username, () => {
  fetchUserProfileChain()
  loadOrderCount()
  loadAddressCount()
}, { deep: true })

onMounted(() => {
  fetchUserProfileChain()
  loadOrderCount()
  loadAddressCount()
})
</script>

<style scoped>
.profile-info-container {
  padding: 20px 10px;
  display: flex;
  justify-content: center;
}
.profile-layout-wrapper {
  width: 100%;
  max-width: 650px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.profile-card, .relation-card {
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  background-color: #fff;
}
.profile-header {
  display: flex;
  align-items: center;
  gap: 25px;
}
.profile-avatar {
  border: 3px solid #ecf5ff;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
}
.profile-meta {
  flex-grow: 1;
}
.name-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.username {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin: 0;
}
.bio-text {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin: 0;
}
.stats-row {
  display: flex;
  text-align: center;
}
.stats-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  user-select: none;
  border-right: 1px solid #ebeef5;
}
.stats-item:last-child {
  border-right: none;
}
.stats-num {
  font-size: 24px;
  font-weight: bold;
  color: #606266;
  font-family: 'Arial Black', sans-serif;
  transition: all 0.2s ease;
}
.stats-num.active-num, .stats-item:hover .stats-num {
  color: #409eff;
  transform: scale(1.08);
}
.stats-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}
.relation-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
}
.user-list {
  display: flex;
  flex-direction: column;
}
.user-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 12px 10px;
  border-bottom: 1px solid #f2f6fc;
  cursor: pointer;
  border-radius: 6px;
  transition: background-color 0.2s;
}
.user-item:hover {
  background-color: #f5f7fa;
}
.user-item:last-child {
  border-bottom: none;
}
.user-info-mini {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.user-name-mini {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}
.user-bio-mini {
  font-size: 12px;
  color: #909399;
  max-width: 320px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.avatar-uploader {
  text-align: center;
  cursor: pointer;
  border: 1px dashed #dcdfe6;
  border-radius: 8px;
  padding: 15px;
  background: #fafafa;
  transition: border-color 0.2s;
}
.avatar-uploader:hover {
  border-color: #409eff;
}
.edit-preview-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid #dcdfe6;
}
.upload-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}
.quick-entry-card {
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  background-color: #fff;
}
.quick-entry-card :deep(.el-card__header) {
  padding-bottom: 12px;
}
.quick-entry-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.quick-entry-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px 10px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}
.quick-entry-item:hover {
  background-color: #f5f7fa;
  transform: translateY(-2px);
}
.entry-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.order-icon {
  background-color: #fdf6ec;
}
.address-icon {
  background-color: #f0f9eb;
}
.collection-icon {
  background-color: #fef0f0;
}
.post-icon {
  background-color: #f4f4f5;
}
.data-icon {
  background-color: #f5f0ff;
}
.edit-icon {
  background-color: #ecf5ff;
}
.entry-label {
  font-size: 14px;
  color: #606266;
}
</style>