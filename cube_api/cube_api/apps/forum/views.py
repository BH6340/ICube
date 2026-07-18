# forum/views.py
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import F, Count

from .models import Post, Tag, Comment, Report, PostCollect
from .serializers import (
    PostSerializer, PostListSerializer, PostCreateUpdateSerializer,
    TagSerializer, CommentSerializer, ReportSerializer
)
from .services import PostCacheService, PostInteractionService, HotPostService
from utils.common_response import APIResponse
from apps.accounts.permissions import IsOwnerOrReadOnly


class PostViewSet(viewsets.ModelViewSet):
    """帖子视图集"""

    queryset = Post.objects.filter(status='published').select_related('author').prefetch_related('tags')
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'view_count', 'like_count', 'comment_count', 'is_pinned', 'is_essence']
    ordering = ['-is_pinned', '-is_essence', '-created_at']
    filterset_fields = ['tags__name', 'is_pinned', 'is_essence']

    def get_serializer_class(self):
        if self.action == 'list':
            return PostListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return PostCreateUpdateSerializer
        return PostSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # 按热度排序
        hot = request.query_params.get('hot')
        if hot:
            queryset = queryset.annotate(
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
        instance = self.get_object()

        # 增加浏览量
        PostCacheService.increase_view(instance.id)

        serializer = self.get_serializer(instance, context={'request': request})
        return APIResponse(post=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return APIResponse(post=serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return APIResponse(msg="删除成功")

    def update(self, request, *args, **kwargs):
        """
        完整更新帖子（PUT）
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
        """点赞帖子"""
        post = self.get_object()
        result = PostInteractionService.toggle_like(post.id, request.user)
        return APIResponse(**result)

    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def collect(self, request, pk=None):
        """收藏帖子"""
        post = self.get_object()
        result = PostInteractionService.toggle_collect(post.id, request.user)
        return APIResponse(**result)

    # 💡 标注修改：帖子详情内的 comments 动作也必须加 parent=None 限制
    @action(detail=True, methods=['GET'], permission_classes=[IsAuthenticated])
    def comments(self, request, pk=None):
        """获取帖子的评论（带分页）"""
        post = self.get_object()

        # 💡 修改点：确保只拉取顶级一级评论，防止多级评论发生并排错位混淆
        comments = post.comments.filter(
            parent=None, is_deleted=False, is_hidden=False
        ).order_by('created_at')

        page = self.paginate_queryset(comments)
        if page is not None:
            serializer = CommentSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return APIResponse(comments=serializer.data)

    @action(detail=False, methods=['GET'])
    def my_posts(self, request):
        """我的帖子"""
        posts = self.get_queryset().filter(author=request.user)
        page = self.paginate_queryset(posts)

        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(posts, many=True, context={'request': request})
        return APIResponse(posts=serializer.data)

    @action(detail=False, methods=['GET'])
    def collected(self, request):
        """我收藏的帖子"""
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
        """热门帖子"""
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


class CommentViewSet(viewsets.ModelViewSet):
    """评论视图集"""

    queryset = Comment.objects.filter(is_deleted=False, is_hidden=False).select_related('author', 'post')
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    # ✅ 标注修改：区分 list 动作和单条操作动作
    def get_queryset(self):
        # 1. 拿到基础的未删除、未隐藏的评论数据集
        queryset = Comment.objects.filter(is_deleted=False, is_hidden=False).select_related('author', 'post')

        # 2. 💡 核心修复：只有当前执行的是『获取列表(list)』动作时，才进行 parent=None 楼层截断
        if self.action == 'list':
            post_id = self.request.query_params.get('post')
            if post_id:
                queryset = queryset.filter(post_id=post_id)
            return queryset.filter(parent=None).order_by('-created_at')

        # 3. 如果是像 like, dislike, destroy, retrieve 这种针对单条特定 ID 的操作
        # 我们必须允许查出二级、三级等所有子孙评论，不要加 parent=None 的限制！
        return queryset.order_by('-created_at')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # 更新帖子的评论数
        post = serializer.instance.post
        post.comment_count = post.comments.filter(is_deleted=False, is_hidden=False).count()
        post.save(update_fields=['comment_count'])

        return APIResponse(comment=serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()

        if comment.author != request.user and not request.user.is_staff:
            return APIResponse(code=403, msg="只能删除自己的评论", status=403)

        comment.soft_delete()

        # 更新帖子的评论数
        post = comment.post
        post.comment_count = post.comments.filter(is_deleted=False, is_hidden=False).count()
        post.save(update_fields=['comment_count'])

        return APIResponse(msg="删除成功")

    @action(detail=True, methods=['POST'])
    def like(self, request, pk=None):
        """点赞评论"""
        comment = self.get_object()
        result = PostInteractionService.toggle_comment_reaction(comment.id, request.user, is_like=True)
        return APIResponse(**result)

    @action(detail=True, methods=['POST'])
    def dislike(self, request, pk=None):
        """点踩评论"""
        comment = self.get_object()
        result = PostInteractionService.toggle_comment_reaction(comment.id, request.user, is_like=False)
        return APIResponse(**result)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """标签视图集（只读）"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class ReportViewSet(viewsets.ModelViewSet):
    """举报视图集"""
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 普通用户只能看到自己的举报，管理员可以看到所有
        if self.request.user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter(reporter=self.request.user)

    def create(self, request, *args, **kwargs):
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