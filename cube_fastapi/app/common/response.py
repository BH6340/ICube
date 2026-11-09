"""
统一响应封装

与 Django 端的 APIResponse 格式保持一致：
{ code, msg, data }
code=100 表示成功，前端拦截器按此判断。
"""
from typing import Any

from fastapi.responses import JSONResponse


def api_response(
    code: int = 100,
    msg: str = "请求成功",
    data: Any = None,
    status_code: int = 200,
) -> JSONResponse:
    """
    生成统一格式的 JSON 响应

    Args:
        code: 业务状态码，100=成功
        msg: 响应消息
        data: 业务数据
        status_code: HTTP 状态码

    Returns:
        JSONResponse 对象
    """
    content = {"code": code, "msg": msg}
    if data is not None:
        content["data"] = data
    return JSONResponse(content=content, status_code=status_code)


def success(data: Any = None, msg: str = "请求成功") -> JSONResponse:
    """成功响应快捷函数"""
    return api_response(code=100, msg=msg, data=data, status_code=200)


def bad_request(msg: str = "参数错误") -> JSONResponse:
    """参数错误快捷函数"""
    return api_response(code=400, msg=msg, status_code=400)


def unauthorized(msg: str = "未授权") -> JSONResponse:
    """未授权快捷函数"""
    return api_response(code=401, msg=msg, status_code=401)


def forbidden(msg: str = "权限不足") -> JSONResponse:
    """权限不足快捷函数"""
    return api_response(code=403, msg=msg, status_code=403)


def not_found(msg: str = "资源不存在") -> JSONResponse:
    """资源不存在快捷函数"""
    return api_response(code=404, msg=msg, status_code=404)


def server_error(msg: str = "系统开小差了，请稍后再试") -> JSONResponse:
    """系统错误快捷函数（不暴露内部细节）"""
    return api_response(code=999, msg=msg, status_code=500)


def business_error(msg: str = "业务错误", code: int = 998) -> JSONResponse:
    """业务逻辑错误快捷函数"""
    return api_response(code=code, msg=msg, status_code=400)
