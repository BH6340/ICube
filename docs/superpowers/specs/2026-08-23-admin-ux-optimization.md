# Admin 后台体验优化

## 背景

Django Admin（基于 django-unfold）存在以下体验问题：
1. 侧边栏模块名称为英文（Home / Accounts / Timer），不符合中文用户习惯
2. 列表页筛选、分页、排序每次操作都整页刷新，体验割裂
3. 页面加载/切换时短暂闪现旧内容或白屏，过渡不自然

## 目标

- 侧边栏三个模块显示中文名
- 列表页筛选/分页/排序操作无整页刷新
- 页面加载过渡平滑，避免闪现旧模板

## 范围

### 包含
- 三个模块（home / accounts / timer）的 verbose_name 中文化
- 列表页无刷新：筛选器、分页、排序的 AJAX 局部刷新
- 加载遮罩：统一的 loading 遮罩层，页面切换时平滑过渡
- Admin 静态资源缓存优化

### 不包含
- 编辑页/详情页的无刷新改造（复杂度高，收益低）
- Admin 整体 UI 风格重做
- 其他模块（forum / formula / shop）的改名

## 详细设计

### 1. 模块标题中文化

在三个 app 的 `apps.py` 中设置 `verbose_name`：

| app | 原名 | 中文名 |
|-----|------|--------|
| home | Home | 主页 |
| accounts | Accounts | 用户 |
| timer | Timer | 计时器 |

实现方式：各 app 的 `AppConfig` 类中添加 `verbose_name = "中文名"`。

### 2. 列表页无刷新（A2）

**技术方案：** 通过注入自定义 JS，使用原生 `fetch` 拦截筛选器和分页的点击事件，局部替换列表内容区。

**实现要点：**
- 创建 `static/admin/js/admin-ux.js`
- 监听侧边栏筛选器的 change/click 事件
- 监听分页链接的 click 事件
- 监听列表表头排序的 click 事件
- 触发时：显示加载遮罩 → fetch 新 URL → 解析返回 HTML → 替换内容区 → 更新 URL（pushState）→ 隐藏遮罩
- 通过 `Media` 类注入到 ModelAdmin 中

**注入方式：** 在各 admin.py 的 `Media` 类中引用 `admin/js/admin-ux.js`，或通过自定义 AdminSite 全局注入。

### 3. 加载遮罩（B1）

**技术方案：** 自定义 CSS + JS 实现全屏半透明遮罩 + 旋转加载动画

**实现要点：**
- 创建 `static/admin/css/admin-ux.css`
- 遮罩层：固定定位全屏、半透明黑底、居中 spinner
- 默认隐藏，`.loading` 类激活时显示
- 进入页面时短暂显示（防白屏闪烁），页面加载完成后淡出
- 无刷新操作期间保持显示

### 4. 静态资源缓存（B2）

**技术方案：** Nginx 中对 Admin 静态资源设置合理的缓存头

**实现要点：**
- Admin 静态文件路径 `/static/admin/`
- 设置 `expires 7d` + `Cache-Control: public, max-age=604800, immutable`
- 版本更新时通过 Django collectstatic 的哈希文件名自动失效

## 文件改动清单

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `cube_api/apps/home/apps.py` | 修改 | 添加 verbose_name |
| `cube_api/apps/accounts/apps.py` | 修改 | 添加 verbose_name |
| `cube_api/apps/timer/apps.py` | 修改 | 添加 verbose_name |
| `cube_api/static/admin/js/admin-ux.js` | 新增 | 无刷新交互 + 加载遮罩逻辑 |
| `cube_api/static/admin/css/admin-ux.css` | 新增 | 加载遮罩样式 |
| `nginx/conf.d/icube.conf` | 修改 | Admin 静态资源缓存配置 |
| `cube_api/cube_api/admin.py` | 新增 | 自定义 AdminSite，全局注入 Media |

## 验证方式

1. 进入 `/admin/`，侧边栏三个模块显示中文名
2. 在任意列表页点击筛选器，页面不刷新，内容区更新，URL 同步变化
3. 点击分页/排序，同上
4. 页面切换时有平滑的加载过渡，无白屏闪烁
5. 浏览器开发者工具 Network 面板查看 `/static/admin/*` 响应头有缓存指令
