# -*- coding: utf-8 -*-
"""
自定义 JWT 认证模块

该模块扩展了 DRF SimpleJWT 的认证类，添加了 Redis 缓存和黑名单机制。

核心功能：
    1. 用户实例缓存：将用户 ID 缓存在 Redis 中，减少数据库查询
    2. Token 黑名单：支持通过 Redis 黑名单使 Token 提前失效（用于退出登录）
    3. 兼容 IsAuthenticatedOrReadOnly：认证失败时返回 None 而非抛出异常

设计原因：
    - CachedJWTAuthentication 的 authenticate 方法在 Token 验证失败时应返回 None
      而非抛出 AuthenticationFailed 异常，以兼容 IsAuthenticatedOrReadOnly 权限
    - 通过缓存用户实例，避免每次请求都查询数据库
    - 通过黑名单机制，实现安全的退出登录功能
"""
from django.core.cache import cache
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from loguru import logger

from .models import User
from .services import JWTCacheService


class CachedJWTAuthentication(JWTAuthentication):
    """
    自定义 JWT 认证类

    继承自 SimpleJWT 的 JWTAuthentication，主要改进：
        1. 添加用户实例缓存，减少数据库查询
        2. 添加 Token 黑名单检查
        3. 认证失败时返回 None，兼容只读接口

    使用方式：
        在 settings.py 中配置：
        REST_FRAMEWORK = {
            'DEFAULT_AUTHENTICATION_CLASSES': [
                'apps.accounts.authentication.CachedJWTAuthentication',
            ],
        }
    """

    def get_user(self, validated_token):
        """
        从缓存或数据库获取用户实例

        缓存策略：
            1. 优先从 Redis 缓存获取用户 ID
            2. 根据缓存的 ID 从数据库获取完整用户对象
            3. 缓存未命中时从数据库查询，并将 ID 存入缓存

        注意：缓存中只存储用户 ID，而非完整用户对象。
        原因：用户对象可能包含敏感信息，且序列化开销较大；
              只存 ID 可以减少缓存大小，同时保证数据一致性。

        Args:
            validated_token: 已验证的 JWT Token 字典

        Returns:
            User 对象或 None
        """
        user_id = validated_token.get('user_id')
        if not user_id:
            return None

        # 定义 Redis 中的用户缓存键
        cache_key = f"user_instance_cache_{user_id}"

        # 尝试从缓存获取用户 ID
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
            # 只存储用户 ID，不存储完整对象
            # 缓存有效期：1小时（3600秒）
            cache.set(cache_key, user.id, timeout=60*60)
            return user
        except User.DoesNotExist:
            return None

    def authenticate(self, request):
        """
        认证入口方法

        流程：
            1. 提取 Token（从 Authorization 头）
            2. 验证 Token 有效性
            3. 检查 Token 是否在黑名单中
            4. 获取用户实例
            5. 返回 (user, token) 元组或 None

        设计要点：
            - Token 无效或已被拉黑时，返回 None 而非抛出异常
            - 这样可以兼容 IsAuthenticatedOrReadOnly 权限类
            - 未认证用户可以访问只读接口，认证用户可以访问所有接口

        Args:
            request: HTTP 请求对象

        Returns:
            (User, validated_token) 元组或 None
        """
        # 从请求头中提取 Authorization 头
        header = self.get_header(request)
        if header is None:
            return None

        # 从 Authorization 头中提取原始 Token
        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        try:
            # 验证 Token 并解析载荷
            validated_token = self.get_validated_token(raw_token)

            # 检查 Token 是否在黑名单中（用于退出登录）
            jti = validated_token.get("jti")
            if JWTCacheService.is_blacklisted(jti):
                return None

            # 获取用户实例
            user = self.get_user(validated_token)

            # 返回认证结果：(user, validated_token) 元组
            return user, validated_token
        except Exception:
            # 任何异常都返回 None，兼容只读接口
            # 异常包括：Token 过期、签名无效、用户不存在等
            return None