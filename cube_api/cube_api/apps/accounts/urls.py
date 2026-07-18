# accounts/urls.py
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import ProfileDetailView, UserView, AuthViewSet

# 使用 SimpleRouter 减少不必要的根路由生成
# 保持 trailing_slash=False 与你的 profiles 逻辑一致
router = SimpleRouter(trailing_slash=False)
router.register('profiles', ProfileDetailView, basename='profile')
# 身份认证相关(登录注册)
router.register('users', AuthViewSet, basename='auth')

urlpatterns = [
    # 当前登录用户信息 (操作当前 Session/Token 对应的资源)
    # 建议加上斜杠，或者根据你的 API 规范统一去掉
    path('users/info', UserView.as_view(), name='user-account'),

    # 引入路由器的 URL
    path('', include(router.urls)),
]