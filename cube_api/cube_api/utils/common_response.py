# -*- coding: utf-8 -*-
"""
统一响应封装模块

该模块定义了项目的统一 API 响应格式，确保所有接口返回一致的数据结构。

设计背景：
    - DRF 默认的 Response 格式不够统一，缺少业务状态码
    - 前端需要统一的 code/message/data 结构来处理响应
    - 分页响应需要特殊处理，包含 count/next/previous/results 字段

核心类：
    - APIResponse: 通用响应类，支持自定义业务状态码和消息
    - PaginatedResponse: 分页响应专用类，适配 DRF 分页器
    - PageNumberPaginationResponse: 基于 PageNumberPagination 的分页响应

状态码约定：
    - 100: 请求成功（默认）
    - 400: 请求参数错误
    - 403: 权限不足
    - 404: 资源不存在
    - 998: 业务逻辑错误（客户端行为错误）
    - 999: 系统内部错误（服务端异常）
"""
from rest_framework.response import Response
from rest_framework import status as http_status


class APIResponse(Response):
    """
    统一 API 响应类

    继承自 DRF 的 Response，封装了统一的响应格式：
    {
        "code": 100,      // 业务状态码
        "msg": "success", // 响应消息
        "data": {...}     // 业务数据（可选，通过 kwargs 传入）
    }

    设计原因：
        1. 统一前后端交互协议，前端只需判断 code 即可知道请求状态
        2. 区分 HTTP 状态码和业务状态码：HTTP 状态码用于网络层面，业务状态码用于业务逻辑层面
        3. 支持灵活的附加数据，通过 **kwargs 动态添加字段

    Args:
        code: 业务状态码，默认为 100（成功）
        msg: 响应消息，默认为 '请求成功'
        status: HTTP 状态码，默认为 200
        headers: 响应头字典
        **kwargs: 额外的业务数据，会被合并到 data 字段中

    Examples:
        >>> APIResponse()
        {"code": 100, "msg": "请求成功"}
        
        >>> APIResponse(data={"user": {...}}, msg="登录成功")
        {"code": 100, "msg": "登录成功", "data": {"user": {...}}}
        
        >>> APIResponse(code=400, msg="参数错误")
        {"code": 400, "msg": "参数错误"}
        
        >>> APIResponse(code=999, msg="系统错误", status=500)
        {"code": 999, "msg": "系统错误"}  // HTTP 状态码为 500
    """

    def __init__(self, code=100, msg='请求成功', status=200, headers={}, **kwargs):
        # 构建响应数据结构
        data = {'code': code, 'msg': msg}
        # 将额外参数合并到 data 中
        if kwargs:
            data.update(kwargs)
        # 调用父类构造函数，传入封装后的数据
        super().__init__(data=data, status=status, headers=headers)


class PaginatedResponse(APIResponse):
    """
    分页响应专用类

    基于 APIResponse 封装，专门处理 DRF 分页器的响应数据。
    输出格式：
    {
        "code": 100,
        "msg": "success",
        "data": {
            "count": 100,              // 总记录数
            "next": "http://.../page=2", // 下一页链接（None 表示没有下一页）
            "previous": null,          // 上一页链接（None 表示没有上一页）
            "results": [...]           // 当前页数据列表
        }
    }

    设计原因：
        1. DRF 分页器默认返回的数据结构与项目统一格式不一致
        2. 需要将分页信息（count/next/previous）和数据列表（results）统一封装
        3. 兼容不同类型的分页器实现

    Args:
        paginator: DRF 分页器实例（如 PageNumberPagination、LimitOffsetPagination）
        page_data: 序列化后的数据列表
        code: 业务状态码，默认为 100
        msg: 响应消息，默认为 'success'
        status: HTTP 状态码，默认为 200
    """

    def __init__(self, paginator, page_data, code=100, msg="success", status=http_status.HTTP_200_OK):
        # 构建分页数据结构
        # 使用 hasattr 检查分页器类型，确保兼容性
        data = {
            "count": paginator.page.paginator.count if hasattr(paginator, 'page') else 0,
            "next": paginator.get_next_link() if hasattr(paginator, 'get_next_link') else None,
            "previous": paginator.get_previous_link() if hasattr(paginator, 'get_previous_link') else None,
            "results": page_data
        }
        # 调用父类构造函数
        super().__init__(data=data, code=code, msg=msg, status=status)


class PageNumberPaginationResponse(APIResponse):
    """
    基于 PageNumberPagination 的分页响应

    专门适配 DRF 的 PageNumberPagination 分页器，
    当直接使用 paginate_queryset 返回的 page 对象时使用。

    设计原因：
        某些场景下，代码直接操作分页后的 page 对象而不是分页器实例，
        此时需要通过 page 对象的方法获取分页信息。

    Args:
        page: 分页后的 Page 对象（由 PageNumberPagination.paginate_queryset 返回）
        page_data: 序列化后的数据列表
        code: 业务状态码，默认为 100
        msg: 响应消息，默认为 'success'
        status: HTTP 状态码，默认为 200
    """

    def __init__(self, page, page_data, code=100, msg="success", status=http_status.HTTP_200_OK):
        # 通过 page 对象获取分页信息
        # has_next() / has_previous() 方法判断是否存在下一页/上一页
        # next_page_number() / previous_page_number() 获取页码（不是完整链接）
        data = {
            "count": page.paginator.count if hasattr(page, 'paginator') else len(page),
            "next": page.next_page_number() if hasattr(page, 'has_next') and page.has_next() else None,
            "previous": page.previous_page_number() if hasattr(page, 'has_previous') and page.has_previous() else None,
            "results": page_data
        }
        super().__init__(data=data, code=code, msg=msg, status=status)
