## 7. accounts 模块

### 7.1 模块职责

自定义用户认证与社交关系管理：email 登录、JWT 黑名单注销、用户资料管理、关注/粉丝关系（数据库 + Redis 双写双读）。

### 7.2 数据模型（[models.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/models.py)）

#### User（[L98-L298](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/models.py#L98-L298)）

继承 `AbstractUser`，email 登录模型。

| 字段        | 类型            | 关键约束                                                |
| --------- | ------------- | --------------------------------------------------- |
| email     | EmailField    | unique, db\_index（登录用户名）                            |
| username  | CharField(60) | unique, db\_index                                   |
| bio       | TextField     | blank                                               |
| image     | ImageField    | upload\_to='avatars/', null/blank                   |
| followers | M2M("self")   | symmetrical=False, related\_name="following"（自关联关注） |

- 移除 `first_name`、`last_name`
- `USERNAME_FIELD = "email"`、`REQUIRED_FIELDS = []`
- `objects = UserManager()`

**关注/取关操作**（[L211-L250](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/models.py#L211-L250)）：

- `follow(user)`：禁止关注自己；`following.add` 后用 `get_redis_connection` 双写 `sadd` 自己 following + 对方 followers
- `unfollow(user)`：对称 `srem`

**懒加载属性**（[L254-L298](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/models.py#L254-L298)）：

- `followers_count`（property）：Redis `exists` 判断 → `scard`；未命中查库 + `sadd` 回写
- `following_count`（property）：同上

> 注：模型层缓存只 `sadd` 不写 `-1` 占位符，与 Service 层策略不同。

#### UserManager（[L24-L95](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/models.py#L24-L95)）

- `create_user(email, password, **other)`：标准化 email、`set_unusable_password` 兜底
- `create_superuser`：默认 `is_staff/is_superuser/is_active=True`

### 7.3 URL 路由表（[urls.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/urls.py)）

使用 `SimpleRouter(trailing_slash=False)`：

| 路由                               | 视图                           | 方法            | 权限                           | 功能           |
| -------------------------------- | ---------------------------- | ------------- | ---------------------------- | ------------ |
| `/users/info`                    | UserView                     | GET/PUT/PATCH | IsAuthenticated              | 当前用户资料       |
| `/users/register`                | AuthViewSet\@register        | POST          | AllowAny                     | 注册           |
| `/users/login`                   | AuthViewSet\@login           | POST          | AllowAny + LoginRateThrottle | 登录获取 JWT     |
| `/users/logout`                  | AuthViewSet\@logout          | POST          | IsAuthenticated              | 注销（jti 入黑名单） |
| `/profiles/`                     | ProfileDetailView            | GET           | IsAuthenticatedOrReadOnly    | 用户列表         |
| `/profiles/{username}`           | ProfileDetailView            | GET           | IsAuthenticatedOrReadOnly    | 用户详情         |
| `/profiles/{username}/follow`    | ProfileDetailView\@follow    | POST/DELETE   | IsAuthenticated              | 关注/取关        |
| `/profiles/{username}/following` | ProfileDetailView\@following | GET           | IsAuthenticatedOrReadOnly    | 关注列表         |
| `/profiles/{username}/followers` | ProfileDetailView\@followers | GET           | IsAuthenticatedOrReadOnly    | 粉丝列表         |

### 7.4 视图说明（[views.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/views.py)）

#### AuthViewSet（[L33-L230](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/views.py#L33-L230)）

- 继承 `GenericViewSet`，permission=`AllowAny`
- `get_throttles()`：仅 `action=='login'` 时追加 `LoginRateThrottle`
- `register`（[L89-L122](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/views.py#L89-L122)）：用户名重名自动加 `_N` 后缀
- `login`（[L164-L202](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/views.py#L164-L202)）：`authenticate(email, password)` 校验，失败 `code=102, 401`；成功 `RefreshToken.for_user` 生成 token
- `logout`（[L204-L230](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/views.py#L204-L230)）：`JWTCacheService.add_to_blacklist(request.auth)`

#### UserView（[L233-L307](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/views.py#L233-L307)）

- 继承 `RetrieveUpdateAPIView`，permission=`IsAuthenticated`
- `parser_classes = [MultiPartParser, FormParser, JSONParser]`
- `get_serializer_class()`：PUT/PATCH → `UserUpdateSerializer`，GET → `UserSerializer`
- `get_object()`：直接返回 `request.user`
- `update()`：强制 `partial=True`，取 `request.data`（非嵌套 user 键）

#### ProfileDetailView（[L310-L474](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/views.py#L310-L474)）

- 继承 `ReadOnlyModelViewSet`，`lookup_field='username'`
- `get_serializer_class()`：following/followers → `ProfileListSerializer`，其他 → `ProfileSerializer`
- `retrieve()`：必须传 `context={'request': request}`（否则 `get_following` 永远 False）
- `follow` action（[L377-L426](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/views.py#L377-L426)）：禁止操作自己（`code=103`）；POST 走 `following.add` + `ProfileCacheService.update_follow_relation(is_follow=True)`；DELETE 对称

### 7.5 序列化器（[serializers.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/serializers.py)）

| 序列化器                    | 用途             | 关键设计                                                                                                                                                                                               |
| ----------------------- | -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `UserSerializer`        | 创建/登录返回        | `image` SerializerMethodField → `build_image_url`；`create` 调 `create_user`                                                                                                                         |
| `UserUpdateSerializer`  | 资料更新           | `avatar` write\_only ImageField；`process_image(max_width=512, max_height=512, quality=85, crop_square=True, convert_webp=True)` 头像压缩转 WebP；**更新后** **`cache.delete(f"user_instance_cache_{id}")`** |
| `ProfileSerializer`     | 用户详情（含关注状态+统计） | `following`/`followers_count`/`following_count` 走 `ProfileCacheService`；`collection_count` 直接查库                                                                                                    |
| `ProfileListSerializer` | 关注/粉丝列表（轻量）    | 去除计数字段，仅 `username/bio/image/following`                                                                                                                                                            |

### 7.6 服务层（[services.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/services.py)）

#### JWTCacheService（[L23-L105](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/services.py#L23-L105)）

JWT Token 黑名单管理（无状态 JWT + 黑名单注销机制）。

**缓存键**：`jwt:blacklist:{jti}`（String，TTL = Token 剩余有效期）

| 方法                          | 逻辑                                                                         |
| --------------------------- | -------------------------------------------------------------------------- |
| `add_to_blacklist(payload)` | 提取 `jti`/`exp` → 计算剩余秒数 → `setex(jwt:blacklist:{jti}, remaining, 1)`；已过期不入 |
| `is_blacklisted(jti)`       | jti 为空返回 True；否则 `exists(jwt:blacklist:{jti}) == 1`                        |
| `_get_con()`                | 兼容测试环境：Django 代理层穿透 `con.client.get_client()`                              |

#### ProfileCacheService（[L108-L333](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/services.py#L108-L333)）

用户资料与社交关系缓存。

**缓存键**：

- `user:{user_id}:following` → 关注 ID 集合（Set）
- `user:{user_id}:followers` → 粉丝 ID 集合（Set）

| 方法                                            | 关键逻辑                                                                                            |
| --------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `get_following_ids(user_id)`                  | `scard > 0` → `smembers`；未命中查库 + Pipeline 回写；空集合 `sadd(key, -1)` + `expire(600)` **防穿透**        |
| `is_following(cur, target)`                   | 复用上面 + Python `in`（O(1)）                                                                        |
| `get_followers_count(user_id)`                | `scard > 0` 时若 `sismember(-1)` 则 `total-1`；未命中查库 + 回写                                           |
| `get_following_count(user_id)`                | 复用 `get_following_ids`，若 `-1 in set` 返回 0                                                       |
| `get_collection_count(user_id)`               | **直接查库** `FormulaCollection.objects.filter(user_id=).count()`（无缓存）                              |
| `update_follow_relation(from, to, is_follow)` | **Pipeline 批量**：关注 → `sadd following` + `srem -1` + `sadd followers` + `srem -1`；取关 → 对称 `srem` |

**缓存策略**：

- 懒加载重建（exists/scard 判断命中）
- -1 占位符防穿透（10 分钟 TTL）
- Pipeline 批量减少网络往返
- 测试环境兼容（Django 缓存代理穿透）

### 7.7 认证与权限

#### CachedJWTAuthentication（[authentication.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/authentication.py)）

继承 `JWTAuthentication`，扩展缓存与黑名单。

**authenticate() 流程**（[L93-L142](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/authentication.py#L93-L142)）：

1. 提取 Authorization 头；为空返回 None
2. 验证签名/过期
3. **黑名单检查**：`jti = validated_token.get("jti")`，`JWTCacheService.is_blacklisted(jti)` 命中返回 None
4. `get_user(validated_token)` 返回用户实例
5. 返回 `(user, validated_token)` 或 None
6. **任何异常都返回 None，不抛 AuthenticationFailed**

**设计原因**：兼容 `IsAuthenticatedOrReadOnly`，让无 Token 的只读请求不被 401 拦截。

**get\_user() 缓存机制**（[L45-L91](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/authentication.py#L45-L91)）：

- 缓存键 `user_instance_cache_{user_id}`，TTL 1 小时
- **只存用户 ID 不存完整对象**（避免敏感信息泄露 + 减小缓存）
- 命中：`User.objects.get(id=cached_id)` 重新拉库
- 未命中：查库后 `cache.set(cache_key, user.id, timeout=60*60)`

> **修改用户状态后需清理 JWT 缓存**（`UserUpdateSerializer.update` 已实现 `cache.delete`）。

#### 权限类（[permissions.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/permissions.py)）

| 权限类                       | 适用场景        | 逻辑                                                                         |
| ------------------------- | ----------- | -------------------------------------------------------------------------- |
| `IsOwnerOrReadOnly`       | 帖子/通用资源编辑   | 读放行；写按字段优先级 `author → user → owner` 检查；回退 `is_staff`                       |
| `IsAdminOrReadOnly`       | 全局配置        | 读放行；写要求 `is_staff`                                                         |
| `IsAuthenticatedAndOwner` | 必须登录且操作自己资源 | has\_permission: is\_authenticated；has\_object\_permission: 检查 author/user |
| `IsSelfOrReadOnly`        | 用户资料管理      | 读放行；写要求 `obj == request.user`                                              |
| `IsFollowingOrReadOnly`   | 粉丝专属内容      | 读检查 `following.filter(id=obj.author.id).exists()`                          |

### 7.8 限流（[throttles.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/throttles.py)）

#### LoginRateThrottle（[L19-L74](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/throttles.py#L19-L74)）

- 继承 `SimpleRateThrottle`
- `scope = 'login_scope'`（settings 中 `5/minute`）
- **get\_cache\_key 三级过滤**：
  1. `view.action != 'login'` → None（仅对 login 动作）
  2. `request.data.get('user', {}).get('email', '')` 为空 → None
  3. `ident = self.get_ident(request)` 处理 X-Forwarded-For
- **限流键**：`throttle_login_scope_{IP}_{email}`（滑动窗口算法）

***
