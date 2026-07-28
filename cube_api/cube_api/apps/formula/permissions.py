# -*- coding: utf-8 -*-
"""
公式库权限模块

该模块定义了公式库相关的自定义权限类，用于控制用户对公式数据的访问权限。

主要权限类：
    - IsAdminOrReadOnly: 管理员可写，其他用户只读
    - IsOwnerOrReadOnly: 对象所有者可写，其他用户只读
    - IsAdminOrCustomCreator: 管理员或自定义公式创建者可写

设计特点：
    - 遵循 DRF 权限类规范
    - 支持 SAFE_METHODS（GET/HEAD/OPTIONS）只读放行
    - 区分管理员权限和普通用户权限
"""
from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    管理员或只读权限

    允许所有用户读取数据（GET/HEAD/OPTIONS），只有管理员可以修改数据。

    使用场景：
        - 魔方分类、魔方状态等基础数据的管理
        - 普通用户只能查看，管理员可以增删改

    权限逻辑：
        - SAFE_METHODS：直接放行
        - 其他方法：检查用户是否为管理员（is_staff）
    """

    def has_permission(self, request, view):
        """
        检查视图级权限

        Args:
            request: HTTP 请求对象
            view: 视图实例

        Returns:
            bool: 是否有权限
        """
        # 只读方法直接放行
        if request.method in permissions.SAFE_METHODS:
            return True

        # 写操作需要管理员权限
        return request.user and request.user.is_staff


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    对象所有者或只读权限

    允许对象所有者修改自己的数据，其他用户只能读取。

    使用场景：
        - 用户自定义公式的编辑权限控制

    权限逻辑：
        - SAFE_METHODS：直接放行
        - 写操作：
            1. 如果对象有 created_by 属性且是当前用户，放行
            2. 如果用户是管理员，放行
    """

    def has_object_permission(self, request, view, obj):
        """
        检查对象级权限

        Args:
            request: HTTP 请求对象
            view: 视图实例
            obj: 目标对象

        Returns:
            bool: 是否有权限
        """
        # 只读方法直接放行
        if request.method in permissions.SAFE_METHODS:
            return True

        # 检查是否为对象的创建者
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True

        # 管理员也可以操作
        return request.user and request.user.is_staff


class IsAdminOrCustomCreator(permissions.BasePermission):
    """
    管理员或自定义公式创建者权限

    管理员可以操作所有公式，普通用户只能操作自己创建的自定义公式。

    使用场景：
        - 公式的创建、编辑、删除权限控制

    权限逻辑：
        - SAFE_METHODS：直接放行
        - 写操作（has_permission）：需要登录
        - 对象操作（has_object_permission）：
            1. SAFE_METHODS：直接放行
            2. 如果是自定义公式且是创建者，放行
            3. 如果用户是管理员，放行
    """

    def has_permission(self, request, view):
        """
        检查视图级权限

        Args:
            request: HTTP 请求对象
            view: 视图实例

        Returns:
            bool: 是否有权限
        """
        # 只读方法直接放行
        if request.method in permissions.SAFE_METHODS:
            return True

        # 写操作需要登录
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        检查对象级权限

        Args:
            request: HTTP 请求对象
            view: 视图实例
            obj: 目标公式对象

        Returns:
            bool: 是否有权限
        """
        # 只读方法直接放行
        if request.method in permissions.SAFE_METHODS:
            return True

        # 自定义公式且是创建者本人
        if obj.is_custom and obj.created_by == request.user:
            return True

        # 管理员可以操作所有公式
        return request.user and request.user.is_staff