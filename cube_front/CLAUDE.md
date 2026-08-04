# CLAUDE.md - 前端 — Vue 3 + Vite

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 命令
- `npm install`: 安装依赖
- `npm run dev`: 开发服务器（端口 5173，/api 代理到 127.0.0.1:8000）
- `npm run build`: 生产构建
- `npm run preview`: 预览构建产物

## 自动导入（无需手动 import）
通过 `unplugin-auto-import` 和 `unplugin-vue-components` 自动导入以下内容，**不需要在组件中手动写 import 语句**：
- Vue API：`ref`、`reactive`、`computed`、`watch`、`onMounted`、`onBeforeUnmount` 等
- Vue Router：`useRouter`、`useRoute`
- Pinia：`useStore` / `defineStore`
- Element Plus：所有组件（`ElButton`、`ElMessage`、`ElForm` 等）

## 项目结构
- src/api/ — API 接口封装（按模块划分：user.js、posts.js、formula.js、shop.js、comments.js、tags.js、home.js）
- src/stores/ — Pinia 状态管理（user.js、menu.js）
- src/components/ — 可复用组件
  - formula/CubeDemo.vue — 3D 魔方核心组件（Three.js），清理逻辑见下文
  - formula/FormulaLibrary.vue — 公式库展示
  - forum/CommentSection.vue、MarkdownEditor.vue、TagSelector.vue — 论坛组件
- src/views/ — 页面级组件（forum/、profiles/ 等子目录）
- src/http/request.js — Axios 实例配置（统一拦截器、错误处理）
- src/router/index.js — 路由定义（HomeView 为父布局，其余页面为其子路由）

## 开发约定
- Vue 3 Composition API，`<script setup>` 语法
- Pinia 状态管理：`stores/`
- API 调用：`api/`
- HTTP 请求：`http/request.js`
- API 模块导入 request 用 `@/http/request`（禁止写 `@/utils/request`）
- 禁止硬编码 `localhost:8000`：API 走 `/api` 代理，媒体走 `/media/`

## 关键约定

### API 响应格式
后端返回 `{ code: 100, msg: "success", data: {...} }`。`request.js` 拦截器将 `code !== 100` 视为错误并通过 `ElMessage` 显示。组件中直接用 `response.data` 获取数据。

### Vite 代理
本地开发时，`/api` 请求通过 Vite 代理到 `http://127.0.0.1:8000`。生产环境由 Nginx 处理。
`vite.config.js` 需同时配置 `dev` 和 `preview` 的 proxy，确保 `/api` 与 `/media` 请求正确代理到后端。

### Three.js 内存清理（CubeDemo.vue）
在 `onBeforeUnmount` 中**必须**：
1. 调用 `geometry.dispose()` 和 `material.dispose()` 清理所有 mesh
2. 调用 `renderer.dispose()` 销毁渲染器
3. 取消 `requestAnimationFrame`（通过 `cancelAnimationFrame`）
4. 停止 `TWEEN` 动画
否则会导致内存泄漏。

### 认证
JWT token 存储在 `localStorage`，通过 `Authorization: Token <token>` 头发送。

## 业务领域约定
- 公式列表排序字段：`view_count`（不是 `views`）
- 公式缩略图路径匹配：`/media/formulas/`（不是 `/media/formula_thumbnails/`）
- 公式卡片显示：头部=公式名+难度标签，底部=分类名  by  用户名（中间两个空格）
- 帖子图片关联：全量同步模式——从 Markdown 解析所有 `![alt](url)`，删除多余、补齐缺失
- 帖子列表布局：flex 左右结构，左侧内容自适应，右侧图片固定 140px，垂直居中；图片 1:1、`object-fit: contain`，不裁剪
- 公式列表和公式选择弹窗图片均使用 1:1 比例，`object-fit: contain` 确保完整显示，不裁剪
- 轮播图推荐规格：16:9，1280×720~1920×1080，100-300KB，PNG
- 教程导航：`/tutorials` → `/tutorial/beginner`、`/tutorial/cfop` 及子页面

## 易踩坑位（历史教训）
- 前端导入路径错误（如使用 `@/utils/request` 而非 `@/http/request`）会导致 Vite 编译失败
- 浏览器 Private Network Access (PNA) 策略会阻止公网域名直接访问 localhost 回环地址的图片资源
- 后端返回的图片路径可能不含 `/media/` 前缀，需通过 `build_image_url` 统一添加