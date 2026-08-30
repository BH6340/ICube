# forum/tests/test_models.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from apps.forum.models import Post, Tag, Comment, PostLike, PostCollect

from apps.forum.models import CommentLike

User = get_user_model()


class TagModelTest(TestCase):
    """标签模型测试"""

    def setUp(self):
        self.tag = Tag.objects.create(
            name='CFOP',
            color='#409EFF'
        )

    def test_tag_creation(self):
        """测试创建标签"""
        self.assertEqual(self.tag.name, 'CFOP')
        self.assertEqual(self.tag.color, '#409EFF')
        self.assertEqual(self.tag.use_count, 0)

    def test_tag_str(self):
        """测试字符串表示"""
        self.assertEqual(str(self.tag), 'CFOP')

    def test_increment_use_count(self):
        """测试增加使用次数"""
        self.tag.increment_use_count()
        self.assertEqual(self.tag.use_count, 1)

    def test_tag_name_unique(self):
        """测试标签名唯一性"""
        with self.assertRaises(IntegrityError):
            Tag.objects.create(name='CFOP', color='#FF0000')


class PostModelTest(TestCase):
    """帖子模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='test123',
            username='testuser'
        )
        self.tag = Tag.objects.create(name='CFOP', color='#409EFF')
        self.post = Post.objects.create(
            title='测试帖子',
            content='这是测试内容',
            author=self.user
        )
        self.post.tags.add(self.tag)

    def test_post_creation(self):
        """测试创建帖子"""
        self.assertEqual(self.post.title, '测试帖子')
        self.assertEqual(self.post.content, '这是测试内容')
        self.assertEqual(self.post.author, self.user)
        self.assertEqual(self.post.status, 'published')
        self.assertEqual(self.post.view_count, 0)
        self.assertEqual(self.post.like_count, 0)

    def test_post_str(self):
        """测试字符串表示"""
        self.assertEqual(str(self.post), '测试帖子')

    def test_soft_delete(self):
        """测试软删除"""
        self.post.soft_delete()
        self.assertEqual(self.post.status, 'deleted')

    def test_hot_score_calculation(self):
        """测试热度评分计算公式（点赞*3 + 评论*2 + 浏览*1）"""
        self.post.like_count = 10
        self.post.comment_count = 5
        self.post.view_count = 100
        self.post.save(update_fields=['like_count', 'comment_count', 'view_count'])

        # 通过 annotate 计算热度（与服务层一致）
        from django.db.models import F
        post = Post.objects.filter(pk=self.post.pk).annotate(
            hot_score=F('like_count') * 3 + F('comment_count') * 2 + F('view_count')
        ).first()

        expected_score = 10 * 3 + 5 * 2 + 100
        self.assertEqual(post.hot_score, expected_score)

    def test_post_tags_relation(self):
        """测试帖子与标签的关联"""
        self.assertEqual(self.post.tags.count(), 1)
        self.assertEqual(self.post.tags.first().name, 'CFOP')


class CommentModelTest(TestCase):
    """评论模型测试"""

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
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='测试评论'
        )

    def test_comment_creation(self):
        """测试创建评论"""
        self.assertEqual(self.comment.content, '测试评论')
        self.assertEqual(self.comment.author, self.user)
        self.assertEqual(self.comment.post, self.post)
        self.assertFalse(self.comment.is_deleted)

    def test_reply_comment(self):
        """测试回复评论"""
        reply = Comment.objects.create(
            post=self.post,
            author=self.user,
            parent=self.comment,
            content='回复内容'
        )
        self.assertEqual(reply.parent, self.comment)
        self.assertEqual(self.comment.replies.count(), 1)

    def test_soft_delete(self):
        """测试软删除"""
        self.comment.soft_delete()
        self.assertTrue(self.comment.is_deleted)


class InteractionModelTest(TestCase):
    """互动模型测试"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='test123',
            username='user1'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='test123',
            username='user2'
        )
        self.post = Post.objects.create(
            title='测试帖子',
            content='测试内容',
            author=self.user1
        )
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.user1,
            content='测试评论'
        )

    def test_post_like(self):
        """测试帖子点赞"""
        like = PostLike.objects.create(post=self.post, user=self.user2)
        self.assertEqual(PostLike.objects.count(), 1)
        self.assertEqual(like.post, self.post)
        self.assertEqual(like.user, self.user2)

    def test_post_like_unique(self):
        """测试同一用户不能重复点赞"""
        PostLike.objects.create(post=self.post, user=self.user2)
        with self.assertRaises(IntegrityError):
            PostLike.objects.create(post=self.post, user=self.user2)

    def test_post_collect(self):
        """测试帖子收藏"""
        collect = PostCollect.objects.create(post=self.post, user=self.user2)
        self.assertEqual(PostCollect.objects.count(), 1)

    def test_comment_like_dislike(self):
        """测试评论点赞/点踩"""
        like = CommentLike.objects.create(
            comment=self.comment,
            user=self.user2,
            is_like=True
        )
        self.assertTrue(like.is_like)

        dislike = CommentLike.objects.create(
            comment=self.comment,
            user=self.user1,
            is_like=False
        )
        self.assertFalse(dislike.is_like)