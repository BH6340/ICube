from rest_framework import serializers
from .models import TimerRecord


class TimerRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimerRecord
        fields = ('id', 'cube_type', 'method', 'time_ms', 'scramble', 'created_at')
        read_only_fields = ('id', 'created_at')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TimerStatsSerializer(serializers.Serializer):
    cube_type = serializers.CharField()
    method = serializers.CharField()
    total_count = serializers.IntegerField()
    best_time = serializers.IntegerField()
    avg_time = serializers.FloatField()


class TimerTrendSerializer(serializers.Serializer):
    date = serializers.DateField()
    times = serializers.ListField(child=serializers.IntegerField())
    avg_time = serializers.FloatField()