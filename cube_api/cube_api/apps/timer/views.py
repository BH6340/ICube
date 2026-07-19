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
    queryset = TimerRecord.objects.all()
    serializer_class = TimerRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
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
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return APIResponse(data=serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return APIResponse(code=403, msg='无权删除该记录', status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(instance)
        return APIResponse(msg='删除成功')

    @action(detail=False, methods=['get'])
    def stats(self, request):
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