# -*- coding: utf-8 -*-
"""
自定义权限类

该模块定义了项目中使用的自定义权限类，用于控制对 API 资源的访问权限。

核心权限类：
    - IsOwnerOrReadOnly: 只有对象所有者可以修改，其他人只读
    - IsAdminOrReadOnly: 只有管理员可以修改，其他人只读
    - IsAuthenticatedAndOwner: 用户必须登录且是对象所有者
    - IsSelfOrReadOnly: 用户只能操作自己的资料
    - IsFollowingOrReadOnly: 只有关注者才能查看某些内容

设计原则：
    - 遵循 DRF 的权限类接口（has_permission 和 has_object_permission）
    - 读操作（GET, HEAD, OPTIONS）通常允许所有用户
    - 写操作（POST, PUT, DELETE）需要特定权限
"""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    所有者权限：只有对象的所有者才能编辑/删除，其他用户只有只读权限

    支持的所有者字段：author, user, owner, creator
    如果找不到所有者字段，只有管理员可以修改。
    """

    def has_object_permission(self, request, view, obj):
        """
        判断对象级别的权限

        Args:
            request: HTTP 请求对象
            view: 视图对象
            obj: 要访问的对象

        Returns:
            True：有权限
            False：无权限
        """
        # 读权限：任何请求都允许（GET, HEAD, OPTIONS）
        if request.method in permissions.SAFE_METHODS:
            return True

        # 写权限：只有对象的所有者才允许
        # 适配不同的模型，支持多种所有者字段名
        if hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        else:
            # 如果没有明确的所有者字段，尝试常见的字段名
            for field_name in ['author', 'user', 'creator', 'owner']:
                if hasattr(obj, field_name):
                    return getattr(obj, field_name) == request.user

        # 如果找不到所有者字段，只有管理员可以修改
        return request.user.is_staff


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    管理员权限：只有管理员可以修改，其他人只能读取

    适用于全局配置、系统设置等需要管理员权限的资源。
    """

    def has_permission(self, request, view):
        """
        判断视图级别的权限

        Args:
            request: HTTP 请求对象
            view: 视图对象

        Returns:
            True：有权限
            False：无权限
        """
        # 读权限：任何请求都允许
        if request.method in permissions.SAFE_METHODS:
            return True
        # 写权限：只有管理员可以修改
        return request.user and request.user.is_staff


class IsAuthenticatedAndOwner(permissions.BasePermission):
    """
    认证且所有者权限：用户必须登录且是对象的所有者

    适用于需要登录且只能操作自己资源的场景。
    """

    def has_permission(self, request, view):
        """
        判断视图级别的权限（用户必须登录）

        Args:
            request: HTTP 请求对象
            view: 视图对象

        Returns:
            True：有权限
            False：无权限
        """
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        判断对象级别的权限（必须是对象所有者）

        Args:
            request: HTTP 请求对象
            view: 视图对象
            obj: 要访问的对象

        Returns:
            True：有权限
            False：无权限
        """
        # 检查是否是所有者
        if hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsSelfOrReadOnly(permissions.BasePermission):
    """
    自身权限：用户只能操作自己的资料

    适用于用户资料管理，确保用户只能修改自己的资料。
    """

    def has_object_permission(self, request, view, obj):
        """
        判断对象级别的权限

        Args:
            request: HTTP 请求对象
            view: 视图对象
            obj: 要访问的对象（用户对象）

        Returns:
            True：有权限
            False：无权限
        """
        # 读取权限：允许任何请求
        if request.method in permissions.SAFE_METHODS:
            return True

        # 写权限：只有操作自己的资料才允许
        return obj == request.user


class IsFollowingOrReadOnly(permissions.BasePermission):
    """
    关注者权限：只有关注者才能查看某些内容

    适用于需要关注才能查看的内容，如私密帖子、粉丝专属内容等。
    """

    def has_object_permission(self, request, view, obj):
        """
        判断对象级别的权限

        Args:
            request: HTTP 请求对象
            view: 视图对象
            obj: 要访问的对象

        Returns:
            True：有权限
            False：无权限
        """
        if request.method in permissions.SAFE_METHODS:
            # 对于读取操作，检查当前用户是否关注了作者
            if hasattr(obj, 'author'):
                return request.user.is_authenticated and request.user.following.filter(id=obj.author.id).exists()
            return False
        # 写操作：需要登录
        return request.user.is_authenticated