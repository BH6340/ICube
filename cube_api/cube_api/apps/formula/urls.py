from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CubeCategoryViewSet,
    CubeStateViewSet,
    FormulaCollectionViewSet,
    FormulaTagViewSet,
    FormulaViewSet,
)

router = DefaultRouter()
router.register(r"categories", CubeCategoryViewSet, basename="formula-category")
router.register(r"states", CubeStateViewSet, basename="formula-state")
router.register(r"formulas", FormulaViewSet, basename="formula")
router.register(r"tags", FormulaTagViewSet, basename="formula-tag")
router.register(r"collections", FormulaCollectionViewSet, basename="formula-collection")

urlpatterns = [
    path("", include(router.urls)),
]
