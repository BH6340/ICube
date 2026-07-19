from django.core.files.storage import default_storage
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from django.core.cache import cache
from django.conf import settings

from .models import User
from .services import ProfileCacheService


class UserSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'bio', 'image')
        extra_kwargs = {'password': {'write_only': True}}

    def get_image(self, obj):
        from cube_api.utils.image_url import build_image_url
        return build_image_url(obj.image)

    def create(self, validated_data):
        # 使用 Manager 中定义的 create_user 确保逻辑统一
        return User.objects.create_user(**validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    专门用于用户资料更新的序列化器，严格限制可修改字段
    """
    # 这样 DRF 就能无缝剥离前端 FormData 里的文件，并根据 settings.py 自动将其保存到 media 文件夹！
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        # 💡 核心：这里只填写允许前端修改的字段
        fields = ('username', 'bio', 'image')

    def update(self, instance: User, validated_data):
        image_file = validated_data.pop('image', None)
        if image_file:
            saved_path = default_storage.save(f"avatars/{image_file.name}", image_file)
            instance.image = f"{settings.MEDIA_URL}{saved_path}"
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        # 2. 💡 保持你原有的 Redis 缓存清理逻辑
        cache_key = f"user_instance_cache_{instance.id}"
        cache.delete(cache_key)

        return instance


class ProfileSerializer(serializers.ModelSerializer):
    following = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    collection_count = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('username', 'bio', 'image', 'following', 'followers_count', 'following_count', 'collection_count')

    def get_image(self, obj):
        from cube_api.utils.image_url import build_image_url
        return build_image_url(obj.image)

    @extend_schema_field(serializers.BooleanField)
    def get_following(self, obj):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return False

        # 💡 一行代码，清晰直观
        return ProfileCacheService.is_following(request.user.id, obj.id)

    @extend_schema_field(serializers.IntegerField)
    def get_followers_count(self, obj) -> int:
        # 💡 一行代码，干净利落
        return ProfileCacheService.get_followers_count(obj.id)

    @extend_schema_field(serializers.IntegerField)
    def get_following_count(self, obj) -> int:
        # 💡 一行代码，逻辑内聚
        return ProfileCacheService.get_following_count(obj.id)

    @extend_schema_field(serializers.IntegerField)
    def get_collection_count(self, obj) -> int:
        return ProfileCacheService.get_collection_count(obj.id)


class ProfileListSerializer(serializers.ModelSerializer):
    """
    专门用于关注/粉丝列表展示的轻量级序列化器（去除了计数相关字段）
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
