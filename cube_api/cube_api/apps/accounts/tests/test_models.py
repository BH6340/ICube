# -*- coding: utf-8 -*-
"""
Accounts 模块模型测试

测试 User 模型的核心功能，包括：
    - 用户创建（普通用户、超级用户）
    - 字段验证（唯一性、格式验证）
    - 密码加密与验证
    - 关注关系（follow/unfollow）
    - Redis 缓存同步
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class UserModelTest(TestCase):
    """User 模型基础测试"""

    def setUp(self):
        """测试前准备"""
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123456',
            'username': 'testuser'
        }

    def test_create_user_success(self):
        """测试创建普通用户成功"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123456',
            username='testuser'
        )

        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpass123456'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser_success(self):
        """测试创建超级用户成功"""
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123456',
            username='adminuser'
        )

        self.assertEqual(admin.email, 'admin@example.com')
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)

    def test_create_user_without_email_raises_error(self):
        """测试无邮箱创建用户时抛出异常"""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='testpass', username='test')

    def test_create_superuser_without_is_staff_raises_error(self):
        """测试创建超级用户但is_staff不为True时抛出异常"""
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='admin@example.com',
                password='testpass',
                username='admin',
                is_staff=False
            )

    def test_email_normalization(self):
        """测试邮箱标准化（域名部分转小写，本地部分保留原大小写）"""
        user = User.objects.create_user(
            email='Test@Example.COM',
            password='testpass',
            username='test'
        )
        # Django normalize_email 只标准化域名部分
        self.assertEqual(user.email, 'Test@example.com')

    def test_email_uniqueness(self):
        """测试邮箱唯一性约束"""
        User.objects.create_user(
            email='unique@example.com',
            password='testpass1',
            username='user1'
        )
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email='unique@example.com',
                password='testpass2',
                username='user2'
            )

    def test_username_uniqueness(self):
        """测试用户名唯一性约束"""
        User.objects.create_user(
            email='user1@example.com',
            password='testpass',
            username='sameuser'
        )
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email='user2@example.com',
                password='testpass',
                username='sameuser'
            )

    def test_password_not_stored_as_plaintext(self):
        """测试密码不以明文存储"""
        user = User.objects.create_user(
            email='test@example.com',
            password='mypassword123',
            username='testuser'
        )
        # 密码应被哈希，不应该等于原始密码
        self.assertNotEqual(user.password, 'mypassword123')
        # check_password 应该返回 True
        self.assertTrue(user.check_password('mypassword123'))
        # 错误密码应该返回 False
        self.assertFalse(user.check_password('wrongpassword'))

    def test_user_str_method(self):
        """测试 __str__ 方法返回邮箱"""
        user = User.objects.create_user(
            email='str@example.com',
            password='testpass',
            username='struser'
        )
        self.assertEqual(str(user), 'str@example.com')

    def test_get_full_name_returns_username(self):
        """测试 get_full_name 返回 username"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass',
            username='MyName'
        )
        self.assertEqual(user.get_full_name(), 'MyName')

    def test_get_short_name_returns_username(self):
        """测试 get_short_name 返回 username"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass',
            username='ShortName'
        )
        self.assertEqual(user.get_short_name(), 'ShortName')

    def test_create_user_without_password(self):
        """测试无密码创建用户（设置为不可用密码）"""
        user = User.objects.create_user(
            email='nopass@example.com',
            username='nopass'
        )
        # 密码应为不可用状态
        self.assertFalse(user.has_usable_password())

    def test_bio_field(self):
        """测试个人简介字段"""
        user = User.objects.create_user(
            email='bio@example.com',
            password='testpass',
            username='biouser',
            bio='这是一段个人简介'
        )
        self.assertEqual(user.bio, '这是一段个人简介')

    def test_ordering_by_date_joined(self):
        """测试默认按注册时间倒序排列"""
        user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass',
            username='user1'
        )
        user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass',
            username='user2'
        )
        # 默认 ordering 为 ["-date_joined"]，user2 应该排在前面（后创建的）
        users = User.objects.all()
        self.assertEqual(users[0].id, user2.id)
        self.assertEqual(users[1].id, user1.id)


class UserFollowTest(TestCase):
    """用户关注关系测试"""

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
        self.user3 = User.objects.create_user(
            email='user3@example.com',
            password='testpass3',
            username='user3'
        )

        # 清空 Redis 中的关注/粉丝缓存，避免测试间数据污染
        from django_redis import get_redis_connection
        con = get_redis_connection("default")
        for key in con.scan_iter("user:*:following"):
            con.delete(key)
        for key in con.scan_iter("user:*:followers"):
            con.delete(key)

    def test_follow_user_success(self):
        """测试成功关注用户"""
        self.user1.follow(self.user2)

        # 数据库验证
        self.assertEqual(self.user1.following.count(), 1)
        self.assertIn(self.user2, self.user1.following.all())
        self.assertIn(self.user1, self.user2.followers.all())

    def test_follow_self_should_be_blocked(self):
        """测试不能关注自己"""
        self.user1.follow(self.user1)
        # 关注自己应该被阻止，following 数量不变
        self.assertEqual(self.user1.following.count(), 0)

    def test_unfollow_user_success(self):
        """测试成功取消关注"""
        self.user1.follow(self.user2)
        self.assertEqual(self.user1.following.count(), 1)

        self.user1.unfollow(self.user2)
        self.assertEqual(self.user1.following.count(), 0)

    def test_follow_multiple_users(self):
        """测试关注多个用户"""
        self.user1.follow(self.user2)
        self.user1.follow(self.user3)

        self.assertEqual(self.user1.following.count(), 2)
        self.assertIn(self.user2, self.user1.following.all())
        self.assertIn(self.user3, self.user1.following.all())

    def test_followers_count_property(self):
        """测试粉丝数量属性"""
        self.user1.follow(self.user2)
        self.user3.follow(self.user2)

        # user2 应该有 2 个粉丝
        self.assertEqual(self.user2.followers_count, 2)

    def test_following_count_property(self):
        """测试关注数量属性"""
        self.user1.follow(self.user2)
        self.user1.follow(self.user3)

        # user1 应该关注了 2 个人
        self.assertEqual(self.user1.following_count, 2)

    def test_mutual_follow(self):
        """测试互相关注"""
        self.user1.follow(self.user2)
        self.user2.follow(self.user1)

        self.assertEqual(self.user1.following.count(), 1)
        self.assertEqual(self.user2.following.count(), 1)
        self.assertEqual(self.user1.followers_count, 1)
        self.assertEqual(self.user2.followers_count, 1)

    def test_unfollow_nonexistent_follow(self):
        """测试取消关注未关注的用户（不报错）"""
        # 不应抛出异常
        self.user1.unfollow(self.user2)
        self.assertEqual(self.user1.following.count(), 0)
