"""
计时器模块路由配置

定义计时记录和智能魔方设备的 API 路由：
    - 计时记录：/api/timer/records/
    - 统计接口：/api/timer/records/stats/
    - 趋势接口：/api/timer/records/trend/
    - 设备管理：/api/timer/devices/
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SmartCubeDeviceViewSet, TimerRecordViewSet

router = DefaultRouter()
router.register("records", TimerRecordViewSet, basename="timer-record")
router.register("devices", SmartCubeDeviceViewSet, basename="smart-cube-device")

urlpatterns = [
    path("", include(router.urls)),
]
