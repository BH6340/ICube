"""
计时器模块服务层

封装 Redis 缓存操作，提供计时记录相关的缓存读写和失效能力。

缓存粒度：user_id + cube_type + method
缓存有效期：到当日 23:59:59 自然过期
"""

import fnmatch

from django.core.cache import cache
from django.utils import timezone


class TimerStatsCacheService:
    """
    计时记录缓存服务

    提供今日记录列表和今日统计的缓存读写，以及用户级缓存失效。
    """

    @staticmethod
    def _today_key(user_id, cube_type, method):
        """今日记录列表缓存 key"""
        date_str = timezone.now().date().isoformat()
        return f"timer:today:{user_id}:{cube_type}:{method}:{date_str}"

    @staticmethod
    def _stats_key(user_id, cube_type, method):
        """今日统计缓存 key"""
        date_str = timezone.now().date().isoformat()
        return f"timer:today_stats:{user_id}:{cube_type}:{method}:{date_str}"

    @staticmethod
    def _ttl_to_midnight():
        """计算到当日结束的秒数"""
        now = timezone.now()
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return int((end - now).total_seconds())

    @classmethod
    def get_today_records(cls, user_id, cube_type, method):
        """获取今日记录缓存"""
        key = cls._today_key(user_id, cube_type, method)
        return cache.get(key)

    @classmethod
    def set_today_records(cls, user_id, cube_type, method, records):
        """设置今日记录缓存"""
        key = cls._today_key(user_id, cube_type, method)
        cache.set(key, records, timeout=cls._ttl_to_midnight())

    @classmethod
    def get_today_stats(cls, user_id, cube_type, method):
        """获取今日统计缓存"""
        key = cls._stats_key(user_id, cube_type, method)
        return cache.get(key)

    @classmethod
    def set_today_stats(cls, user_id, cube_type, method, stats):
        """设置今日统计缓存"""
        key = cls._stats_key(user_id, cube_type, method)
        cache.set(key, stats, timeout=cls._ttl_to_midnight())

    @classmethod
    def _delete_pattern(cls, pattern):
        """
        按通配符删除缓存键

        Redis 后端使用原生 delete_pattern，LocMemCache 等后端遍历删除（测试用）。
        """
        if hasattr(cache, "delete_pattern"):
            cache.delete_pattern(pattern)
            return
        # 兼容不支持 delete_pattern 的后端（如 LocMemCache）
        if hasattr(cache, "_cache"):
            for full_key in list(cache._cache.keys()):
                # 提取原始 key（去掉前缀和版本号）
                # 默认 make_key 格式: prefix:version:raw_key
                parts = full_key.split(":", 2)
                raw_key = parts[-1] if len(parts) >= 3 else full_key
                if fnmatch.fnmatch(raw_key, pattern):
                    cache.delete(raw_key)

    @classmethod
    def invalidate_user_cache(cls, user_id):
        """
        失效用户所有 timer 相关缓存

        新增/删除记录时调用。用通配符删除所有匹配 key。
        """
        cls._delete_pattern(f"timer:today:{user_id}:*")
        cls._delete_pattern(f"timer:today_stats:{user_id}:*")
