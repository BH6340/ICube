from rest_framework.pagination import PageNumberPagination
from .common_response import APIResponse


class UnifiedPagination(PageNumberPagination):
    """
    统一分页器 - 自动使用 APIResponse 格式

    使用方式：
        在 settings.py 中设置：
        REST_FRAMEWORK = {
            'DEFAULT_PAGINATION_CLASS': 'utils.common_pagination.UnifiedPagination',
        }
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'

    def get_paginated_response(self, data):
        """
        重写分页响应，返回统一格式
        """
        return APIResponse(
            data={
                'count': self.page.paginator.count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'results': data
            }
        )

    def get_paginated_response_schema(self, schema):
        """
        OpenAPI 文档生成用
        """
        return {
            'type': 'object',
            'properties': {
                'code': {'type': 'integer', 'example': 0},
                'msg': {'type': 'string', 'example': 'success'},
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
    大数据量分页（每页 50 条）
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500


class SmallResultsSetPagination(UnifiedPagination):
    """
    小数据量分页（每页 10 条）
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50
