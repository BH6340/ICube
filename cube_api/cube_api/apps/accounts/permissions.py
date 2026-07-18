from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    自定义权限：只有对象的所有者才能编辑/删除
    其他用户只有只读权限
    """

    def has_object_permission(self, request, view, obj):
        # 读权限：任何请求都允许（GET, HEAD, OPTIONS）
        if request.method in permissions.SAFE_METHODS:
            return True

        # 写权限：只有对象的所有者才允许
        # 假设对象有一个 'author' 或 'user' 属性
        # 适配不同的模型
        if hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        else:
            # 如果没有明确的作者字段，尝试获取用户外键
            # 常见的外键字段名
            for field_name in ['author', 'user', 'creator', 'owner']:
                if hasattr(obj, field_name):
                    return getattr(obj, field_name) == request.user

        # 如果找不到作者字段，只有管理员可以修改
        return request.user.is_staff


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    只有管理员可以修改，其他人只能读取
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsAuthenticatedAndOwner(permissions.BasePermission):
    """
    用户必须登录且是对象的所有者
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # 检查是否是所有者
        if hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsSelfOrReadOnly(permissions.BasePermission):
    """
    用户只能操作自己的资料
    """

    def has_object_permission(self, request, view, obj):
        # 读取权限允许任何请求
        if request.method in permissions.SAFE_METHODS:
            return True

        # 检查是否是操作自己
        return obj == request.user


class IsFollowingOrReadOnly(permissions.BasePermission):
    """
    只有关注者才能查看某些内容
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            # 对于读取操作，检查是否互相关注
            if hasattr(obj, 'author'):
                # 检查当前用户是否关注了作者
                return request.user.is_authenticated and request.user.following.filter(id=obj.author.id).exists()
            return False
        return request.user.is_authenticated