"""
配置管理

直接从环境变量读取，前缀 FASTAPI_。
不用 pydantic-settings 是为了减少依赖，cube_api 环境已装的包足够用。
"""
import os


def _get_bool(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes", "on")


def _get_int(name: str, default: int = 0) -> int:
    val = os.environ.get(name)
    if val is None or val == "":
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


class Settings:
    # Redis
    redis_host: str = os.environ.get("FASTAPI_REDIS_HOST", "redis")
    redis_port: int = _get_int("FASTAPI_REDIS_PORT", 6379)
    redis_db: int = _get_int("FASTAPI_REDIS_DB", 1)
    cache_enabled: bool = _get_bool("FASTAPI_CACHE_ENABLED", True)
    cache_batch_size: int = _get_int("FASTAPI_CACHE_BATCH_SIZE", 50)
    cache_ttl: int = _get_int("FASTAPI_CACHE_TTL", 3600)

    # JWT（与 Django 共享同一套）
    jwt_secret_key: str = os.environ.get("FASTAPI_JWT_SECRET_KEY", "change-me-in-production")
    jwt_algorithm: str = os.environ.get("FASTAPI_JWT_ALGORITHM", "HS256")
    jwt_auth_header_type: str = os.environ.get("FASTAPI_JWT_AUTH_HEADER_TYPE", "Token")
    # 黑名单 key 前缀，与 Django 对齐
    jwt_blacklist_prefix: str = os.environ.get("FASTAPI_JWT_BLACKLIST_PREFIX", "token_blacklist_")

    # 环境
    env: str = os.environ.get("FASTAPI_ENV", "dev")  # dev / prod


settings = Settings()
