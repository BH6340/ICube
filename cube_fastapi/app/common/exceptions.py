"""
全局异常处理器

与 Django 端 common_exception_handler 对应：
- 业务错误 → code=998
- 系统错误 → code=999
- 参数校验错误 → code=998，格式化字段错误信息
"""
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger


class BusinessError(Exception):
    """业务逻辑异常（客户端问题）"""
    def __init__(self, message: str, code: int = 998):
        self.message = message
        self.code = code
        super().__init__(message)


async def business_error_handler(request: Request, exc: BusinessError) -> JSONResponse:
    """业务异常处理"""
    logger.bind(
        path=request.url.path,
        method=request.method,
    ).warning(f"Business Error | {exc.message}")
    return JSONResponse(
        status_code=400,
        content={"code": exc.code, "msg": exc.message},
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """请求参数校验错误处理"""
    errors = exc.errors()
    # 提取第一个错误的字段和消息
    if errors:
        first_err = errors[0]
        loc = first_err.get("loc", [])
        field = ".".join(str(x) for x in loc[1:]) if len(loc) > 1 else "参数"
        msg = first_err.get("msg", "参数错误")
        error_msg = f"{field}: {msg}"
    else:
        error_msg = "参数错误"

    logger.bind(
        path=request.url.path,
        method=request.method,
    ).warning(f"Validation Error | {error_msg}")

    return JSONResponse(
        status_code=400,
        content={"code": 998, "msg": error_msg},
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """全局未捕获异常处理（系统错误）"""
    logger.bind(
        path=request.url.path,
        method=request.method,
    ).error(f"Internal Server Error | {type(exc).__name__}: {exc!s}")
    return JSONResponse(
        status_code=500,
        content={"code": 999, "msg": "系统开小差了，请稍后再试"},
    )
