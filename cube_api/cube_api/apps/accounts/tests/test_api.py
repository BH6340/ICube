# -*- coding: utf-8 -*-
"""
Accounts 模块 API 接口测试

测试用户认证相关的 API 接口，包括：
    - 用户注册
    - 用户登录
    - 用户登出
    - 用户资料获取与更新
    - 关注/粉丝列表
    - 关注/取消关注
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from .base import AccountsBaseTestCase

User = get_user_model()


class AuthAPITest(AccountsBaseTestCase):
    """认证相关 API 测试"""

    def test_register_success(self):
        """测试用户注册成功"""
        data = {
            'user': {
                'email': 'newuser@example.com',
                'password': 'newpass123456',
                'username': 'newuser'
            }
        }
        response = self.client.post('/api/users/register/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')

        # 验证数据库中确实创建了用户
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_register_with_duplicate_email_fails(self):
        """测试重复邮箱注册失败"""
        # 先创建一个用户
        User.objects.create_user(
            email='duplicate@example.com',
            password='testpass',
            username='existinguser'
        )

        # 使用相同邮箱注册
        data = {
            'user': {
                'email': 'duplicate@example.com',
                'password': 'newpass123456',
                'username': 'newuser'
            }
        }
        response = self.client.post('/api/users/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_with_duplicate_username_auto_suffix(self):
        """测试用户名重复时自动添加后缀"""
        # 先创建一个用户
        User.objects.create_user(
            email='user1@example.com',
            password='testpass',
            username='sameusername'
        )

        # 使用相同用户名注册，应该自动添加后缀
        data = {
            'user': {
                'email': 'user2@example.com',
                'password': 'newpass123456',
                'username': 'sameusername'
            }
        }
        response = self.client.post('/api/users/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 验证用户名被添加了后缀
        new_username = response.data['user']['username']
        self.assertNotEqual(new_username, 'sameusername')
        self.assertTrue(new_username.startswith('sameusername_'))

    def test_login_success(self):
        """测试用户登录成功"""
        data = {
            'user': {
                'email': 'test@example.com',
                'password': 'test123456'
            }
        }
        response = self.client.post('/api/users/login/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertIn('token', response.data['user'])

    def test_login_with_wrong_password_fails(self):
        """测试错误密码登录失败"""
        data = {
            'user': {
                'email': 'test@example.com',
                'password': 'wrongpassword'
            }
        }
        response = self.client.post('/api/users/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_nonexistent_email_fails(self):
        """测试不存在的邮箱登录失败"""
        data = {
            'user': {
                'email': 'nonexistent@example.com',
                'password': 'testpass'
            }
        }
        response = self.client.post('/api/users/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_success(self):
        """测试用户登出成功"""
        self.authenticate()
        response = self.client.post('/api/users/logout/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_without_authentication_fails(self):
        """测试未认证用户登出失败"""
        client = APIClient()
        response = client.post('/api/users/logout/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserProfileAPITest(AccountsBaseTestCase):
    """用户资料 API 测试"""

    def setUp(self):
        super().setUp()
        self.authenticate()

    def test_get_user_info_success(self):
        """测试获取当前用户信息成功"""
        response = self.client.get('/api/users/info/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'test@example.com')

    def test_get_user_info_without_authentication_fails(self):
        """测试未认证获取用户信息失败"""
        client = APIClient()
        response = client.get('/api/users/info/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_info_success(self):
        """测试更新用户信息成功"""
        data = {
            'username': 'updateduser',
            'bio': '这是更新后的个人简介'
        }
        response = self.client.put('/api/users/info/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], 'updateduser')
        self.assertEqual(response.data['user']['bio'], '这是更新后的个人简介')

        # 验证数据库已更新
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updateduser')

    def test_update_user_info_partial_success(self):
        """测试部分更新用户信息"""
        data = {
            'bio': '仅更新简介'
        }
        response = self.client.patch('/api/users/info/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['bio'], '仅更新简介')
        # username 应保持不变
        self.assertEqual(response.data['user']['username'], 'testuser')


class ProfileDetailAPITest(AccountsBaseTestCase):
    """用户资料详情 API 测试"""

    def setUp(self):
        super().setUp()
        self.authenticate()

    def test_get_profile_detail_success(self):
        """测试获取用户资料详情"""
        response = self.client.get(f'/api/profiles/{self.user2.username}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('profiles', response.data)
        self.assertEqual(response.data['profiles']['username'], 'testuser2')

    def test_get_profile_list_success(self):
        """测试获取用户列表"""
        response = self.client.get('/api/profiles/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('profiles', response.data)
        self.assertGreaterEqual(len(response.data['profiles']), 2)

    def test_follow_user_success(self):
        """测试关注用户成功"""
        response = self.client.post(f'/api/profiles/{self.user2.username}/follow/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user2.refresh_from_db()
        self.assertEqual(self.user2.followers_count, 1)

    def test_follow_self_fails(self):
        """测试关注自己失败"""
        response = self.client.post(f'/api/profiles/{self.user.username}/follow/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 103)

    def test_unfollow_user_success(self):
        """测试取消关注成功"""
        # 先关注
        self.user.follow(self.user2)

        response = self.client.delete(f'/api/profiles/{self.user2.username}/follow/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_following_list_success(self):
        """测试获取关注列表"""
        self.user.follow(self.user2)

        response = self.client.get(f'/api/profiles/{self.user.username}/following/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('profiles', response.data)

    def test_get_followers_list_success(self):
        """测试获取粉丝列表"""
        self.user2.follow(self.user)

        response = self.client.get(f'/api/profiles/{self.user.username}/followers/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('profiles', response.data)

    def test_follow_without_authentication_fails(self):
        """测试未认证用户关注失败"""
        client = APIClient()
        response = client.post(f'/api/profiles/{self.user2.username}/follow/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
