/**
 * Admin UX 优化脚本
 *
 * 功能：
 * 1. 页面加载遮罩（防止白屏闪烁）
 * 2. 列表页无刷新：筛选器、分页、排序、搜索
 * 3. URL 同步（pushState）
 * 4. 浏览器前进/后退支持
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

    // 判断是否在列表页
    function isChangeList() {
        return document.body.classList.contains('change-list');
    }

    // ========== 无刷新加载核心 ==========

    function loadPage(url, pushState) {
        showOverlay();

        fetch(url, {
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(function (response) {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.text();
            })
            .then(function (html) {
                var parser = new DOMParser();
                var doc = parser.parseFromString(html, 'text/html');

                // 替换主内容区
                var newContent = doc.querySelector('#changelist');
                var oldContent = document.querySelector('#changelist');
                if (!newContent || !oldContent) {
                    window.location.href = url;
                    return;
                }
                oldContent.innerHTML = newContent.innerHTML;

                // 替换分页区（在 footer 中）
                var newPagination = doc.querySelector('.element-classes-pagination');
                var oldPagination = document.querySelector('.element-classes-pagination');
                if (newPagination && oldPagination) {
                    oldPagination.innerHTML = newPagination.innerHTML;
                } else {
                    // 尝试另一种选择器
                    var newPag = doc.querySelector('[class*="pagination"]');
                    var oldPag = document.querySelector('[class*="pagination"]');
                    if (newPag && oldPag && newPag.parentNode.tagName === 'FOOTER') {
                        oldPag.innerHTML = newPag.innerHTML;
                    }
                }

                // 更新页面标题
                if (doc.title) {
                    document.title = doc.title;
                }

                // 更新 URL
                if (pushState) {
                    history.pushState({ path: url }, '', url);
                }

                // 重新绑定事件
                bindEvents();

                // 滚动到顶部
                window.scrollTo({ top: 0, behavior: 'smooth' });

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

        // 1. 水平筛选器表单（oninput 自动提交的 form）
        var filterForms = document.querySelectorAll('#changelist form[oninput]');
        filterForms.forEach(function (form) {
            if (form._uxBound) return;
            form._uxBound = true;

            // 移除原生 oninput 提交
            form.removeAttribute('oninput');

            var debounceTimer = null;
            form.addEventListener('input', function (e) {
                // 忽略非表单控件的 input 事件
                if (!e.target.closest('input, select')) return;

                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(function () {
                    submitFilterForm(form);
                }, 300);
            });

            // select 的 change 事件立即触发
            form.addEventListener('change', function (e) {
                if (e.target.tagName === 'SELECT') {
                    clearTimeout(debounceTimer);
                    submitFilterForm(form);
                }
            });
        });

        // 2. 垂直筛选器（侧边栏链接）
        var filterLinks = document.querySelectorAll('#changelist-filter a, .changelist-filter a');
        filterLinks.forEach(function (link) {
            if (link._uxBound) return;
            link._uxBound = true;

            link.addEventListener('click', function (e) {
                var href = link.getAttribute('href');
                if (!href || href === '#' || href.startsWith('javascript:')) return;
                e.preventDefault();
                loadPage(href, true);
            });
        });

        // 3. 分页链接
        var paginationLinks = document.querySelectorAll('.paginator a, .pagination a');
        paginationLinks.forEach(function (link) {
            if (link._uxBound) return;
            link._uxBound = true;

            link.addEventListener('click', function (e) {
                var href = link.getAttribute('href');
                if (!href || href === '#' || href.startsWith('javascript:')) return;
                e.preventDefault();
                loadPage(href, true);
            });
        });

        // 4. 表头排序链接
        var sortLinks = document.querySelectorAll('thead th a');
        sortLinks.forEach(function (link) {
            if (link._uxBound) return;
            link._uxBound = true;

            link.addEventListener('click', function (e) {
                var href = link.getAttribute('href');
                if (!href || href === '#' || href.startsWith('javascript:')) return;
                if (href.indexOf('o=') === -1 && href.indexOf('ot=') === -1) return; // 不是排序链接
                e.preventDefault();
                loadPage(href, true);
            });
        });

        // 5. 搜索表单
        var searchForm = document.querySelector('#changelist-search');
        if (searchForm && !searchForm._uxBound) {
            searchForm._uxBound = true;
            searchForm.addEventListener('submit', function (e) {
                e.preventDefault();
                var formData = new FormData(searchForm);
                var params = new URLSearchParams(formData).toString();
                var url = window.location.pathname + (params ? '?' + params : '');
                loadPage(url, true);
            });
        }

        // 6. 日期层级导航
        var dateHierarchyLinks = document.querySelectorAll('.toplinks a, .date-hierarchy a');
        dateHierarchyLinks.forEach(function (link) {
            if (link._uxBound) return;
            link._uxBound = true;

            link.addEventListener('click', function (e) {
                var href = link.getAttribute('href');
                if (!href || href === '#' || href.startsWith('javascript:')) return;
                e.preventDefault();
                loadPage(href, true);
            });
        });
    }

    // 提交筛选器表单
    function submitFilterForm(form) {
        var formData = new FormData(form);
        var params = new URLSearchParams(formData).toString();
        // 移除空参数，保持 URL 整洁
        var cleanParams = [];
        params.split('&').forEach(function (pair) {
            var parts = pair.split('=');
            if (parts[1] && parts[1] !== '') {
                cleanParams.push(pair);
            }
        });
        var url = window.location.pathname + (cleanParams.length ? '?' + cleanParams.join('&') : '');
        loadPage(url, true);
    }

    // ========== 浏览器前进/后退 ==========

    function bindPopState() {
        window.addEventListener('popstate', function (e) {
            if (e.state && e.state.path && isChangeList()) {
                loadPage(e.state.path, false);
            } else if (isChangeList()) {
                // 没有 state 时（比如首次进入后后退再前进），用当前 URL
                loadPage(window.location.href, false);
            }
        });
    }

    // ========== 页面跳转遮罩 ==========

    function bindLinkClicks() {
        document.addEventListener('click', function (e) {
            var link = e.target.closest('a');
            if (!link) return;

            var href = link.getAttribute('href');
            if (!href) return;

            // 忽略特殊链接
            if (href.startsWith('#') ||
                href.startsWith('javascript:') ||
                href.startsWith('mailto:') ||
                link.target === '_blank') {
                return;
            }

            // 只处理同域 admin 页面
            var isSameDomain = link.host === window.location.host || href.startsWith('/admin/');
            if (!isSameDomain) return;

            // 排除已被无刷新绑定的链接
            if (link._uxBound) return;
            if (link.closest('#changelist-filter') ||
                link.closest('.paginator') ||
                link.closest('.pagination') ||
                link.closest('thead th')) {
                return;
            }

            // 排除下载链接
            if (link.getAttribute('download')) return;

            showOverlay();
        });
    }

    // ========== 初始化 ==========

    function init() {
        // 1. 创建加载遮罩 DOM
        var overlay = document.createElement('div');
        overlay.id = 'admin-ux-overlay';
        overlay.innerHTML = '<div class="spinner"></div>';
        document.body.appendChild(overlay);

        // 2. 移除初始加载类，触发遮罩淡出
        requestAnimationFrame(function () {
            document.body.classList.remove('admin-ux-initial');
            setTimeout(hideOverlay, 150);
        });

        // 3. 绑定无刷新事件
        bindEvents();

        // 4. 绑定前进/后退
        bindPopState();

        // 5. 绑定页面跳转遮罩
        bindLinkClicks();
    }

    // 页面加载过程中立即添加初始类，防止白屏
    if (document.readyState === 'loading') {
        document.body.classList.add('admin-ux-initial');
        document.addEventListener('DOMContentLoaded', init);
    } else {
        document.body.classList.add('admin-ux-initial');
        init();
    }

    // 页面卸载前显示遮罩（浏览器前进/后退缓存时）
    window.addEventListener('pageshow', function () {
        hideOverlay();
    });
})();
