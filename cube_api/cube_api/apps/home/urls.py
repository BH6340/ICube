from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.home.views import NavigationMenuViewSet

router = DefaultRouter()
router.register(r'navigation/menus', NavigationMenuViewSet, basename='nav-menus')

urlpatterns = [
    path('', include(router.urls)),
]