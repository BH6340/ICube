"""
API 请求监控中间件

记录每个 /api/ 请求的方法、路径、状态码和耗时，写入 Loguru 日志。
供 check_api_errors.py 和 daily_report.py 解析。
"""

import time

from loguru import logger


class MonitoringMiddleware:
    """记录 /api/ 请求的耗时和状态码"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        start = time.monotonic()
        response = self.get_response(request)
        duration = time.monotonic() - start

        logger.info(
            "API_REQUEST method={} path={} status={} duration={:.3f}",
            request.method,
            request.path,
            response.status_code,
            duration,
        )

        if response.status_code >= 500:
            logger.error(
                "API_ERROR method={} path={} status={} duration={:.3f}",
                request.method,
                request.path,
                response.status_code,
                duration,
            )

        return response
