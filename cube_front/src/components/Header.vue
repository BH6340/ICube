<template>
  <!-- 顶部导航栏组件 -->
  <!-- 使用 Element Plus 的 el-menu 组件实现水平导航 -->
  <!-- :ellipsis="false" 禁止菜单项省略，确保所有菜单项都显示 -->
  <!-- :default-active 绑定当前激活的菜单索引，@select 监听菜单点击事件 -->
  <el-menu mode="horizontal" :ellipsis="false" class="nav-menu" :default-active="activeMenuIndex"
           @select="handleMenuSelect">
    <!-- Logo 区域 -->
    <el-menu-item index="logo" class="logo-section">
      <img src="@/assets/cube.svg" alt="ICube Logo" class="logo-img"/>
      <span class="site-name">ICube</span>
    </el-menu-item>

    <!-- 动态渲染菜单项 -->
    <!-- 根据当前路由动态切换显示主菜单或个人中心菜单 -->
    <template v-for="item in currentMenuItems" :key="item.index">
      <el-menu-item :index="item.index">{{ item.label }}</el-menu-item>
    </template>

    <!-- 占位符，将右侧元素推到最右边 -->
    <div class="flex-grow"/>

    <!-- 购物车图标（仅登录用户显示） -->
    <!-- 使用 el-badge 显示购物车数量，最多显示99 -->
    <div class="cart-section" v-if="userStore.token" @click="goToCart">
      <el-badge :value="cartCount" :max="99" class="cart-badge">
        <el-icon size="24" color="#409EFF">
          <ShoppingCart />
        </el-icon>
      </el-badge>
    </div>

    <!-- 用户认证区域 -->
    <!-- 根据登录状态显示不同内容：未登录显示登录/注册按钮，已登录显示用户下拉菜单 -->
    <div class="auth-section">
      <template v-if="!userStore.token">
        <el-button text @click="$router.push('/login')">登录</el-button>
        <el-button type="primary" round @click="$router.push('/register')">注册</el-button>
      </template>
      <template v-else>
        <!-- 用户信息下拉菜单 -->
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
              <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </template>
    </div>
  </el-menu>
</template>

<script setup>
/**
 * Header.vue - 顶部导航栏组件
 * 
 * 核心职责：
 * 1. 展示网站 Logo 和品牌名称
 * 2. 根据当前路由动态渲染导航菜单（主菜单 / 个人中心菜单）
 * 3. 显示购物车数量徽标（实时同步）
 * 4. 处理用户认证状态显示（登录/注册按钮 / 用户下拉菜单）
 * 5. 响应路由变化，自动更新菜单高亮状态
 * 
 * 设计要点：
 * - 使用 Pinia store 管理用户状态、菜单状态和购物车状态
 * - 通过 match_paths 实现深度路径前缀匹配，确保嵌套路由也能正确高亮
 * - 购物车数量通过 cartVersion 监听实现响应式更新，避免频繁 API 调用
 * - 菜单数据从后端动态获取，支持后台配置导航结构
 */

import {ref, watch, nextTick, onMounted} from 'vue'
import {useUserStore} from '@/stores/user'      // 用户状态管理
import {useMenuStore} from '@/stores/menu'      // 菜单状态管理
import {useCartRefresh} from '@/stores/cart'    // 购物车刷新状态
import {useRouter, useRoute} from 'vue-router'  // 路由实例
import {ElMessage} from 'element-plus'          // 消息提示
import {ArrowDown, ShoppingCart} from '@element-plus/icons-vue'
import defaultAvatar from '@/assets/default_avatar.svg'
import {logoutApi} from "@/api/user.js"         // 退出登录 API
import {getCart} from "@/api/shop.js"           // 获取购物车 API

// 初始化 Store 和路由实例
const userStore = useUserStore()
const menuStore = useMenuStore()
const { cartVersion } = useCartRefresh()  // 解构获取购物车版本号
const router = useRouter()
const route = useRoute()

// 响应式状态
const activeMenuIndex = ref('')       // 当前激活的菜单索引
const currentMenuItems = ref([])      // 当前显示的菜单项列表
const cartCount = ref(0)              // 购物车商品数量

/**
 * 深度路径前缀匹配函数
 * 根据当前路由路径查找对应的菜单项
 * 
 * @param {string} path - 当前路由路径
 * @param {Array} menus - 菜单列表
 * @returns {Object|null} - 匹配到的菜单项，未匹配返回 null
 * 
 * 匹配逻辑：
 * 1. 优先使用 match_paths 进行前缀匹配（支持嵌套路由）
 * 2. 如果 match_paths 匹配失败，尝试精确路径匹配
 * 3. 都不匹配则返回 null
 */
const findActiveMenu = (path, menus) => {
  const matched = menus.find(menu => {
    if (menu.path === '/' || !menu.match_paths) return false
    return menu.match_paths.some(matchPath => path.startsWith(matchPath))
  })
  if (matched) return matched
  return menus.find(menu => menu.path === path) || null
}

/**
 * 更新导航状态
 * 根据当前路由路径动态切换菜单源并计算高亮项
 * 
 * @param {string} path - 当前路由路径
 * 
 * 设计逻辑：
 * 1. 如果路径以 /profiles 开头，使用个人中心菜单集
 * 2. 其他路径使用主系统菜单集
 * 3. 特殊处理首页和论坛路径的默认高亮
 */
const updateNavigation = (path) => {
  nextTick(() => {
    if (path.startsWith('/profiles')) {
      // 个人中心页面：切换到个人中心菜单
      currentMenuItems.value = menuStore.profileMenus
      const activeItem = findActiveMenu(path, menuStore.profileMenus)
      activeMenuIndex.value = activeItem ? activeItem.index : 'p-2'
    } else {
      // 其他页面：使用主系统菜单
      currentMenuItems.value = menuStore.mainMenus
      const activeItem = findActiveMenu(path, menuStore.mainMenus)
      if (path === '/' || path === '/home') {
        activeMenuIndex.value = '1'           // 首页默认高亮第一个菜单
      } else if (path.startsWith('/forum')) {
        activeMenuIndex.value = activeItem ? activeItem.index : '5'  // 论坛默认高亮
      } else {
        activeMenuIndex.value = activeItem ? activeItem.index : ''
      }
    }
  })
}

/**
 * 监听路由变化
 * 当路由路径改变时，自动更新导航高亮状态
 * 
 * 注意：只有菜单数据加载完成后才执行更新，避免空数据导致的错误
 */
watch(() => route.path, (newPath) => {
  if (menuStore.isLoaded) {
    updateNavigation(newPath)
  }
}, {immediate: true})

/**
 * 跳转到购物车页面
 */
const goToCart = () => {
  router.push('/shop/cart')
}

/**
 * 加载购物车数量
 * 
 * 逻辑：
 * 1. 如果用户未登录，购物车数量设为 0
 * 2. 调用 API 获取购物车数据，计算商品数量
 * 3. 异常情况下数量设为 0，避免显示错误信息
 */
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

/**
 * 组件挂载时执行初始化
 * 
 * 初始化流程：
 * 1. 调用 menuStore.fetchMenus() 从后端获取菜单数据
 * 2. 菜单数据加载完成后，立即根据当前路由计算菜单高亮
 * 3. 加载购物车数量
 */
onMounted(async () => {
  await menuStore.fetchMenus()
  updateNavigation(route.path)
  loadCartCount()
})

/**
 * 监听购物车版本变化
 * 
 * 设计说明：
 * 当购物车商品发生变化时（添加/删除/修改），cartVersion 会自增
 * 监听到变化后自动重新加载购物车数量，实现响应式更新
 */
watch(cartVersion, () => {
  loadCartCount()
})

/**
 * 处理菜单点击事件
 * 
 * @param {string} index - 点击的菜单索引
 * 
 * 逻辑：
 * 1. 如果点击的是 Logo，跳转到首页
 * 2. 根据索引查找对应的菜单项，跳转到其配置的路径
 */
const handleMenuSelect = (index) => {
  if (index === 'logo') {
    router.push('/');
    return
  }
  const target = menuStore.allMenus.find(item => item.index === index)
  if (target && target.path) router.push(target.path)
}

/**
 * 处理用户下拉菜单命令
 * 
 * @param {string} command - 命令类型（logout/profiles/settings）
 * 
 * 逻辑：
 * 1. logout：调用退出登录 API，清除用户信息，跳转到首页
 * 2. profiles：跳转到个人中心页面
 * 3. settings：跳转到设置页面
 */
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