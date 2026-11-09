"""
打乱公式 API 路由

公开接口，无需认证（游客也能获取打乱公式）。
"""
import asyncio
import uuid

from fastapi import APIRouter, Query

from app.common.response import success
from app.common.exceptions import BusinessError
from app.scramble.generator import generate_scramble, generate_scramble_batch
from app.scramble.cache import scramble_cache
from app.config import settings

router = APIRouter(prefix="/api/scramble", tags=["scramble"])

VALID_CUBE_TYPES = {"2x2", "3x3", "4x4", "5x5"}
MAX_BATCH_COUNT = 100


@router.get("/generate")
async def generate(
    cube_type: str = Query(..., description="魔方类型: 2x2/3x3/4x4/5x5"),
):
    """生成单个打乱公式

    - **cube_type**: 魔方类型
    - 返回: 单个打乱公式 + scramble_id
    """
    if cube_type not in VALID_CUBE_TYPES:
        raise BusinessError(f"不支持的魔方类型: {cube_type}")

    from_cache = False
    scramble = await scramble_cache.get_one(cube_type)

    if scramble is None:
        scramble = generate_scramble(cube_type)
        # 后台异步补充缓存
        asyncio.create_task(_refill_cache(cube_type))
    else:
        from_cache = True

    return success(data={
        "cube_type": cube_type,
        "scramble": scramble,
        "scramble_id": _gen_id(),
        "from_cache": from_cache,
    })


@router.get("/batch")
async def batch_generate(
    cube_type: str = Query(..., description="魔方类型"),
    count: int = Query(10, ge=1, le=MAX_BATCH_COUNT, description="数量，最大100"),
):
    """批量生成打乱公式

    - **cube_type**: 魔方类型
    - **count**: 数量，1~100
    """
    if cube_type not in VALID_CUBE_TYPES:
        raise BusinessError(f"不支持的魔方类型: {cube_type}")

    # 先从缓存取
    cached = await scramble_cache.get_batch(cube_type, count)
    from_cache = len(cached)

    # 不够的部分实时生成
    remaining = count - from_cache
    if remaining > 0:
        generated = generate_scramble_batch(cube_type, remaining)
        cached.extend(generated)
        # 后台补充缓存
        asyncio.create_task(_refill_cache(cube_type))

    return success(data={
        "cube_type": cube_type,
        "scrambles": cached,
        "count": len(cached),
        "from_cache": from_cache,
    })


async def _refill_cache(cube_type: str):
    """异步补充缓存池到 batch_size 水平"""
    current_size = await scramble_cache.pool_size(cube_type)
    if current_size >= settings.cache_batch_size:
        return
    need = settings.cache_batch_size - current_size
    scrambles = generate_scramble_batch(cube_type, need)
    await scramble_cache.refill(cube_type, scrambles)


def _gen_id() -> str:
    """生成打乱公式唯一 ID（16 位 hex）"""
    return uuid.uuid4().hex[:16]
