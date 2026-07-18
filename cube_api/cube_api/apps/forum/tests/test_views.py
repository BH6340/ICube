# forum/tests/test_views.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.forum.models import Post, Tag, Comment

User = get_user_model()


class PostViewSetTest(TestCase):
    """帖子视图集测试"""

    def setUp(self):
        self.client = APIClient()

        # 创建用户
        self.user = User.objects.create_user(
            email='test@example.com',
            password='test123456',
            username='testuser'
        )

        # 创建标签
        self.tag = Tag.objects.create(name='CFOP', color='#409EFF')

        # 创建帖子
        self.post = Post.objects.create(
            title='测试帖子标题',
            content='这是魔方学习帖子的测试内容',
            author=self.user
        )
        self.post.tags.add(self.tag)

        # ✅ 使用 force_authenticate 代替真实登录（推荐）
        self.client.force_authenticate(user=self.user)

    def test_create_post(self):
        """测试创建帖子"""
        url = '/api/forum/posts/'
        data = {
            'title': '新帖子标题内容',
            'content': '这是新帖子的内容展示'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_like_post(self):
        """测试点赞帖子"""
        url = f'/api/forum/posts/{self.post.id}/like/'
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CommentViewSetTest(TestCase):
    """评论视图集测试"""

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email='commenter@example.com',
            password='test123456',
            username='commenter'
        )

        self.post = Post.objects.create(
            title='测试帖子内容',
            content='测试内容展示部分，展示内容',
            author=self.user
        )

        # ✅ 使用 force_authenticate
        self.client.force_authenticate(user=self.user)

    def test_create_comment(self):
        """测试创建评论"""
        url = '/api/forum/comments/'
        data = {
            'post': self.post.id,
            'content': '这是一条测试评论'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)