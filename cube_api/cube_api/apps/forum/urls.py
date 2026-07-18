# forum/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet, CommentViewSet, TagViewSet, ReportViewSet

router = DefaultRouter()
router.register('posts', PostViewSet, basename='post')
router.register('comments', CommentViewSet, basename='comment')
router.register('tags', TagViewSet, basename='tag')
router.register('reports', ReportViewSet, basename='report')

urlpatterns = [
    path('', include(router.urls)),
]
