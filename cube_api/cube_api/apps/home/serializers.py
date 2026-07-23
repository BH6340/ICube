# -*- coding: utf-8 -*-
"""
首页导航模块序列化器

定义导航菜单的数据序列化逻辑，返回前端需要的菜单字段。

设计特点：
    - **精简字段**：只返回前端需要的字段（index、label、path、category、match_paths）
    - **无需验证**：只读操作，不涉及数据写入验证
"""

from rest_framework import serializers
from .models import NavigationMenu


class NavigationMenuSerializer(serializers.ModelSerializer):
    """
    导航菜单序列化器

    序列化导航菜单数据，返回前端渲染导航栏所需的字段。

    设计要点：
        - **精简字段**：排除 id、sort_order 等后端内部字段
        - **match_paths**：保留路由匹配路径集，用于前端路由高亮
    """
    class Meta:
        model = NavigationMenu
        fields = ('index', 'label', 'path', 'category', 'match_paths')