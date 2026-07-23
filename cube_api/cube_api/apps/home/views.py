# -*- coding: utf-8 -*-
"""
首页导航模块视图集

提供导航菜单的只读查询接口，用于前端动态渲染导航栏。

设计特点：
    - **公开访问**：使用 AllowAny 权限，无需登录即可获取菜单配置
    - **统一响应**：使用项目统一的 APIResponse 封装返回格式
    - **只读操作**：导航菜单由管理员在后台管理，前端仅需查询
"""

from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import NavigationMenu
from .serializers import NavigationMenuSerializer
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