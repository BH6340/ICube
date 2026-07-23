# -*- coding: utf-8 -*-
"""
论坛服务层

该模块提供论坛的核心业务服务，包括：
    - 帖子浏览量缓存服务
    - 帖子互动服务（点赞、收藏）
    - 评论互动服务（点赞、点踩）
    - 热门帖子计算服务

设计特点：
    - **浏览量缓存策略**：使用 Redis incr 原子操作，定时批量同步到数据库
    - **幂等性设计**：点赞/收藏操作支持切换状态，避免重复操作
    - **F表达式更新**：使用 Django F 表达式避免并发更新问题
"""
import sys

from django.core.cache import cache
from django.db.models import F
from django.utils import timezone
from datetime import timedelta
from .models import Post, Comment
import logging

logger = logging.getLogger(__name__)


class PostCacheService:
    """
    帖子浏览量缓存服务

    使用 Redis 缓存浏览量，减少数据库写入压力。

    缓存策略：
        1. 浏览量增加时，优先使用 Redis incr 原子操作
        2. 获取浏览量时，先查缓存，缓存未命中则从数据库加载并缓存
        3. 通过定时任务（sync_all_views）将缓存中的浏览量批量同步到数据库

    缓存键格式：
        forum:post:{post_id}:view

    降级策略：
        当 Redis 不可用时，直接操作数据库
    """

    @staticmethod
    def _get_view_key(post_id):
        """
        生成浏览量缓存键

        Args:
            post_id: 帖子 ID

        Returns:
            缓存键字符串
        """
        return f"forum:post:{post_id}:view"

    @classmethod
    def increase_view(cls, post_id):
        """
        增加帖子浏览量

        使用 Redis incr 原子操作保证并发安全，
        如果缓存不可用则降级到数据库更新。

        Args:
            post_id: 帖子 ID

        Returns:
            更新后的浏览量
        """
        key = cls._get_view_key(post_id)
        try:
            # 优先使用 Redis incr，原子操作保证并发安全
            return cache.incr(key)
        except Exception as e:
            # 缓存不可用时，降级到数据库操作
            logger.warning(f"Cache error in increase_view: {e}")
            try:
                post = Post.objects.get(id=post_id)
                # 使用 F 表达式避免并发更新问题
                post.view_count = F('view_count') + 1
                post.save(update_fields=['view_count'])
                post.refresh_from_db()
                return post.view_count
            except Post.DoesNotExist:
                return 0

    @classmethod
    def get_view_count(cls, post_id):
        """
        获取帖子浏览量

        先从缓存获取，缓存未命中则从数据库加载并缓存。

        Args:
            post_id: 帖子 ID

        Returns:
            当前浏览量
        """
        key = cls._get_view_key(post_id)
        try:
            count = cache.get(key)
            if count is None:
                try:
                    # 只获取 view_count 字段，减少查询开销
                    post = Post.objects.only('view_count').get(id=post_id)
                    count = post.view_count
                    # 缓存 1 小时
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
        """
        同步所有缓存的浏览量到数据库

        通过定时任务调用，批量将 Redis 中的浏览量增量写入数据库。

        同步流程：
            1. 获取所有 forum:post:*:view 格式的缓存键
            2. 解析每个键中的 post_id
            3. 将缓存值作为增量更新到数据库
            4. 删除已同步的缓存键

        Returns:
            成功同步的帖子数量
        """
        try:
            # 使用原生 Redis 连接，支持 keys 命令
            from django_redis import get_redis_connection
            con = get_redis_connection("default")

            # 获取所有浏览量缓存键
            # 注意：如果 settings 中设置了缓存前缀，键会带上前缀
            keys = con.keys("*forum:post:*:view")

            count = 0
            for key in keys:
                try:
                    # Redis 返回的 key 可能是 bytes 类型，需要解码
                    if isinstance(key, bytes):
                        key_str = key.decode('utf-8')
                    else:
                        key_str = key

                    # 解析键格式：{prefix}:forum:post:{post_id}:view
                    # 倒数第二个部分是 post_id
                    parts = key_str.split(':')
                    post_id = parts[-2]

                    # 获取缓存的浏览量增量
                    views = con.get(key_str)
                    if views:
                        # 使用 F 表达式累加浏览量
                        Post.objects.filter(id=post_id).update(view_count=F('view_count') + int(views))
                        # 同步完成后删除缓存键
                        con.delete(key_str)
                        count += 1
                except Exception as e:
                    logger.error(f"Error syncing post key {key}: {e}")

            return count
        except Exception as e:
            logger.warning(f"Sync error: {e}")
            return 0


class PostInteractionService:
    """
    帖子互动服务

    处理帖子和评论的互动操作，包括点赞、收藏和评论反应。

    设计原则：
        - **幂等性**：同一用户对同一内容的操作具有幂等性
        - **原子性**：使用 F 表达式保证计数更新的原子性
        - **状态切换**：支持切换操作（点赞↔取消点赞）
    """

    @staticmethod
    def toggle_like(post_id, user):
        """
        切换帖子点赞状态

        如果已点赞则取消，未点赞则点赞。

        Args:
            post_id: 帖子 ID
            user: 当前用户对象

        Returns:
            包含点赞状态和点赞数的字典
        """
        from .models import PostLike

        # 查询是否已点赞
        like = PostLike.objects.filter(post_id=post_id, user=user)

        if like.exists():
            # 已点赞：取消点赞
            like.delete()
            # 使用 F 表达式原子递减点赞数
            Post.objects.filter(id=post_id).update(like_count=F('like_count') - 1)
            post = Post.objects.get(id=post_id)
            return {'liked': False, 'like_count': post.like_count}
        else:
            # 未点赞：添加点赞
            PostLike.objects.create(post_id=post_id, user=user)
            # 使用 F 表达式原子递增点赞数
            Post.objects.filter(id=post_id).update(like_count=F('like_count') + 1)
            post = Post.objects.get(id=post_id)
            return {'liked': True, 'like_count': post.like_count}

    @staticmethod
    def toggle_collect(post_id, user):
        """
        切换帖子收藏状态

        如果已收藏则取消，未收藏则收藏。

        Args:
            post_id: 帖子 ID
            user: 当前用户对象

        Returns:
            包含收藏状态和收藏数的字典
        """
        from .models import PostCollect

        # 查询是否已收藏
        collect = PostCollect.objects.filter(post_id=post_id, user=user)

        if collect.exists():
            # 已收藏：取消收藏
            collect.delete()
            # 使用 F 表达式原子递减收藏数
            Post.objects.filter(id=post_id).update(collect_count=F('collect_count') - 1)
            post = Post.objects.get(id=post_id)
            return {'collected': False, 'collect_count': post.collect_count}
        else:
            # 未收藏：添加收藏
            PostCollect.objects.create(post_id=post_id, user=user)
            # 使用 F 表达式原子递增收藏数
            Post.objects.filter(id=post_id).update(collect_count=F('collect_count') + 1)
            post = Post.objects.get(id=post_id)
            return {'collected': True, 'collect_count': post.collect_count}

    @staticmethod
    def toggle_comment_reaction(comment_id, user, is_like):
        """
        切换评论反应（点赞/点踩）

        支持三种操作：
            1. 新建反应（从未操作过）
            2. 取消反应（重复相同操作）
            3. 切换反应（从点赞变为点踩，或反之）

        Args:
            comment_id: 评论 ID
            user: 当前用户对象
            is_like: True 表示点赞，False 表示点踩

        Returns:
            包含反应状态和计数的字典
        """
        from .models import CommentLike, Comment
        from django.db.models import F

        # 查询用户是否已有反应记录
        existing = CommentLike.objects.filter(comment_id=comment_id, user=user)

        if existing.exists():
            reaction = existing.first()

            if reaction.is_like == is_like:
                # 相同操作：取消反应
                existing.delete()
                action_type = "canceled"
                if is_like:
                    Comment.objects.filter(id=comment_id).update(like_count=F('like_count') - 1)
                else:
                    Comment.objects.filter(id=comment_id).update(dislike_count=F('dislike_count') - 1)
            else:
                # 切换操作：从点赞变为点踩，或反之
                reaction.is_like = is_like
                reaction.save()
                action_type = "switched"
                if is_like:
                    # 切换为点赞：点赞数+1，点踩数-1
                    Comment.objects.filter(id=comment_id).update(
                        like_count=F('like_count') + 1,
                        dislike_count=F('dislike_count') - 1
                    )
                else:
                    # 切换为点踩：点赞数-1，点踩数+1
                    Comment.objects.filter(id=comment_id).update(
                        like_count=F('like_count') - 1,
                        dislike_count=F('dislike_count') + 1
                    )
        else:
            # 新建反应
            CommentLike.objects.create(comment_id=comment_id, user=user, is_like=is_like)
            action_type = "created"
            if is_like:
                Comment.objects.filter(id=comment_id).update(like_count=F('like_count') + 1)
            else:
                Comment.objects.filter(id=comment_id).update(dislike_count=F('dislike_count') + 1)

        # 获取最新的评论数据
        comment = Comment.objects.get(id=comment_id)

        # 计算当前用户的点赞/点踩状态
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
            'data': {
                'reaction': current_reaction,
                'like_count': comment.like_count,
                'dislike_count': comment.dislike_count,
                'liked': is_liked,
                'disliked': is_disliked
            }
        }


class HotPostService:
    """
    热门帖子服务

    根据热度算法计算热门帖子，用于首页推荐和热门榜单。

    热度计算公式：
        hot_score = like_count * 3 + comment_count * 2 + view_count

    权重设计原因：
        - 点赞权重最高（×3）：反映用户认可度
        - 评论权重次之（×2）：反映用户参与度
        - 浏览量权重最低（×1）：防止刷浏览量作弊
    """

    @staticmethod
    def get_hot_posts(days=7, limit=20):
        """
        获取热门帖子列表

        使用 annotate 在数据库层面计算热度分数，避免在 Python 层面排序。

        Args:
            days: 时间范围（最近 N 天），默认 7 天
            limit: 返回数量限制，默认 20 条

        Returns:
            QuerySet: 按热度降序排列的帖子列表
        """
        since = timezone.now() - timedelta(days=days)

        # 使用 annotate 在数据库层面计算热度分数
        # 这样可以利用数据库索引，性能优于在 Python 层面计算
        posts = Post.objects.filter(
            status='published',
            created_at__gte=since
        ).annotate(
            # 热度计算公式：点赞×3 + 评论×2 + 浏览量×1
            hot_score=F('like_count') * 3 + F('comment_count') * 2 + F('view_count')
        ).order_by('-hot_score')[:limit]

        return posts
