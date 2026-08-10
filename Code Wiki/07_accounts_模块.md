## 7. accounts 模块

### 7.1 模块职责

自定义用户认证与社交关系管理：email 登录、JWT 黑名单注销、用户资料管理、关注/粉丝关系（数据库 + Redis 双写双读）。

### 7.2 数据模型（[models.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/models.py)）

#### User（[L99-L304](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/models.py#L99-L304)）

继承 `AbstractUser`，email 登录模型。字段分四类：继承自父类原样保留、重写覆盖、本项目新增、显式移除。

**继承自 AbstractBaseUser / PermissionsMixin（原样保留）**：

| 字段               | 类型              | 关键约束                          |
| ---------------- | --------------- | ----------------------------- |
| id               | BigAutoField    | 主键，自增                         |
| password         | CharField(128)  | 哈希存储，`set_password` 写入        |
| last_login       | DateTimeField   | null=True                     |
| is_superuser     | BooleanField    | default=False                 |
| groups           | M2M(Group)      | related\_name="user\_set"     |
| user_permissions | M2M(Permission) | related\_name="user\_set"     |

**继承自 AbstractUser（原样保留）**：

| 字段          | 类型            | 关键约束                  |
| ----------- | ------------- | --------------------- |
| is_staff    | BooleanField  | default=False         |
| is_active   | BooleanField  | default=True          |
| date_joined | DateTimeField | default=timezone.now  |

**重写覆盖**：

| 字段       | 类型            | 关键约束                                                          |
| -------- | ------------- | ------------------------------------------------------------- |
| email    | EmailField    | unique, db\_index（登录用户名，`USERNAME_FIELD`）                      |
| username | CharField(60) | unique, db\_index，`UnicodeUsernameValidator`，自定义 unique 错误提示 |

**新增字段**：

| 字段        | 类型           | 关键约束                                                |
| --------- | ------------ | --------------------------------------------------- |
| bio       | TextField    | blank                                               |
| image     | ImageField   | upload\_to='avatars/', null/blank                   |
| followers | M2M("self")  | symmetrical=False, related\_name="following"（自关联关注） |

**移除字段**：`first_name`、`last_name` 设为 `None`。

**认证与 Meta 配置**：

- `USERNAME_FIELD = "email"`、`EMAIL_FIELD = "email"`、`REQUIRED_FIELDS = []`
- `objects = UserManager()`
- `Meta`：`app_label='accounts'`、`verbose_name="用户"`、`ordering=["-date_joined"]`
- `__str__` 返回 `email`；`get_full_name`/`get_short_name` 返回 `username`

**关注/取关操作**（[L217-L256](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/models.py#L217-L256)）：

- `follow(user)`：禁止关注自己；`following.add` 后用 `get_redis_connection` 双写 `sadd` 自己 following + 对方 followers
- `unfollow(user)`：对称 `srem`

**懒加载属性**（[L260-L304](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/models.py#L260-L304)）：

- `followers_count`（property）：Redis `exists` 判断 → `scard`；未命中查库 + `sadd` 回写
- `following_count`（property）：同上

> 注：模型层缓存只 `sadd` 不写 `-1` 占位符，与 Service 层策略不同。

#### UserManager（[L25-L96](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/models.py#L25-L96)）

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

### 7.9 信号Signal（Signal.py）

#### ⚠️ `ready()` 方法的注意事项

- **避免执行耗时操作**：`ready()` 是在 Django 启动时执行的，如果里面有很慢的代码（比如复杂查询），会拖慢整个项目的启动过程。
- **只执行一次**：`ready()` 在 Django 的生命周期中只会被调用一次，适合做初始化工作。
- **注意导入循环**：在 `ready()` 方法里导入模块时，要小心循环导入的问题。

------

#### 💎 总结：你什么时候需要用到 `apps.py`？

- **必须**：你的应用中如果定义了信号（`signals.py`），就**必须**在 `apps.py` 的 `ready()` 方法中导入它。
- **推荐**：当你需要在应用启动时，执行一些初始化的“打扫”或“准备”工作时。
- **可选**：想给你的应用在后台改个更漂亮的名字时。

### 7.10 后台管理（[admin.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/admin.py)）

基于 django-unfold 定制用户后台，所有 Admin 类继承 `unfold.admin.ModelAdmin`（非原生 `admin.ModelAdmin`），提供 Tailwind CSS 样式、Tab 布局与高级过滤器。装饰器使用 Unfold 特有的 `@display`/`@action`（替代原生 `admin.display`/`admin.action`，额外支持样式参数）。

#### UserAdmin（[L33-L311](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/admin.py#L33-L311)）

`@admin.register(User)` 注册，针对 User 模型的后台管理。

**列表页配置**：

| 配置项                | 值                                                              | 说明                          |
| ------------------ | -------------------------------------------------------------- | --------------------------- |
| list_display       | avatar_preview, email, username, followers_count, following_count, date_joined, status_badge | 头像/状态为 `@display` 自定义列     |
| list_display_links | email                                                          | 仅邮箱可点击进入编辑                  |
| search_fields      | email, username                                                | 模糊搜索                        |
| list_filter        | is_active, is_staff, date_joined                               | 侧边栏过滤                       |
| list_per_page      | 50                                                             | 兼顾浏览效率与分页频率                 |
| ordering           | -date_joined                                                   | 最新注册排前                      |

**编辑页配置**：

| 配置项               | 说明                                                                   |
| ----------------- | -------------------------------------------------------------------- |
| readonly_fields   | date_joined, last_login, password_display（密码哈希不展示明文）                 |
| fieldsets         | 基本信息 / 权限控制 / 重要时间戳（collapse 折叠）/ 密码安全提示 四组                          |
| filter_horizontal | groups, user_permissions（M2M 水平选择器）                                  |

**自定义列**（`@display` 装饰器）：

| 方法                | 说明                                                |
| ----------------- | ------------------------------------------------- |
| avatar_preview    | 40x40 圆形头像缩略图；无头像显示 N/A 占位；`escape` 防 XSS        |
| status_badge      | is_active 渲染为绿/红 Badge 标签                         |
| password_display  | 密码安全提示文本（不展示哈希），引导使用「修改密码」链接                      |
| followers_count   | 取 `obj.followers_count`（Redis 缓存，O(1)）            |
| following_count   | 取 `obj.following_count`（Redis 缓存，O(1)）            |

**批量操作**（`@action` 装饰器）：

| 方法             | 说明                                                       |
| -------------- | -------------------------------------------------------- |
| disable_users  | `queryset.update(is_active=False)` 批量禁用，`message_user` 反馈 |
| enable_users   | `queryset.update(is_active=True)` 批量解冻                   |

> 注：批量 `update()` 不触发 `save()` 与信号，适合纯状态切换；密码修改走 Django 内置 change_password 链接。
