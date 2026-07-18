# forum/permissions.py
from rest_framework import permissions


class IsPostOwnerOrReadOnly(permissions.BasePermission):
    """帖子所有者才能编辑/删除"""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class IsCommentOwnerOrReadOnly(permissions.BasePermission):
    """评论所有者才能删除"""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class CanModeratePost(permissions.BasePermission):
    """管理员或版主可以管理帖子"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
                request.user.is_staff or getattr(request.user, 'is_moderator', False)
        )

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and (
                request.user.is_staff or
                getattr(request.user, 'is_moderator', False) or
                obj.author == request.user
        )