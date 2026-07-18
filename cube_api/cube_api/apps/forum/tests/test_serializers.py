# forum/tests/test_serializers.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.forum.models import Post, Tag, Comment
from apps.forum.serializers import (
    PostSerializer, PostListSerializer, PostCreateUpdateSerializer,
    CommentSerializer, TagSerializer
)

User = get_user_model()


class TagSerializerTest(TestCase):
    """标签序列化器测试"""

    def setUp(self):
        self.tag = Tag.objects.create(name='CFOP', color='#409EFF')
        self.serializer = TagSerializer(instance=self.tag)

    def test_contains_expected_fields(self):
        """测试包含预期字段"""
        data = self.serializer.data
        self.assertIn('id', data)
        self.assertIn('name', data)
        self.assertIn('color', data)
        self.assertIn('use_count', data)


class PostListSerializerTest(TestCase):
    """帖子列表序列化器测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='test123',
            username='testuser'
        )
        self.post = Post.objects.create(
            title='测试帖子',
            content='测试内容',
            author=self.user
        )
        self.serializer = PostListSerializer(instance=self.post)

    def test_contains_expected_fields(self):
        """测试包含预期字段（轻量级）"""
        data = self.serializer.data
        self.assertIn('id', data)
        self.assertIn('title', data)
        self.assertIn('author', data)
        self.assertIn('view_count', data)
        self.assertIn('like_count', data)
        self.assertIn('comment_count', data)
        # 列表页不应该有 content 字段
        self.assertNotIn('content', data)


class PostSerializerTest(TestCase):
    """帖子详情序列化器测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='test123',
            username='testuser'
        )
        self.post = Post.objects.create(
            title='测试帖子',
            content='测试内容',
            author=self.user
        )
        self.serializer = PostSerializer(
            instance=self.post,
            context={'request': None}
        )

    def test_contains_expected_fields(self):
        """测试包含预期字段"""
        data = self.serializer.data
        self.assertIn('id', data)
        self.assertIn('title', data)
        self.assertIn('content', data)
        self.assertIn('author', data)
        self.assertIn('is_liked', data)
        self.assertIn('is_collected', data)

    def test_is_liked_default_false(self):
        """测试未登录时 is_liked 为 False"""
        self.assertFalse(self.serializer.data['is_liked'])


class PostCreateUpdateSerializerTest(TestCase):
    """帖子创建/更新序列化器测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='test123',
            username='testuser'
        )

    def test_validate_title(self):
        """测试标题验证"""
        serializer = PostCreateUpdateSerializer(
            data={'title': '短', 'content': '测试内容'}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)

    def test_validate_content(self):
        """测试内容验证"""
        serializer = PostCreateUpdateSerializer(
            data={'title': '有效标题', 'content': '短'}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('content', serializer.errors)