from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler as drf_exception_handler
from loguru import logger
from rest_framework import status

from .common_response import APIResponse

def common_exception_handler(exc, context):
    """
    统一异常处理：
    1. 结构化日志记录
    2. 屏蔽敏感堆栈信息
    3. 统一 APIResponse 格式输出
    """
    request=context.get('request')
    view=context.get('view')

    # 提取有价值的诊断信息
    user = getattr(request.user, 'email', 'Anonymous') if request else 'Anonymous'
    path = request.path if request else 'Unknown'
    method = request.method if request else 'N/A'
    view_name = f"{view.__class__.__module__}.{view.__class__.__name__}"

    # 3. 处理 DRF 响应
    response = drf_exception_handler(exc, context)

    if response is not None:
        # 格式化错误消息
        if isinstance(response.data, dict):
            # 针对校验错误 {'field': ['error']}，提取第一个错误详情
            if isinstance(exc, ValidationError):
                # 尝试获取第一个字段的第一个错误，例如 "email: 具有 Email Address 的 用户 已存在。"
                first_field = next(iter(response.data))
                first_error = response.data[first_field]
                msg = f"{first_field}: {first_error[0] if isinstance(first_error, list) else first_error}"
            else:
                msg = response.data.get('detail') or str(response.data)
        elif isinstance(response.data, list):
            msg = response.data[0]
        else:
            msg = str(response.data)

        # 记录警告日志（客户端行为错误通常用 warning）
        logger.bind(user=user, path=path, method=method, view=view_name).warning(
            f"Business Error | {msg}"
        )

        return APIResponse(code=998, msg=msg, status=response.status_code)

    # --- 情况 B: 系统级崩溃（未捕获的 Python 异常） ---

    # 记录错误日志（error 等级会触发 loguru 的 backtrace 记录）
    logger.bind(user=user, path=path, method=method, view=view_name).error(
        f"Internal Server Error | Detail: {str(exc)}"
    )
    # Loguru 的 diagnose=True 会在此处提供非常详细的堆栈
    return APIResponse(
        code=999,
        msg="系统开小差了，请稍后再试",
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )