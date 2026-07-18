# forum/services.py
import sys

from django.core.cache import cache
from django.db.models import F
from django.utils import timezone
from datetime import timedelta
from .models import Post, Comment
import logging

logger = logging.getLogger(__name__)


class PostCacheService:
    """帖子缓存服务"""

    @staticmethod
    def _get_view_key(post_id):
        return f"forum:post:{post_id}:view"

    @classmethod
    def increase_view(cls, post_id):
        """增加浏览量"""
        key = cls._get_view_key(post_id)
        try:
            # 尝试使用缓存
            return cache.incr(key)
        except Exception as e:
            # 缓存不可用时，直接更新数据库
            logger.warning(f"Cache error in increase_view: {e}")
            try:
                post = Post.objects.get(id=post_id)
                post.view_count = F('view_count') + 1
                post.save(update_fields=['view_count'])
                post.refresh_from_db()
                return post.view_count
            except Post.DoesNotExist:
                return 0

    @classmethod
    def get_view_count(cls, post_id):
        """获取浏览量"""
        key = cls._get_view_key(post_id)
        try:
            count = cache.get(key)
            if count is None:
                try:
                    post = Post.objects.only('view_count').get(id=post_id)
                    count = post.view_count
                    cache.set(key, count, timeout=3600)
                except Post.DoesNotExist:
                    count = 0
            return count
        except Exception as e:
            logger.warning(f"Cache error in get_view_count: {e}")
            try:
                post = Post.objects.only('view_count').get(id=post_id)
                return post.view_count
            except Post.DoesNotExist:
                return 0

    @classmethod
    def sync_all_views(cls):
        """同步所有浏览量到数据库"""
        try:
            # 💡 抛弃 Django 的 cache 包装，直接用 django_redis 获取原生连接
            from django_redis import get_redis_connection
            con = get_redis_connection("default")

            # 为了更稳妥，如果你在 settings 设了前缀，django-redis 的 get_redis_connection 拿到的 keys 会带上前缀。
            # 更通用的做法是，直接用 con.keys("*forum:post:*:view")
            keys = con.keys("*forum:post:*:view")

            count = 0
            for key in keys:
                try:
                    # 💡 注意：原生返回的 key 可能是 bytes 类型（取决于客户端配置），解包前先 decode()
                    if isinstance(key, bytes):
                        key_str = key.decode('utf-8')
                    else:
                        key_str = key

                    # 比如 key 是 "icube_test:forum:post:12:view"
                    parts = key_str.split(':')
                    post_id = parts[-2]  # 倒数第二个就是 id

                    # 获取该键对应的值
                    views = con.get(key_str)
                    if views:
                        Post.objects.filter(id=post_id).update(view_count=F('view_count') + int(views))
                        con.delete(key_str)
                        count += 1
                except Exception as e:
                    logger.error(f"Error syncing post key {key}: {e}")

            return count
        except Exception as e:
            logger.warning(f"Sync error: {e}")
            return 0


class PostInteractionService:
    """帖子互动服务"""

    @staticmethod
    def toggle_like(post_id, user):
        """切换点赞状态"""
        from .models import PostLike

        like = PostLike.objects.filter(post_id=post_id, user=user)

        if like.exists():
            like.delete()
            Post.objects.filter(id=post_id).update(like_count=F('like_count') - 1)
            post = Post.objects.get(id=post_id)
            return {'liked': False, 'like_count': post.like_count}
        else:
            PostLike.objects.create(post_id=post_id, user=user)
            Post.objects.filter(id=post_id).update(like_count=F('like_count') + 1)
            post = Post.objects.get(id=post_id)
            return {'liked': True, 'like_count': post.like_count}

    @staticmethod
    def toggle_collect(post_id, user):
        """切换收藏状态"""
        from .models import PostCollect

        collect = PostCollect.objects.filter(post_id=post_id, user=user)

        if collect.exists():
            collect.delete()
            Post.objects.filter(id=post_id).update(collect_count=F('collect_count') - 1)
            post = Post.objects.get(id=post_id)
            return {'collected': False, 'collect_count': post.collect_count}
        else:
            PostCollect.objects.create(post_id=post_id, user=user)
            Post.objects.filter(id=post_id).update(collect_count=F('collect_count') + 1)
            post = Post.objects.get(id=post_id)
            return {'collected': True, 'collect_count': post.collect_count}

    @staticmethod
    def toggle_comment_reaction(comment_id, user, is_like):
        """切换评论反应（点赞/点踩）"""
        from .models import CommentLike, Comment
        from django.db.models import F

        existing = CommentLike.objects.filter(comment_id=comment_id, user=user)

        if existing.exists():
            reaction = existing.first()

            if reaction.is_like == is_like:
                # 相同操作：取消
                existing.delete()
                action_type = "canceled"
                if is_like:
                    Comment.objects.filter(id=comment_id).update(like_count=F('like_count') - 1)
                else:
                    Comment.objects.filter(id=comment_id).update(dislike_count=F('dislike_count') - 1)
            else:
                # 切换操作
                reaction.is_like = is_like
                reaction.save()
                action_type = "switched"
                if is_like:
                    Comment.objects.filter(id=comment_id).update(
                        like_count=F('like_count') + 1,
                        dislike_count=F('dislike_count') - 1
                    )
                else:
                    Comment.objects.filter(id=comment_id).update(
                        like_count=F('like_count') - 1,
                        dislike_count=F('dislike_count') + 1
                    )
        else:
            # 新建
            CommentLike.objects.create(comment_id=comment_id, user=user, is_like=is_like)
            action_type = "created"
            if is_like:
                Comment.objects.filter(id=comment_id).update(like_count=F('like_count') + 1)
            else:
                Comment.objects.filter(id=comment_id).update(dislike_count=F('dislike_count') + 1)

        # ✅ 获取最新的评论数据
        comment = Comment.objects.get(id=comment_id)

        # ✅ 计算当前用户的点赞/点踩状态
        user_reaction = CommentLike.objects.filter(comment_id=comment_id, user=user).first()
        is_liked = (user_reaction.is_like == True) if user_reaction else False
        is_disliked = (user_reaction.is_like == False) if user_reaction else False

        # 计算返回给前端的动作标识
        if action_type == "canceled":
            current_reaction = "none"
        else:
            current_reaction = "liked" if is_like else "disliked"

        return {
            'code': 100,
            'msg': '请求成功',
            'data': {  # 👈 用 data 包裹核心交互数据
                'reaction': current_reaction,
                'like_count': comment.like_count,
                'dislike_count': comment.dislike_count,
                'liked': is_liked,
                'disliked': is_disliked
            }
        }


class HotPostService:
    """热门帖子服务"""

    @staticmethod
    def get_hot_posts(days=7, limit=20):
        """获取热门帖子（使用 annotate 而不是 property）"""
        since = timezone.now() - timedelta(days=days)

        # ✅ 使用 annotate 添加计算字段，而不是使用 property
        posts = Post.objects.filter(
            status='published',
            created_at__gte=since
        ).annotate(
            hot_score=F('like_count') * 3 + F('comment_count') * 2 + F('view_count')
        ).order_by('-hot_score')[:limit]

        return posts
