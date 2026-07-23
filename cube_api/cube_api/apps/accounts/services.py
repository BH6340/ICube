# -*- coding: utf-8 -*-
"""
用户认证模块缓存服务

该模块提供两个核心缓存服务：
    1. JWTCacheService：JWT Token 黑名单管理
    2. ProfileCacheService：用户资料与社交关系的 Redis 缓存管理

设计特点：
    - 使用 Redis Set 存储关注/粉丝关系，支持 O(1) 复杂度的存在性检查
    - 支持懒加载重建：缓存未命中时从数据库查询并回写 Redis
    - 使用 -1 占位符防止缓存穿透（空集合场景）
    - 使用 Pipeline 批量操作，减少网络往返
    - 测试环境兼容：处理 Django 测试缓存代理层的特殊情况
"""
import datetime

from django_redis import get_redis_connection

from .models import User


class JWTCacheService:
    """
    JWT Token 黑名单缓存服务

    提供 Token 黑名单的添加和查询功能，用于实现退出登录时使 Token 提前失效。

    设计原理：
        - JWT 本身是无状态的，无法主动使 Token 失效
        - 通过 Redis 黑名单机制，在每次认证时检查 Token 是否被拉黑
        - 黑名单的 TTL 设置为 Token 的剩余有效期，过期后自动清理
    """

    @staticmethod
    def _get_con():
        """
        获取 Redis 原生客户端

        处理测试环境的特殊情况：
            在测试环境中，get_redis_connection 返回的可能是 Django 的 RedisCache 对象，
            需要通过 .client.get_client() 获取真正的 redis-py 客户端实例。

        Returns:
            redis-py 客户端实例
        """
        from django_redis import get_redis_connection
        con = get_redis_connection("default")

        # 测试环境兼容：如果 con 被 Django 代理层包装，
        # 通过 .client.get_client() 获取原生 redis-py 客户端实例
        if hasattr(con, 'client') and hasattr(con.client, 'get_client'):
            return con.client.get_client()
        return con

    @classmethod
    def add_to_blacklist(cls, payload: dict):
        """
        将 Token 添加到 Redis 黑名单

        流程：
            1. 提取 Token 的唯一标识符 jti
            2. 计算 Token 的剩余有效期
            3. 如果未过期，将 jti 存入 Redis 并设置 TTL

        Args:
            payload: JWT Token 解析后的载荷字典
        """
        con = cls._get_con()

        # 提取 Token 的唯一标识符（jti 是 JWT 规范中定义的 Token 唯一 ID）
        jti = payload.get("jti")
        if not jti:
            return

        # 计算该 Token 还有多久自然过期
        exp_timestamp = payload.get("exp")
        now_timestamp = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        remaining_seconds = exp_timestamp - now_timestamp

        # 如果已经过期了，就不需要加入黑名单了
        # 没过期，则塞入 Redis 并设置残余时间为 TTL
        if remaining_seconds > 0:
            redis_key = f"jwt:blacklist:{jti}"
            # 只需要存个占位符 1 即可，关键在 TTL（自动过期）
            con.setex(redis_key, remaining_seconds, 1)

    @classmethod
    def is_blacklisted(cls, jti: str) -> bool:
        """
        检查 Token 是否在黑名单中

        Args:
            jti: Token 的唯一标识符

        Returns:
            True：Token 在黑名单中（已失效）
            False：Token 不在黑名单中（有效）
        """
        if not jti:
            # jti 为空时，认为是无效 Token
            return True
        con = cls._get_con()
        # exists() 返回 1 说明在黑名单中，返回 0 说明安全
        return con.exists(f"jwt:blacklist:{jti}") == 1


class ProfileCacheService:
    """
    用户资料与社交关系的 Redis 缓存服务类

    封装了以下核心功能：
        - 关注/粉丝关系的读写分离
        - 懒加载重建：缓存未命中时从数据库查询并回写 Redis
        - Pipeline 批量操作：减少网络往返
        - 防穿透：使用 -1 占位符处理空集合场景

    缓存键设计：
        - user:{user_id}:following: 用户关注的人 ID 集合（Redis Set）
        - user:{user_id}:followers: 用户的粉丝 ID 集合（Redis Set）
    """

    @staticmethod
    def _get_con():
        """
        获取 Redis 原生客户端

        处理测试环境的特殊情况：
            在测试环境中，get_redis_connection 返回的可能是 Django 的 RedisCache 对象，
            需要通过 .client.get_client() 获取真正的 redis-py 客户端实例。

        Returns:
            redis-py 客户端实例
        """
        from django_redis import get_redis_connection
        con = get_redis_connection("default")

        # 测试环境兼容：如果 con 被 Django 代理层包装，
        # 通过 .client.get_client() 获取原生 redis-py 客户端实例
        if hasattr(con, 'client') and hasattr(con.client, 'get_client'):
            return con.client.get_client()

        return con

    @classmethod
    def get_following_ids(cls, user_id: int) -> set:
        """
        获取用户关注的所有人 ID 集合（支持懒加载重建）

        缓存策略：
            1. 如果 Redis 中存在该集合（即使只有 -1 占位符），直接返回
            2. 缓存未命中时，从数据库查询并回写 Redis
            3. 空集合场景使用 -1 占位符，设置 10 分钟 TTL 防穿透

        Args:
            user_id: 用户 ID

        Returns:
            用户关注的人 ID 集合（int 类型）
        """
        con = cls._get_con()
        key = f"user:{user_id}:following"

        # 1. 如果集合存在（即使只有 -1），直接返回
        if con.scard(key) > 0:
            # 使用 smembers 获取全部元素，并转为 Python 的 set
            # Redis 返回的是 bytes 类型，需要转换为 int
            return {int(x) for x in con.smembers(key)}

        # 2. 缓存未命中：安全降级查库
        try:
            user = User.objects.get(id=user_id)
            following_ids = list(user.following.values_list('id', flat=True))
        except User.DoesNotExist:
            following_ids = []

        # 3. 使用 Pipeline 批量回写 Redis，减少网络往返
        pipe = con.pipeline()
        if following_ids:
            # 有数据：直接添加所有关注的 ID
            pipe.sadd(key, *following_ids)
        else:
            # 空集合：添加 -1 占位符，并设置 10 分钟过期（防穿透）
            pipe.sadd(key, -1)
            pipe.expire(key, 600)
        pipe.execute()

        return set(following_ids)

    @classmethod
    def is_following(cls, current_user_id: int, target_user_id: int) -> bool:
        """
        判断当前用户是否关注了目标用户

        实现方式：
            1. 调用 get_following_ids 获取当前用户的关注集合
            2. 使用 Python Set 进行 O(1) 复杂度的存在性检查

        优化点：
            在同一个请求生命周期内多次调用时，get_following_ids 的结果会被缓存，
            不需要每次都查询 Redis。

        Args:
            current_user_id: 当前用户 ID
            target_user_id: 目标用户 ID

        Returns:
            True：已关注
            False：未关注
        """
        following_set = cls.get_following_ids(current_user_id)
        return target_user_id in following_set

    @classmethod
    def get_followers_count(cls, user_id: int) -> int:
        """
        获取用户的粉丝数（带 Redis 缓存）

        缓存策略：
            1. 优先从 Redis 获取集合大小
            2. 如果集合包含 -1 占位符，返回 0
            3. 缓存未命中时，从数据库查询并回写 Redis

        Args:
            user_id: 用户 ID

        Returns:
            粉丝数量
        """
        con = cls._get_con()
        key = f"user:{user_id}:followers"

        total = con.scard(key)
        if total > 0:
            # 如果集合包含 -1 占位符，说明是空集合，返回 0
            return total - 1 if con.sismember(key, -1) else total

        # 缓存未命中：查库重建
        try:
            user = User.objects.get(id=user_id)
            followers_ids = list(user.followers.values_list('id', flat=True))
        except User.DoesNotExist:
            followers_ids = []

        pipe = con.pipeline()
        if followers_ids:
            pipe.sadd(key, *followers_ids)
            count = len(followers_ids)
        else:
            # 空集合：添加 -1 占位符，设置 10 分钟过期
            pipe.sadd(key, -1)
            pipe.expire(key, 600)
            count = 0
        pipe.execute()

        return count

    @classmethod
    def get_following_count(cls, user_id: int) -> int:
        """
        获取用户的关注数

        实现方式：
            复用 get_following_ids 方法，返回集合大小（排除 -1 占位符）

        Args:
            user_id: 用户 ID

        Returns:
            关注数量
        """
        following_set = cls.get_following_ids(user_id)
        # 如果包含 -1 占位符，说明是空集合，返回 0
        if -1 in following_set:
            return 0
        return len(following_set)

    @classmethod
    def get_collection_count(cls, user_id: int) -> int:
        """
        获取用户的公式收藏数

        注意：该方法直接查询数据库，没有使用缓存。
        原因：公式收藏数相对不常变化，且查询成本较低。

        Args:
            user_id: 用户 ID

        Returns:
            公式收藏数量
        """
        from apps.formula.models import FormulaCollection
        try:
            return FormulaCollection.objects.filter(user_id=user_id).count()
        except Exception:
            return 0

    @classmethod
    def update_follow_relation(cls, from_user_id: int, to_user_id: int, is_follow: bool):
        """
        更新关注关系（数据一致性控制核心）

        当发生关注或取关动作时，同步更新 Redis 中的两个集合：
            - from_user_id 的 following 集合
            - to_user_id 的 followers 集合

        使用 Pipeline 批量操作，确保原子性。

        Args:
            from_user_id: 发起关注/取关的用户 ID
            to_user_id: 被关注/取关的用户 ID
            is_follow: True 表示关注，False 表示取关
        """
        con = cls._get_con()
        following_key = f"user:{from_user_id}:following"
        followers_key = f"user:{to_user_id}:followers"

        pipe = con.pipeline()
        if is_follow:
            # 关注动作：添加到集合
            pipe.sadd(following_key, to_user_id)
            pipe.srem(following_key, -1)  # 移除可能存在的 -1 空集合占位符

            pipe.sadd(followers_key, from_user_id)
            pipe.srem(followers_key, -1)
        else:
            # 取关动作：从集合中移除
            pipe.srem(following_key, to_user_id)
            pipe.srem(followers_key, from_user_id)

            # 可选优化：如果剔除后集合变空了，可以顺手塞个 -1 进去防止它变成未命中状态
            # 这里交给未来的定时任务或下一次懒加载重建更轻量
        pipe.execute()
