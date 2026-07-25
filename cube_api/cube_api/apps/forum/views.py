# -*- coding: utf-8 -*-
"""
论坛视图层

该模块定义了论坛的 API 视图，处理帖子、评论、标签和举报的 CRUD 操作。

设计特点：
    - **多序列化器策略**：列表和详情使用不同的序列化器
    - **搜索和过滤**：支持关键词搜索、排序和标签过滤
    - **权限控制**：登录用户可创建，只有作者可编辑/删除
    - **缓存策略**：浏览量使用 Redis 缓存，减少数据库压力
"""
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import F, Count

from .models import Post, Tag, Comment, Report, PostCollect, PostImage
from .serializers import (
    PostSerializer, PostListSerializer, PostCreateUpdateSerializer,
    TagSerializer, CommentSerializer, ReportSerializer, PostImageSerializer
)
from .services import PostCacheService, PostInteractionService, HotPostService
from utils.common_response import APIResponse
from utils.image_processor import process_image
from apps.accounts.permissions import IsOwnerOrReadOnly


class PostViewSet(viewsets.ModelViewSet):
    """
    帖子视图集

    处理帖子的 CRUD 操作，支持搜索、过滤、排序和互动功能。

    自定义动作：
        - like: 点赞帖子
        - collect: 收藏帖子
        - comments: 获取帖子评论
        - my_posts: 获取当前用户的帖子
        - collected: 获取当前用户收藏的帖子
        - hot: 获取热门帖子
        - upload_image: 上传图片

    查询优化：
        - select_related: 预加载作者信息
        - prefetch_related: 预加载标签和图片
        - 过滤已发布状态的帖子
    """

    # 查询集：只包含已发布的帖子，预加载相关数据
    queryset = Post.objects.filter(status='published').select_related('author').prefetch_related('tags', 'images')
    # 权限：登录用户可创建，只有作者可编辑/删除
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    # 过滤器：搜索、排序、标签过滤
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'view_count', 'like_count', 'comment_count', 'is_pinned', 'is_essence']
    # 默认排序：置顶优先 > 精华优先 > 最新发布优先
    ordering = ['-is_pinned', '-is_essence', '-created_at']
    filterset_fields = ['tags__name', 'is_pinned', 'is_essence', 'created_at']

    def get_serializer_class(self):
        """
        动态选择序列化器

        根据不同动作选择合适的序列化器：
            - list: 轻量级序列化器（PostListSerializer）
            - create/update/partial_update: 创建/更新序列化器（PostCreateUpdateSerializer）
            - 其他: 详情序列化器（PostSerializer）

        Returns:
            序列化器类
        """
        if self.action == 'list':
            return PostListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return PostCreateUpdateSerializer
        return PostSerializer

    def list(self, request, *args, **kwargs):
        """
        获取帖子列表

        支持关键词搜索、标签过滤、排序和热度排序。

        查询参数：
            - search: 关键词搜索（标题或内容）
            - tags__name: 标签名过滤
            - ordering: 排序字段
            - hot: 按热度排序（非空值启用）

        Returns:
            APIResponse: 包含帖子列表的响应
        """
        queryset = self.filter_queryset(self.get_queryset())

        # 按热度排序（查询参数 hot 存在时）
        hot = request.query_params.get('hot')
        if hot:
            queryset = queryset.annotate(
                # 热度计算公式：点赞×3 + 评论×2 + 收藏×1
                hot_score=(
                        Count('likes') * 3 +
                        Count('comments') * 2 +
                        Count('collects')
                )
            ).order_by('-hot_score')

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return APIResponse(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        获取帖子详情

        获取帖子详情时自动增加浏览量（使用 Redis 缓存）。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含帖子详情的响应
        """
        instance = self.get_object()

        # 增加浏览量（使用缓存服务）
        PostCacheService.increase_view(instance.id)

        serializer = self.get_serializer(instance, context={'request': request})
        return APIResponse(post=serializer.data)

    def create(self, request, *args, **kwargs):
        """
        创建帖子

        登录用户可创建帖子，作者自动设置为当前用户。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含创建的帖子数据
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return APIResponse(post=serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """
        删除帖子

        使用软删除，将帖子状态标记为 'deleted'。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 删除成功的响应
        """
        instance = self.get_object()
        instance.soft_delete()
        return APIResponse(msg="删除成功")

    def update(self, request, *args, **kwargs):
        """
        更新帖子（PUT/PATCH）

        只有作者可以编辑自己的帖子。

        Args:
            request: HTTP 请求对象
            partial: 是否部分更新（PUT=False, PATCH=True）

        Returns:
            APIResponse: 更新后的帖子数据
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # 权限检查：只有作者可以编辑
        if instance.author != request.user:
            return APIResponse(code=403, msg="只能编辑自己的帖子", status=status.HTTP_403_FORBIDDEN)

        # 使用序列化器验证和更新
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # 返回更新后的数据
        return APIResponse(post=serializer.data, code=100, msg="更新成功")

    def partial_update(self, request, *args, **kwargs):
        """
        部分更新帖子（PATCH）

        调用 update 方法，设置 partial=True。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 更新后的帖子数据
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @extend_schema(
        summary="点赞帖子",
        description="切换帖子点赞状态，已点赞则取消，未点赞则点赞",
        parameters=[
            OpenApiParameter(name='id', type=int, location='path', description='帖子ID')
        ],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'liked': {'type': 'boolean', 'description': '点赞后的状态'},
                    'like_count': {'type': 'integer', 'description': '当前点赞数'}
                }
            }
        }
    )
    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        """
        点赞帖子

        切换帖子点赞状态，已点赞则取消，未点赞则点赞。

        Args:
            request: HTTP 请求对象
            pk: 帖子 ID

        Returns:
            APIResponse: 包含点赞状态和点赞数的响应
        """
        post = self.get_object()
        result = PostInteractionService.toggle_like(post.id, request.user)
        return APIResponse(**result)

    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def collect(self, request, pk=None):
        """
        收藏帖子

        切换帖子收藏状态，已收藏则取消，未收藏则收藏。

        Args:
            request: HTTP 请求对象
            pk: 帖子 ID

        Returns:
            APIResponse: 包含收藏状态和收藏数的响应
        """
        post = self.get_object()
        result = PostInteractionService.toggle_collect(post.id, request.user)
        return APIResponse(**result)

    @action(detail=True, methods=['GET'], permission_classes=[IsAuthenticatedOrReadOnly])
    def comments(self, request, pk=None):
        """
        获取帖子的评论（带分页）

        只返回一级评论，子评论通过递归获取并扁平化存储。

        设计原因：
            - 只拉取顶级一级评论，防止多级评论发生并排错位混淆
            - 子评论通过 serializer 的 get_replies 方法递归获取

        Args:
            request: HTTP 请求对象
            pk: 帖子 ID

        Returns:
            APIResponse: 包含评论列表的响应（带分页）
        """
        post = self.get_object()

        # 只获取一级评论（parent=None），排除已删除和隐藏的评论
        comments = post.comments.filter(
            parent=None, is_deleted=False, is_hidden=False
        ).order_by('created_at')

        page = self.paginate_queryset(comments)
        if page is not None:
            serializer = CommentSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return APIResponse(comments=serializer.data)

    @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticated])
    def my_posts(self, request):
        """
        获取当前用户的帖子

        返回当前登录用户发布的所有帖子。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含帖子列表的响应（带分页）
        """
        posts = self.get_queryset().filter(author=request.user)
        page = self.paginate_queryset(posts)

        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(posts, many=True, context={'request': request})
        return APIResponse(posts=serializer.data)

    @action(detail=False, methods=['GET'])
    def collected(self, request):
        """
        获取当前用户收藏的帖子

        通过 PostCollect 表获取用户收藏的帖子 ID，然后查询帖子详情。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含收藏帖子列表的响应（带分页）
        """
        post_ids = PostCollect.objects.filter(user=request.user).values_list('post_id', flat=True)
        posts = self.get_queryset().filter(id__in=post_ids)

        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(posts, many=True, context={'request': request})
        return APIResponse(posts=serializer.data)

    @action(detail=False, methods=['GET'])
    def hot(self, request):
        """
        获取热门帖子

        根据热度算法计算最近 N 天的热门帖子。

        查询参数：
            - days: 时间范围（最近 N 天），默认 7 天
            - limit: 返回数量限制，默认 20 条

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含热门帖子列表的响应
        """
        days = request.query_params.get('days', 7)
        limit = request.query_params.get('limit', 20)

        try:
            days = int(days)
            limit = int(limit)
        except ValueError:
            days, limit = 7, 20

        posts = HotPostService.get_hot_posts(days, limit)
        serializer = PostListSerializer(posts, many=True, context={'request': request})
        return APIResponse(posts=serializer.data)

    @action(detail=False, methods=['POST'], permission_classes=[IsAuthenticated])
    def upload_image(self, request):
        """
        上传图片

        上传帖子图片，返回图片URL。支持延迟关联机制（先上传后关联帖子）。
        自动对图片进行压缩处理，可选1:1裁剪。

        验证规则：
            - 必须选择图片文件
            - 支持格式：jpeg, jpg, png, gif, webp
            - 大小限制：不超过 5MB

        请求参数：
            - image: 图片文件
            - crop_square: 是否裁剪为1:1（可选，默认False）

        Returns:
            APIResponse: 包含图片信息的响应
        """
        image_file = request.FILES.get('image')
        if not image_file:
            return APIResponse(code=400, msg='请选择图片文件')

        valid_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if image_file.content_type not in valid_types:
            return APIResponse(code=400, msg='不支持的图片格式')

        if image_file.size > 5 * 1024 * 1024:
            return APIResponse(code=400, msg='图片大小不能超过5MB')

        crop_square = request.data.get('crop_square', 'false').lower() == 'true'

        processed_file = process_image(
            image_file,
            max_width=1200,
            max_height=1200,
            quality=85,
            crop_square=crop_square,
            convert_webp=True
        )

        from django.core.files.uploadedfile import InMemoryUploadedFile
        import os
        ext = os.path.splitext(image_file.name)[1].lower()
        new_name = f"{os.path.splitext(image_file.name)[0]}_compressed.webp"

        processed_image = InMemoryUploadedFile(
            processed_file,
            None,
            new_name,
            'image/webp',
            processed_file.tell(),
            None
        )

        post_image = PostImage(
            image=processed_image,
            alt=image_file.name.replace('.', '_')
        )
        post_image.save()

        serializer = PostImageSerializer(post_image, context={'request': request})
        return APIResponse(image=serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    """
    评论视图集

    处理评论的 CRUD 操作，支持点赞和点踩功能。

    自定义动作：
        - like: 点赞评论
        - dislike: 点踩评论

    查询优化：
        - select_related: 预加载作者和帖子信息
        - 过滤已删除和隐藏的评论
    """

    queryset = Comment.objects.filter(is_deleted=False, is_hidden=False).select_related('author', 'post')
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        根据动作类型动态调整查询集

        核心设计：
            - list 动作：只返回一级评论（parent=None），支持按帖子过滤
            - 其他动作（like, dislike, destroy, retrieve）：允许查询所有层级的评论

        设计原因：
            - 列表查询时只返回一级评论，避免多级评论并排显示造成混淆
            - 单条操作时需要允许操作二级、三级等所有层级的评论

        Returns:
            QuerySet: 根据动作类型过滤后的评论查询集
        """
        # 基础查询集：未删除、未隐藏的评论，预加载作者和帖子
        queryset = Comment.objects.filter(is_deleted=False, is_hidden=False).select_related('author', 'post')

        # list 动作：只返回一级评论，支持按帖子过滤
        if self.action == 'list':
            post_id = self.request.query_params.get('post')
            if post_id:
                queryset = queryset.filter(post_id=post_id)
            return queryset.filter(parent=None).order_by('-created_at')

        # 其他动作：允许查询所有层级的评论
        return queryset.order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """
        创建评论

        创建评论后自动更新帖子的评论数。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含创建的评论数据
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # 更新帖子的评论数（排除已删除和隐藏的评论）
        post = serializer.instance.post
        post.comment_count = post.comments.filter(is_deleted=False, is_hidden=False).count()
        post.save(update_fields=['comment_count'])

        return APIResponse(comment=serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """
        删除评论

        只有评论作者或管理员可以删除评论，使用软删除。
        删除后自动更新帖子的评论数。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 删除成功的响应
        """
        comment = self.get_object()

        # 权限检查：只有作者或管理员可以删除
        if comment.author != request.user and not request.user.is_staff:
            return APIResponse(code=403, msg="只能删除自己的评论", status=403)

        # 软删除评论
        comment.soft_delete()

        # 更新帖子的评论数（排除已删除和隐藏的评论）
        post = comment.post
        post.comment_count = post.comments.filter(is_deleted=False, is_hidden=False).count()
        post.save(update_fields=['comment_count'])

        return APIResponse(msg="删除成功")

    @action(detail=True, methods=['POST'])
    def like(self, request, pk=None):
        """
        点赞评论

        切换评论点赞状态，支持取消点赞。

        Args:
            request: HTTP 请求对象
            pk: 评论 ID

        Returns:
            APIResponse: 包含点赞状态和计数的响应
        """
        comment = self.get_object()
        result = PostInteractionService.toggle_comment_reaction(comment.id, request.user, is_like=True)
        return APIResponse(**result)

    @action(detail=True, methods=['POST'])
    def dislike(self, request, pk=None):
        """
        点踩评论

        切换评论点踩状态，支持取消点踩。

        Args:
            request: HTTP 请求对象
            pk: 评论 ID

        Returns:
            APIResponse: 包含点踩状态和计数的响应
        """
        comment = self.get_object()
        result = PostInteractionService.toggle_comment_reaction(comment.id, request.user, is_like=False)
        return APIResponse(**result)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    标签视图集（只读）

    提供标签的列表和详情查询，支持关键词搜索。

    设计原因：
        - 标签由管理员管理，普通用户只读
        - 支持搜索便于前端标签选择
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class ReportViewSet(viewsets.ModelViewSet):
    """
    举报视图集

    处理举报的 CRUD 操作，支持帖子和评论的举报。

    权限控制：
        - 普通用户：只能查看自己的举报，只能创建新举报
        - 管理员：可以查看所有举报，处理举报

    创建举报时自动增加被举报内容的举报计数。
    """
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        根据用户角色过滤举报列表

        权限逻辑：
            - 管理员：查看所有举报
            - 普通用户：只查看自己的举报

        Returns:
            QuerySet: 过滤后的举报查询集
        """
        if self.request.user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter(reporter=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        创建举报

        创建举报后自动增加被举报内容的举报计数。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含举报数据的响应
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # 增加被举报内容的举报计数
        content_type = serializer.instance.content_type
        object_id = serializer.instance.object_id

        if content_type == 'post':
            Post.objects.filter(id=object_id).update(report_count=F('report_count') + 1)
        elif content_type == 'comment':
            Comment.objects.filter(id=object_id).update(report_count=F('report_count') + 1)

        return APIResponse(report=serializer.data, status=status.HTTP_201_CREATED)