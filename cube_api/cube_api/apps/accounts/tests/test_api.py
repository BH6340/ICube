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

from apps.forum.models import Post
from apps.formula.models import Formula
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

    def test_register_rejects_username_with_slash(self):
        """测试注册时拒绝无法用于公开主页路径的用户名"""
        data = {
            'user': {
                'email': 'invalid-username@example.com',
                'password': 'newpass123456',
                'username': 'invalid/name'
            }
        }

        response = self.client.post('/api/users/register', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

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
        response = self.client.get(f'/api/profiles/{self.user2.username}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('profiles', response.data)
        self.assertEqual(response.data['profiles']['username'], 'testuser2')

    def test_get_profile_list_success(self):
        """测试获取用户列表"""
        response = self.client.get('/api/profiles')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('profiles', response.data)
        self.assertGreaterEqual(len(response.data['profiles']), 2)

    def test_search_profiles_matches_partial_username_anonymously(self):
        """匿名用户可按部分用户名搜索，且不泄露邮箱"""
        response = APIClient().get('/api/profiles?search=user')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 100)
        usernames = [
            item['username']
            for item in response.data['data']['results']
        ]
        self.assertIn(self.user.username, usernames)
        self.assertNotIn('email', response.data['data']['results'][0])

    def test_search_profiles_prioritizes_case_insensitive_exact_match(self):
        """大小写不敏感的完整匹配排在模糊匹配之前"""
        User.objects.create_user(
            email='prefix@example.com',
            password='test123456',
            username=f'{self.user.username}_extra',
        )

        response = self.client.get(
            f'/api/profiles?search={self.user.username.upper()}'
        )

        self.assertEqual(
            response.data['data']['results'][0]['username'],
            self.user.username,
        )

    def test_search_profiles_with_blank_keyword_returns_empty_page(self):
        """空关键词不枚举用户"""
        response = self.client.get('/api/profiles?search=%20')

        self.assertEqual(response.data['data']['count'], 0)
        self.assertEqual(response.data['data']['results'], [])

    def test_search_profiles_excludes_inactive_users(self):
        """搜索结果排除停用用户"""
        self.user2.is_active = False
        self.user2.save(update_fields=['is_active'])

        response = self.client.get(
            f'/api/profiles?search={self.user2.username}'
        )

        self.assertEqual(response.data['data']['results'], [])

    def test_search_profiles_returns_following_state(self):
        """登录用户搜索时返回正确关注状态"""
        self.user.following.add(self.user2)

        response = self.client.get(
            f'/api/profiles?search={self.user2.username}'
        )

        self.assertTrue(response.data['data']['results'][0]['following'])

    def test_profile_detail_supports_search_and_dotted_usernames(self):
        """搜索保留字和含点用户名均可访问公开主页"""
        for index, username in enumerate(('search', 'dot.user'), start=1):
            User.objects.create_user(
                email=f'route-user-{index}@example.com',
                password='test123456',
                username=username,
            )

            response = self.client.get(f'/api/profiles/{username}')

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['profiles']['username'], username)

    def test_profile_counts_only_public_posts_and_custom_formulas(self):
        """公开资料只统计已发布文章和自创公式"""
        Post.objects.create(
            title='公开文章',
            content='公开内容',
            author=self.user,
            status='published',
        )
        Post.objects.create(
            title='草稿文章',
            content='草稿内容',
            author=self.user,
            status='draft',
        )
        Formula.objects.create(
            name='用户公式',
            notation='R U',
            created_by=self.user,
            is_custom=True,
        )
        Formula.objects.create(
            name='非自创公式',
            notation='L U',
            created_by=self.user,
            is_custom=False,
        )

        response = self.client.get(f'/api/profiles/{self.user.username}')
        profile = response.data['profiles']

        self.assertEqual(profile['post_count'], 1)
        self.assertEqual(profile['custom_formula_count'], 1)

    def test_inactive_profile_returns_not_found(self):
        """停用用户的公开资料不可访问"""
        self.user2.is_active = False
        self.user2.save(update_fields=['is_active'])

        response = self.client.get(f'/api/profiles/{self.user2.username}')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_profile_relation_counts_exclude_inactive_users(self):
        """公开关系统计与仅展示启用用户的列表口径一致"""
        inactive_user = User.objects.create_user(
            email='inactive-relation@example.com',
            password='test123456',
            username='inactive_relation',
            is_active=False,
        )
        self.user.following.add(inactive_user)
        inactive_user.following.add(self.user)

        response = self.client.get(f'/api/profiles/{self.user.username}')
        profile = response.data['profiles']

        self.assertEqual(profile['following_count'], 0)
        self.assertEqual(profile['followers_count'], 0)

    def test_follow_user_success(self):
        """测试关注用户成功"""
        response = self.client.post(f'/api/profiles/{self.user2.username}/follow')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.following.filter(pk=self.user2.pk).exists())

    def test_follow_self_fails(self):
        """测试关注自己失败"""
        response = self.client.post(f'/api/profiles/{self.user.username}/follow')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 103)

    def test_unfollow_user_success(self):
        """测试取消关注成功"""
        # 先关注
        self.user.follow(self.user2)

        response = self.client.delete(f'/api/profiles/{self.user2.username}/follow')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_following_list_success(self):
        """测试获取关注列表"""
        self.user.follow(self.user2)

        response = self.client.get(f'/api/profiles/{self.user.username}/following')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('profiles', response.data)

    def test_get_followers_list_success(self):
        """测试获取粉丝列表"""
        self.user2.follow(self.user)

        response = self.client.get(f'/api/profiles/{self.user.username}/followers')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('profiles', response.data)

    def test_get_following_list_supports_pagination(self):
        """传分页参数时关注列表返回统一分页结构"""
        self.user.following.add(self.user2)

        response = self.client.get(
            f'/api/profiles/{self.user.username}/following?page=1&page_size=20'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(
            response.data['data']['results'][0]['username'],
            self.user2.username,
        )

    def test_get_followers_list_supports_pagination(self):
        """传分页参数时粉丝列表返回统一分页结构"""
        self.user2.following.add(self.user)

        response = self.client.get(
            f'/api/profiles/{self.user.username}/followers?page=1&page_size=20'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(
            response.data['data']['results'][0]['username'],
            self.user2.username,
        )

    def test_follow_without_authentication_fails(self):
        """测试未认证用户关注失败"""
        client = APIClient()
        response = client.post(f'/api/profiles/{self.user2.username}/follow')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
