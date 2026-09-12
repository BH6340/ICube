"""
计时器模块序列化器

定义计时记录和智能魔方设备的数据序列化和验证逻辑。
"""

from django.utils import timezone
from rest_framework import serializers

from .models import SmartCubeDevice, TimerRecord


class SmartCubeDeviceSerializer(serializers.ModelSerializer):
    """
    智能魔方设备序列化器
    """

    class Meta:
        model = SmartCubeDevice
        fields = ("id", "mac_address", "name", "last_connected_at", "is_active", "created_at")
        read_only_fields = ("id", "created_at")

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        user = validated_data["user"]
        mac = validated_data["mac_address"]
        obj, _created = SmartCubeDevice.objects.update_or_create(
            user=user,
            mac_address=mac,
            defaults={
                "name": validated_data.get("name", ""),
                "is_active": validated_data.get("is_active", True),
                "last_connected_at": timezone.now(),
            },
        )
        return obj


class TimerRecordSerializer(serializers.ModelSerializer):
    """
    计时记录序列化器

    设计要点：
        - **自动用户关联**：create 方法中从 context 获取当前用户
        - **只读字段**：id 和 created_at 不允许修改
        - **毫秒精度**：time_ms 使用整数类型，保证精度
    """

    device_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = TimerRecord
        fields = (
            "id",
            "cube_type",
            "method",
            "timing_mode",
            "time_ms",
            "scramble",
            "solve_sequence",
            "observation_time_ms",
            "move_count",
            "is_dnf",
            "device",
            "device_id",
            "created_at",
        )
        read_only_fields = ("id", "created_at", "device")
        depth = 0

    def create(self, validated_data):
        """创建计时记录时自动关联当前用户，并处理 device_id"""
        validated_data["user"] = self.context["request"].user
        device_id = validated_data.pop("device_id", None)
        if device_id:
            # 确保设备属于当前用户
            try:
                device = SmartCubeDevice.objects.get(id=device_id, user=validated_data["user"])
                validated_data["device"] = device
            except SmartCubeDevice.DoesNotExist:
                pass
        return super().create(validated_data)


class TimerStatsSerializer(serializers.Serializer):
    """
    计时统计序列化器

    用于 stats 接口的返回数据序列化。
    """

    cube_type = serializers.CharField()
    method = serializers.CharField()
    timing_mode = serializers.CharField(required=False)
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
