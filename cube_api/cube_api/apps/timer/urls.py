from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TimerRecordViewSet

router = DefaultRouter()
router.register('records', TimerRecordViewSet, basename='timer-record')

urlpatterns = [
    path('', include(router.urls)),
]