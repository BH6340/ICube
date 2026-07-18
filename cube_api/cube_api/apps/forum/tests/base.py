# forum/tests/base.py
"""
Forum 应用测试基类
提供通用的测试工具和配置
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient
from datetime import timedelta

from apps.forum.models import Post, Tag, Comment

User = get_user_model()


class ForumBaseTestCase(TestCase):
    """Forum 测试基类"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # 禁用信号（可选，提高测试速度）
        # from forum import signals
        # cls._signals = signals.post_save.receivers
        # signals.post_save.receivers = []

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # 恢复信号
        # from forum import signals
        # signals.post_save.receivers = cls._signals

    def setUp(self):
        """每个测试方法执行前的设置"""
        super().setUp()
        # 清空缓存
        cache.clear()

        # 创建 API 客户端
        self.client = APIClient()

        # 创建测试用户
        self.user = self.create_test_user(
            email='test@example.com',
            password='test123456',
            username='testuser'
        )

        # 创建第二个用户
        self.user2 = self.create_test_user(
            email='test2@example.com',
            password='test123456',
            username='testuser2'
        )

        # 创建测试标签
        self.tag_cfop = Tag.objects.create(name='CFOP', color='#409EFF')
        self.tag_sanjie = Tag.objects.create(name='三阶', color='#67C23A')
        self.tag_siji = Tag.objects.create(name='四阶', color='#E6A23C')

    def tearDown(self):
        """每个测试方法执行后的清理"""
        cache.clear()
        super().tearDown()

    # ============ 辅助方法 ============

    def create_test_user(self, email, password, username, **kwargs):
        """创建测试用户"""
        return User.objects.create_user(
            email=email,
            password=password,
            username=username,
            **kwargs
        )

    def create_test_post(self, author=None, title=None, content=None, **kwargs):
        """创建测试帖子"""
        if author is None:
            author = self.user

        if title is None:
            title = '这是一个测试帖子标题，长度足够'

        if content is None:
            content = '这是测试内容，确保长度足够满足验证要求，至少十个字符以上。'

        post = Post.objects.create(
            title=title,
            content=content,
            author=author,
            **kwargs
        )
        return post

    def create_test_comment(self, post=None, author=None, content=None, parent=None):
        """创建测试评论"""
        if post is None:
            post = self.create_test_post()

        if author is None:
            author = self.user

        if content is None:
            content = '这是一条测试评论内容'

        return Comment.objects.create(
            post=post,
            author=author,
            content=content,
            parent=parent
        )

    def authenticate(self, user=None):
        """认证用户"""
        if user is None:
            user = self.user
        self.client.force_authenticate(user=user)
        return self.client

    def get_valid_post_data(self, **kwargs):
        """获取有效的帖子数据"""
        data = {
            'title': kwargs.get('title', '这是一个有效的帖子标题'),
            'content': kwargs.get('content', '这是一个有效的帖子内容，长度足够满足验证要求。'),
            'tag_ids': kwargs.get('tag_ids', [self.tag_cfop.id])
        }
        return data

    def get_invalid_post_data(self):
        """获取无效的帖子数据（用于测试验证）"""
        return {
            'title': '短',
            'content': '短',
            'tag_ids': []
        }


class ForumAPITestCase(ForumBaseTestCase):
    """Forum API 测试基类（自动认证）"""

    def setUp(self):
        super().setUp()
        # 自动认证
        self.authenticate()


class ForumServiceTestCase(ForumBaseTestCase):
    """Forum 服务层测试基类"""

    def setUp(self):
        super().setUp()
        # 服务层测试不需要 API 客户端
        pass

    def create_hot_post(self):
        """创建热门帖子"""
        return Post.objects.create(
            title='热门帖子标题',
            content='热门帖子内容内容内容内容',
            author=self.user,
            like_count=100,
            comment_count=50,
            view_count=1000,
            created_at=timezone.now() - timedelta(days=1)
        )

    def create_cold_post(self):
        """创建冷门帖子"""
        return Post.objects.create(
            title='冷门帖子标题',
            content='冷门帖子内容内容内容内容',
            author=self.user2,
            like_count=1,
            comment_count=0,
            view_count=10,
            created_at=timezone.now() - timedelta(days=30)
        )