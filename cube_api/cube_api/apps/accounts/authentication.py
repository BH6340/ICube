# accounts/authentication.py
from django.core.cache import cache
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from loguru import logger

from .models import User
from .services import JWTCacheService
# from .services import ProfileCacheService


class CachedJWTAuthentication(JWTAuthentication):
    """
    自定义 JWT 认证，从 Redis 缓存中获取用户实例，减少数据库查询
    """

    def get_user(self, validated_token):
        user_id = validated_token.get('user_id')
        if not user_id:
            return None

        # 1. 定义 Redis 中的 User Cache Key
        cache_key = f"user_instance_cache_{user_id}"

        # 尝试从缓存获取用户 ID（注意：存的是 ID，不是整个对象）
        cached_user_id = cache.get(cache_key)

        if cached_user_id:
            logger.info("查询用户走的缓存（ID）")
            # 根据缓存的 ID 从数据库获取完整 User 对象
            try:
                return User.objects.get(id=cached_user_id)
            except User.DoesNotExist:
                return None

            # 缓存未命中，从数据库查询
        try:
            user = User.objects.get(id=user_id)
            logger.info("查询用户走的数据库")
            # 只存储用户 ID
            cache.set(cache_key, user.id, timeout=60*60)
            return user
        except User.DoesNotExist:
            return None

    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)

            jti = validated_token.get("jti")
            if JWTCacheService.is_blacklisted(jti):
                return None

            user = self.get_user(validated_token)
            return user, validated_token
        except Exception:
            return None