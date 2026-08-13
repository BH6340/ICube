# -*- coding: utf-8 -*-
"""
公式库视图层

该模块定义了公式库的 API 视图，处理魔方分类、状态、公式、标签和收藏的 CRUD 操作。

设计特点：
    - **多序列化器策略**：列表和详情使用不同的序列化器
    - **搜索和过滤**：支持关键词搜索、排序和分类过滤
    - **权限控制**：管理员可管理所有数据，普通用户可创建自定义公式
    - **公式匹配**：根据用户当前状态匹配适用公式
    - **收藏管理**：支持用户收藏和取消收藏公式
"""
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import F, Q
from django.db import models
from django.shortcuts import get_object_or_404

from .models import CubeCategory, CubeState, Formula, FormulaTag, FormulaCollection
from .serializers import (
    CubeCategorySerializer, CubeStateSerializer, FormulaSerializer,
    FormulaListSerializer, FormulaSimpleSerializer, FormulaTagSerializer, FormulaMatchSerializer
)
from .permissions import IsAdminOrReadOnly, IsAdminOrCustomCreator
from .services import FormulaMatchService
from .filters import FormulaFilter
from utils.common_pagination import UnifiedPagination
from utils.common_response import APIResponse

User = get_user_model()


class CubeCategoryViewSet(viewsets.ModelViewSet):
    """
    魔方分类视图集

    处理魔方分类的 CRUD 操作，支持用户自定义分类。

    权限控制：
        - 列表/详情：公开访问
        - 创建：需登录（自动标记为自定义分类）
        - 删除：仅创建者可删除自己的自定义分类

    查询逻辑：
        - 未登录：仅可见系统分类（created_by=None）
        - 已登录：可见系统分类 + 当前用户的自定义分类

    查询优化：
        - 支持按阶数、方法、阶段过滤
        - 支持关键词搜索（名称、方法、阶段）
    """
    serializer_class = CubeCategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'method', 'phase']
    ordering_fields = ['order', 'method', 'sort_order']
    ordering = ['order', 'method', 'sort_order']
    filterset_fields = ['order', 'method', 'phase']

    def get_permissions(self):
        """动态设置权限：列表和详情公开，其他操作需登录"""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """
        获取分类查询集

        未登录用户：仅系统分类
        已登录用户：系统分类 + 自己的自定义分类
        """
        user = self.request.user
        if user.is_authenticated:
            return CubeCategory.objects.filter(
                models.Q(created_by__isnull=True) |
                models.Q(created_by=user)
            )
        return CubeCategory.objects.filter(created_by__isnull=True)

    def list(self, request, *args, **kwargs):
        """
        获取魔方分类列表

        支持搜索、排序和过滤。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含分类列表的响应
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(data=serializer.data)

    def create(self, request, *args, **kwargs):
        """
        创建自定义魔方分类

        自动设置创建者和标记为自定义分类。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含创建的分类数据
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return APIResponse(data=serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        """创建时自动设置创建者和标记"""
        serializer.save(created_by=self.request.user, is_custom=True)

    def retrieve(self, request, *args, **kwargs):
        """
        获取单个魔方分类详情

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含分类详情的响应
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return APIResponse(data=serializer.data)

    def update(self, request, *args, **kwargs):
        """
        更新魔方分类

        仅允许创建者更新自己的自定义分类。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 更新后的分类数据
        """
        instance = self.get_object()
        # 权限检查：非自定义分类或非创建者不允许修改
        if not instance.is_custom or instance.created_by != request.user:
            raise PermissionDenied('无权修改此分类')
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return APIResponse(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        删除魔方分类

        仅允许创建者删除自己的自定义分类。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 删除成功的响应
        """
        instance = self.get_object()
        if not instance.is_custom or instance.created_by != request.user:
            raise PermissionDenied('无权删除此分类')
        instance.delete()
        return APIResponse(msg="删除成功")

    @action(detail=False, methods=['get'])
    def my_custom(self, request):
        """
        获取当前用户的自定义分类

        Returns:
            APIResponse: 包含当前用户自定义分类列表
        """
        categories = CubeCategory.objects.filter(
            created_by=request.user, is_custom=True
        )
        serializer = self.get_serializer(categories, many=True)
        return APIResponse(data={'categories': serializer.data})


class CubeStateViewSet(viewsets.ModelViewSet):
    """
    魔方状态视图集

    处理魔方状态的 CRUD 操作，支持搜索和过滤。

    权限控制：
        - 管理员：可创建、编辑、删除状态
        - 普通用户：只读

    查询优化：
        - 支持按名称搜索
        - 支持按分类过滤
    """
    queryset = CubeState.objects.all()
    serializer_class = CubeStateSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name']
    filterset_fields = ['category']

    def list(self, request, *args, **kwargs):
        """
        获取魔方状态列表

        支持搜索和过滤。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含状态列表的响应
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(data=serializer.data)

    def create(self, request, *args, **kwargs):
        """
        创建魔方状态

        只有管理员可以创建状态。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含创建的状态数据
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return APIResponse(data=serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        """
        获取单个魔方状态详情

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含状态详情的响应
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return APIResponse(data=serializer.data)

    def update(self, request, *args, **kwargs):
        """
        更新魔方状态

        只有管理员可以更新状态。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 更新后的状态数据
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return APIResponse(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        删除魔方状态

        只有管理员可以删除状态。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 删除成功的响应
        """
        instance = self.get_object()
        instance.delete()
        return APIResponse(msg="删除成功")
class FormulaViewSet(viewsets.ModelViewSet):
    """
    公式视图集

    处理公式的 CRUD 操作，支持搜索、过滤、排序和公式匹配。

    自定义动作：
        - match: 根据用户当前状态匹配适用公式
        - my_custom: 获取当前用户创建的自定义公式

    权限控制：
        - 管理员：可管理所有公式
        - 普通用户：可创建自定义公式，只能编辑/删除自己创建的自定义公式
        - 未登录用户：只读

    查询优化：
        - select_related: 预加载分类和目标状态
        - prefetch_related: 预加载标签关联
    """
    queryset = Formula.objects.select_related('category', 'target_state', 'created_by').prefetch_related('tag_relations__tag')
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminOrCustomCreator]
    pagination_class = UnifiedPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'notation', 'description', 'created_by__username', 'category__name']
    ordering_fields = ['category', 'difficulty', 'created_at', 'view_count']
    # 默认排序：分类 → 名称
    ordering = ['category', 'name']
    filterset_class = FormulaFilter

    def get_serializer_class(self):
        """
        动态选择序列化器

        根据不同动作选择合适的序列化器：
            - list: 轻量级序列化器（FormulaListSerializer）
            - 其他: 详情序列化器（FormulaSerializer）

        Returns:
            序列化器类
        """
        if self.action == 'list':
            return FormulaListSerializer
        return FormulaSerializer

    def list(self, request, *args, **kwargs):
        """
        获取公式列表

        支持搜索、过滤、排序和分页。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含公式列表的响应（带分页）
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return APIResponse(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        获取公式详情

        获取公式详情时自动增加浏览量。

        使用 F 表达式更新浏览量，避免并发更新问题。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含公式详情的响应
        """
        instance = self.get_object()
        # 使用 F 表达式原子递增浏览量
        Formula.objects.filter(id=instance.id).update(view_count=F('view_count') + 1)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance, context={'request': request})
        return APIResponse(data=serializer.data)

    def create(self, request, *args, **kwargs):
        """
        创建公式

        登录用户可创建公式，普通用户创建的公式自动标记为自定义公式。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含创建的公式数据
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return APIResponse(data=serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        更新公式

        只有管理员或公式创建者可以更新公式。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 更新后的公式数据
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return APIResponse(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        删除公式

        只有管理员或公式创建者可以删除公式。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 删除成功的响应
        """
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
        """
        根据用户当前状态匹配适用的公式

        用户提交当前魔方状态，系统返回匹配的公式列表。

        匹配策略：
            1. 前置状态匹配：直接比较用户状态与公式的前置状态
            2. 目标状态匹配：应用公式后比较结果状态与公式的目标状态

        Args:
            request: HTTP 请求对象（包含 state_definition）

        Returns:
            APIResponse: 包含匹配公式列表的响应
        """
        serializer = FormulaMatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        matched_formulas = FormulaMatchService.match_formulas(serializer.validated_data['state_definition'])
        formula_serializer = FormulaListSerializer(matched_formulas, many=True, context={'request': request})

        return APIResponse(formulas=formula_serializer.data)

    @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticated])
    def my_custom(self, request):
        """
        获取当前用户创建的自定义公式

        返回当前登录用户创建的所有自定义公式。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含自定义公式列表的响应（带分页）
        """
        formulas = self.get_queryset().filter(is_custom=True, created_by=request.user)
        page = self.paginate_queryset(formulas)

        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(formulas, many=True, context={'request': request})
        return APIResponse(data=serializer.data)

    @extend_schema(
        summary="获取公式作者列表",
        description="返回所有创建过公式的作者列表，用于筛选",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'authors': {'type': 'array', 'description': '作者列表'}
                }
            }
        }
    )
    @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticatedOrReadOnly])
    def authors(self, request):
        """
        获取公式作者列表

        返回所有创建过公式的用户列表，用于前端筛选器。

        查询策略：
            - 从 Formula 模型中提取 distinct 的 created_by
            - 排除空值（系统预设公式）

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含作者列表的响应
        """
        authors = Formula.objects.filter(created_by__isnull=False)\
            .values('created_by__id', 'created_by__username')\
            .distinct()

        author_list = [
            {'id': author['created_by__id'], 'username': author['created_by__username']}
            for author in authors
        ]

        return APIResponse(data={'authors': author_list})

    @extend_schema(
        summary="获取精简公式列表（帖子编辑器专用）",
        description="返回精简的公式列表，用于帖子编辑器选择公式插入",
        parameters=[
            OpenApiParameter(name='search', type=str, location='query', description='关键词搜索'),
            OpenApiParameter(name='category', type=int, location='query', description='分类ID'),
            OpenApiParameter(name='difficulty', type=int, location='query', description='难度等级'),
            OpenApiParameter(name='page', type=int, location='query', description='页码'),
            OpenApiParameter(name='page_size', type=int, location='query', description='每页数量')
        ],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'count': {'type': 'integer', 'description': '总数'},
                    'results': {'type': 'array', 'description': '公式列表'}
                }
            }
        }
    )
    @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticatedOrReadOnly])
    def simple_list(self, request):
        """
        获取精简公式列表（帖子编辑器专用）

        返回精简的公式列表，只包含必要字段，用于帖子编辑器选择公式插入。

        查询参数：
            - search: 关键词搜索（名称、记号）
            - category: 分类ID
            - difficulty: 难度等级
            - page: 页码
            - page_size: 每页数量

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含公式列表的响应（带分页）
        """
        queryset = Formula.objects.select_related('category').filter(is_custom=False)

        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search) | queryset.filter(notation__icontains=search)

        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)

        difficulty = request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = FormulaSimpleSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = FormulaSimpleSerializer(queryset, many=True, context={'request': request})
        return APIResponse(data=serializer.data)


class FormulaTagViewSet(viewsets.ModelViewSet):
    """
    公式标签视图集

    处理公式标签的 CRUD 操作，支持搜索。

    权限控制：
        - 管理员：可创建、编辑、删除标签
        - 普通用户：只读

    查询优化：
        - 支持按名称搜索
    """
    queryset = FormulaTag.objects.all()
    serializer_class = FormulaTagSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def list(self, request, *args, **kwargs):
        """
        获取公式标签列表

        支持搜索。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含标签列表的响应
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(data=serializer.data)

    def create(self, request, *args, **kwargs):
        """
        创建公式标签

        只有管理员可以创建标签。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含创建的标签数据
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return APIResponse(data=serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        """
        获取单个公式标签详情

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含标签详情的响应
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return APIResponse(data=serializer.data)

    def update(self, request, *args, **kwargs):
        """
        更新公式标签

        只有管理员可以更新标签。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 更新后的标签数据
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return APIResponse(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        删除公式标签

        只有管理员可以删除标签。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 删除成功的响应
        """
        instance = self.get_object()
        instance.delete()
        return APIResponse(msg="删除成功")


class FormulaCollectionViewSet(viewsets.ModelViewSet):
    """
    公式收藏视图集

    处理公式收藏的 CRUD 操作，支持搜索和过滤。

    权限控制：
        - 用户只能查看和管理自己的收藏
        - 需要登录

    查询优化：
        - select_related: 预加载公式和用户
        - 支持按分类、难度过滤
        - 支持按公式名称搜索

    特殊处理：
        - list 动作返回的是公式列表，而非收藏记录列表
        - create 动作支持幂等性（已收藏则返回已收藏）
        - destroy 动作通过公式ID删除收藏记录
    """
    queryset = FormulaCollection.objects.select_related('formula', 'user')
    serializer_class = FormulaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = UnifiedPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['formula__name', 'formula__notation']
    ordering_fields = ['formula__difficulty', 'formula__name']
    # 默认排序：按公式名称排序
    ordering = ['formula__name']

    def get_queryset(self):
        """
        获取当前用户的收藏记录

        覆盖父方法，只返回当前用户的收藏。

        Returns:
            QuerySet: 当前用户的收藏记录
        """
        return super().get_queryset().filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        """
        获取当前用户收藏的公式列表

        支持按分类、难度过滤和排序。

        查询参数：
            - category: 分类ID
            - difficulty: 难度等级（支持逗号分隔多个值）
            - ordering: 排序字段（difficulty 或 formula__name）

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含收藏公式列表的响应（带分页）
        """
        queryset = self.get_queryset()

        # 按分类过滤
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(formula__category_id=category)

        # 按难度过滤（支持多个难度）
        difficulty = request.query_params.get('difficulty')
        if difficulty:
            difficulty_values = difficulty.split(',')
            queryset = queryset.filter(formula__difficulty__in=difficulty_values)

        # 关键词搜索（公式名、记号、作者、分类名）
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(formula__name__icontains=search) |
                models.Q(formula__notation__icontains=search) |
                models.Q(formula__created_by__username__icontains=search) |
                models.Q(formula__category__name__icontains=search)
            )

        # 自定义排序
        ordering = request.query_params.get('ordering')
        if ordering:
            # 将 'difficulty' 替换为 'formula__difficulty'
            queryset = queryset.order_by(ordering.replace('difficulty', 'formula__difficulty'))

        # 提取公式对象列表
        formulas = [item.formula for item in queryset]
        page = self.paginate_queryset(formulas)

        if page is not None:
            serializer = FormulaListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = FormulaListSerializer(formulas, many=True, context={'request': request})
        return APIResponse(data=serializer.data)

    @action(
        detail=False,
        methods=['GET'],
        url_path=r'users/(?P<username>[^/]+)',
        permission_classes=[AllowAny],
    )
    def user_collections(self, request, username=None):
        """获取指定启用用户公开收藏的公式列表"""
        user = get_object_or_404(
            User,
            username=username,
            is_active=True,
        )
        collections = FormulaCollection.objects.filter(
            user=user,
        ).select_related(
            'formula__category',
            'formula__target_state',
            'formula__created_by',
        ).prefetch_related(
            'formula__tag_relations__tag',
        ).order_by('-created_at')

        page = self.paginate_queryset(collections)
        formulas = [item.formula for item in page]
        serializer = FormulaListSerializer(
            formulas,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        收藏公式

        支持幂等性：如果已收藏则返回"已收藏"，否则创建收藏记录。

        请求参数：
            - formula: 公式ID

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 收藏结果
        """
        formula_id = request.data.get('formula')
        if not formula_id:
            return APIResponse(code=400, msg="缺少公式ID", status=status.HTTP_400_BAD_REQUEST)

        try:
            formula = Formula.objects.get(id=formula_id)
        except Formula.DoesNotExist:
            return APIResponse(code=404, msg="公式不存在", status=status.HTTP_404_NOT_FOUND)

        # 使用 get_or_create 实现幂等性
        collection, created = FormulaCollection.objects.get_or_create(user=request.user, formula=formula)

        if created:
            return APIResponse(msg="收藏成功", status=status.HTTP_201_CREATED)
        return APIResponse(msg="已收藏")

    def destroy(self, request, *args, **kwargs):
        """
        取消收藏公式

        通过公式ID删除收藏记录。

        Args:
            request: HTTP 请求对象
            pk: 公式ID（通过URL传递）

        Returns:
            APIResponse: 取消收藏结果
        """
        formula_id = kwargs.get('pk')
        try:
            collection = FormulaCollection.objects.get(user=request.user, formula_id=formula_id)
            collection.delete()
            return APIResponse(msg="取消收藏成功")
        except FormulaCollection.DoesNotExist:
            return APIResponse(code=404, msg="收藏记录不存在", status=status.HTTP_404_NOT_FOUND)
