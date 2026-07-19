from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import F

from .models import CubeCategory, CubeState, Formula, FormulaTag, FormulaCollection
from .serializers import (
    CubeCategorySerializer, CubeStateSerializer, FormulaSerializer,
    FormulaListSerializer, FormulaTagSerializer, FormulaMatchSerializer
)
from .permissions import IsAdminOrReadOnly, IsAdminOrCustomCreator
from .services import FormulaMatchService
from .filters import FormulaFilter
from utils.common_response import APIResponse


class CubeCategoryViewSet(viewsets.ModelViewSet):
    queryset = CubeCategory.objects.all()
    serializer_class = CubeCategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'method', 'phase']
    ordering_fields = ['order', 'method', 'sort_order']
    ordering = ['order', 'method', 'sort_order']
    filterset_fields = ['order', 'method', 'phase']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return APIResponse(data=serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return APIResponse(data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return APIResponse(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return APIResponse(msg="删除成功")


class CubeStateViewSet(viewsets.ModelViewSet):
    queryset = CubeState.objects.all()
    serializer_class = CubeStateSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name']
    filterset_fields = ['category']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return APIResponse(data=serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return APIResponse(data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return APIResponse(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return APIResponse(msg="删除成功")
class FormulaViewSet(viewsets.ModelViewSet):
    queryset = Formula.objects.select_related('category', 'target_state').prefetch_related('tag_relations__tag')
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminOrCustomCreator]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'notation', 'description']
    ordering_fields = ['category', 'difficulty', 'created_at', 'view_count']
    ordering = ['category', 'name']
    filterset_class = FormulaFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return FormulaListSerializer
        return FormulaSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return APIResponse(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Formula.objects.filter(id=instance.id).update(view_count=F('view_count') + 1)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance, context={'request': request})
        return APIResponse(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return APIResponse(data=serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return APIResponse(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return APIResponse(msg="删除成功")

    @extend_schema(
        summary="状态匹配",
        description="根据用户当前魔方状态匹配适用的公式",
        request=FormulaMatchSerializer,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'formulas': {'type': 'array', 'description': '匹配的公式列表'}
                }
            }
        }
    )
    @action(detail=False, methods=['POST'], permission_classes=[IsAuthenticated])
    def match(self, request):
        serializer = FormulaMatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        matched_formulas = FormulaMatchService.match_formulas(serializer.validated_data['state_definition'])
        formula_serializer = FormulaListSerializer(matched_formulas, many=True, context={'request': request})

        return APIResponse(formulas=formula_serializer.data)

    @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticated])
    def my_custom(self, request):
        formulas = self.get_queryset().filter(is_custom=True, created_by=request.user)
        page = self.paginate_queryset(formulas)

        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(formulas, many=True, context={'request': request})
        return APIResponse(data=serializer.data)


class FormulaTagViewSet(viewsets.ModelViewSet):
    queryset = FormulaTag.objects.all()
    serializer_class = FormulaTagSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return APIResponse(data=serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return APIResponse(data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return APIResponse(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return APIResponse(msg="删除成功")


class FormulaCollectionViewSet(viewsets.ModelViewSet):
    queryset = FormulaCollection.objects.select_related('formula', 'user')
    serializer_class = FormulaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['formula__name', 'formula__notation']
    ordering_fields = ['formula__difficulty', 'formula__name']
    ordering = ['formula__name']

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(formula__category_id=category)

        difficulty = request.query_params.get('difficulty')
        if difficulty:
            difficulty_values = difficulty.split(',')
            queryset = queryset.filter(formula__difficulty__in=difficulty_values)

        ordering = request.query_params.get('ordering')
        if ordering:
            queryset = queryset.order_by(ordering.replace('difficulty', 'formula__difficulty'))

        formulas = [item.formula for item in queryset]
        page = self.paginate_queryset(formulas)

        if page is not None:
            serializer = FormulaListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = FormulaListSerializer(formulas, many=True, context={'request': request})
        return APIResponse(data=serializer.data)

    def create(self, request, *args, **kwargs):
        formula_id = request.data.get('formula')
        if not formula_id:
            return APIResponse(code=400, msg="缺少公式ID", status=status.HTTP_400_BAD_REQUEST)

        try:
            formula = Formula.objects.get(id=formula_id)
        except Formula.DoesNotExist:
            return APIResponse(code=404, msg="公式不存在", status=status.HTTP_404_NOT_FOUND)

        collection, created = FormulaCollection.objects.get_or_create(user=request.user, formula=formula)

        if created:
            return APIResponse(msg="收藏成功", status=status.HTTP_201_CREATED)
        return APIResponse(msg="已收藏")

    def destroy(self, request, *args, **kwargs):
        formula_id = kwargs.get('pk')
        try:
            collection = FormulaCollection.objects.get(user=request.user, formula_id=formula_id)
            collection.delete()
            return APIResponse(msg="取消收藏成功")
        except FormulaCollection.DoesNotExist:
            return APIResponse(code=404, msg="收藏记录不存在", status=status.HTTP_404_NOT_FOUND)