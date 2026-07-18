<template>
  <el-menu mode="horizontal" :ellipsis="false" class="nav-menu" :default-active="activeMenuIndex"
           @select="handleMenuSelect">
    <el-menu-item index="logo" class="logo-section">
      <img src="@/assets/cube.svg" alt="ICube Logo" class="logo-img"/>
      <span class="site-name">ICube</span>
    </el-menu-item>

    <template v-for="item in currentMenuItems" :key="item.index">
      <el-menu-item :index="item.index">{{ item.label }}</el-menu-item>
    </template>

    <div class="flex-grow"/>

    <div class="cart-section" v-if="userStore.token" @click="goToCart">
      <el-badge :value="cartCount" :max="99" class="cart-badge">
        <el-icon size="24" color="#409EFF">
          <ShoppingCart />
        </el-icon>
      </el-badge>
    </div>

    <div class="auth-section">
      <template v-if="!userStore.token">
        <el-button text @click="$router.push('/login')">登录</el-button>
        <el-button type="primary" round @click="$router.push('/register')">注册</el-button>
      </template>
      <template v-else>
        <el-dropdown @command="handleDropdownCommand" trigger="click">
          <div class="user-info">
            <el-avatar :size="32" :src="userStore.image || defaultAvatar" class="avatar-hover"/>
            <span class="username">{{ userStore.username }}</span>
            <el-icon class="el-icon--right">
              <arrow-down/>
            </el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profiles">个人中心</el-dropdown-item>
              <el-dropdown-item command="settings">设置</el-dropdown-item>
              <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </template>
    </div>
  </el-menu>
</template>

<script setup>
import {ref, watch, nextTick, onMounted} from 'vue'
import {useUserStore} from '@/stores/user'
import {useMenuStore} from '@/stores/menu' // 💡 引入菜单仓库
import {useRouter, useRoute} from 'vue-router'
import {ElMessage} from 'element-plus'
import {ArrowDown, ShoppingCart} from '@element-plus/icons-vue'
import defaultAvatar from '@/assets/default_avatar.svg'
import {logoutApi} from "@/api/user.js"
import {getCart} from "@/api/shop.js"

const userStore = useUserStore()
const menuStore = useMenuStore()
const router = useRouter()
const route = useRoute()

const activeMenuIndex = ref('')
const currentMenuItems = ref([])
const cartCount = ref(0)

// 深度路径前缀匹配
const findActiveMenu = (path, menus) => {
  const matched = menus.find(menu => {
    if (menu.path === '/' || !menu.match_paths) return false
    return menu.match_paths.some(matchPath => path.startsWith(matchPath))
  })
  if (matched) return matched
  return menus.find(menu => menu.path === path) || null
}

// 核心解耦驱动：动态分配菜单源，并计算高亮
const updateNavigation = (path) => {
  nextTick(() => {
    // 🌟 1. 只要发现进入 /profiles 路由，自动切换显示“个人中心菜单集”
    if (path.startsWith('/profiles')) {
      currentMenuItems.value = menuStore.profileMenus
      const activeItem = findActiveMenu(path, menuStore.profileMenus)
      activeMenuIndex.value = activeItem ? activeItem.index : 'p-2'
    }
    // 🌟 2. 其他页面一律自动展示“主系统菜单集”
    else {
      currentMenuItems.value = menuStore.mainMenus
      const activeItem = findActiveMenu(path, menuStore.mainMenus)
      if (path === '/' || path === '/home') {
        activeMenuIndex.value = '1'
      } else if (path.startsWith('/forum')) {
        activeMenuIndex.value = activeItem ? activeItem.index : '5'
      } else {
        activeMenuIndex.value = activeItem ? activeItem.index : ''
      }
    }
  })
}

// 实时监听路由
watch(() => route.path, (newPath) => {
  if (menuStore.isLoaded) {
    updateNavigation(newPath)
  }
}, {immediate: true})

const goToCart = () => {
  router.push('/shop/cart')
}

const loadCartCount = async () => {
  if (!userStore.token) {
    cartCount.value = 0
    return
  }
  try {
    const res = await getCart()
    if (res.code === 100) {
      const data = res.data.results || res.data
      cartCount.value = Array.isArray(data) ? data.length : 0
    }
  } catch (error) {
    cartCount.value = 0
  }
}

onMounted(async () => {
  // 1. 初始化拉取后端数据库菜单数据
  await menuStore.fetchMenus()
  // 2. 拉取完成后立刻校准高亮
  updateNavigation(route.path)
  // 3. 加载购物车数量
  loadCartCount()
})

const handleMenuSelect = (index) => {
  if (index === 'logo') {
    router.push('/');
    return
  }
  const target = menuStore.allMenus.find(item => item.index === index)
  if (target && target.path) router.push(target.path)
}

const handleDropdownCommand = async (command) => {
  if (command === 'logout') {
    try {
      await logoutApi()
    } catch (err) {
    } finally {
      userStore.clearInfo()
      ElMessage.success('已退出登录')
      await router.push('/')
    }
  } else if (command === 'profiles') {
    await router.push('/profiles/info')
  } else if (command === 'settings') {
    await router.push('/profiles/settings')
  }
}
</script>

<style scoped>
.nav-menu {
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.logo-section {
  display: flex;
  align-items: center;
  margin-right: 20px;
  border-bottom: none !important;
}

.logo-img {
  width: 35px;
  height: 35px;
  margin-right: 10px;
}

.site-name {
  font-size: 22px;
  font-weight: bold;
  background: linear-gradient(45deg, #409eff, #67c23a);
  -webkit-background-clip: text;
  color: transparent;
  letter-spacing: 1px;
}

.flex-grow {
  flex-grow: 1;
}

.cart-section {
  display: flex;
  align-items: center;
  padding: 0 15px;
  cursor: pointer;
}

.cart-badge {
  cursor: pointer;
}

.el-menu-item {
  font-size: 16px !important;
}

.auth-section {
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  outline: none;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 20px;
  transition: background-color 0.2s;
}

.user-info:hover {
  background-color: #f5f7fa;
}

.avatar-hover {
  border: 1px solid #e4e7ed;
}

.username {
  font-weight: 500;
  color: #409EFF;
}
</style>