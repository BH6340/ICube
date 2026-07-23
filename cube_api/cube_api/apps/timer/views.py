# -*- coding: utf-8 -*-
"""
计时器模块视图集

提供计时记录的 CRUD 操作和统计接口，包括：
    - 计时记录列表/详情/创建/删除
    - stats: 分组统计（按魔方类型和还原方法）
    - trend: 趋势统计（按日期分组）

设计特点：
    - **权限控制**：用户只能查看和管理自己的计时记录
    - **多条件过滤**：支持按魔方类型、还原方法、日期范围过滤
    - **聚合查询**：使用 Django ORM 聚合函数计算最佳成绩和平均成绩
    - **趋势分析**：按日期分组的统计，支持自定义天数范围
"""

from django.db.models import Count, Min, Avg, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import TimerRecord
from .serializers import TimerRecordSerializer
from cube_api.utils.common_response import APIResponse


class TimerRecordViewSet(viewsets.ModelViewSet):
    """
    计时记录视图集

    处理计时记录的完整 CRUD 操作，以及统计和趋势分析接口。

    自定义动作：
        - stats: 获取分组统计信息（最佳成绩、平均成绩、记录数）
        - trend: 获取按日期分组的趋势统计

    过滤参数：
        - cube_type: 魔方类型（2x2/3x3/4x4/5x5/other）
        - method: 还原方法（layer/cfop/roux/zbll/other）
        - start_date: 开始日期（格式 YYYY-MM-DD）
        - end_date: 结束日期（格式 YYYY-MM-DD）
    """
    queryset = TimerRecord.objects.all()
    serializer_class = TimerRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        获取当前用户的计时记录，支持多条件过滤

        过滤参数：
            - cube_type: 魔方类型
            - method: 还原方法
            - start_date: 开始日期
            - end_date: 结束日期
        """
        queryset = self.queryset.filter(user=self.request.user)

        cube_type = self.request.query_params.get('cube_type')
        method = self.request.query_params.get('method')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if cube_type:
            queryset = queryset.filter(cube_type=cube_type)
        if method:
            queryset = queryset.filter(method=method)
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)

        return queryset

    def list(self, request, *args, **kwargs):
        """获取计时记录列表，支持分页"""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(data=serializer.data)

    def create(self, request, *args, **kwargs):
        """创建计时记录，自动关联当前用户"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return APIResponse(data=serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        """删除计时记录，验证权限"""
        instance = self.get_object()
        if instance.user != request.user:
            return APIResponse(code=403, msg='无权删除该记录', status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(instance)
        return APIResponse(msg='删除成功')

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        获取分组统计信息

        按魔方类型和还原方法分组，计算每组的：
            - total_count: 记录总数
            - best_time: 最佳成绩（最小时间）
            - avg_time: 平均成绩

        返回同时包含分组统计和总体统计。

        过滤参数：
            - cube_type: 魔方类型
            - method: 还原方法
        """
        queryset = self.get_queryset()

        cube_type = request.query_params.get('cube_type')
        method = request.query_params.get('method')

        if cube_type:
            queryset = queryset.filter(cube_type=cube_type)
        if method:
            queryset = queryset.filter(method=method)

        stats = queryset.values('cube_type', 'method').annotate(
            total_count=Count('id'),
            best_time=Min('time_ms'),
            avg_time=Avg('time_ms')
        ).order_by('cube_type', 'method')

        result = []
        for stat in stats:
            result.append({
                'cube_type': stat['cube_type'],
                'cube_type_label': dict(TimerRecord.CUBE_TYPE_CHOICES).get(stat['cube_type'], stat['cube_type']),
                'method': stat['method'],
                'method_label': dict(TimerRecord.METHOD_CHOICES).get(stat['method'], stat['method']),
                'total_count': stat['total_count'],
                'best_time': stat['best_time'],
                'avg_time': round(stat['avg_time'], 2) if stat['avg_time'] else 0
            })

        overall_stats = {
            'total_count': queryset.count(),
            'best_time': queryset.aggregate(Min('time_ms'))['time_ms__min'] or 0,
            'avg_time': round(queryset.aggregate(Avg('time_ms'))['time_ms__avg'], 2) if queryset.exists() else 0
        }

        return APIResponse(data={'group_stats': result, 'overall_stats': overall_stats})

    @action(detail=False, methods=['get'])
    def trend(self, request):
        """
        获取按日期分组的趋势统计

        按日期分组，计算每天的：
            - best_time: 当日最佳成绩
            - avg_time: 当日平均成绩

        参数：
            - days: 统计天数（默认 30 天）
            - cube_type: 魔方类型（可选）
            - method: 还原方法（可选）
        """
        queryset = self.get_queryset()

        cube_type = request.query_params.get('cube_type')
        method = request.query_params.get('method')

        if cube_type:
            queryset = queryset.filter(cube_type=cube_type)
        if method:
            queryset = queryset.filter(method=method)

        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timezone.timedelta(days=days)

        queryset = queryset.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)

        date_stats = queryset.values('created_at__date').annotate(
            times=Min('time_ms'),
            avg_time=Avg('time_ms')
        ).order_by('created_at__date')

        result = []
        for stat in date_stats:
            result.append({
                'date': stat['created_at__date'],
                'best_time': stat['times'],
                'avg_time': round(stat['avg_time'], 2) if stat['avg_time'] else 0
            })

        return APIResponse(data=result)