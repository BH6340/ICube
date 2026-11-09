"""
打乱公式 Redis 缓存

使用 List 结构预生成打乱公式，请求时从左侧弹出。
Key 格式: scramble:pool:{cube_type}
"""
from typing import List, Optional

from app.common.redis_client import RedisClient
from app.config import settings


class ScrambleCache:
    """打乱公式缓存池"""

    def __init__(self):
        self.enabled = settings.cache_enabled

    @property
    def _redis(self):
        return RedisClient.get()

    async def get_one(self, cube_type: str) -> Optional[str]:
        """从缓存池获取一个打乱公式"""
        if not self.enabled:
            return None
        try:
            return await self._redis.lpop(f"scramble:pool:{cube_type}")
        except Exception:
            return None

    async def get_batch(self, cube_type: str, count: int) -> List[str]:
        """从缓存池批量获取"""
        if not self.enabled:
            return []
        results = []
        for _ in range(count):
            try:
                item = await self._redis.lpop(f"scramble:pool:{cube_type}")
            except Exception:
                break
            if item is None:
                break
            results.append(item)
        return results

    async def refill(self, cube_type: str, scrambles: List[str]):
        """补充缓存池"""
        if not self.enabled or not scrambles:
            return
        try:
            key = f"scramble:pool:{cube_type}"
            await self._redis.rpush(key, *scrambles)
            await self._redis.expire(key, settings.cache_ttl)
        except Exception:
            pass

    async def pool_size(self, cube_type: str) -> int:
        """获取缓存池当前大小"""
        if not self.enabled:
            return 0
        try:
            return await self._redis.llen(f"scramble:pool:{cube_type}")
        except Exception:
            return 0


scramble_cache = ScrambleCache()
