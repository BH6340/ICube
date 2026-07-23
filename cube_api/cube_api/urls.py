# -*- coding: utf-8 -*-
"""
项目路由入口文件

该文件定义了项目的顶层 URL 路由，将请求分发到各个应用模块。

路由结构：
    - /admin/                 Django 后台管理系统
    - /api/schema/            OpenAPI Schema 文件（YAML 格式）
    - /api/schema/swagger-ui/ Swagger UI 交互式文档
    - /api/schema/redoc/      Redoc 文档界面
    - /api/home/              首页导航模块
    - /api/                   用户认证模块（包含登录、注册、用户信息等）
    - /api/forum/             论坛模块（帖子、评论、标签等）
    - /api/formula/           公式库模块（公式浏览、搜索、收藏等）
    - /api/shop/              商城模块（商品、购物车、订单、支付等）
    - /api/timer/             计时器模块（计时记录、统计等）

设计特点：
    - 使用统一的 /api/ 前缀区分 API 接口和其他路由
    - 引入 drf-spectacular 提供自动生成的 API 文档
    - 开发环境下自动挂载媒体文件服务
"""
from django.contrib import admin
from django.urls import path, include
# drf-spectacular 视图：用于生成 OpenAPI 文档
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# 引入 Django 的静态/媒体文件挂载工具
# 用于在开发环境中让 Django 提供媒体文件服务
from django.conf import settings
from django.conf.urls.static import static


# API 前缀定义（当前未使用，保留作为配置参考）
api_prefix = 'api'

# 顶层 URL 路由配置
urlpatterns = [
    # Django 后台管理系统
    path('admin/', admin.site.urls),

    # ==================== API 文档路由 ====================

    # 1. YAML 格式的原始 OpenAPI Schema 文件
    # 访问地址：/api/schema/
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # 2. Swagger UI 交互式文档界面
    # 访问地址：/api/schema/swagger-ui/
    # 提供可视化的 API 文档，支持在线测试接口
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # 3. Redoc 文档界面（另一种风格）
    # 访问地址：/api/schema/redoc/
    # 提供更简洁的 API 文档展示
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # ==================== 业务模块路由 ====================

    # 首页导航模块
    # 包含导航菜单的增删改查接口
    path('api/home/', include('apps.home.urls')),

    # 用户认证模块（包含在根 API 路径下）
    # 包含登录、注册、用户信息、关注等接口
    path('api/', include('apps.accounts.urls')),

    # 论坛模块
    # 包含帖子、评论、标签、举报等接口
    path('api/forum/', include('apps.forum.urls')),

    # 公式库模块
    # 包含公式浏览、搜索、收藏、分类等接口
    path('api/formula/', include('apps.formula.urls')),

    # 商城模块
    # 包含商品、购物车、订单、支付等接口
    path('api/shop/', include('apps.shop.urls')),

    # 计时器模块
    # 包含计时记录、统计、趋势等接口
    path('api/timer/', include('apps.timer.urls')),
]

# 开发环境媒体文件服务
# 只有在 DEBUG = True（开发环境）时，让 Django 充当文件服务器来映射媒体文件
# 生产环境中，媒体文件应由 Nginx 或其他 Web 服务器提供服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)