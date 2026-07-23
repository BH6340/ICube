# -*- coding: utf-8 -*-
"""
计时器模块序列化器

定义计时记录的数据序列化和验证逻辑，包括：
    - TimerRecordSerializer: 计时记录序列化（自动关联用户）
    - TimerStatsSerializer: 统计数据序列化
    - TimerTrendSerializer: 趋势数据序列化

设计特点：
    - **自动用户关联**：创建时自动将当前用户写入 validated_data
    - **只读字段**：id 和 created_at 为只读字段
    - **自定义序列化器**：TimerStatsSerializer 和 TimerTrendSerializer 用于统计接口
"""

from rest_framework import serializers
from .models import TimerRecord


class TimerRecordSerializer(serializers.ModelSerializer):
    """
    计时记录序列化器

    序列化计时记录数据，创建时自动关联当前用户。

    设计要点：
        - **自动用户关联**：create 方法中从 context 获取当前用户
        - **只读字段**：id 和 created_at 不允许修改
        - **毫秒精度**：time_ms 使用整数类型，保证精度
    """
    class Meta:
        model = TimerRecord
        fields = ('id', 'cube_type', 'method', 'time_ms', 'scramble', 'created_at')
        read_only_fields = ('id', 'created_at')

    def create(self, validated_data):
        """创建计时记录时自动关联当前用户"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TimerStatsSerializer(serializers.Serializer):
    """
    计时统计序列化器

    用于 stats 接口的返回数据序列化。
    """
    cube_type = serializers.CharField()
    method = serializers.CharField()
    total_count = serializers.IntegerField()
    best_time = serializers.IntegerField()
    avg_time = serializers.FloatField()


class TimerTrendSerializer(serializers.Serializer):
    """
    计时趋势序列化器

    用于 trend 接口的返回数据序列化。
    """
    date = serializers.DateField()
    times = serializers.ListField(child=serializers.IntegerField())
    avg_time = serializers.FloatField()