# forum/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CommentViewSet, PostViewSet, ReportViewSet, TagViewSet

router = DefaultRouter()
router.register("posts", PostViewSet, basename="post")
router.register("comments", CommentViewSet, basename="comment")
router.register("tags", TagViewSet, basename="tag")
router.register("reports", ReportViewSet, basename="report")

urlpatterns = [
    path("", include(router.urls)),
]
