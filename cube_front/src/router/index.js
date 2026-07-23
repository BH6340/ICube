/**
 * Vue Router 路由配置
 *
 * 定义前端路由结构，支持嵌套路由和按需加载。
 *
 * 路由结构：
 *   - / (HomeView): 主布局，包含所有功能页面的子路由
 *     - /: 首页（Main.vue）
 *     - /tutorials: 教程列表
 *     - /tutorial/beginner: 新手教程
 *     - /tutorial/cfop: CFOP 教程
 *     - /tutorial/oll-essentials: OLL 精华
 *     - /tutorial/pll-essentials: PLL 精华
 *     - /tutorial/complete-oll: 完整 OLL
 *     - /tutorial/complete-pll: 完整 PLL
 *     - /formulas: 公式库
 *     - /timer: 计时器
 *     - /forum: 论坛首页
 *     - /forum/post/:id: 帖子详情
 *     - /forum/create: 创建帖子（需登录）
 *     - /forum/edit/:id: 编辑帖子（需登录）
 *     - /shop: 商城首页
 *     - /shop/cart: 购物车（需登录）
 *     - /shop/checkout: 结算页（需登录）
 *     - /shop/pay/callback: 支付回调
 *     - /shop/pay/:orderNo: 支付页面（需登录）
 *     - /profiles/info: 个人信息
 *     - /profiles/collections: 收藏列表
 *     - /profiles/orders: 订单列表
 *     - /profiles/posts: 我的帖子
 *     - /profiles/data: 数据统计
 *   - /login: 登录页（独立，不含导航栏）
 *   - /register: 注册页（独立，不含导航栏）
 *
 * 设计特点：
 *   - **嵌套路由**：功能页面作为 HomeView 的子路由，共享导航栏和侧边栏
 *   - **按需加载**：使用动态 import() 实现组件懒加载，优化首屏加载速度
 *   - **登录保护**：需要登录的路由通过 meta.requiresAuth 标记
 *   - **History 模式**：使用 createWebHistory，去除 URL 中的 #
 */

import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            component: HomeView,
            children: [
                {
                    path: '',
                    name: 'home',
                    component: () => import('@/components/Main.vue')
                },
                {
                    path: 'tutorials',
                    name: 'tutorials',
                    component: () => import('@/views/TutorialView.vue')
                },
                {
                    path: 'tutorial/beginner',
                    name: 'beginnerTutorial',
                    component: () => import('@/views/tutorial/BeginnerTutorial.vue')
                },
                {
                    path: 'tutorial/cfop',
                    name: 'cfopTutorial',
                    component: () => import('@/views/tutorial/CFOPTutorial.vue')
                },
                {
                    path: 'tutorial/oll-essentials',
                    name: 'ollEssentials',
                    component: () => import('@/views/tutorial/OLLEssentials.vue')
                },
                {
                    path: 'tutorial/pll-essentials',
                    name: 'pllEssentials',
                    component: () => import('@/views/tutorial/PLLEssentials.vue')
                },
                {
                    path: 'tutorial/complete-oll',
                    name: 'completeOLL',
                    component: () => import('@/views/tutorial/CompleteOLL.vue')
                },
                {
                    path: 'tutorial/complete-pll',
                    name: 'completePLL',
                    component: () => import('@/views/tutorial/CompletePLL.vue')
                },
                {
                    path: 'formulas',
                    name: 'formulas',
                    component: () => import('@/views/FormulaView.vue')
                },
                {
                    path: 'timer',
                    name: 'timer',
                    component: () => import('@/views/TimerView.vue')
                },
                {
                    path: 'forum',
                    name: 'forum',
                    component: () => import('@/views/forum/ForumView.vue')
                },
                {
                    path: 'forum/post/:id',
                    name: 'postDetail',
                    component: () => import('@/views/forum/PostDetailView.vue')
                },
                {
                    path: 'forum/create',
                    name: 'createPost',
                    component: () => import('@/views/forum/PostEditorView.vue'),
                    meta: { requiresAuth: true }
                },
                {
                    path: 'forum/edit/:id',
                    name: 'editPost',
                    component: () => import('@/views/forum/PostEditorView.vue'),
                    meta: { requiresAuth: true }
                },
                {
                    path: 'shop',
                    name: 'shop',
                    component: () => import('@/views/ShopView.vue')
                },
                {
                    path: 'shop/cart',
                    name: 'shopCart',
                    component: () => import('@/views/CartView.vue'),
                    meta: { requiresAuth: true }
                },
                {
                    path: 'shop/checkout',
                    name: 'shopCheckout',
                    component: () => import('@/views/CheckoutView.vue'),
                    meta: { requiresAuth: true }
                },
                {
                    path: 'shop/pay/callback',
                    name: 'shopPayCallback',
                    component: () => import('@/views/PayCallbackView.vue')
                },
                {
                    path: 'shop/pay/:orderNo',
                    name: 'shopPay',
                    component: () => import('@/views/PayView.vue'),
                    meta: { requiresAuth: true }
                },
                {
                    path: 'profiles/info',
                    name: 'profileInfo',
                    component: () => import('@/views/profiles/InfoView.vue')
                },
                {
                    path: 'profiles/collections',
                    name: 'profileCollections',
                    component: () => import('@/views/profiles/CollectionView.vue')
                },
                {
                    path: 'profiles/orders',
                    name: 'profileOrders',
                    component: () => import('@/views/profiles/OrderView.vue')
                },
                {
                    path: 'profiles/posts',
                    name: 'profilePosts',
                    component: () => import('@/views/profiles/MyPostsView.vue')
                },
                {
                    path: 'profiles/data',
                    name: 'profileData',
                    component: () => import('@/views/profiles/MyDataView.vue')
                }
            ]
        },
        {
            path: '/login',
            name: 'login',
            component: () => import('@/views/LoginView.vue')
        },
        {
            path: '/register',
            name: 'register',
            component: () => import('@/views/RegisterView.vue')
        }
    ]
})

export default router