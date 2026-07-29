# -*- coding: utf-8 -*-
"""
Accounts 模块服务层测试

测试 accounts 服务层的核心功能，包括：
    - JWT Token 生成与验证
    - Token 黑名单管理
    - 缓存服务
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.services import JWTCacheService, ProfileCacheService

User = get_user_model()


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
