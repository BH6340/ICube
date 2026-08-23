# Admin 后台体验优化 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** Admin 侧边栏三个模块中文化、列表页无刷新筛选/分页/排序、页面加载过渡平滑

**架构：** 通过 AppConfig.verbose_name 实现中文名；通过自定义 AdminSite 全局注入 JS/CSS，JS 拦截筛选/分页/排序事件用 fetch 局部替换内容区；Nginx 增加 Admin 静态资源缓存

**技术栈：** Django 6.0 + django-unfold + 原生 JS + Nginx

---

## 文件清单

| 文件 | 类型 | 职责 |
|------|------|------|
| `cube_api/apps/home/apps.py` | 修改 | 添加 verbose_name = "主页" |
| `cube_api/apps/accounts/apps.py` | 修改 | 添加 verbose_name = "用户" |
| `cube_api/apps/timer/apps.py` | 修改 | 添加 verbose_name = "计时器" |
| `cube_api/cube_api/admin.py` | 新增 | 自定义 AdminSite，全局注入 Media（JS/CSS） |
| `cube_api/cube_api/urls.py` | 修改 | 注册自定义 AdminSite |
| `cube_api/static/admin/css/admin-ux.css` | 新增 | 加载遮罩样式 |
| `cube_api/static/admin/js/admin-ux.js` | 新增 | 无刷新交互 + 加载遮罩逻辑 |
| `nginx/conf.d/icube.conf` | 修改 | Admin 静态资源缓存配置 |

---

### 任务 1：模块标题中文化

**文件：**
- 修改：`cube_api/apps/home/apps.py`
- 修改：`cube_api/apps/accounts/apps.py`
- 修改：`cube_api/apps/timer/apps.py`

- [ ] **步骤 1：修改 home/apps.py 添加 verbose_name**

```python
from django.apps import AppConfig


class HomeConfig(AppConfig):
    name = 'apps.home'
    verbose_name = '主页'
```

- [ ] **步骤 2：修改 accounts/apps.py 添加 verbose_name**

```python
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'apps.accounts'
    verbose_name = '用户'
```

- [ ] **步骤 3：修改 timer/apps.py 添加 verbose_name**

```python
from django.apps import AppConfig


class TimerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.timer'
    label = 'timer'
    verbose_name = '计时器'
```

- [ ] **步骤 4：启动开发服务器验证**

运行：`cd cube_api && python manage.py runserver --settings=cube_api.settings.dev`
访问 `http://127.0.0.1:8000/admin/` 登录后查看侧边栏，三个模块应显示中文名。

- [ ] **步骤 5：Commit**

```bash
git add cube_api/apps/home/apps.py cube_api/apps/accounts/apps.py cube_api/apps/timer/apps.py
git commit -m "feat(admin): 侧边栏模块名称中文化（主页/用户/计时器）"
```

---

### 任务 2：自定义 AdminSite 全局注入 Media

**文件：**
- 新建：`cube_api/cube_api/admin.py`
- 修改：`cube_api/cube_api/urls.py`

- [ ] **步骤 1：创建自定义 AdminSite**

在 `cube_api/cube_api/admin.py` 中：

```python
# -*- coding: utf-8 -*-
"""
自定义 AdminSite

全局注入自定义 JS/CSS，实现列表页无刷新、加载遮罩等体验优化。
"""
from django.contrib.admin import AdminSite
from unfold.admin import ModelAdmin


class IcubeAdminSite(AdminSite):
    """自定义 AdminSite，用于全局注入自定义 Media"""

    site_header = 'ICube 管理后台'
    site_title = 'ICube Admin'
    index_title = '站点管理'

    class Media:
        css = {
            'all': ('admin/css/admin-ux.css',),
        }
        js = ('admin/js/admin-ux.js',)


# 全局单例
admin_site = IcubeAdminSite(name='admin')
```

- [ ] **步骤 2：修改 urls.py 注册自定义 AdminSite**

将 `urls.py` 中的 `path('admin/', admin.site.urls)` 改为使用自定义 site。

修改 `cube_api/cube_api/urls.py`：
- 顶部导入 `from .admin import admin_site`
- 将 `path('admin/', admin.site.urls)` 改为 `path('admin/', admin_site.urls)`

注意：各 app 的 admin.py 中仍使用 `@admin.register(Model)` 注册，但需要确认它们注册到默认 site 还是自定义 site。由于各 admin.py 继承的是 `unfold.admin.ModelAdmin` 且用 `@admin.register` 装饰器注册到默认 `admin.site`，需要改注册方式。

更简单的做法：不改各 app 的注册方式，而是通过中间件或 base_site.html 模板覆盖的方式注入 JS/CSS。

**修正方案：** 不用自定义 AdminSite，改用模板覆盖方式注入。创建 `templates/admin/base_site.html`，在 `extrahead` 块中引入自定义 CSS 和 JS。

新建 `cube_api/templates/admin/base_site.html`：

```html
{% extends "admin/base_site.html" %}
{% load static %}

{% block extrahead %}
{{ block.super }}
<link rel="stylesheet" href="{% static 'admin/css/admin-ux.css' %}">
<script src="{% static 'admin/js/admin-ux.js' %}" defer></script>
{% endblock %}
```

这种方式无需改动各 app 的 admin.py 注册逻辑，侵入性最小。

- [ ] **步骤 3：验证模板覆盖生效**

启动服务访问 admin，查看页面源码，应能看到 `admin-ux.css` 和 `admin-ux.js` 的引用。

- [ ] **步骤 4：Commit**

```bash
git add cube_api/cube_api/admin.py cube_api/cube_api/urls.py cube_api/templates/admin/base_site.html
git commit -m "feat(admin): 通过模板覆盖全局注入自定义 JS/CSS"
```

---

### 任务 3：加载遮罩 CSS

**文件：**
- 新建：`cube_api/static/admin/css/admin-ux.css`

- [ ] **步骤 1：编写加载遮罩样式**

```css
/* Admin UX 优化样式 */

/* 加载遮罩 */
#admin-ux-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(2px);
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s ease;
}

#admin-ux-overlay.active {
    opacity: 1;
    pointer-events: auto;
}

#admin-ux-overlay .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid #e5e7eb;
    border-top-color: #3b82f6;
    border-radius: 50%;
    animation: admin-ux-spin 0.8s linear infinite;
}

@keyframes admin-ux-spin {
    to { transform: rotate(360deg); }
}

/* 页面初始加载时防止白屏闪烁：先显示遮罩，JS 加载完后移除 */
body.admin-ux-initial #admin-ux-overlay {
    opacity: 1;
    pointer-events: auto;
}
```

- [ ] **步骤 2：验证样式文件存在**

确认 `cube_api/static/admin/css/admin-ux.css` 已创建，内容正确。

- [ ] **步骤 3：Commit**

```bash
git add cube_api/static/admin/css/admin-ux.css
git commit -m "feat(admin): 添加加载遮罩样式"
```

---

### 任务 4：Admin UX JS（无刷新 + 加载遮罩）

**文件：**
- 新建：`cube_api/static/admin/js/admin-ux.js`

- [ ] **步骤 1：编写 JS 逻辑**

```javascript
/**
 * Admin UX 优化脚本
 *
 * 功能：
 * 1. 页面加载遮罩（防止白屏闪烁）
 * 2. 列表页无刷新：筛选器、分页、排序
 * 3. URL 同步（pushState）
 */

(function () {
    'use strict';

    // ========== 工具函数 ==========

    function showOverlay() {
        var overlay = document.getElementById('admin-ux-overlay');
        if (overlay) overlay.classList.add('active');
    }

    function hideOverlay() {
        var overlay = document.getElementById('admin-ux-overlay');
        if (overlay) overlay.classList.remove('active');
    }

    // 判断是否在列表页（有 changelist 类）
    function isChangeList() {
        return document.body.classList.contains('change-list');
    }

    // 从 HTML 字符串中提取内容区
    function extractContent(html) {
        var parser = new DOMParser();
        var doc = parser.parseFromString(html, 'text/html');
        var content = doc.querySelector('#changelist-form');
        var pagination = doc.querySelector('.paginator');
        var resultCount = doc.querySelector('.results');
        return {
            changelistForm: content ? content.innerHTML : null,
            doc: doc
        };
    }

    // ========== 无刷新加载 ==========

    function loadPage(url, pushState) {
        showOverlay();

        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(function (response) {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.text();
            })
            .then(function (html) {
                var result = extractContent(html);
                if (!result.changelistForm) {
                    // 解析失败，回退到整页刷新
                    window.location.href = url;
                    return;
                }

                // 替换内容区
                var target = document.querySelector('#changelist-form');
                if (target) {
                    target.innerHTML = result.changelistForm;
                }

                // 更新页面标题
                if (result.doc.title) {
                    document.title = result.doc.title;
                }

                // 更新 URL
                if (pushState) {
                    history.pushState({ path: url }, '', url);
                }

                // 重新绑定事件
                bindEvents();

                hideOverlay();
            })
            .catch(function () {
                // 失败时回退到整页刷新
                window.location.href = url;
            });
    }

    // ========== 事件绑定 ==========

    function bindEvents() {
        if (!isChangeList()) return;

        // 侧边栏筛选器链接（Unfold 的筛选器是 a 标签）
        var filterLinks = document.querySelectorAll('#changelist-filter a');
        filterLinks.forEach(function (link) {
            link.addEventListener('click', function (e) {
                e.preventDefault();
                var href = link.getAttribute('href');
                if (href && href !== '#') {
                    loadPage(href, true);
                }
            });
        });

        // 分页链接
        var paginationLinks = document.querySelectorAll('.pagination a, .paginator a');
        paginationLinks.forEach(function (link) {
            link.addEventListener('click', function (e) {
                e.preventDefault();
                var href = link.getAttribute('href');
                if (href && href !== '#') {
                    loadPage(href, true);
                }
            });
        });

        // 列表表头排序链接
        var sortLinks = document.querySelectorAll('thead th.sortable a');
        sortLinks.forEach(function (link) {
            link.addEventListener('click', function (e) {
                e.preventDefault();
                var href = link.getAttribute('href');
                if (href && href !== '#') {
                    loadPage(href, true);
                }
            });
        });

        // 搜索表单提交
        var searchForm = document.querySelector('#changelist-search');
        if (searchForm && !searchForm._uxBound) {
            searchForm._uxBound = true;
            searchForm.addEventListener('submit', function (e) {
                e.preventDefault();
                var formData = new FormData(searchForm);
                var params = new URLSearchParams(formData).toString();
                var action = searchForm.getAttribute('action') || window.location.pathname;
                var url = action + (params ? '?' + params : '');
                loadPage(url, true);
            });
        }
    }

    // ========== 浏览器前进/后退 ==========

    function bindPopState() {
        window.addEventListener('popstate', function (e) {
            if (e.state && e.state.path && isChangeList()) {
                loadPage(e.state.path, false);
            }
        });
    }

    // ========== 初始化 ==========

    function init() {
        // 1. 创建加载遮罩 DOM
        var overlay = document.createElement('div');
        overlay.id = 'admin-ux-overlay';
        overlay.innerHTML = '<div class="spinner"></div>';
        document.body.appendChild(overlay);

        // 2. 移除初始加载类（触发遮罩淡出）
        requestAnimationFrame(function () {
            document.body.classList.remove('admin-ux-initial');
            setTimeout(hideOverlay, 100);
        });

        // 3. 绑定无刷新事件
        bindEvents();

        // 4. 绑定前进/后退
        bindPopState();

        // 5. 整页跳转前显示遮罩（链接点击时）
        document.addEventListener('click', function (e) {
            var link = e.target.closest('a');
            if (!link) return;
            var href = link.getAttribute('href');
            if (!href || href.startsWith('#') || href.startsWith('javascript:')) return;
            // 只处理同域的 admin 页面链接
            if (href.startsWith('/admin/') || link.host === window.location.host) {
                // 排除已被无刷新绑定的链接
                if (link.closest('#changelist-filter') ||
                    link.closest('.pagination') ||
                    link.closest('.paginator') ||
                    link.closest('thead th.sortable')) {
                    return;
                }
                showOverlay();
            }
        });
    }

    // 初始加载时立即添加类，防止白屏
    if (document.readyState === 'loading') {
        document.body.classList.add('admin-ux-initial');
        document.addEventListener('DOMContentLoaded', init);
    } else {
        document.body.classList.add('admin-ux-initial');
        init();
    }
})();
```

- [ ] **步骤 2：启动服务验证**

1. 访问 admin 列表页，点击侧边栏筛选器 → 内容区更新，URL 变化，页面不刷新
2. 点击分页 → 同上
3. 点击表头排序 → 同上
4. 页面间跳转 → 有加载遮罩过渡，无白屏闪烁
5. 浏览器前进/后退 → 正确恢复状态

- [ ] **步骤 3：Commit**

```bash
git add cube_api/static/admin/js/admin-ux.js
git commit -m "feat(admin): 列表页无刷新 + 加载遮罩"
```

---

### 任务 5：Nginx Admin 静态资源缓存

**文件：**
- 修改：`nginx/conf.d/icube.conf`

- [ ] **步骤 1：添加 Admin 静态资源缓存配置**

在现有的 `location /static/` 块中，或添加一个更具体的 `location ~ ^/static/admin/` 块：

```nginx
    # Django Admin 静态资源（7天缓存）
    location ~ ^/static/admin/ {
        alias /usr/share/nginx/html/static/admin/;
        expires 7d;
        add_header Cache-Control "public, max-age=604800, immutable";
    }

    # Django collectstatic 产物通过 collected_static 命名卷共享
    location /static/ {
        alias /usr/share/nginx/html/static/;
        expires 30d;
    }
```

注意：更具体的 `location ~ ^/static/admin/` 正则匹配优先级高于前缀匹配 `/static/`，所以 Admin 的静态文件会走 7 天缓存，其他静态文件走 30 天。

- [ ] **步骤 2：验证 Nginx 配置语法**

本地无法直接验证 nginx 配置，记录验证命令：

```bash
docker compose exec nginx nginx -t
```

- [ ] **步骤 3：Commit**

```bash
git add nginx/conf.d/icube.conf
git commit -m "feat(admin): Nginx 增加 Admin 静态资源 7 天缓存"
```

---

### 任务 6：集成验证

- [ ] **步骤 1：collectstatic 收集静态文件**

```bash
cd cube_api
python manage.py collectstatic --noinput --settings=cube_api.settings.dev
```

确认 `admin/css/admin-ux.css` 和 `admin/js/admin-ux.js` 被收集到 STATIC_ROOT。

- [ ] **步骤 2：启动开发服务器完整验证**

1. 访问 `/admin/` → 侧边栏显示「主页」「用户」「计时器」
2. 进入用户列表 → 点击侧边栏筛选 → 无刷新更新
3. 点击分页 → 无刷新更新
4. 点击表头排序 → 无刷新更新
5. 搜索 → 无刷新更新
6. 页面间跳转 → 有加载遮罩过渡
7. 浏览器前进/后退 → 状态正确

- [ ] **步骤 3：更新修改日志**

按项目规则，在 `修改日志.md` 的「后端」分类下添加记录。

- [ ] **步骤 4：Commit**

```bash
git add 修改日志.md
git commit -m "docs: 更新修改日志 - Admin 体验优化"
```
