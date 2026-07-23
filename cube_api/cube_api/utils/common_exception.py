# -*- coding: utf-8 -*-
"""
统一异常处理模块

该模块提供项目的全局异常处理器，确保所有异常都能被捕获并返回统一格式的响应。

设计背景：
    - DRF 默认的异常处理只返回简单的错误信息，缺少结构化日志
    - 生产环境中需要屏蔽敏感的堆栈信息，同时记录详细日志用于排查
    - 需要区分业务错误（客户端问题）和系统错误（服务端问题）
    - 所有异常都应返回统一的 APIResponse 格式

核心函数：
    - common_exception_handler: 全局异常处理器，替换 DRF 默认的异常处理

处理逻辑：
    1. 提取请求上下文信息（用户、路径、方法、视图）
    2. 调用 DRF 原生异常处理器获取响应
    3. 如果是 DRF 已处理的异常（业务错误）：
       - 格式化错误消息
       - 记录 warning 级别的日志
       - 返回 code=998 的 APIResponse
    4. 如果是未捕获的异常（系统错误）：
       - 记录 error 级别的日志（包含堆栈）
       - 返回 code=999 的 APIResponse，屏蔽敏感信息
"""
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler as drf_exception_handler
from loguru import logger
from rest_framework import status

from .common_response import APIResponse


def common_exception_handler(exc, context):
    """
    统一异常处理器

    作为 DRF 的全局异常处理器，替换默认的 exception_handler。
    通过在 settings.py 中配置：
    REST_FRAMEWORK = {
        'EXCEPTION_HANDLER': 'utils.common_exception.common_exception_handler',
    }

    主要职责：
        1. 提取诊断信息：用户、请求路径、HTTP 方法、视图类名
        2. 区分业务错误和系统错误，分别记录不同级别的日志
        3. 格式化错误消息，使其更易读
        4. 屏蔽敏感堆栈信息，只返回友好的错误提示
        5. 统一使用 APIResponse 格式返回

    Args:
        exc: 捕获到的异常对象
        context: 异常上下文，包含 request、view 等信息

    Returns:
        APIResponse: 统一格式的异常响应
    """
    # 从上下文中提取请求和视图对象
    request = context.get('request')
    view = context.get('view')

    # 提取有价值的诊断信息，用于日志记录
    # 用户信息：优先获取 email，如果是匿名用户则显示 'Anonymous'
    user = getattr(request.user, 'email', 'Anonymous') if request else 'Anonymous'
    # 请求路径：便于定位问题接口
    path = request.path if request else 'Unknown'
    # HTTP 方法：GET/POST/PUT/DELETE 等
    method = request.method if request else 'N/A'
    # 视图类名：包含模块路径，便于定位代码位置
    view_name = f"{view.__class__.__module__}.{view.__class__.__name__}"

    # 调用 DRF 原生异常处理器，获取初步响应
    # DRF 会处理其内置异常（如 ValidationError、PermissionDenied 等）
    response = drf_exception_handler(exc, context)

    # --- 情况 A: DRF 已处理的异常（业务逻辑错误） ---
    # 这类异常通常是客户端行为导致的，如参数校验失败、权限不足等
    if response is not None:
        # 格式化错误消息，使其更易读
        if isinstance(response.data, dict):
            # 针对校验错误（ValidationError），格式为 {'field': ['error1', 'error2']}
            # 需要提取第一个字段的第一个错误信息
            if isinstance(exc, ValidationError):
                # 获取第一个字段名
                first_field = next(iter(response.data))
                # 获取该字段的错误信息（可能是列表或字符串）
                first_error = response.data[first_field]
                # 如果是列表，取第一个错误；否则直接使用
                msg = f"{first_field}: {first_error[0] if isinstance(first_error, list) else first_error}"
            else:
                # 其他字典类型错误，尝试获取 'detail' 字段，否则转为字符串
                msg = response.data.get('detail') or str(response.data)
        elif isinstance(response.data, list):
            # 列表类型错误，取第一个元素
            msg = response.data[0]
        else:
            # 其他类型，直接转为字符串
            msg = str(response.data)

        # 记录警告日志（业务错误使用 warning 级别）
        # 使用 logger.bind 添加结构化上下文信息，便于日志分析
        logger.bind(user=user, path=path, method=method, view=view_name).warning(
            f"Business Error | {msg}"
        )

        # 返回统一格式的业务错误响应，code=998 表示业务逻辑错误
        return APIResponse(code=998, msg=msg, status=response.status_code)

    # --- 情况 B: 系统级崩溃（未捕获的 Python 异常） ---
    # 这类异常是服务端代码问题，如数据库连接失败、代码逻辑错误等

    # 记录错误日志（使用 error 级别，会触发 loguru 的 backtrace 记录）
    # 详细记录异常信息，便于排查问题
    logger.bind(user=user, path=path, method=method, view=view_name).error(
        f"Internal Server Error | Detail: {str(exc)}"
    )
    # Loguru 的 diagnose=True 配置会在此处提供非常详细的堆栈跟踪信息
    # 这些信息只会出现在日志文件中，不会暴露给客户端

    # 返回统一格式的系统错误响应，code=999 表示系统内部错误
    # 注意：不要返回异常详情给客户端，只返回友好的错误提示
    return APIResponse(
        code=999,
        msg="系统开小差了，请稍后再试",
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )