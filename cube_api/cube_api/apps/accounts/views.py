from drf_spectacular.utils import extend_schema, OpenApiRequest, OpenApiResponse
from rest_framework.decorators import action
from rest_framework import status, viewsets, generics
from django.contrib.auth import authenticate
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly, AllowAny

from .models import User
from .serializers import UserSerializer, ProfileSerializer, UserUpdateSerializer, ProfileListSerializer
from utils.common_response import APIResponse
from .services import ProfileCacheService, JWTCacheService
from .throttles import LoginRateThrottle


class AuthViewSet(viewsets.GenericViewSet):
    """
    仅包含登录与注册动作的 ViewSet
    """
    serializer_class = UserSerializer
    # 登录注册不需要权限校验
    permission_classes = [AllowAny]

    def get_throttles(self):
        """
        动态添加限流：如果是登录操作，则加上 LoginRateThrottle
        """
        throttles = super().get_throttles()
        if self.action == 'login':
            throttles.append(LoginRateThrottle())
        return throttles

    @extend_schema(
        summary="用户注册",
        description="使用邮箱和密码注册",
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
        user_data = request.data.get('user', {})
        # 💡 核心：3行代码解决重名问题
        username = user_data.get('username')
        if username and User.objects.filter(username=username).exists():
            counter = 1
            while User.objects.filter(username=f"{username}_{counter}").exists():
                counter += 1
            user_data['username'] = f"{username}_{counter}"

        serializer = self.get_serializer(data=user_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return APIResponse(user=serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="用户登录",
        description="使用邮箱和密码登录",
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
        user_data = request.data.get('user', {})
        user = authenticate(
            email=user_data.get('email'),
            password=user_data.get('password')
        )

        if not user:
            return APIResponse(code=102, msg="邮箱或密码错误", status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(user)
        token = RefreshToken.for_user(user)

        res_data = serializer.data
        res_data['token'] = str(token.access_token)
        return APIResponse(user=res_data)

    @action(detail=False, methods=['POST'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        退出登录：将当前使用的 Token 强行注入 Redis 黑名单
        """
        # request.auth 会在通过认证后，自动存放当前请求解密后的临时 token 字典对象
        token_payload = request.auth

        if token_payload:
            # 💡 调用服务层，将该 Token 封杀至其寿命结束
            JWTCacheService.add_to_blacklist(token_payload)

        return APIResponse(msg="退出登录成功")


class UserView(generics.RetrieveUpdateAPIView):
    """
    处理 GET /api/user 和 PUT /api/user
    """
    permission_classes = [IsAuthenticated]
    # 💡 核心新增：确保当前视图集能完美解析前端传过来的普通表单和文件流
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        """
        动态选择序列化器：更新时用严格限制版，获取时用完整版
        """
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer

    def get_object(self):
        # 覆盖此方法，确保总是返回当前登录请求的用户
        return self.request.user

    # 重写这些方法是为了包裹 'user' 键，以符合你的原有 API 契约
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return APIResponse(user=serializer.data)

    def update(self, request, *args, **kwargs):
        # 💡 支持部分更新 (因为用户可能只改了简介，没换头像)
        partial = kwargs.pop('partial', True)  # 强制设为部分更新，容错率更高
        instance = self.get_object()

        # 💡 核心修改：不再去取嵌套的 request.data.get('user')，而是直接取 request.data 展平的数据
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # 💡 返回数据格式和 retrieve 保持一致，包裹在 'user' 键中返回
        return APIResponse(user=serializer.data)


class ProfileDetailView(viewsets.ReadOnlyModelViewSet):
    """
    处理 Profiles 列表和详情，以及关注逻辑
    """
    queryset = User.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'username'

    def get_serializer_class(self):
        """
        动态选择序列化器
        """
        # 💡 当执行 following 或 followers 动作时，使用不带计数的大规模列表序列化器
        if self.action in ['following', 'followers']:
            return ProfileListSerializer
        # 其他动作（如 retrieve 详情页）依然使用自带计数的 ProfileSerializer
        return self.serializer_class

    def list(self, request, *args, **kwargs):
        # 此处的日志会被自动记录到 info.log，因为 setup_logging 拦截了 django
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(profiles=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # 记得把 request 上下文传给 serializer，否则里面的 get_following 会因为找不到 request 永远返回 False
        serializer = self.get_serializer(instance, context={'request': request})
        return APIResponse(profiles=serializer.data)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def follow(self, request, **kwargs):
        profile = self.get_object()

        if request.user == profile:
            return APIResponse(code=103, msg="不能关注或取关自己")

        if request.method == 'POST':
            # 1. 数据库写入关系
            request.user.following.add(profile)
            # 2. 💡 工具类出马：实时让 Redis 两个集合对应更新
            ProfileCacheService.update_follow_relation(
                from_user_id=request.user.id,
                to_user_id=profile.id,
                is_follow=True
            )
            return APIResponse(msg="关注成功")  # 调用 Model 中定义的封装方法
        elif request.method == 'DELETE':
            # 1. 数据库解除关系
            request.user.following.remove(profile)
            # 2. 💡 工具类出马：实时让 Redis 对应移除
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
        获取该用户关注的人的列表
        URL: GET /api/profiles/{username}/following
        """
        # 1. 获取当前 URL 对应的目标用户实例
        profile_user = self.get_object()

        # 2. 从数据库获取该用户关注的所有人（可以通过 select_related/prefetch_related 优化）
        following_queryset = profile_user.following.all()

        # 3. 序列化这些用户资料。别忘了传递 context={'request': request} 保证关注状态动态计算正确
        serializer = self.get_serializer(following_queryset, many=True, context={'request': request})

        # 4. 统一用 APIResponse 格式返回
        return APIResponse(profiles=serializer.data)

    @action(detail=True, methods=['GET'], permission_classes=[IsAuthenticatedOrReadOnly])
    def followers(self, request, **kwargs):
        """
        获取关注该用户的人的列表（粉丝列表）
        URL: GET /api/profiles/{username}/followers
        """
        # 1. 获取目标用户
        profile_user = self.get_object()

        # 2. 获取粉丝集合
        followers_queryset = profile_user.followers.all()

        # 3. 序列化
        serializer = self.get_serializer(followers_queryset, many=True, context={'request': request})

        # 4. 返回
        return APIResponse(profiles=serializer.data)
