from rest_framework.response import Response
from rest_framework import status as http_status


class APIResponse(Response):
    def __init__(self, code=100, msg='请求成功', status=200, headers={}, **kwargs):
        data = {'code': code, 'msg': msg}
        if kwargs:
            data.update(kwargs)
        super().__init__(data=data, status=status, headers=headers)


class PaginatedResponse(APIResponse):
    """
    分页响应专用类

    输出格式：
    {
        "code": 0,
        "msg": "success",
        "data": {
            "count": 100,
            "next": "http://.../page=2",
            "previous": null,
            "results": [...]
        }
    }
    """

    def __init__(self, paginator, page_data, code=100, msg="success", status=http_status.HTTP_200_OK):
        """
        Args:
            paginator: DRF 分页器实例
            page_data: 序列化后的数据列表
            code: 业务状态码
            msg: 消息
            status: HTTP 状态码
        """
        data = {
            "count": paginator.page.paginator.count if hasattr(paginator, 'page') else 0,
            "next": paginator.get_next_link() if hasattr(paginator, 'get_next_link') else None,
            "previous": paginator.get_previous_link() if hasattr(paginator, 'get_previous_link') else None,
            "results": page_data
        }
        super().__init__(data=data, code=code, msg=msg, status=status)


class PageNumberPaginationResponse(APIResponse):
    """
    基于 PageNumberPagination 的分页响应
    """

    def __init__(self, page, page_data, code=100, msg="success", status=http_status.HTTP_200_OK):
        """
        Args:
            page: 分页后的 QuerySet 或列表
            page_data: 序列化后的数据
        """
        data = {
            "count": page.paginator.count if hasattr(page, 'paginator') else len(page),
            "next": page.next_page_number() if hasattr(page, 'has_next') and page.has_next() else None,
            "previous": page.previous_page_number() if hasattr(page, 'has_previous') and page.has_previous() else None,
            "results": page_data
        }
        super().__init__(data=data, code=code, msg=msg, status=status)
