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
import random
import string

from django.conf import settings
from django.core.mail import send_mail
from django_redis import get_redis_connection
from loguru import logger

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
        try:
            from django_redis import get_redis_connection
            con = get_redis_connection("default")
        except Exception as exc:
            logger.error(
                "获取 Redis 连接失败: alias=default, exception_type={}",
                type(exc).__name__,
            )
            exc.args = ("Redis 连接失败",)
            raise

        # 测试环境兼容：如果 con 被 Django 代理层包装，
        # 通过 .client.get_client() 获取原生 redis-py 客户端实例
        if hasattr(con, 'client') and hasattr(con.client, 'get_client'):
            con = con.client.get_client()

        logger.debug("获取 Redis 连接成功: alias=default")
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
            try:
                con.setex(redis_key, remaining_seconds, 1)
            except Exception as exc:
                logger.error(
                    "写入 JWT 黑名单失败: exception_type={}",
                    type(exc).__name__,
                )
                exc.args = ("Redis 黑名单写入失败",)
                raise
            logger.debug(
                "写入 JWT 黑名单成功: ttl_seconds={}",
                remaining_seconds,
            )

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
        try:
            return con.exists(f"jwt:blacklist:{jti}") == 1
        except Exception as exc:
            logger.error(
                "查询 JWT 黑名单失败: exception_type={}",
                type(exc).__name__,
            )
            exc.args = ("Redis 黑名单查询失败",)
            raise


class EmailCodeService:
    """
    邮箱验证码服务

    负责验证码的生成、存储、发送和验证，支持注册、登录、重置密码三种场景。

    Redis 键设计：
        - email_code:{action}:{email}  — 验证码本身，TTL 5 分钟
        - email_code:send_time:{action}:{email}  — 上次发送时间戳，TTL 60 秒（防重发）

    测试模式：
        - 假邮箱（后缀匹配 EMAIL_TEST_SUFFIXES）直接返回固定验证码 999999，不实际发送邮件
        - 测试环境（'test' in sys.argv）所有邮箱均为假邮箱
    """

    CODE_PREFIX = 'email_code'
    CODE_TTL = 300          # 验证码有效期 5 分钟
    RESEND_INTERVAL = 60    # 重发间隔 60 秒
    TEST_CODE = '999999'    # 测试模式固定验证码
    CODE_LENGTH = 6         # 验证码位数

    @staticmethod
    def _get_con():
        con = get_redis_connection("default")
        if hasattr(con, 'client') and hasattr(con.client, 'get_client'):
            return con.client.get_client()
        return con

    @classmethod
    def _key(cls, action, email):
        """验证码 Redis key"""
        return f"{cls.CODE_PREFIX}:{action}:{email}"

    @classmethod
    def _send_time_key(cls, action, email):
        """发送时间 Redis key"""
        return f"{cls.CODE_PREFIX}:send_time:{action}:{email}"

    @classmethod
    def _is_test_email(cls, email):
        """判断是否为假邮箱：测试环境全部为 True，开发环境匹配后缀列表"""
        import sys
        if 'test' in sys.argv:
            return True
        suffixes = getattr(settings, 'EMAIL_TEST_SUFFIXES', [])
        email_lower = email.lower()
        return any(email_lower.endswith(s.lower()) for s in suffixes)

    @classmethod
    def send_code(cls, action, email):
        """
        发送验证码

        Args:
            action: 场景（register / login / reset）
            email: 邮箱地址

        Returns:
            tuple: (success: bool, msg: str)
        """
        con = cls._get_con()
        send_time_key = cls._send_time_key(action, email)

        # 检查重发间隔
        if con.exists(send_time_key):
            return False, "验证码已发送，请60秒后再试"

        is_test = cls._is_test_email(email)

        # 生成验证码
        smtp_enabled = getattr(settings, 'EMAIL_SMTP_ENABLED', True)
        if is_test or not smtp_enabled:
            code = cls.TEST_CODE
        else:
            code = ''.join(random.choices(string.digits, k=cls.CODE_LENGTH))

        # 存入 Redis
        code_key = cls._key(action, email)
        pipe = con.pipeline()
        pipe.setex(code_key, cls.CODE_TTL, code)
        pipe.setex(send_time_key, cls.RESEND_INTERVAL, int(datetime.datetime.now().timestamp()))
        pipe.execute()

        # 假邮箱或 SMTP 未启用时不实际发送
        if is_test or not smtp_enabled:
            logger.info("验证码（未发邮件）: email={}, code={}, smtp_enabled={}", email, code, smtp_enabled)
            return True, "验证码已发送"

        # 真实发送邮件
        subject_map = {
            'register': 'ICube 注册验证码',
            'login': 'ICube 登录验证码',
            'reset': 'ICube 重置密码验证码',
        }
        subject = subject_map.get(action, 'ICube 验证码')
        message = f"您的验证码是：{code}，5分钟内有效。如非本人操作请忽略此邮件。"

        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
            logger.info("验证码邮件已发送: email={}, action={}", email, action)
            return True, "验证码已发送"
        except Exception as exc:
            logger.error("验证码邮件发送失败: email={}, error={}", email, str(exc))
            # 发送失败时清除 Redis 中的验证码和发送时间
            con.delete(code_key, send_time_key)
            return False, "验证码发送失败，请稍后重试"

    @classmethod
    def verify_code(cls, action, email, code):
        """
        验证码校验

        Args:
            action: 场景（register / login / reset）
            email: 邮箱地址
            code: 用户输入的验证码

        Returns:
            tuple: (valid: bool, msg: str)
        """
        con = cls._get_con()
        code_key = cls._key(action, email)
        stored_code = con.get(code_key)

        if stored_code is None:
            return False, "验证码已过期，请重新获取"

        # Redis 返回 bytes，统一转为字符串比较
        if isinstance(stored_code, bytes):
            stored_code = stored_code.decode()

        if stored_code != code:
            return False, "验证码错误"

        # 验证成功，删除验证码（一次性使用）
        con.delete(code_key)
        return True, "验证成功"


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

        当发生关注或取关动作时，从数据库重建 Redis 中的两个完整集合：
            - from_user_id 的 following 集合
            - to_user_id 的 followers 集合

        重建后再应用本次变更，兼容数据库更新前后两种调用顺序，避免缓存
        冷启动时把单次增量误当成完整关系集合。

        Args:
            from_user_id: 发起关注/取关的用户 ID
            to_user_id: 被关注/取关的用户 ID
            is_follow: True 表示关注，False 表示取关
        """
        con = cls._get_con()
        following_key = f"user:{from_user_id}:following"
        followers_key = f"user:{to_user_id}:followers"

        try:
            from_user = User.objects.get(id=from_user_id)
            following_ids = set(
                from_user.following.values_list('id', flat=True)
            )
        except User.DoesNotExist:
            following_ids = set()

        try:
            to_user = User.objects.get(id=to_user_id)
            followers_ids = set(
                to_user.followers.values_list('id', flat=True)
            )
        except User.DoesNotExist:
            followers_ids = set()

        if is_follow:
            following_ids.add(to_user_id)
            followers_ids.add(from_user_id)
        else:
            following_ids.discard(to_user_id)
            followers_ids.discard(from_user_id)

        pipe = con.pipeline()
        pipe.delete(following_key, followers_key)

        if following_ids:
            pipe.sadd(following_key, *following_ids)
        else:
            pipe.sadd(following_key, -1)
            pipe.expire(following_key, 600)

        if followers_ids:
            pipe.sadd(followers_key, *followers_ids)
        else:
            pipe.sadd(followers_key, -1)
            pipe.expire(followers_key, 600)

        pipe.execute()
