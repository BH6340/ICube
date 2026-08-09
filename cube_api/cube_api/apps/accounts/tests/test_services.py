# -*- coding: utf-8 -*-
"""
Accounts 模块服务层测试

测试 accounts 服务层的核心功能，包括：
    - JWT Token 生成与验证
    - Token 黑名单管理
    - 缓存服务
"""
import time
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from loguru import logger
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.authentication import CachedJWTAuthentication
from apps.accounts.services import JWTCacheService, ProfileCacheService

User = get_user_model()


class AuthenticationLoggingTest(SimpleTestCase):
    """Redis 与 JWT 认证日志测试"""

    def setUp(self):
        self.records = []
        self.sink_id = logger.add(
            lambda message: self.records.append(message.record),
            level="DEBUG",
        )

    def tearDown(self):
        logger.remove(self.sink_id)

    def _messages(self, level):
        return "\n".join(
            record["message"]
            for record in self.records
            if record["level"].name == level
        )

    @patch(
        'django_redis.get_redis_connection',
        side_effect=ConnectionError('redis://:redis-password@localhost'),
    )
    def test_redis_connection_failure_logs_sanitized_error(self, _mock_connection):
        with self.assertRaises(ConnectionError) as raised:
            JWTCacheService._get_con()

        messages = self._messages("ERROR")
        self.assertIn("获取 Redis 连接失败", messages)
        self.assertIn("ConnectionError", messages)
        self.assertNotIn("redis-password", messages)
        self.assertNotIn("redis-password", str(raised.exception))

    def test_blacklist_query_failure_logs_sanitized_error(self):
        connection = Mock()
        connection.exists.side_effect = TimeoutError('redis-password')

        with patch.object(JWTCacheService, '_get_con', return_value=connection):
            with self.assertRaises(TimeoutError) as raised:
                JWTCacheService.is_blacklisted('sensitive-jti')

        messages = self._messages("ERROR")
        self.assertIn("查询 JWT 黑名单失败", messages)
        self.assertIn("TimeoutError", messages)
        self.assertNotIn("sensitive-jti", messages)
        self.assertNotIn("redis-password", messages)
        self.assertNotIn("redis-password", str(raised.exception))

    def test_blacklist_write_failure_logs_sanitized_error(self):
        connection = Mock()
        connection.setex.side_effect = ConnectionError('redis-password')
        payload = {
            'jti': 'sensitive-jti',
            'exp': int(time.time()) + 300,
        }

        with patch.object(JWTCacheService, '_get_con', return_value=connection):
            with self.assertRaises(ConnectionError) as raised:
                JWTCacheService.add_to_blacklist(payload)

        messages = self._messages("ERROR")
        self.assertIn("写入 JWT 黑名单失败", messages)
        self.assertIn("ConnectionError", messages)
        self.assertNotIn("sensitive-jti", messages)
        self.assertNotIn("redis-password", messages)
        self.assertNotIn("redis-password", str(raised.exception))

    def test_user_cache_read_failure_logs_sanitized_error(self):
        authentication = CachedJWTAuthentication()

        with patch(
            'apps.accounts.authentication.cache.get',
            side_effect=ConnectionError('redis-password'),
        ):
            with self.assertRaises(ConnectionError):
                authentication.get_user({'user_id': 7})

        messages = self._messages("ERROR")
        self.assertIn("读取 JWT 用户缓存失败", messages)
        self.assertIn("ConnectionError", messages)
        self.assertNotIn("redis-password", messages)

    def test_user_cache_write_failure_logs_sanitized_error(self):
        authentication = CachedJWTAuthentication()
        user = SimpleNamespace(id=7)

        with patch(
            'apps.accounts.authentication.cache.get',
            return_value=None,
        ), patch(
            'apps.accounts.authentication.User.objects.get',
            return_value=user,
        ), patch(
            'apps.accounts.authentication.cache.set',
            side_effect=ConnectionError('redis-password'),
        ):
            with self.assertRaises(ConnectionError):
                authentication.get_user({'user_id': 7})

        messages = self._messages("ERROR")
        self.assertIn("写入 JWT 用户缓存失败", messages)
        self.assertIn("ConnectionError", messages)
        self.assertNotIn("redis-password", messages)

    def test_invalid_jwt_logs_warning_without_raw_token(self):
        authentication = CachedJWTAuthentication()
        request = APIRequestFactory().get(
            '/api/forum/posts/',
            HTTP_AUTHORIZATION='Token sensitive-raw-token',
        )

        with patch.object(
            authentication,
            'get_validated_token',
            side_effect=AuthenticationFailed('sensitive-raw-token'),
        ):
            result = authentication.authenticate(request)

        self.assertIsNone(result)
        messages = self._messages("WARNING")
        self.assertIn("JWT 验证失败", messages)
        self.assertIn("AuthenticationFailed", messages)
        self.assertIn("/api/forum/posts/", messages)
        self.assertNotIn("sensitive-raw-token", messages)

    def test_malformed_authorization_header_logs_warning(self):
        authentication = CachedJWTAuthentication()
        request = APIRequestFactory().get(
            '/api/forum/posts/',
            HTTP_AUTHORIZATION='Token',
        )

        try:
            result = authentication.authenticate(request)
        except AuthenticationFailed:
            self.fail("畸形 Authorization 头不应抛出 AuthenticationFailed")

        self.assertIsNone(result)
        messages = self._messages("WARNING")
        self.assertIn("JWT 验证失败", messages)
        self.assertIn("/api/forum/posts/", messages)

    def test_blacklisted_jwt_logs_warning_without_jti(self):
        authentication = CachedJWTAuthentication()
        request = APIRequestFactory().get(
            '/api/forum/posts/',
            HTTP_AUTHORIZATION='Token sensitive-raw-token',
        )
        validated_token = {'jti': 'sensitive-jti', 'user_id': 7}

        with patch.object(
            authentication,
            'get_validated_token',
            return_value=validated_token,
        ), patch.object(JWTCacheService, 'is_blacklisted', return_value=True):
            result = authentication.authenticate(request)

        self.assertIsNone(result)
        messages = self._messages("WARNING")
        self.assertIn("JWT 已进入黑名单", messages)
        self.assertIn("/api/forum/posts/", messages)
        self.assertNotIn("sensitive-jti", messages)
        self.assertNotIn("sensitive-raw-token", messages)

    def test_valid_jwt_logs_debug_without_jti(self):
        authentication = CachedJWTAuthentication()
        request = APIRequestFactory().get(
            '/api/forum/posts/',
            HTTP_AUTHORIZATION='Token sensitive-raw-token',
        )
        validated_token = {'jti': 'sensitive-jti', 'user_id': 7}
        user = SimpleNamespace(id=7)

        with patch.object(
            authentication,
            'get_validated_token',
            return_value=validated_token,
        ), patch.object(
            JWTCacheService,
            'is_blacklisted',
            return_value=False,
        ), patch.object(authentication, 'get_user', return_value=user):
            result = authentication.authenticate(request)

        self.assertEqual(result, (user, validated_token))
        messages = self._messages("DEBUG")
        self.assertIn("JWT 验证成功", messages)
        self.assertIn("user_id=7", messages)
        self.assertNotIn("sensitive-jti", messages)
        self.assertNotIn("sensitive-raw-token", messages)

    def test_missing_user_logs_warning_and_returns_none(self):
        authentication = CachedJWTAuthentication()
        request = APIRequestFactory().get(
            '/api/forum/posts/',
            HTTP_AUTHORIZATION='Token sensitive-raw-token',
        )
        validated_token = {'jti': 'sensitive-jti', 'user_id': 7}

        with patch.object(
            authentication,
            'get_validated_token',
            return_value=validated_token,
        ), patch.object(
            JWTCacheService,
            'is_blacklisted',
            return_value=False,
        ), patch.object(authentication, 'get_user', return_value=None):
            result = authentication.authenticate(request)

        self.assertIsNone(result)
        warning_messages = self._messages("WARNING")
        self.assertIn("JWT 对应用户不存在", warning_messages)
        self.assertNotIn("sensitive-jti", warning_messages)
        self.assertNotIn("sensitive-raw-token", warning_messages)
        self.assertNotIn("JWT 验证成功", self._messages("DEBUG"))


class JWTCacheServiceTest(TestCase):
    """JWT 缓存服务测试"""

    def setUp(self):
        """创建测试用户"""
        self.user = User.objects.create_user(
            email='jwt@example.com',
            password='testpass123456',
            username='jwttester'
        )

    def test_add_to_blacklist_success(self):
        """测试添加 Token 到黑名单"""
        refresh = RefreshToken.for_user(self.user)
        token_payload = refresh.access_token

        # 不应抛出异常
        JWTCacheService.add_to_blacklist(token_payload)

    def test_add_to_blacklist_multiple_tokens(self):
        """测试添加多个 Token 到黑名单"""
        token1 = RefreshToken.for_user(self.user).access_token
        token2 = RefreshToken.for_user(self.user).access_token

        JWTCacheService.add_to_blacklist(token1)
        JWTCacheService.add_to_blacklist(token2)

    def test_add_to_blacklist_with_invalid_payload(self):
        """测试添加无效 payload 到黑名单（不报错）"""
        invalid_payload = {}
        # 不应抛出异常
        JWTCacheService.add_to_blacklist(invalid_payload)


class ProfileCacheServiceTest(TestCase):
    """用户资料缓存服务测试"""

    def setUp(self):
        """创建测试用户"""
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass1',
            username='user1'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass2',
            username='user2'
        )
        self.redis = ProfileCacheService._get_con()
        self.addCleanup(self._clear_profile_cache)
        self._clear_profile_cache()

    def _clear_profile_cache(self):
        keys = [
            f"user:{user.id}:{relation}"
            for user in (self.user1, self.user2)
            for relation in ("following", "followers")
        ]
        self.redis.delete(*keys)

    def test_is_following_false_initially(self):
        """测试初始状态下未关注"""
        result = ProfileCacheService.is_following(self.user1.id, self.user2.id)
        self.assertFalse(result)

    def test_is_following_true_after_follow(self):
        """测试关注后 is_following 返回 True"""
        self.user1.follow(self.user2)

        result = ProfileCacheService.is_following(self.user1.id, self.user2.id)
        self.assertTrue(result)

    def test_get_followers_count_initially_zero(self):
        """测试初始粉丝数量为 0"""
        count = ProfileCacheService.get_followers_count(self.user1.id)
        self.assertEqual(count, 0)

    def test_get_followers_count_after_follow(self):
        """测试关注后粉丝数量正确"""
        self.user2.follow(self.user1)
        self.user1.follow(self.user1)  # 不能关注自己

        count = ProfileCacheService.get_followers_count(self.user1.id)
        self.assertEqual(count, 1)

    def test_get_following_count_initially_zero(self):
        """测试初始关注数量为 0"""
        count = ProfileCacheService.get_following_count(self.user1.id)
        self.assertEqual(count, 0)

    def test_get_following_count_after_follow(self):
        """测试关注后关注数量正确"""
        self.user1.follow(self.user2)

        count = ProfileCacheService.get_following_count(self.user1.id)
        self.assertEqual(count, 1)

    def test_update_follow_relation_follow(self):
        """测试更新关注关系（关注）"""
        ProfileCacheService.update_follow_relation(
            from_user_id=self.user1.id,
            to_user_id=self.user2.id,
            is_follow=True
        )

        # 验证关注状态
        result = ProfileCacheService.is_following(self.user1.id, self.user2.id)
        self.assertTrue(result)

    def test_update_follow_relation_unfollow(self):
        """测试更新关注关系（取消关注）"""
        self.user1.follow(self.user2)
        self.user1.following.remove(self.user2)

        ProfileCacheService.update_follow_relation(
            from_user_id=self.user1.id,
            to_user_id=self.user2.id,
            is_follow=False
        )

        # 验证已取消关注
        result = ProfileCacheService.is_following(self.user1.id, self.user2.id)
        self.assertFalse(result)

    def test_get_collection_count_initially_zero(self):
        """测试初始收藏数量为 0"""
        count = ProfileCacheService.get_collection_count(self.user1.id)
        self.assertEqual(count, 0)
