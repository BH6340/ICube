# apps/forum/tests/test_api.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.forum.models import Post, Tag
from django_redis import get_redis_connection  # 💡 引入获取 Redis 连接的方法

User = get_user_model()


class ForumAPITest(TestCase):
    """论坛 API 集成测试"""

    def setUp(self):
        self.client = APIClient()

        # 创建用户
        self.user = User.objects.create_user(
            email='apitester@example.com',
            password='test123456',
            username='apitester'
        )

        # 创建标签
        self.tag = Tag.objects.create(name='测试标签', color='#409EFF')

        # ✅ 直接认证，避免登录请求
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        """每个测试用例跑完后的清理工作"""
        try:
            from django_redis import get_redis_connection
            con = get_redis_connection("default")

            # 💡 核心安全兼容逻辑：
            # 如果 con 倒霉地变成了 RedisCache 包装对象，我们通过它的 client 属性穿透过去
            if hasattr(con, 'client') and hasattr(con.client, 'get_client'):
                raw_client = con.client.get_client()
                raw_client.flushdb()
            # 如果它身上直接有 flushdb，说明是正常原生连接，直接调
            elif hasattr(con, 'flushdb'):
                con.flushdb()
            else:
                # 万一还是不行，直接用底层最暴力的原生 redis 库连过去清空测试库
                import redis
                # 这里根据你 settings 里的测试库配置连过去（测试环境用的是 db 2）
                r = redis.Redis(host='127.0.0.1', port=6379, db=2)
                r.flushdb()
        except Exception as e:
            print(f"⚠️ TearDown Redis clear warning: {e}")

        super().tearDown()

    def test_create_and_get_post(self):
        """测试创建和获取帖子"""
        # 创建帖子
        create_res = self.client.post('/api/forum/posts/', {
            'title': 'API测试帖子标题',
            'content': 'API测试帖子内容内容内容',
            'tag_ids': [self.tag.id]
        }, format='json')

        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        post_id = create_res.data.get('post', {}).get('id')

        # 获取帖子
        get_res = self.client.get(f'/api/forum/posts/{post_id}/')
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertEqual(get_res.data.get('post', {}).get('title'), 'API测试帖子标题')

    def test_list_posts(self):
        """测试帖子列表"""
        # 创建几个帖子
        for i in range(3):
            Post.objects.create(
                title=f'列表测试帖子{i}',
                content='测试内容内容内容',
                author=self.user
            )

        # 获取列表
        res = self.client.get('/api/forum/posts/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        results = res.data.get('data', {}).get('results', [])
        self.assertGreaterEqual(len(results), 3)

    def test_like_post(self):
        """测试点赞帖子"""
        post = Post.objects.create(
            title='点赞测试帖子',
            content='测试内容内容内容',
            author=self.user
        )

        # 点赞
        like_res = self.client.post(f'/api/forum/posts/{post.id}/like/', {}, format='json')
        self.assertEqual(like_res.status_code, status.HTTP_200_OK)

        # 验证点赞状态
        self.assertTrue(like_res.data.get('data', {}).get('liked', False))