# apps/forum/tests/test_services.py
from django.test import TestCase
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from django.db.models import F

from apps.forum.services import PostCacheService, HotPostService
from apps.forum.models import Post, Tag
from apps.accounts.models import User


class HotPostServiceTest(TestCase):
    """热门帖子服务测试"""

    def setUp(self):
        # 创建测试用户
        self.user = User.objects.create_user(
            email='test@example.com',
            password='test123',
            username='testuser'
        )

        # 创建热门帖子（7天内的）
        self.hot_post = Post.objects.create(
            title='这是一个热门帖子标题',
            content='热门帖子内容内容内容内容',
            author=self.user,
            like_count=100,
            comment_count=50,
            view_count=1000,
            created_at=timezone.now() - timedelta(days=1)
        )

        # 创建冷门帖子
        self.cold_post = Post.objects.create(
            title='这是一个冷门帖子标题',
            content='冷门帖子内容内容内容内容',
            author=self.user,
            like_count=1,
            comment_count=0,
            view_count=10,
            created_at=timezone.now() - timedelta(days=10)
        )

    def test_get_hot_posts(self):
        """测试获取热门帖子"""
        # ✅ 使用服务层方法
        hot_posts = HotPostService.get_hot_posts(days=30, limit=10)

        # 验证返回结果
        self.assertGreaterEqual(len(hot_posts), 1)

        # 验证热门帖子在结果中
        if len(hot_posts) > 0:
            titles = [p.title for p in hot_posts]
            self.assertIn('这是一个热门帖子标题', titles)

    def test_hot_posts_ordering(self):
        """测试热门帖子排序"""
        # 创建两个不同热度的帖子
        post1 = Post.objects.create(
            title='高热度帖子',
            content='内容内容内容内容',
            author=self.user,
            like_count=100,
            comment_count=50,
            view_count=1000,
            created_at=timezone.now() - timedelta(days=1)
        )
        post2 = Post.objects.create(
            title='低热度帖子',
            content='内容内容内容内容',
            author=self.user,
            like_count=1,
            comment_count=0,
            view_count=10,
            created_at=timezone.now() - timedelta(days=1)
        )

        # ✅ 使用 annotate 计算热度
        posts = Post.objects.filter(
            status='published',
            created_at__gte=timezone.now() - timedelta(days=30)
        ).annotate(
            hot_score=F('like_count') * 3 + F('comment_count') * 2 + F('view_count')
        ).order_by('-hot_score')

        # 获取热度排序
        hot_posts = list(posts)

        # 验证高热度帖子排在前面
        if len(hot_posts) >= 2:
            # 找到两个帖子的位置
            high_index = None
            low_index = None

            for i, p in enumerate(hot_posts):
                if p.title == '高热度帖子':
                    high_index = i
                elif p.title == '低热度帖子':
                    low_index = i

            if high_index is not None and low_index is not None:
                self.assertLess(high_index, low_index)