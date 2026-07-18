# accounts/services.py
import datetime

from django_redis import get_redis_connection

from .models import User


class JWTCacheService:
    @staticmethod
    def _get_con():
        from django_redis import get_redis_connection
        con = get_redis_connection("default")
        # 💡 核心修复逻辑：
        # 如果测试环境中 con 被 Django 代理层污染成了 'RedisCache' 对象
        # 我们通过 .client.get_client() 暴力穿透它，强制拿到原生的 redis-py 客户端实例！
        if hasattr(con, 'client') and hasattr(con.client, 'get_client'):
            return con.client.get_client()
        return con

    @classmethod
    def add_to_blacklist(cls, payload: dict):
        """
        将 Token 塞入 Redis 黑名单
        """
        con = cls._get_con()
        # 1. 提取 Token 的唯一标识符（jti 是 JWT 规范中定义的 Token 唯一 ID）
        jti = payload.get("jti")
        if not jti:
            return

        # 2. 计算该 Token 还有多久自然过期
        exp_timestamp = payload.get("exp")
        now_timestamp = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        remaining_seconds = exp_timestamp - now_timestamp

        # 3. 如果已经过期了，就不需要管了；没过期，则塞入 Redis 并设置残余时间为 TTL
        if remaining_seconds > 0:
            redis_key = f"jwt:blacklist:{jti}"
            # 只需要存个占位符 1 即可，关键在 TTL
            con.setex(redis_key, remaining_seconds, 1)

    @classmethod
    def is_blacklisted(cls, jti: str) -> bool:
        """
        检查某个 Token 是否在黑名单中
        """
        if not jti:
            return True
        con = cls._get_con()
        # exists() 返回 1 说明在黑名单中，返回 0 说明安全
        return con.exists(f"jwt:blacklist:{jti}") == 1


class ProfileCacheService:
    """
    用户资料与社交关系的 Redis 缓存服务类
    封装了读写分离、懒加载重建、Pipeline优化、防穿透等底层细节
    """

    @staticmethod
    def _get_con():
        from django_redis import get_redis_connection
        con = get_redis_connection("default")

        # 💡 核心修复逻辑：
        # 如果测试环境中 con 被 Django 代理层污染成了 'RedisCache' 对象
        # 我们通过 .client.get_client() 暴力穿透它，强制拿到原生的 redis-py 客户端实例！
        if hasattr(con, 'client') and hasattr(con.client, 'get_client'):
            return con.client.get_client()

        return con

    @classmethod
    def get_following_ids(cls, user_id: int) -> set:
        """
        核心方法：获取用户关注的所有人 ID 集合（支持懒加载重建）
        """
        con = cls._get_con()
        key = f"user:{user_id}:following"

        # 1. 如果集合存在（即使只有-1），直接返回
        if con.scard(key) > 0:
            # 使用 smembers 获取全部元素，并转为 Python 的 set (元素通常是 bytes)
            # 在内存中做类型转换或判定
            return {int(x) for x in con.smembers(key)}

        # 2. 缓存未命中：安全降级查库
        try:
            user = User.objects.get(id=user_id)
            following_ids = list(user.following.values_list('id', flat=True))
        except User.DoesNotExist:
            following_ids = []

        # 3. 异步/管道回写 Redis
        pipe = con.pipeline()
        if following_ids:
            pipe.sadd(key, *following_ids)
        else:
            pipe.sadd(key, -1)
            pipe.expire(key, 600)  # 空集合 10 分钟过期防穿透
        pipe.execute()

        return set(following_ids)

    @classmethod
    def is_following(cls, current_user_id: int, target_user_id: int) -> bool:
        """
        判断 A 是否关注了 B
        """
        # 巧妙复用：直接获取当前用户的关注集合，通过 Python Set 进行 O(1) 的判断
        # 这样在多级调用或序列化列表时，相同的 key 在同一个请求生命周期内还能进一步优化
        following_set = cls.get_following_ids(current_user_id)
        return target_user_id in following_set

    @classmethod
    def get_followers_count(cls, user_id: int) -> int:
        """
        获取用户的粉丝数
        """
        con = cls._get_con()
        key = f"user:{user_id}:followers"

        total = con.scard(key)
        if total > 0:
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
            pipe.sadd(key, -1)
            pipe.expire(key, 600)
            count = 0
        pipe.execute()

        return count

    @classmethod
    def get_following_count(cls, user_id: int) -> int:
        """
        获取用户的关注数
        """
        # 关注数直接取 get_following_ids 的长度，排除 -1
        following_set = cls.get_following_ids(user_id)
        if -1 in following_set:
            return 0
        return len(following_set)

    @classmethod
    def get_collection_count(cls, user_id: int) -> int:
        """
        获取用户的公式收藏数
        """
        from apps.formula.models import FormulaCollection
        try:
            return FormulaCollection.objects.filter(user_id=user_id).count()
        except Exception:
            return 0

    @classmethod
    def update_follow_relation(cls, from_user_id: int, to_user_id: int, is_follow: bool):
        """
        【数据一致性控制核心】当发生关注或取关动作时，主动更新 Redis 集合
        """
        con = cls._get_con()
        following_key = f"user:{from_user_id}:following"
        followers_key = f"user:{to_user_id}:followers"

        pipe = con.pipeline()
        if is_follow:
            # 1. 关注动作
            pipe.sadd(following_key, to_user_id)
            pipe.srem(following_key, -1)  # 移除可能存在的 -1 空集合占位符

            pipe.sadd(followers_key, from_user_id)
            pipe.srem(followers_key, -1)
        else:
            # 2. 取关动作
            pipe.srem(following_key, to_user_id)
            pipe.srem(followers_key, from_user_id)

            # 💡 可选高级优化：如果剔除后集合变空了，可以顺手塞个 -1 进去防止它变成未命中状态
            # 这里交给未来的定时任务或下一次懒加载重建更轻量
        pipe.execute()
