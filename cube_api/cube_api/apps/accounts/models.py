# accounts/models.py
from __future__ import annotations
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django_redis import get_redis_connection


class UserManager(BaseUserManager):
    def create_user(
            self, email: str, password: str | None = None, **other_fields
    ) -> User:
        if not email:
            raise ValueError("必须设置电子邮箱字段")

        email = self.normalize_email(email)  # 标准化 email（统一小写域名部分）
        user = User(email=email, **other_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save()
        return user

    def create_superuser(self, email: str, password: str | None = None, **other_fields) -> User:
        other_fields.setdefault("is_staff", True)
        other_fields.setdefault("is_superuser", True)
        other_fields.setdefault("is_active", True)

        if not other_fields.get("is_staff") or not other_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_staff=True and is_superuser=True.")

        return self.create_user(email, password, **other_fields)


class User(AbstractUser):
    """
        自定义用户模型，使用 email 作为登录凭证
    """
    # 移除默认字段
    first_name = None
    last_name = None

    email = models.EmailField("Email Address", unique=True, db_index=True)
    username = models.CharField(
        max_length=60,
        db_index=True,
        unique=True,
        error_messages={
            'unique': "该用户名已被使用",
        }
    )
    bio = models.TextField(blank=True)
    image: str | None = models.URLField(null=True, blank=True)

    # 当定义 followers = models.ManyToManyField("self", ...) 时，
    # 由于数据库无法直接在单列里存多个 ID，Django 会自动创建一张中间关系表来处理“关注”逻辑。
    # 非对称关系 (symmetrical=False)：这决定了这张表的逻辑。
    # 如果 A 关注了 B，表中会插入 (from:A, to:B)。此时 B 并不自动关注 A，除非另外插入一条 (from:B, to:A)。
    followers = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="following"
    )

    # Django AbstractUser 模型中的核心配置变量
    # 定义了用户模型中用作唯一标识符的字段，
    # 当你使用 Django 的认证系统（如 authenticate() 函数）登录时，你必须提供 email 而不是 username
    USERNAME_FIELD = "email"
    # 告诉 Django 框架及其内置插件：“哪一个字段才是真正的邮箱字段？”
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        app_label = 'accounts'  # 明确指定所属的 app
        verbose_name = "用户"
        verbose_name_plural = "用户"
        ordering = ["-date_joined"]  # 按注册时间倒序

    def __str__(self) -> str:
        """在 admin 和 shell 中友好显示"""
        return self.email

    def get_full_name(self) -> str:
        return self.username  # 既然 first_name/last_name 始终是 None，直接返回用户名

    def get_short_name(self) -> str:
        return self.username

    # 定义 Redis Key 的辅助方法
    def _following_cache_key(self):
        return f"user:{self.id}:following"

    def _followers_cache_key(self):
        return f"user:{self.id}:followers"

    def follow(self, user: "User") -> None:
        """关注用户"""
        if user != self:
            # 1. 写入数据库
            self.following.add(user)

            # 2. 同步写入 Redis (由于 django-redis 封装，可以用 get_redis_connection("default") 获取原生 redis 客户端)
            con = get_redis_connection("default")
            # 自己的关注集合中加入对方 ID
            con.sadd(self._following_cache_key(), user.id)
            # 对方的粉丝集合中加入自己 ID
            con.sadd(user._followers_cache_key(), self.id)

    def unfollow(self, user: "User") -> None:
        """取消关注"""
        if user != self:
            # 1. 操作数据库
            self.following.remove(user)

            # 2. 同步移除 Redis
            con = get_redis_connection("default")
            con.srem(self._following_cache_key(), user.id)
            con.srem(user._followers_cache_key(), self.id)

    @property
    def followers_count(self) -> int:
        """粉丝数量"""
        con = get_redis_connection("default")
        key = self._followers_cache_key()
        # 如果 Redis 中存在该 Key，直接返回数量；否则从数据库算，并回写 Redis
        if con.exists(key):
            return con.scard(key)

        # 缓存重建（Lazy Load）
        followers_ids = list(self.followers.values_list('id', flat=True))
        if followers_ids:
            con.sadd(key, *followers_ids)
        return len(followers_ids)

    @property
    def following_count(self) -> int:
        """关注数量"""
        con = get_redis_connection("default")
        key = self._following_cache_key()
        if con.exists(key):
            return con.scard(key)

        following_ids = list(self.following.values_list('id', flat=True))
        if following_ids:
            con.sadd(key, *following_ids)
        return len(following_ids)
