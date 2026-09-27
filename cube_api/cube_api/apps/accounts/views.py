"""
用户认证模块视图

该模块定义了用户认证相关的视图类，处理登录、注册、退出、Token 刷新和用户资料管理。

核心视图：
    - AuthViewSet：登录、注册、退出、Token 刷新
    - UserView：当前用户资料获取和更新
    - ProfileDetailView：用户资料详情、关注列表、粉丝列表、关注操作

设计特点：
    - 使用 extend_schema 装饰器生成 OpenAPI 文档
    - 动态选择序列化器，优化不同场景的数据返回
    - 使用自定义限流类防止暴力破解
    - 登录/注册同时返回 access_token 和 refresh_token
    - 关注操作同时更新数据库和 Redis 缓存
"""

from django.contrib.auth import authenticate
from django.db.models import Case, IntegerField, Value, When
from drf_spectacular.utils import OpenApiRequest, OpenApiResponse, extend_schema
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework_simplejwt.tokens import RefreshToken
from utils.common_pagination import UnifiedPagination
from utils.common_response import APIResponse

from .models import User
from .serializers import (
    LoginWithCodeSerializer,
    ProfileListSerializer,
    ProfileSerializer,
    RegisterWithCodeSerializer,
    ResetPasswordSerializer,
    SendCodeSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from .services import EmailCodeService, JWTCacheService, ProfileCacheService, SessionService
from .throttles import LoginRateThrottle, SendCodeRateThrottle


class AuthViewSet(viewsets.GenericViewSet):
    """
    认证视图集

    处理用户登录、注册、退出和 Token 刷新操作。

    动作列表：
        - register: 用户注册
        - login: 用户登录
        - send_code: 发送邮箱验证码
        - register_with_code: 验证码注册
        - login_with_code: 验证码登录
        - reset_password: 重置密码
        - refresh: 刷新 Token
        - logout: 用户退出（需登录）
    """

    serializer_class = UserSerializer
    # 登录注册不需要权限校验
    permission_classes = [AllowAny]

    def get_throttles(self):
        """
        动态添加限流

        login 动作添加 LoginRateThrottle，send_code 动作添加 SendCodeRateThrottle。
        默认限流（AnonRateThrottle、UserRateThrottle）仍有效。

        Returns:
            限流类实例列表
        """
        throttles = super().get_throttles()
        if self.action == "login":
            throttles.append(LoginRateThrottle())
        elif self.action == "send_code":
            throttles.append(SendCodeRateThrottle())
        return throttles

    @extend_schema(
        summary="用户注册",
        description="使用邮箱和密码注册，支持自动处理用户名重名问题",
        request=OpenApiRequest(
            request={
                "application/json": {
                    "type": "object",
                    "properties": {
                        "user": {
                            "type": "object",
                            "properties": {
                                "email": {"type": "string", "format": "email"},
                                "password": {"type": "string"},
                                "username": {"type": "string"},
                            },
                            "required": ["email", "password"],
                        }
                    },
                }
            }
        ),
        responses={201: UserSerializer, 400: OpenApiResponse(description="注册失败")},
    )
    @action(detail=False, methods=["POST"])
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
        user_data = request.data.get("user", {})

        # 处理用户名重名问题
        # 如果用户名已存在，自动添加数字后缀（如 username_1, username_2）
        username = user_data.get("username")
        if username and User.objects.filter(username=username).exists():
            counter = 1
            while User.objects.filter(username=f"{username}_{counter}").exists():
                counter += 1
            user_data["username"] = f"{username}_{counter}"

        # 验证并保存用户
        serializer = self.get_serializer(data=user_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return APIResponse(user=serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="用户登录",
        description="使用邮箱和密码登录，返回 JWT Token",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "user": {
                        "type": "object",
                        "properties": {"email": {"type": "string", "format": "email"}, "password": {"type": "string"}},
                        "required": ["email", "password"],
                    }
                },
            }
        },
        responses={
            200: OpenApiResponse(
                description="登录成功",
                response={
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer"},
                        "msg": {"type": "string"},
                        "user": {
                            "type": "object",
                            "properties": {
                                "username": {"type": "string"},
                                "email": {"type": "string"},
                                "token": {"type": "string"},
                            },
                        },
                    },
                },
            ),
            401: OpenApiResponse(description="邮箱或密码错误"),
        },
    )
    @action(detail=False, methods=["POST"], permission_classes=[AllowAny])
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
        user_data = request.data.get("user", {})

        # 使用 Django 的 authenticate 函数验证邮箱和密码
        user = authenticate(email=user_data.get("email"), password=user_data.get("password"))

        # 验证失败：返回 401 错误
        if not user:
            return APIResponse(code=102, msg="邮箱或密码错误", status=status.HTTP_401_UNAUTHORIZED)

        # 验证成功：生成 JWT Token
        serializer = self.get_serializer(user)
        token = RefreshToken.for_user(user)

        # 将 Token 添加到返回数据中
        res_data = serializer.data
        res_data["token"] = str(token.access_token)
        res_data["refresh_token"] = str(token)

        # 注册会话（多端登录管理）
        SessionService.add_session(user.id, str(token["jti"]))

        return APIResponse(user=res_data)

    @extend_schema(
        summary="发送邮箱验证码",
        description="发送6位数字验证码到指定邮箱，支持注册/登录/重置密码三种场景",
        request=SendCodeSerializer,
        responses={200: OpenApiResponse(description="发送成功"), 400: OpenApiResponse(description="发送失败")},
    )
    @action(detail=False, methods=["POST"])
    def send_code(self, request):
        """
        发送邮箱验证码

        参数：email, action(register/login/reset)
        - register: 检查邮箱未注册
        - login/reset: 检查邮箱已注册
        """
        serializer = SendCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        action_type = serializer.validated_data["action"]

        # 场景校验
        if action_type == "register":
            if User.objects.filter(email=email).exists():
                return APIResponse(code=103, msg="该邮箱已注册")
        else:
            if not User.objects.filter(email=email).exists():
                return APIResponse(code=104, msg="该邮箱未注册")

        success, msg = EmailCodeService.send_code(action_type, email)
        if success:
            return APIResponse(msg=msg)
        return APIResponse(code=105, msg=msg)

    @extend_schema(
        summary="验证码注册",
        description="使用邮箱+验证码+密码注册新用户，注册成功返回JWT Token",
        request=RegisterWithCodeSerializer,
        responses={201: OpenApiResponse(description="注册成功"), 400: OpenApiResponse(description="注册失败")},
    )
    @action(detail=False, methods=["POST"])
    def register_with_code(self, request):
        """验证码注册：验证码通过后创建用户并返回 JWT"""
        serializer = RegisterWithCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]
        password = serializer.validated_data["password"]
        username = serializer.validated_data.get("username")

        # 验证码校验
        valid, msg = EmailCodeService.verify_code("register", email, code)
        if not valid:
            return APIResponse(code=106, msg=msg)

        # 邮箱已注册检查
        if User.objects.filter(email=email).exists():
            return APIResponse(code=103, msg="该邮箱已注册")

        # 用户名处理
        if not username:
            username = email.split("@")[0]
        if User.objects.filter(username=username).exists():
            counter = 1
            while User.objects.filter(username=f"{username}_{counter}").exists():
                counter += 1
            username = f"{username}_{counter}"

        user = User.objects.create_user(email=email, password=password, username=username)
        user_serializer = UserSerializer(user)
        token = RefreshToken.for_user(user)
        res_data = user_serializer.data
        res_data["token"] = str(token.access_token)
        res_data["refresh_token"] = str(token)
        SessionService.add_session(user.id, str(token["jti"]))
        return APIResponse(user=res_data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="验证码登录",
        description="使用邮箱+验证码免密登录，验证通过后返回JWT Token",
        request=LoginWithCodeSerializer,
        responses={200: OpenApiResponse(description="登录成功"), 400: OpenApiResponse(description="登录失败")},
    )
    @action(detail=False, methods=["POST"])
    def login_with_code(self, request):
        """验证码登录：验证码通过后查找用户并返回 JWT"""
        serializer = LoginWithCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]

        valid, msg = EmailCodeService.verify_code("login", email, code)
        if not valid:
            return APIResponse(code=106, msg=msg)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return APIResponse(code=104, msg="该邮箱未注册")

        user_serializer = UserSerializer(user)
        token = RefreshToken.for_user(user)
        res_data = user_serializer.data
        res_data["token"] = str(token.access_token)
        res_data["refresh_token"] = str(token)
        SessionService.add_session(user.id, str(token["jti"]))
        return APIResponse(user=res_data)

    @extend_schema(
        summary="重置密码",
        description="使用邮箱+验证码重置密码，重置后需重新登录",
        request=ResetPasswordSerializer,
        responses={200: OpenApiResponse(description="重置成功"), 400: OpenApiResponse(description="重置失败")},
    )
    @action(detail=False, methods=["POST"])
    def reset_password(self, request):
        """重置密码：验证码通过后设置新密码"""
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]
        new_password = serializer.validated_data["new_password"]

        valid, msg = EmailCodeService.verify_code("reset", email, code)
        if not valid:
            return APIResponse(code=106, msg=msg)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return APIResponse(code=104, msg="该邮箱未注册")

        user.set_password(new_password)
        user.save()

        # 清理用户实例缓存，使旧 Token 失效
        from django.core.cache import cache

        cache.delete(f"user_instance_cache_{user.id}")

        return APIResponse(msg="密码重置成功，请重新登录")

    @extend_schema(
        summary="刷新 Token",
        description="使用 refresh_token 换取新的 access_token 和 refresh_token",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "refresh": {"type": "string", "description": "Refresh Token"},
                },
                "required": ["refresh"],
            }
        },
        responses={
            200: OpenApiResponse(
                description="刷新成功",
                response={
                    "type": "object",
                    "properties": {
                        "token": {"type": "string"},
                        "refresh_token": {"type": "string"},
                    },
                },
            ),
            401: OpenApiResponse(description="Refresh Token 无效或已过期"),
        },
    )
    @action(detail=False, methods=["POST"], permission_classes=[AllowAny])
    def refresh(self, request):
        """
        刷新 Access Token

        使用 ROTATE_REFRESH_TOKENS 策略：每次刷新签发新的 refresh_token，
        旧 refresh_token 进入黑名单。同时更新会话活跃时间。
        """
        refresh_str = request.data.get("refresh")
        if not refresh_str:
            return APIResponse(code=107, msg="缺少 refresh_token", status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_str)
        except Exception:
            return APIResponse(code=108, msg="Refresh Token 无效或已过期", status=status.HTTP_401_UNAUTHORIZED)

        user_id = refresh.get("user_id")
        jti = refresh.get("jti")

        # 检查是否在黑名单
        if JWTCacheService.is_blacklisted(jti):
            return APIResponse(code=108, msg="Refresh Token 已失效", status=status.HTTP_401_UNAUTHORIZED)

        # 检查会话是否活跃（是否被踢下线）
        if not SessionService.is_session_active(user_id, jti):
            return APIResponse(code=109, msg="登录已在其他设备失效", status=status.HTTP_401_UNAUTHORIZED)

        # 旧 refresh_token 入黑名单并移除会话
        JWTCacheService.add_to_blacklist(refresh.payload)
        SessionService.remove_session(user_id, jti)

        # 生成新的 token 对
        new_refresh = RefreshToken.for_user(User.objects.get(id=user_id))
        new_access = str(new_refresh.access_token)

        # 注册新会话
        SessionService.add_session(user_id, str(new_refresh["jti"]))

        return APIResponse(token=new_access, refresh_token=str(new_refresh))

    @action(detail=False, methods=["POST"], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        用户退出登录

        将当前 access_token 和传入的 refresh_token 都加入黑名单，
        并从会话列表中移除。
        """
        # access token 入黑名单
        token_payload = request.auth
        if token_payload:
            JWTCacheService.add_to_blacklist(token_payload)

        # refresh token 入黑名单 + 移除会话
        refresh_str = request.data.get("refresh_token")
        if refresh_str:
            JWTCacheService.add_token_to_blacklist(refresh_str)
            try:
                refresh = RefreshToken(refresh_str)
                user_id = refresh.get("user_id")
                jti = refresh.get("jti")
                SessionService.remove_session(user_id, jti)
            except Exception:
                pass

        # 清理用户实例缓存
        from django.core.cache import cache

        cache.delete(f"user_instance_cache_{request.user.id}")

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
        if self.request.method in ["PUT", "PATCH"]:
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
        partial = kwargs.pop("partial", True)
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
    lookup_field = "username"
    lookup_value_regex = r"[^/]+"

    def get_serializer_class(self):
        """
        动态选择序列化器

        关注列表和粉丝列表使用轻量级的 ProfileListSerializer（不含计数字段），
        详情页使用 ProfileSerializer（含关注状态和统计数据）。

        Returns:
            序列化器类
        """
        if self.action in ["following", "followers"]:
            return ProfileListSerializer
        if self.action == "list" and "search" in self.request.query_params:
            return ProfileListSerializer
        return self.serializer_class

    def list(self, request, *args, **kwargs):
        """
        获取所有用户资料列表

        Returns:
            APIResponse: 包含用户资料列表的响应（包裹在 'profiles' 键中）
        """
        if "search" in request.query_params:
            keyword = request.query_params.get("search", "").strip()
            queryset = self.get_queryset().none()

            if keyword:
                queryset = (
                    self.get_queryset()
                    .filter(username__icontains=keyword)
                    .annotate(
                        exact_match=Case(
                            When(username__iexact=keyword, then=Value(0)),
                            default=Value(1),
                            output_field=IntegerField(),
                        )
                    )
                    .order_by("exact_match", "username")
                )

            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer(
                page,
                many=True,
                context={"request": request},
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
        serializer = self.get_serializer(instance, context={"request": request})
        return APIResponse(profiles=serializer.data)

    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
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

        if request.method == "POST":
            # 关注动作
            # 1. 更新数据库
            request.user.following.add(profile)
            # 2. 同步更新 Redis 缓存
            ProfileCacheService.update_follow_relation(
                from_user_id=request.user.id, to_user_id=profile.id, is_follow=True
            )
            return APIResponse(msg="关注成功")
        elif request.method == "DELETE":
            # 取消关注动作
            # 1. 更新数据库
            request.user.following.remove(profile)
            # 2. 同步更新 Redis 缓存
            ProfileCacheService.update_follow_relation(
                from_user_id=request.user.id, to_user_id=profile.id, is_follow=False
            )
            return APIResponse(msg="取消关注成功")

        serializer = self.get_serializer(profile)
        return APIResponse(profile=serializer.data)

    @action(detail=True, methods=["GET"], permission_classes=[IsAuthenticatedOrReadOnly])
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
        following_queryset = profile_user.following.filter(is_active=True).order_by("username")

        # 序列化，传递 request 上下文确保关注状态能正确计算
        if "page" in request.query_params or "page_size" in request.query_params:
            page = self.paginate_queryset(following_queryset)
            serializer = self.get_serializer(
                page,
                many=True,
                context={"request": request},
            )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            following_queryset,
            many=True,
            context={"request": request},
        )

        return APIResponse(profiles=serializer.data)

    @action(detail=True, methods=["GET"], permission_classes=[IsAuthenticatedOrReadOnly])
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
        followers_queryset = profile_user.followers.filter(is_active=True).order_by("username")

        # 序列化，传递 request 上下文确保关注状态能正确计算
        if "page" in request.query_params or "page_size" in request.query_params:
            page = self.paginate_queryset(followers_queryset)
            serializer = self.get_serializer(
                page,
                many=True,
                context={"request": request},
            )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            followers_queryset,
            many=True,
            context={"request": request},
        )

        return APIResponse(profiles=serializer.data)
