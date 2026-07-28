/**
 * Pinia 状态管理入口文件
 *
 * 本项目采用 Pinia 进行全局状态管理，各 Store 定义在独立文件中：
 *   - user.js: 用户登录状态和个人信息管理
 *   - cart.js: 购物车版本控制（跨组件刷新）
 *   - menu.js: 导航菜单动态加载和分类
 *
 * 使用方式：
 *   import { useUserStore } from '@/stores/user'
 *   import { useCartRefresh } from '@/stores/cart'
 *   import { useMenuStore } from '@/stores/menu'
 *
 * 设计特点：
 *   - 按功能模块拆分 Store，职责单一
 *   - 使用 Composition API 风格定义（setup stores）
 *   - 状态持久化通过 localStorage 实现（在各 Store 内部处理）
 */

// 目前为空实现，各 Store 直接从对应文件导入使用
// 如需统一导出，可在此处添加 re-export
