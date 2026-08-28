# accounts/urls.py
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import ProfileDetailView, UserView, AuthViewSet

# 使用 SimpleRouter
# trailing_slash=True（默认）：生成带尾部斜杠的路由，符合 REST 风格
# 生成的路由示例：
#   /users/login/
#   /users/logout/
#   /users/register/
router = SimpleRouter(trailing_slash=True)
router.register('profiles', ProfileDetailView, basename='profile')
# 身份认证相关(登录注册)
router.register('users', AuthViewSet, basename='auth')

urlpatterns = [
    # 当前登录用户信息 (操作当前 Session/Token 对应的资源)
    path('users/info/', UserView.as_view(), name='user-account'),

    # 引入路由器的 URL
    path('', include(router.urls)),
]
