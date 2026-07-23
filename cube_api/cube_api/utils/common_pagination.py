# -*- coding: utf-8 -*-
"""
统一分页器模块

该模块定义了项目的统一分页器，确保分页响应格式与项目的 APIResponse 保持一致。

设计背景：
    - DRF 默认的分页器返回格式与项目统一响应格式不一致
    - 需要将分页信息封装到 APIResponse 的 data 字段中
    - 不同业务场景需要不同的默认分页大小（如列表页用大分页，管理页用小分页）
    - 需要支持 OpenAPI 文档生成

核心类：
    - UnifiedPagination: 通用分页器，默认每页 20 条
    - LargeResultsSetPagination: 大数据量分页器，每页 50 条
    - SmallResultsSetPagination: 小数据量分页器，每页 10 条

使用方式：
    在 settings.py 中配置全局默认分页器：
    REST_FRAMEWORK = {
        'DEFAULT_PAGINATION_CLASS': 'utils.common_pagination.UnifiedPagination',
        'PAGE_SIZE': 20,
    }

    在视图集中使用特定分页器：
    class MyViewSet(viewsets.ModelViewSet):
        pagination_class = LargeResultsSetPagination
"""
from rest_framework.pagination import PageNumberPagination
from .common_response import APIResponse


class UnifiedPagination(PageNumberPagination):
    """
    统一分页器 - 自动使用 APIResponse 格式

    继承自 DRF 的 PageNumberPagination，重写分页响应方法，
    将分页信息封装到项目统一的 APIResponse 格式中。

    分页参数说明：
        - page: 当前页码，从 1 开始
        - page_size: 每页条数，默认 20，最大 100

    输出格式：
    {
        "code": 100,
        "msg": "请求成功",
        "data": {
            "count": 100,              // 总记录数
            "next": "?page=2",         // 下一页链接（None 表示没有下一页）
            "previous": null,          // 上一页链接（None 表示没有上一页）
            "results": [...]           // 当前页数据列表
        }
    }

    设计原因：
        1. DRF 默认的 PageNumberPagination 返回的是标准 Response，
           缺少项目统一的 code/message 结构
        2. 需要确保所有分页接口返回一致的格式，便于前端统一处理
        3. 通过重写 get_paginated_response_schema 支持 drf-spectacular 的文档生成
    """

    # 默认每页显示 20 条记录
    page_size = 20
    # 前端可通过 page_size 参数自定义每页条数
    page_size_query_param = 'page_size'
    # 限制最大每页条数，防止一次请求过多数据
    max_page_size = 100
    # 页码参数名
    page_query_param = 'page'

    def get_paginated_response(self, data):
        """
        重写分页响应方法，返回统一格式

        替代 DRF 默认的分页响应，使用 APIResponse 封装。

        Args:
            data: 序列化后的数据列表

        Returns:
            APIResponse: 包含分页信息的统一响应
        """
        return APIResponse(
            data={
                # 总记录数，用于前端计算总页数
                'count': self.page.paginator.count,
                # 下一页链接，如果没有下一页则为 None
                'next': self.get_next_link(),
                # 上一页链接，如果没有上一页则为 None
                'previous': self.get_previous_link(),
                # 当前页的数据列表
                'results': data
            }
        )

    def get_paginated_response_schema(self, schema):
        """
        重写分页响应的 OpenAPI Schema

        为 drf-spectacular 提供正确的响应格式定义，
        确保自动生成的 API 文档包含正确的字段描述和示例值。

        Args:
            schema: 当前视图序列化器的 Schema

        Returns:
            dict: OpenAPI Schema 定义
        """
        return {
            'type': 'object',
            'properties': {
                'code': {'type': 'integer', 'example': 100},
                'msg': {'type': 'string', 'example': '请求成功'},
                'data': {
                    'type': 'object',
                    'properties': {
                        'count': {'type': 'integer', 'example': 100},
                        'next': {'type': 'string', 'nullable': True, 'example': 'http://api.example.org/?page=4'},
                        'previous': {'type': 'string', 'nullable': True, 'example': 'http://api.example.org/?page=2'},
                        'results': schema,
                    }
                }
            }
        }


class LargeResultsSetPagination(UnifiedPagination):
    """
    大数据量分页器

    继承自 UnifiedPagination，仅修改默认分页参数。
    适用于数据量较大的列表页，如商品列表、帖子列表等。

    默认配置：
        - page_size: 50（每页显示 50 条）
        - max_page_size: 500（最大允许每页 500 条）
    """

    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500


class SmallResultsSetPagination(UnifiedPagination):
    """
    小数据量分页器

    继承自 UnifiedPagination，仅修改默认分页参数。
    适用于数据量较小的列表或管理后台，如订单列表、用户列表等。

    默认配置：
        - page_size: 10（每页显示 10 条）
        - max_page_size: 50（最大允许每页 50 条）
    """

    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50
