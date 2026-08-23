# -*- coding: utf-8 -*-
"""
首页导航模块视图集

提供导航菜单的只读查询接口，用于前端动态渲染导航栏。

设计特点：
    - **公开访问**：使用 AllowAny 权限，无需登录即可获取菜单配置
    - **统一响应**：使用项目统一的 APIResponse 封装返回格式
    - **只读操作**：导航菜单由管理员在后台管理，前端仅需查询
"""

import os
import json

from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from .models import NavigationMenu, Banner
from .serializers import NavigationMenuSerializer, BannerSerializer
from utils.common_response import APIResponse


class NavigationMenuViewSet(viewsets.ReadOnlyModelViewSet):
    """
    导航菜单视图集

    提供导航菜单的列表查询接口，支持前端动态渲染导航栏。

    设计要点：
        - **权限控制**：AllowAny 允许所有用户访问
        - **无分页**：菜单数据量较小，直接返回全部
        - **排序规则**：按 sort_order 字段排序（模型层定义）
    """
    queryset = NavigationMenu.objects.all()
    serializer_class = NavigationMenuSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        """获取导航菜单列表"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(code=100, msg="获取成功", data=serializer.data)


class BannerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    轮播图视图集

    提供轮播图的列表查询接口，支持前端动态渲染首页轮播图。

    设计要点：
        - **权限控制**：AllowAny 允许所有用户访问
        - **筛选条件**：只返回 is_active=True 的轮播图
        - **排序规则**：按 sort_order 字段排序（模型层定义）
        - **无分页**：轮播图数据量较小，直接返回全部
    """
    queryset = Banner.objects.filter(is_active=True)
    serializer_class = BannerSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        """获取轮播图列表"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return APIResponse(code=100, msg="获取成功", data=serializer.data)


class AppVersionView(APIView):
    """APP 版本检查接口，返回最新版本号、下载地址和更新说明"""
    permission_classes = [AllowAny]

    def get(self, request):
        version_file = os.path.join(os.path.dirname(__file__), 'app_version.json')
        with open(version_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        download_url = data.get('download_url', '')
        if download_url and not download_url.startswith('http'):
            host = request.META.get('HTTP_HOST', '')
            if host:
                data['download_url'] = f"http://{host}{download_url}"
        return APIResponse(code=100, msg="获取成功", data=data)