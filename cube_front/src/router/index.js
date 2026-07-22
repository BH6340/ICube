// 导入路由创建的相关方法
import {createRouter, createWebHistory} from 'vue-router'

import HomeView from '../views/HomeView.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            component: HomeView,
            children: [
                {
                    path: '', // 空路径代表默认展示，即打开网站时的中间内容
                    name: 'home',
                    component:()=> import('@/components/Main.vue')
                },
                {
                    path: 'tutorials', // 匹配 /formulas
                    name: 'tutorials',
                    component:()=> import('@/views/TutorialView.vue')
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
                    path: 'formulas', // 匹配 /formulas
                    name: 'formulas',
                    component:()=> import('@/views/FormulaView.vue')
                },
                {
                    path: 'timer', // 匹配 /formulas
                    name: 'timer',
                    component:()=> import('@/views/TimerView.vue')
                },
                {
                    path: 'forum', // 匹配 /formulas
                    name: 'forum',
                    component:()=> import('@/views/forum/ForumView.vue')
                },
                {
                    path: 'forum/post/:id',  // 帖子详情
                    name: 'postDetail',
                    component: () => import('@/views/forum/PostDetailView.vue')
                },
                {
                    path: 'forum/create',  // 发布帖子
                    name: 'createPost',
                    component: () => import('@/views/forum/PostEditorView.vue'),
                    meta: { requiresAuth: true }
                },
                {
                    path: 'forum/edit/:id',  // 编辑帖子
                    name: 'editPost',
                    component: () => import('@/views/forum/PostEditorView.vue'),
                    meta: { requiresAuth: true }
                },
                {
                    path: 'shop', // 匹配 /formulas
                    name: 'shop',
                    component:()=> import('@/views/ShopView.vue')
                },
                {
                    path: 'shop/cart', // 匹配 /shop/cart
                    name: 'shopCart',
                    component: () => import('@/views/CartView.vue'),
                    meta: { requiresAuth: true }
                },
                {
                    path: 'shop/checkout', // 匹配 /shop/checkout
                    name: 'shopCheckout',
                    component: () => import('@/views/CheckoutView.vue'),
                    meta: { requiresAuth: true }
                },
                {
                    path: 'shop/pay/callback', // 支付宝同步回调降级
                    name: 'shopPayCallback',
                    component: () => import('@/views/PayCallbackView.vue')
                },
                {
                    path: 'shop/pay/:orderNo', // 匹配 /shop/pay/xxx
                    name: 'shopPay',
                    component: () => import('@/views/PayView.vue'),
                    meta: { requiresAuth: true }
                },
                // ===== 个人中心子路由 =====
                {
                    path: 'profiles/info', // 匹配 /profiles/info
                    name: 'profileInfo',
                    component:()=> import('@/views/profiles/InfoView.vue')
                },
                {
                    path: 'profiles/collections', // 匹配 /profiles/collections
                    name: 'profileCollections',
                    component: () => import('@/views/profiles/CollectionView.vue')
                },
                {
                    path: 'profiles/orders', // 匹配 /profiles/orders
                    name: 'profileOrders',
                    component: () => import('@/views/profiles/OrderView.vue')
                },
                {
                    path: 'profiles/posts', // 匹配 /profiles/posts
                    name: 'profilePosts',
                    component: () => import('@/views/profiles/MyPostsView.vue')
                },
                {
                    path: 'profiles/data', // 匹配 /profiles/data
                    name: 'profileData',
                    component: () => import('@/views/profiles/MyDataView.vue')
                }
            ]
        },
        {
            path: '/login',
            name: 'login',
            component: () => import('@/views/LoginView.vue') // 登录页不需要导航栏，所以独立出来
        },
        {
            path: '/register',
            name: 'register',
            component: () => import('@/views/RegisterView.vue') // 注册页同样独立
        }
    ]

})

export default router