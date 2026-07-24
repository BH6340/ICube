# -*- coding: utf-8 -*-
"""
首页导航模块路由配置

定义导航菜单的 API 路由：
    - 导航菜单：/api/home/navigation/menus/

设计特点：
    - **标准视图集路由**：使用 DefaultRouter 自动生成 CRUD 路由
    - **basename 设置**：显式指定 basename='nav-menus'，避免模型无主键的路由冲突
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.home.views import NavigationMenuViewSet, BannerViewSet

router = DefaultRouter()
router.register(r'navigation/menus', NavigationMenuViewSet, basename='nav-menus')
router.register(r'banners', BannerViewSet, basename='banners')

urlpatterns = [
    path('', include(router.urls)),
]