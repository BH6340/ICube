# -*- coding: utf-8 -*-
"""
计时器模块路由配置

定义计时记录的 API 路由：
    - 计时记录：/api/timer/records/
    - 统计接口：/api/timer/records/stats/
    - 趋势接口：/api/timer/records/trend/

设计特点：
    - **标准视图集路由**：使用 DefaultRouter 自动生成 CRUD 路由
    - **自定义动作路由**：stats 和 trend 通过 @action 装饰器自动注册
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TimerRecordViewSet

router = DefaultRouter()
router.register('records', TimerRecordViewSet, basename='timer-record')

urlpatterns = [
    path('', include(router.urls)),
]