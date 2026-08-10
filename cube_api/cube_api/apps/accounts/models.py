# -*- coding: utf-8 -*-
"""
用户认证模块模型

该模块定义了项目的自定义用户模型和关注关系，使用 email 作为登录凭证。

核心设计：
    1. 自定义 UserManager：封装用户创建逻辑
    2. 自定义 User 模型：继承 AbstractUser，使用 email 作为唯一标识
    3. 关注关系：通过 ManyToManyField 自关联实现，支持 Redis 缓存同步

缓存策略：
    - 关注/粉丝关系同时写入数据库和 Redis
    - 使用 Redis Set 存储关注和粉丝 ID 集合
    - 支持懒加载重建：缓存未命中时从数据库查询并回写 Redis
    - 使用 -1 占位符防止缓存穿透（空集合场景）
"""
from __future__ import annotations
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django_redis import get_redis_connection


class UserManager(BaseUserManager):
    """
    自定义用户管理器

    封装用户创建逻辑，确保 email 是必需字段，并提供创建超级用户的方法。

    设计原因：
        Django 默认的 UserManager 以 username 为登录凭证，
        本项目使用 email 作为登录凭证，需要自定义管理器。
    """

    def create_user(
            self, email: str, password: str | None = None, **other_fields
    ) -> User:
        """
        创建普通用户

        Args:
            email: 用户邮箱（必需）
            password: 用户密码（可选，不传则设置为不可用密码）
            **other_fields: 其他字段（如 username、bio 等）

        Returns:
            创建的 User 对象

        Raises:
            ValueError: 未提供 email 时抛出
        """
        if not email:
            raise ValueError("必须设置电子邮箱字段")

        # 标准化 email：统一域名部分为小写
        # 例如：Test@Example.COM -> test@example.com
        email = self.normalize_email(email)
        user = User(email=email, **other_fields)

        # 设置密码
        if password:
            user.set_password(password)
        else:
            # 无密码时设置为不可用密码（用于第三方登录等场景）
            user.set_unusable_password()

        user.save()
        return user

    def create_superuser(self, email: str, password: str | None = None, **other_fields) -> User:
        """
        创建超级用户

        Args:
            email: 超级用户邮箱（必需）
            password: 超级用户密码（可选）
            **other_fields: 其他字段

        Returns:
            创建的超级用户对象

        Raises:
            ValueError: is_staff 或 is_superuser 不为 True 时抛出
        """
        # 设置超级用户必需的字段
        other_fields.setdefault("is_staff", True)
        other_fields.setdefault("is_superuser", True)
        other_fields.setdefault("is_active", True)

        # 验证超级用户权限
        if not other_fields.get("is_staff") or not other_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_staff=True and is_superuser=True.")

        # 复用 create_user 方法创建超级用户
        return self.create_user(email, password, **other_fields)


class User(AbstractUser):
    """
    自定义用户模型，使用 email 作为登录凭证

    继承自 Django 的 AbstractUser，移除了 first_name/last_name 字段，
    添加了 bio（个人简介）和 image（头像）字段。

    设计原因：
        1. 使用 email 作为唯一标识，更符合现代 Web 应用习惯
        2. 保留 username 作为显示名称，增强用户体验
        3. 支持关注关系（通过 ManyToManyField 自关联实现）

    认证配置：
        - USERNAME_FIELD = "email": 使用 email 作为登录用户名
        - EMAIL_FIELD = "email": 指定 email 字段用于邮件发送
        - REQUIRED_FIELDS = []: 不需要额外的必需字段
    """

    # 移除默认的 first_name 和 last_name 字段（项目中不需要）
    first_name = None
    last_name = None

    # 用户邮箱（唯一，建立索引）
    email = models.EmailField("Email Address", unique=True, db_index=True)

    # 用户名（唯一，建立索引）
    username = models.CharField(
        max_length=60,
        db_index=True,
        unique=True,
        validators=[
            UnicodeUsernameValidator(
                message="用户名只能包含字母、数字和 @/./+/-/_ 字符"
            )
        ],
        error_messages={
            'unique': "该用户名已被使用",
        }
    )

    # 个人简介（可选）
    bio = models.TextField(blank=True)

    # 头像（可选，上传路径：avatars/）
    image = models.ImageField(
        '头像',
        upload_to='avatars/',
        null=True,
        blank=True
    )

    # ==================== 关注关系 ====================

    # 关注关系使用 ManyToManyField 自关联实现
    # symmetrical=False：非对称关系（A 关注 B 不代表 B 关注 A）
    # related_name="following"：反向查询名为 following（获取用户关注的人）
    # Django 会自动创建中间表：accounts_user_followers
    followers = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="following"
    )

    # ==================== 认证配置 ====================

    # 定义登录时使用的唯一标识字段（使用 email 而非 username）
    USERNAME_FIELD = "email"

    # 指定邮箱字段（用于 Django 内置的邮件功能）
    EMAIL_FIELD = "email"

    # 创建超级用户时不需要额外的必需字段
    REQUIRED_FIELDS = []

    # 使用自定义的用户管理器
    objects = UserManager()

    class Meta:
        app_label = 'accounts'       # 明确指定所属应用
        verbose_name = "用户"        # 单数显示名称
        verbose_name_plural = "用户"  # 复数显示名称
        ordering = ["-date_joined"]  # 默认按注册时间倒序排列

    def __str__(self) -> str:
        """
        在 admin 和 shell 中友好显示用户信息
        """
        return self.email

    def get_full_name(self) -> str:
        """
        返回用户的全名（项目中使用 username）
        """
        return self.username

    def get_short_name(self) -> str:
        """
        返回用户的短名称（项目中使用 username）
        """
        return self.username

    # ==================== Redis 缓存辅助方法 ====================

    def _following_cache_key(self):
        """
        获取用户关注列表的 Redis 缓存键
        """
        return f"user:{self.id}:following"

    def _followers_cache_key(self):
        """
        获取用户粉丝列表的 Redis 缓存键
        """
        return f"user:{self.id}:followers"

    # ==================== 关注/取关操作 ====================

    def follow(self, user: "User") -> None:
        """
        关注用户

        同时写入数据库和 Redis，确保数据一致性。

        Args:
            user: 要关注的用户对象
        """
        # 防止关注自己
        if user != self:
            # 1. 写入数据库
            self.following.add(user)

            # 2. 同步写入 Redis
            # 使用 get_redis_connection 获取原生 Redis 客户端
            con = get_redis_connection("default")
            # 自己的关注集合中加入对方 ID
            con.sadd(self._following_cache_key(), user.id)
            # 对方的粉丝集合中加入自己 ID
            con.sadd(user._followers_cache_key(), self.id)

    def unfollow(self, user: "User") -> None:
        """
        取消关注用户

        同时从数据库和 Redis 移除，确保数据一致性。

        Args:
            user: 要取消关注的用户对象
        """
        # 防止取消关注自己
        if user != self:
            # 1. 从数据库移除关系
            self.following.remove(user)

            # 2. 同步从 Redis 移除
            con = get_redis_connection("default")
            con.srem(self._following_cache_key(), user.id)
            con.srem(user._followers_cache_key(), self.id)

    # ==================== 关注/粉丝数量统计 ====================

    @property
    def followers_count(self) -> int:
        """
        获取粉丝数量（带 Redis 缓存）

        缓存策略：
            1. 优先从 Redis 获取（O(1) 复杂度）
            2. 缓存未命中时从数据库查询并回写 Redis（懒加载）

        Returns:
            粉丝数量
        """
        con = get_redis_connection("default")
        key = self._followers_cache_key()

        # 如果 Redis 中存在该 Key，直接返回数量
        if con.exists(key):
            return con.scard(key)

        # 缓存重建（Lazy Load）
        followers_ids = list(self.followers.values_list('id', flat=True))
        if followers_ids:
            con.sadd(key, *followers_ids)
        return len(followers_ids)

    @property
    def following_count(self) -> int:
        """
        获取关注数量（带 Redis 缓存）

        缓存策略：与 followers_count 相同

        Returns:
            关注数量
        """
        con = get_redis_connection("default")
        key = self._following_cache_key()

        if con.exists(key):
            return con.scard(key)

        following_ids = list(self.following.values_list('id', flat=True))
        if following_ids:
            con.sadd(key, *following_ids)
        return len(following_ids)
