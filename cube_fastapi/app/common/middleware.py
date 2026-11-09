"""
中间件集合

- RequestIDMiddleware: 每个请求生成唯一 ID，贯穿日志
- AccessLogMiddleware: 请求访问日志（路径、方法、耗时、状态码）
"""
import time
import uuid
from contextvars import ContextVar

from fastapi import Request, Response
from loguru import logger

# 请求 ID 上下文变量，可在任意位置获取当前请求 ID
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


async def request_id_middleware(request: Request, call_next) -> Response:
    """请求 ID 中间件"""
    req_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:16])
    request_id_var.set(req_id)

    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response


async def access_log_middleware(request: Request, call_next) -> Response:
    """访问日志中间件"""
    start_time = time.time()
    method = request.method
    path = request.url.path
    req_id = request_id_var.get() or "-"

    # 记录请求
    logger.bind(
        request_id=req_id,
        method=method,
        path=path,
    ).debug(f"Request started: {method} {path}")

    response = await call_next(request)

    duration_ms = int((time.time() - start_time) * 1000)
    status_code = response.status_code

    # 记录响应
    logger.bind(
        request_id=req_id,
        method=method,
        path=path,
        status=status_code,
        duration_ms=duration_ms,
    ).info(f"{method} {path} → {status_code} ({duration_ms}ms)")

    return response
