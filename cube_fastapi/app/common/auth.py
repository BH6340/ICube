"""
JWT 认证依赖

与 Django 共享同一套 JWT 密钥和 Redis 黑名单。
使用 FastAPI Depends 方式注入，灵活控制每个路由的认证要求。

提供两个依赖：
- get_current_user: 返回用户或 None（匿名请求不报错，用于公开接口）
- require_auth: 必须登录，否则返回 401
"""
from typing import Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger

from app.config import settings
from app.common.redis_client import RedisClient


# auto_error=False：没有 Authorization 头时不抛异常，返回 None
# 这样匿名请求也能通过，由路由自己决定是否需要登录
security = HTTPBearer(
    scheme_name=settings.jwt_auth_header_type,
    auto_error=False,
)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    获取当前登录用户（匿名返回 None，不抛异常）

    Returns:
        {"user_id": int, "email": str} 或 None
    """
    if not credentials:
        return None

    # 验证 scheme（不区分大小写）
    if credentials.scheme.lower() != settings.jwt_auth_header_type.lower():
        return None

    token = credentials.credentials
    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as e:
        logger.debug(f"JWT decode failed: {e}")
        return None

    # 检查黑名单（与 Django 共用 key 格式）
    jti = payload.get("jti")
    if jti:
        redis = RedisClient.get()
        blacklist_key = f"{settings.jwt_blacklist_prefix}{jti}"
        try:
            if await redis.exists(blacklist_key):
                logger.warning(f"JWT in blacklist: jti={jti}")
                return None
        except Exception as e:
            logger.error(f"Redis blacklist check failed: {e}")
            # Redis 挂了不影响认证，降级放行
            pass

    user_id = payload.get("user_id")
    if not user_id:
        return None

    return {
        "user_id": user_id,
        "email": payload.get("email", ""),
    }


async def require_auth(
    user: Optional[dict] = Depends(get_current_user),
) -> dict:
    """
    必须登录的依赖

    Raises:
        HTTPException(401): 未登录或 Token 无效
    """
    if not user:
        raise HTTPException(
            status_code=401,
            detail="请先登录",
            headers={"WWW-Authenticate": settings.jwt_auth_header_type},
        )
    return user
