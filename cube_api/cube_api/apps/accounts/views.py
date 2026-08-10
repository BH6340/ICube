# -*- coding: utf-8 -*-
"""
用户认证模块视图

该模块定义了用户认证相关的视图类，处理登录、注册、退出、用户资料管理和关注逻辑。

核心视图：
    - AuthViewSet：登录、注册、退出
    - UserView：当前用户资料获取和更新
    - ProfileDetailView：用户资料详情、关注列表、粉丝列表、关注操作

设计特点：
    - 使用 extend_schema 装饰器生成 OpenAPI 文档
    - 动态选择序列化器，优化不同场景的数据返回
    - 使用自定义限流类防止暴力破解
    - 关注操作同时更新数据库和 Redis 缓存
"""
from drf_spectacular.utils import extend_schema, OpenApiRequest, OpenApiResponse
from rest_framework.decorators import action
from rest_framework import status, viewsets, generics
from django.contrib.auth import authenticate
from django.db.models import Case, IntegerField, Value, When
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly

from .models import User
from .serializers import UserSerializer, ProfileSerializer, UserUpdateSerializer, ProfileListSerializer
from utils.common_response import APIResponse
from utils.common_pagination import UnifiedPagination
from .services import ProfileCacheService, JWTCacheService
from .throttles import LoginRateThrottle


class AuthViewSet(viewsets.GenericViewSet):
    """
    认证视图集

    处理用户登录、注册和退出操作。

    动作列表：
        - register: 用户注册
        - login: 用户登录
        - logout: 用户退出（需登录）
    """
    serializer_class = UserSerializer
    # 登录注册不需要权限校验
    permission_classes = [AllowAny]

    def get_throttles(self):
        """
        动态添加限流

        仅对登录操作添加 LoginRateThrottle，防止暴力破解。
        默认限流（AnonRateThrottle、UserRateThrottle）仍有效。

        Returns:
            限流类实例列表
        """
        throttles = super().get_throttles()
        if self.action == 'login':
            throttles.append(LoginRateThrottle())
        return throttles

    @extend_schema(
        summary="用户注册",
        description="使用邮箱和密码注册，支持自动处理用户名重名问题",
        request=OpenApiRequest(
            request={
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'user': {
                            'type': 'object',
                            'properties': {
                                'email': {'type': 'string', 'format': 'email'},
                                'password': {'type': 'string'},
                                'username': {'type': 'string'}
                            },
                            'required': ['email', 'password']
                        }
                    }
                }
            }
        ),
        responses={
            201: UserSerializer,
            400: OpenApiResponse(description='注册失败')
        }
    )
    @action(detail=False, methods=['POST'])
    def register(self, request):
        """
        用户注册

        处理逻辑：
            1. 提取用户数据（支持嵌套的 user 键）
            2. 处理用户名重名问题（自动添加数字后缀）
            3. 验证并保存用户
            4. 返回用户信息

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含用户信息的响应
        """
        user_data = request.data.get('user', {})

        # 处理用户名重名问题
        # 如果用户名已存在，自动添加数字后缀（如 username_1, username_2）
        username = user_data.get('username')
        if username and User.objects.filter(username=username).exists():
            counter = 1
            while User.objects.filter(username=f"{username}_{counter}").exists():
                counter += 1
            user_data['username'] = f"{username}_{counter}"

        # 验证并保存用户
        serializer = self.get_serializer(data=user_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return APIResponse(user=serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="用户登录",
        description="使用邮箱和密码登录，返回 JWT Token",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'user': {
                        'type': 'object',
                        'properties': {
                            'email': {'type': 'string', 'format': 'email'},
                            'password': {'type': 'string'}
                        },
                        'required': ['email', 'password']
                    }
                }
            }
        },
        responses={
            200: OpenApiResponse(
                description='登录成功',
                response={
                    'type': 'object',
                    'properties': {
                        'code': {'type': 'integer'},
                        'msg': {'type': 'string'},
                        'user': {
                            'type': 'object',
                            'properties': {
                                'username': {'type': 'string'},
                                'email': {'type': 'string'},
                                'token': {'type': 'string'}
                            }
                        }
                    }
                }
            ),
            401: OpenApiResponse(description='邮箱或密码错误')
        }
    )
    @action(detail=False, methods=['POST'], permission_classes=[AllowAny])
    def login(self, request):
        """
        用户登录

        处理逻辑：
            1. 提取用户数据（支持嵌套的 user 键）
            2. 使用 Django authenticate 验证邮箱和密码
            3. 验证失败返回 401 错误
            4. 验证成功生成 JWT Token
            5. 返回用户信息和 Token

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含用户信息和 Token 的响应
        """
        user_data = request.data.get('user', {})

        # 使用 Django 的 authenticate 函数验证邮箱和密码
        user = authenticate(
            email=user_data.get('email'),
            password=user_data.get('password')
        )

        # 验证失败：返回 401 错误
        if not user:
            return APIResponse(code=102, msg="邮箱或密码错误", status=status.HTTP_401_UNAUTHORIZED)

        # 验证成功：生成 JWT Token
        serializer = self.get_serializer(user)
        token = RefreshToken.for_user(user)

        # 将 Token 添加到返回数据中
        res_data = serializer.data
        res_data['token'] = str(token.access_token)

        return APIResponse(user=res_data)

    @action(detail=False, methods=['POST'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        用户退出登录

        实现原理：
            将当前使用的 JWT Token 添加到 Redis 黑名单，使其提前失效。
            黑名单的 TTL 设置为 Token 的剩余有效期。

        注意：
            JWT 本身是无状态的，无法主动使 Token 失效。
            通过黑名单机制，在每次认证时检查 Token 是否被拉黑。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 退出成功响应
        """
        # request.auth 会在通过认证后，自动存放当前请求解密后的临时 token 字典对象
        token_payload = request.auth

        if token_payload:
            # 调用服务层，将该 Token 添加到黑名单
            JWTCacheService.add_to_blacklist(token_payload)

        return APIResponse(msg="退出登录成功")


class UserView(generics.RetrieveUpdateAPIView):
    """
    当前用户资料视图

    处理 GET /api/user（获取当前用户资料）和 PUT /api/user（更新当前用户资料）。

    设计特点：
        - 动态选择序列化器：获取时用 UserSerializer，更新时用 UserUpdateSerializer
        - 支持文件上传（头像）
        - 返回数据包裹在 'user' 键中
    """
    permission_classes = [IsAuthenticated]
    # 支持多种内容类型：普通表单、文件上传、JSON
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        """
        动态选择序列化器

        更新时使用 UserUpdateSerializer（严格限制可修改字段），
        获取时使用 UserSerializer（返回完整信息）。

        Returns:
            序列化器类
        """
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer

    def get_object(self):
        """
        获取当前登录用户

        覆盖此方法，确保总是返回当前登录请求的用户，
        无需通过 URL 参数指定用户 ID。

        Returns:
            当前登录的 User 对象
        """
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        """
        获取当前用户资料

        Returns:
            APIResponse: 包含用户资料的响应（包裹在 'user' 键中）
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return APIResponse(user=serializer.data)

    def update(self, request, *args, **kwargs):
        """
        更新当前用户资料

        支持部分更新（用户可能只改了简介，没换头像）。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 更新后的用户资料（包裹在 'user' 键中）
        """
        # 强制设为部分更新，容错率更高
        partial = kwargs.pop('partial', True)
        instance = self.get_object()

        # 直接使用展平的 request.data，不再取嵌套的 user 键
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # 返回数据格式和 retrieve 保持一致，包裹在 'user' 键中
        return APIResponse(user=serializer.data)


class ProfileDetailView(viewsets.ReadOnlyModelViewSet):
    """
    用户资料详情视图集

    处理用户资料列表、详情、关注列表、粉丝列表和关注操作。

    动作列表：
        - list: 获取所有用户资料列表
        - retrieve: 获取单个用户资料详情
        - follow: 关注/取消关注用户（POST/DELETE）
        - following: 获取用户关注的人列表
        - followers: 获取用户的粉丝列表

    设计特点：
        - 使用 username 作为 lookup_field（而非主键 ID）
        - 动态选择序列化器：列表使用轻量级的 ProfileListSerializer
        - 关注操作同时更新数据库和 Redis 缓存
    """
    queryset = User.objects.filter(is_active=True)
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = UnifiedPagination
    # 使用 username 作为查找字段（更友好的 URL）
    lookup_field = 'username'
    lookup_value_regex = r'[^/]+'

    def get_serializer_class(self):
        """
        动态选择序列化器

        关注列表和粉丝列表使用轻量级的 ProfileListSerializer（不含计数字段），
        详情页使用 ProfileSerializer（含关注状态和统计数据）。

        Returns:
            序列化器类
        """
        if self.action in ['following', 'followers']:
            return ProfileListSerializer
        if self.action == 'list' and 'search' in self.request.query_params:
            return ProfileListSerializer
        return self.serializer_class

    def list(self, request, *args, **kwargs):
        """
        获取所有用户资料列表

        Returns:
            APIResponse: 包含用户资料列表的响应（包裹在 'profiles' 键中）
        """
        if 'search' in request.query_params:
            keyword = request.query_params.get('search', '').strip()
            queryset = self.get_queryset().none()

            if keyword:
                queryset = self.get_queryset().filter(
                    username__icontains=keyword
                ).annotate(
                    exact_match=Case(
                        When(username__iexact=keyword, then=Value(0)),
                        default=Value(1),
                        output_field=IntegerField(),
                    )
                ).order_by('exact_match', 'username')

            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer(
                page,
                many=True,
                context={'request': request},
            )
            return self.get_paginated_response(serializer.data)

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(profiles=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        获取单个用户资料详情

        注意：必须传递 request 上下文给 serializer，
        否则 get_following 方法会因为找不到 request 永远返回 False。

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含用户资料的响应（包裹在 'profiles' 键中）
        """
        instance = self.get_object()
        # 传递 request 上下文，确保关注状态能正确计算
        serializer = self.get_serializer(instance, context={'request': request})
        return APIResponse(profiles=serializer.data)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def follow(self, request, **kwargs):
        """
        关注/取消关注用户

        POST 请求：关注用户
        DELETE 请求：取消关注用户

        处理逻辑：
            1. 检查是否操作自己（禁止）
            2. 更新数据库中的关注关系
            3. 同步更新 Redis 缓存

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 操作结果
        """
        profile = self.get_object()

        # 禁止关注或取消关注自己
        if request.user == profile:
            return APIResponse(code=103, msg="不能关注或取关自己")

        if request.method == 'POST':
            # 关注动作
            # 1. 更新数据库
            request.user.following.add(profile)
            # 2. 同步更新 Redis 缓存
            ProfileCacheService.update_follow_relation(
                from_user_id=request.user.id,
                to_user_id=profile.id,
                is_follow=True
            )
            return APIResponse(msg="关注成功")
        elif request.method == 'DELETE':
            # 取消关注动作
            # 1. 更新数据库
            request.user.following.remove(profile)
            # 2. 同步更新 Redis 缓存
            ProfileCacheService.update_follow_relation(
                from_user_id=request.user.id,
                to_user_id=profile.id,
                is_follow=False
            )
            return APIResponse(msg="取消关注成功")

        serializer = self.get_serializer(profile)
        return APIResponse(profile=serializer.data)

    @action(detail=True, methods=['GET'], permission_classes=[IsAuthenticatedOrReadOnly])
    def following(self, request, **kwargs):
        """
        获取用户关注的人列表

        URL: GET /api/profiles/{username}/following

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含关注列表的响应（包裹在 'profiles' 键中）
        """
        # 获取目标用户实例
        profile_user = self.get_object()

        # 获取该用户关注的所有人
        following_queryset = profile_user.following.filter(
            is_active=True
        ).order_by('username')

        # 序列化，传递 request 上下文确保关注状态能正确计算
        if 'page' in request.query_params or 'page_size' in request.query_params:
            page = self.paginate_queryset(following_queryset)
            serializer = self.get_serializer(
                page,
                many=True,
                context={'request': request},
            )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            following_queryset,
            many=True,
            context={'request': request},
        )

        return APIResponse(profiles=serializer.data)

    @action(detail=True, methods=['GET'], permission_classes=[IsAuthenticatedOrReadOnly])
    def followers(self, request, **kwargs):
        """
        获取用户的粉丝列表

        URL: GET /api/profiles/{username}/followers

        Args:
            request: HTTP 请求对象

        Returns:
            APIResponse: 包含粉丝列表的响应（包裹在 'profiles' 键中）
        """
        # 获取目标用户
        profile_user = self.get_object()

        # 获取粉丝集合
        followers_queryset = profile_user.followers.filter(
            is_active=True
        ).order_by('username')

        # 序列化，传递 request 上下文确保关注状态能正确计算
        if 'page' in request.query_params or 'page_size' in request.query_params:
            page = self.paginate_queryset(followers_queryset)
            serializer = self.get_serializer(
                page,
                many=True,
                context={'request': request},
            )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            followers_queryset,
            many=True,
            context={'request': request},
        )

        return APIResponse(profiles=serializer.data)
