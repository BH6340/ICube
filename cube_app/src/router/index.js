import { createRouter, createWebHashHistory } from 'vue-router'

// 使用 hash 路由：Capacitor WebView 加载本地文件，
// history 模式刷新会 404，hash 模式更可靠
const routes = [
  {
    path: '/',
    redirect: '/splash',
  },
  {
    path: '/splash',
    name: 'splash',
    component: () => import('@/views/SplashView.vue'),
    meta: { title: '', noTabbar: true },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { title: '登录', noTabbar: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { title: '注册', noTabbar: true },
  },
  {
    path: '/forgot-password',
    name: 'forgot-password',
    component: () => import('@/views/ForgotPasswordView.vue'),
    meta: { title: '找回密码', noTabbar: true },
  },
  {
    path: '/formula',
    name: 'Formula',
    component: () => import('@/views/FormulaView.vue'),
    meta: { title: '公式库' },
  },
  {
    path: '/formula/:id',
    name: 'FormulaDetail',
    component: () => import('@/views/FormulaDetailView.vue'),
    meta: { title: '公式详情', noTabbar: true },
  },
  {
    path: '/timer',
    name: 'Timer',
    component: () => import('@/views/TimerView.vue'),
    meta: { title: '计时' },
  },
  {
    path: '/forum',
    name: 'Forum',
    component: () => import('@/views/ForumView.vue'),
    meta: { title: '论坛' },
  },
  {
    path: '/forum/:id',
    name: 'PostDetail',
    component: () => import('@/views/PostDetailView.vue'),
    meta: { title: '帖子详情', noTabbar: true },
  },
  {
    path: '/forum/create',
    name: 'PostCreate',
    component: () => import('@/views/PostEditorView.vue'),
    meta: { title: '发帖', noTabbar: true },
  },
  {
    path: '/forum/edit/:id',
    name: 'PostEdit',
    component: () => import('@/views/PostEditorView.vue'),
    meta: { title: '编辑帖子', noTabbar: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { title: '我的' },
  },
  {
    path: '/timer-records',
    redirect: '/timer?tab=records',
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

// 路由守卫：未登录访问 requiresAuth 页面时跳转登录
router.beforeEach((to) => {
  const requiresAuth = to.matched.some(r => r.meta.requiresAuth)
  if (requiresAuth && !localStorage.getItem('token')) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
