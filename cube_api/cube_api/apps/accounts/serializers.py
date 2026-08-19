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
from django.core.files.uploadedfile import InMemoryUploadedFile
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from django.core.cache import cache
from django.conf import settings
import os

from .models import User
from .services import ProfileCacheService
from cube_api.utils.image_processor import process_image


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
    # 当你需要返回的数据在数据库模型（Model）中没有直接对应的字段，或者该字段的值需要经过复杂的逻辑计算、数据库查询或权限判断才能生成时，使用 SerializerMethodField。
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
    image = serializers.SerializerMethodField(read_only=True)
    avatar = serializers.ImageField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('username', 'bio', 'image', 'avatar')

    def get_image(self, obj):
        from cube_api.utils.image_url import build_image_url
        return build_image_url(obj.image)

    def update(self, instance: User, validated_data):
        """
        更新用户资料

        流程：
            1. 处理头像上传（如果有），自动裁剪为1:1并压缩
            2. 更新其他字段
            3. 清理用户实例缓存

        Args:
            instance: 要更新的 User 对象
            validated_data: 验证后的更新数据

        Returns:
            更新后的 User 对象
        """
        image_file = validated_data.pop('avatar', None)

        if image_file:
            processed_file = process_image(
                image_file,
                max_width=512,
                max_height=512,
                quality=85,
                crop_square=True,
                convert_webp=True
            )

            new_name = f"{os.path.splitext(image_file.name)[0]}_avatar.webp"
            processed_image = InMemoryUploadedFile(
                processed_file,
                None,
                new_name,
                'image/webp',
                processed_file.tell(),
                None
            )

            saved_path = default_storage.save(f"avatars/{new_name}", processed_image)
            instance.image = saved_path

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

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
    # 已发布文章数量
    post_count = serializers.SerializerMethodField()
    # 自创公式数量
    custom_formula_count = serializers.SerializerMethodField()
    # 头像 URL（标准化处理）
    image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'username', 'bio', 'image', 'following',
            'followers_count', 'following_count', 'collection_count',
            'post_count', 'custom_formula_count'
        )

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
        return obj.followers.filter(is_active=True).count()

    @extend_schema_field(serializers.IntegerField)
    def get_following_count(self, obj) -> int:
        """
        获取关注数量

        Args:
            obj: 用户资料对象

        Returns:
            关注数量
        """
        return obj.following.filter(is_active=True).count()

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

    @extend_schema_field(serializers.IntegerField)
    def get_post_count(self, obj) -> int:
        """获取已发布文章数量"""
        return obj.posts.filter(status='published').count()

    @extend_schema_field(serializers.IntegerField)
    def get_custom_formula_count(self, obj) -> int:
        """获取自创公式数量"""
        return obj.custom_formulas.filter(is_custom=True).count()


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
    following = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('username', 'bio', 'image', 'following')

    def get_image(self, obj):
        from cube_api.utils.image_url import build_image_url
        return build_image_url(obj.image)

    @extend_schema_field(serializers.BooleanField)
    def get_following(self, obj):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return False
        return ProfileCacheService.is_following(request.user.id, obj.id)


class SendCodeSerializer(serializers.Serializer):
    """发送验证码序列化器"""
    email = serializers.EmailField()
    action = serializers.ChoiceField(choices=['register', 'login', 'reset'])


class RegisterWithCodeSerializer(serializers.Serializer):
    """验证码注册序列化器"""
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    password = serializers.CharField(write_only=True)
    username = serializers.CharField(max_length=60, required=False)


class LoginWithCodeSerializer(serializers.Serializer):
    """验证码登录序列化器"""
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)


class ResetPasswordSerializer(serializers.Serializer):
    """重置密码序列化器"""
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)
