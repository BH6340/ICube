# -*- coding: utf-8 -*-
"""
用户认证模块序列化器

该模块定义了用户相关的序列化器，负责数据的序列化和反序列化。

核心序列化器：
    - UserSerializer：用户创建和基本信息序列化
    - UserUpdateSerializer：用户资料更新专用序列化器
    - ProfileSerializer：用户资料详情序列化（含关注状态和统计）
    - ProfileListSerializer：关注/粉丝列表专用序列化器（轻量级）

设计原则：
    - 严格限制可修改字段，防止越权修改
    - 使用 SerializerMethodField 处理动态字段（关注状态、统计数据）
    - 使用 build_image_url 统一处理图片 URL
"""
from django.core.files.storage import default_storage
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from django.core.cache import cache
from django.conf import settings

from .models import User
from .services import ProfileCacheService


class UserSerializer(serializers.ModelSerializer):
    """
    用户基本信息序列化器

    用于用户创建、登录返回等场景。

    字段说明：
        - username: 用户名
        - email: 邮箱（登录凭证）
        - password: 密码（仅写入，不返回）
        - bio: 个人简介
        - image: 头像 URL（通过 SerializerMethodField 处理）
    """
    # 头像 URL：通过 SerializerMethodField 动态生成
    image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'bio', 'image')
        # 密码仅用于写入，不返回给前端
        extra_kwargs = {'password': {'write_only': True}}

    def get_image(self, obj):
        """
        处理头像 URL，添加 /media/ 前缀

        Args:
            obj: User 对象

        Returns:
            标准化的头像 URL
        """
        from cube_api.utils.image_url import build_image_url
        return build_image_url(obj.image)

    def create(self, validated_data):
        """
        创建用户

        使用 UserManager 中的 create_user 方法，确保密码正确加密。

        Args:
            validated_data: 验证后的用户数据

        Returns:
            创建的 User 对象
        """
        return User.objects.create_user(**validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    用户资料更新专用序列化器

    严格限制可修改字段，防止越权修改。
    支持文件上传（头像）。

    允许修改的字段：
        - username: 用户名
        - bio: 个人简介
        - image: 头像（文件上传）
    """
    # 头像字段：支持文件上传，非必需，允许为空
    # DRF 会自动处理前端 FormData 中的文件，并保存到 media 文件夹
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        # 核心：只填写允许前端修改的字段
        fields = ('username', 'bio', 'image')

    def update(self, instance: User, validated_data):
        """
        更新用户资料

        流程：
            1. 处理头像上传（如果有）
            2. 更新其他字段
            3. 清理用户实例缓存

        Args:
            instance: 要更新的 User 对象
            validated_data: 验证后的更新数据

        Returns:
            更新后的 User 对象
        """
        # 提取头像文件（如果有）
        image_file = validated_data.pop('image', None)
        if image_file:
            # 保存头像到 media/avatars/ 目录
            saved_path = default_storage.save(f"avatars/{image_file.name}", image_file)
            # 更新用户的头像路径（只存储相对路径，与 Django ImageField 默认行为一致）
            instance.image = saved_path

        # 更新其他字段
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        # 清理用户实例缓存，下次请求会从数据库重新加载
        cache_key = f"user_instance_cache_{instance.id}"
        cache.delete(cache_key)

        return instance


class ProfileSerializer(serializers.ModelSerializer):
    """
    用户资料详情序列化器

    用于用户资料详情页，包含关注状态和统计数据。

    动态字段说明：
        - following: 当前登录用户是否关注了该用户
        - followers_count: 粉丝数量
        - following_count: 关注数量
        - collection_count: 公式收藏数量
        - image: 头像 URL（标准化处理）
    """
    # 当前登录用户是否关注了该用户
    following = serializers.SerializerMethodField()
    # 粉丝数量
    followers_count = serializers.SerializerMethodField()
    # 关注数量
    following_count = serializers.SerializerMethodField()
    # 公式收藏数量
    collection_count = serializers.SerializerMethodField()
    # 头像 URL（标准化处理）
    image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('username', 'bio', 'image', 'following', 'followers_count', 'following_count', 'collection_count')

    def get_image(self, obj):
        """
        处理头像 URL，添加 /media/ 前缀

        Args:
            obj: User 对象

        Returns:
            标准化的头像 URL
        """
        from cube_api.utils.image_url import build_image_url
        return build_image_url(obj.image)

    @extend_schema_field(serializers.BooleanField)
    def get_following(self, obj):
        """
        判断当前登录用户是否关注了该用户

        Args:
            obj: 用户资料对象

        Returns:
            True：已关注
            False：未关注或未登录
        """
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return False

        # 通过 ProfileCacheService 判断关注状态（使用 Redis 缓存）
        return ProfileCacheService.is_following(request.user.id, obj.id)

    @extend_schema_field(serializers.IntegerField)
    def get_followers_count(self, obj) -> int:
        """
        获取粉丝数量

        Args:
            obj: 用户资料对象

        Returns:
            粉丝数量
        """
        return ProfileCacheService.get_followers_count(obj.id)

    @extend_schema_field(serializers.IntegerField)
    def get_following_count(self, obj) -> int:
        """
        获取关注数量

        Args:
            obj: 用户资料对象

        Returns:
            关注数量
        """
        return ProfileCacheService.get_following_count(obj.id)

    @extend_schema_field(serializers.IntegerField)
    def get_collection_count(self, obj) -> int:
        """
        获取公式收藏数量

        Args:
            obj: 用户资料对象

        Returns:
            公式收藏数量
        """
        return ProfileCacheService.get_collection_count(obj.id)


class ProfileListSerializer(serializers.ModelSerializer):
    """
    关注/粉丝列表专用序列化器（轻量级）

    用于关注列表和粉丝列表，去除了计数相关字段，减少数据传输量。

    字段说明：
        - username: 用户名
        - bio: 个人简介
        - image: 头像 URL
        - following: 当前登录用户是否关注了该用户
    """
    # 当前登录用户是否关注了该用户
    following = serializers.SerializerMethodField()
    # 头像 URL（标准化处理）
    image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('username', 'bio', 'image', 'following')

    def get_image(self, obj):
        """
        处理头像 URL，添加 /media/ 前缀

        Args:
            obj: User 对象

        Returns:
            标准化的头像 URL
        """
        from cube_api.utils.image_url import build_image_url
        return build_image_url(obj.image)

    @extend_schema_field(serializers.BooleanField)
    def get_following(self, obj):
        """
        判断当前登录用户是否关注了该用户

        Args:
            obj: 用户资料对象

        Returns:
            True：已关注
            False：未关注或未登录
        """
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return False

        return ProfileCacheService.is_following(request.user.id, obj.id)
