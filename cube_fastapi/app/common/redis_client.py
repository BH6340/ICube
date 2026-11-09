"""
Redis 连接单例

所有 app 共享同一个 Redis 连接池。
各模块通过此模块获取连接，避免重复创建。
"""
from typing import Optional

import redis.asyncio as redis

from app.config import settings


class RedisClient:
    _instance: Optional[redis.Redis] = None

    @classmethod
    def get(cls) -> redis.Redis:
        if cls._instance is None:
            cls._instance = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,
                socket_connect_timeout=3,  # 连接超时 3 秒，避免无限等待
                socket_timeout=3,          # 读写超时 3 秒
                retry_on_timeout=False,    # 超时不重试，快速失败
            )
        return cls._instance

    @classmethod
    async def close(cls):
        if cls._instance:
            await cls._instance.close()
            cls._instance = None


# 便捷引用
redis_client = RedisClient.get()
