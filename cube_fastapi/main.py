from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.common.exceptions import (
    BusinessError,
    business_error_handler,
    validation_error_handler,
    general_exception_handler,
)
from app.common.middleware import request_id_middleware, access_log_middleware
from app.common.redis_client import RedisClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    logger.info(f"ICube FastAPI starting in {settings.env} mode")
    if settings.cache_enabled:
        try:
            redis = RedisClient.get()
            await redis.ping()
            logger.info("Redis connected")
            # 预热打乱公式缓存
            from app.scramble.generator import generate_scramble_batch
            from app.scramble.cache import scramble_cache
            for ct in ["2x2", "3x3", "4x4", "5x5"]:
                scrambles = generate_scramble_batch(ct, settings.cache_batch_size)
                await scramble_cache.refill(ct, scrambles)
            logger.info("Scramble cache warmed up")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            # Redis 不可用时自动关闭缓存，避免每个请求都尝试连接导致超时
            settings.cache_enabled = False
            from app.scramble.cache import scramble_cache
            scramble_cache.enabled = False
            logger.warning("Cache disabled due to Redis unavailable")
    yield
    # 关闭时
    await RedisClient.close()
    logger.info("ICube FastAPI shutdown")


app = FastAPI(
    title="ICube FastAPI",
    version="0.1.0",
    lifespan=lifespan,
)

# ---- 中间件（注意：先注册的在外层，后注册的在内层） ----
# 1. Request ID（最外层，保证所有日志都有 request_id）
app.middleware("http")(request_id_middleware)
# 2. Access Log
app.middleware("http")(access_log_middleware)
# 3. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- 异常处理器 ----
app.add_exception_handler(BusinessError, business_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, general_exception_handler)


# ---- 健康检查 ----
@app.get("/api/scramble/health")
async def health_check():
    redis_size = {}
    if settings.cache_enabled:
        try:
            redis = RedisClient.get()
            for ct in ["2x2", "3x3", "4x4", "5x5"]:
                size = await redis.llen(f"scramble:pool:{ct}")
                redis_size[ct] = size
        except Exception:
            redis_size = {"error": "redis unavailable"}

    return {
        "code": 100,
        "msg": "ok",
        "data": {
            "status": "ok",
            "env": settings.env,
            "cache_enabled": settings.cache_enabled,
            "pool_sizes": redis_size,
        },
    }


# ---- 路由注册 ----
from app.scramble.routes import router as scramble_router
app.include_router(scramble_router)
