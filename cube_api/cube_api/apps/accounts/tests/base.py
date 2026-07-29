# -*- coding: utf-8 -*-
"""
Accounts 应用测试基类

提供 accounts 模块测试的通用工具和配置，包括：
    - 测试用户创建
    - API 客户端认证
    - 测试数据清理
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

User = get_user_model()


class AccountsBaseTestCase(TestCase):
    """Accounts 测试基类"""

    def setUp(self):
        """每个测试方法执行前的设置"""
        super().setUp()
        cache.clear()

        # 创建 API 客户端
        self.client = APIClient()

        # 创建测试用户
        self.user = self.create_test_user(
            email='test@example.com',
            password='test123456',
            username='testuser'
        )

        # 创建第二个用户（用于关注等场景）
        self.user2 = self.create_test_user(
            email='test2@example.com',
            password='test123456',
            username='testuser2'
        )

        # 创建管理员用户
        self.admin_user = self.create_test_admin(
            email='admin@example.com',
            password='admin123456',
            username='adminuser'
        )

    def tearDown(self):
        """每个测试方法执行后的清理"""
        cache.clear()
        super().tearDown()

    # ============ 辅助方法 ============

    def create_test_user(self, email, password, username, **kwargs):
        """创建普通测试用户"""
        return User.objects.create_user(
            email=email,
            password=password,
            username=username,
            **kwargs
        )

    def create_test_admin(self, email, password, username, **kwargs):
        """创建管理员测试用户"""
        return User.objects.create_superuser(
            email=email,
            password=password,
            username=username,
            **kwargs
        )

    def authenticate(self, user=None):
        """认证用户"""
        if user is None:
            user = self.user
        self.client.force_authenticate(user=user)
        return self.client

    def get_valid_user_data(self, **kwargs):
        """获取有效的用户注册数据"""
        data = {
            'email': kwargs.get('email', 'newuser@example.com'),
            'password': kwargs.get('password', 'newpass123456'),
            'username': kwargs.get('username', 'newuser')
        }
        return data

    def get_invalid_user_data(self):
        """获取无效的用户数据（用于测试验证）"""
        return {
            'email': 'invalid-email',  # 无效邮箱格式
            'password': '123',  # 密码太短
            'username': ''  # 用户名为空
        }


class AccountsAPITestCase(AccountsBaseTestCase):
    """Accounts API 测试基类（自动认证）"""

    def setUp(self):
        super().setUp()
        self.authenticate()
