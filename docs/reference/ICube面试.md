# ICube 面试

## 目录(TOC)

- [项目核心信息](#项目核心信息)
- [面试必掌握知识点](#面试必掌握知识点)
  - [后端重点](#后端重点)
    - [1. 后台管理系统 (django-unfold)](#1-后台管理系统-django-unfold)
    - [2. 自定义JWT认证](#2-自定义jwt认证)
    - [3. 统一响应格式](#3-统一响应格式)
    - [4. 权限系统](#4-权限系统)
    - [5. 限流机制](#5-限流机制)
    - [6. 事务处理与库存扣减](#6-事务处理与库存扣减)
    - [7. 支付宝支付集成](#7-支付宝支付集成)
    - [8. 数据库设计](#8-数据库设计)
    - [9. 日志系统](#9-日志系统)
    - [10. 图片上传与URL管理](#10-图片上传与url管理)
    - [11. 浏览量统计](#11-浏览量统计)
    - [12. 图片处理流水线](#12-图片处理流水线)
    - [13. 公式图片双字段设计](#13-公式图片双字段设计)
    - [14. 目标状态自动绑定](#14-目标状态自动绑定)
    - [15. 作者筛选与权限控制](#15-作者筛选与权限控制)
    - [16. 自定义公式分类](#16-自定义公式分类)
    - [17. 公式编辑逆公式同步](#17-公式编辑逆公式同步)
    - [18. 公式卡片样式优化](#18-公式卡片样式优化)
    - [19. 自定义用户模型与缓存](#19-自定义用户模型与缓存)
    - [20. ORM查询优化](#20-orm查询优化)
    - [21. 序列化器设计](#21-序列化器设计)
    - [22. ViewSet与Action](#22-viewset与action)
    - [23. Redis缓存与三问](#23-redis缓存与三问)
    - [24. Django信号](#24-django信号)
    - [25. 环境与配置](#25-环境与配置)
    - [26. Service层模式](#26-service层模式)
  - [前端重点](#前端重点)
  - [部署重点](#部署重点)
- [已优化项](#已优化项)
- [项目不足与改进建议](#项目不足与改进建议)
- [面试回答技巧](#面试回答技巧)
- [面试常见问题预测](#面试常见问题预测)
- [后端深度面试问题扩展](#后端深度面试问题扩展)

---

## 项目核心信息

### 项目定位
**ICube — 魔方学习平台**，基于 Django + Vue 3 的全栈项目，提供公式库、3D可视化、教程学习、计时器、论坛、商城等功能。使用 Docker Compose 进行容器化部署，支持生产环境变量配置。

### 技术栈
| 层级   | 技术                   | 版本      |
| ------ | ---------------------- | --------- |
| 后端   | Django + DRF           | 6.0.5     |
| 前端   | Vue 3 + Vite           | 3.5.32 + 8.0.8 |
| 数据库 | MySQL + Redis          | 8.0 + 7   |
| 前端UI | Element Plus           | 2.14.0    |
| 3D渲染 | Three.js + Tween.js    | 0.184 + 25.0 |
| 认证   | SimpleJWT              | 5.5.1     |
| 支付   | Python Alipay SDK      | 3.4.0     |
| 部署   | Docker Compose + Nginx | -         |

### 核心功能模块

| 模块         | 功能                           | 关键技术点                   |
| ------------ | ------------------------------ | ---------------------------- |
| **accounts** | 用户认证、JWT、关注系统        | 自定义JWT、Redis缓存、黑名单 |
| **forum**    | 帖子、评论、点赞、收藏、举报、图片上传与预览   | 软删除、多表关联、全量同步、独立上传接口   |
| **formula**  | 公式库、浏览量统计、3D可视化、用户上传、作者筛选、自定义分类、公式卡片优化   | JSON状态定义、逆公式计算、F表达式原子更新、图片压缩裁剪、权限控制、分类权限过滤 |
| **shop**     | 商品、购物车、订单、支付宝支付 | 事务、库存扣减、异步回调     |
| **home**     | 首页菜单、轮播图、精选公式、教程入口   | 基础CRUD、浏览量排序、图片预览、状态管理         |
| **timer**    | 计时记录、成绩统计             | 毫秒级计时、数据库存储       |

---

## 面试必掌握知识点

### 后端重点

#### 1. 后台管理系统 (django-unfold)
**文件**: [accounts/admin.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/admin.py), [shop/admin.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/shop/admin.py), [forum/admin.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/admin.py)

**核心实现**:
- **django-unfold**: 基于 Tailwind CSS 的现代化后台管理框架，替代原生 Django Admin
- **统一继承**: 所有 Admin 类继承自 `unfold.admin.ModelAdmin`，而非 `admin.ModelAdmin`
- **@display 装饰器**: 自定义列表页列，替代原生 `admin.display`，支持 Badge 样式
- **@action 装饰器**: 定义批量操作，替代原生 `admin.action`

**关键技术点**:

**(1) @display 装饰器实现状态 Badge**
```python
from unfold.admin import ModelAdmin
from unfold.decorators import display, action

@admin.register(User)
class UserAdmin(ModelAdmin):
    list_display = ('avatar_preview', 'email', 'status_badge')
    
    @display(description="状态", boolean=False)
    def status_badge(self, obj):
        if obj.is_active:
            return mark_safe('<span class="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">激活</span>')
        return mark_safe('<span class="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">禁用</span>')
```

**(2) 头像预览列**
```python
@display(description="头像", ordering="image")
def avatar_preview(self, obj):
    if obj.image and hasattr(obj.image, 'url'):
        return mark_safe(
            f'<img src="{escape(obj.image.url)}" '
            f'style="width:40px;height:40px;border-radius:50%;object-fit:cover;" />'
        )
    return mark_safe(
        '<div style="width:40px;height:40px;border-radius:50%;background:#e5e7eb;'
        'display:flex;align-items:center;justify-content:center;font-size:12px;color:#9ca3af;">N/A</div>'
    )
```

**(3) @action 批量操作**
```python
@action(description="批量禁用选中用户")
def disable_users(self, request, queryset):
    updated = queryset.update(is_active=False)
    self.message_user(request, f"成功禁用 {updated} 个用户账号")

actions = ("disable_users", "enable_users")
```

**(4) Fieldsets 分组配置**
```python
fieldsets = (
    ("基本信息", {
        "fields": ("email", "username", "image", "bio"),
    }),
    ("权限控制", {
        "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
    }),
    ("重要时间戳", {
        "fields": ("date_joined", "last_login"),
        "classes": ("collapse",),  # 默认折叠
    }),
)
```

**侧边栏配置**:
**文件**: [dev.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L430)
```python
UNFOLD = {
    "SITE_TITLE": "ICube",
    "SITE_HEADER": "ICube 管理后台",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {"title": "认证和授权", "icon": "lock", "collapsible": True, "items": [...]},
            {"title": "Accounts", "icon": "people", "collapsible": True, "items": [...]},
            {"title": "论坛", "icon": "message", "collapsible": True, "items": [...]},
            # ... 其他分组
        ],
    },
}
```

**各模块 Admin 特色**:

| 模块 | Admin类 | 特色功能 |
|------|---------|----------|
| accounts | UserAdmin | 头像预览、状态Badge、密码安全提示、批量禁用/解冻 |
| forum | PostAdmin | 状态Badge、置顶/精华标记、批量置顶/加精/软删除 |
| forum | ReportAdmin | 举报原因Badge、内容类型Badge、批量处理/驳回 |
| shop | ProductAdmin | 缩略图预览、库存状态Badge、批量上架/下架 |
| shop | OrderAdmin | 订单状态Badge、批量发货/完成、时间层级导航 |

**模板覆盖**:
- 通过项目 `templates/unfold/helpers/app_list.html` 覆盖 unfold 包内模板
- 修改一级目录标题字体大小从 `text-sm`（14px）改为 `text-base`（16px），子目录保持默认

---

#### 2. 自定义JWT认证
**文件**: [authentication.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/authentication.py)

**核心实现**:
- **CachedJWTAuthentication**：继承 `JWTAuthentication`，在认证流程中加入 Redis 缓存
- **用户缓存策略**:
  - 缓存 Key: `user_instance_cache_{user_id}`
  - TTL: 1小时 (60*60秒)
  - 缓存内容: 仅存储用户 ID，避免序列化开销，查询时根据 ID 获取完整对象
- **JWT黑名单机制**:
  - 注销时将 `jti` (JWT ID) 存入 Redis 黑名单
  - 认证时检查 `JWTCacheService.is_blacklisted(jti)`
  - 防止 token 被复用
- **Token前缀**: 使用 `Token` 而非标准 `Bearer`
- **认证失败处理**: Token 验证失败时返回 `None` 而非抛出 `AuthenticationFailed` 异常，以兼容 `IsAuthenticatedOrReadOnly` 权限

**认证流程**:
```
请求 → 提取Header → 验证Token签名/时效 → 检查jti黑名单 → 从Redis缓存获取用户 → 认证成功
```

##### 深度讲解:JWT认证流程详解

**JWT 认证体系架构**：本项目基于 `django-rest-framework-simplejwt` 扩展，整体架构：

```
客户端
  │
  ├─ 登录：POST /api/auth/login/
  │   → 邮箱 + 密码 → 验证 → 返回 access_token + refresh_token
  │
  ├─ 请求：Authorization: Token <access_token>
  │   → CachedJWTAuthentication.authenticate()
  │       ├── 提取 Token
  │       ├── 验证签名 + 过期
  │       ├── 检查黑名单（退出登录的 Token）
  │       └── get_user() → Redis 缓存 → DB
  │
  └─ 退出：POST /api/auth/logout/
      → access_token 的 jti 加入 Redis 黑名单
```

**`CachedJWTAuthentication.authenticate()` —— 认证入口**

代码位置：[accounts/authentication.py#L93-L142](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\accounts\authentication.py#L93-L142)

```python
def authenticate(self, request):
    # 1. 提取 Authorization 头
    header = self.get_header(request)        # "Token eyJ0eXAi..."
    if header is None:
        return None                          # 无 Token → 视为未认证

    # 2. 提取原始 Token
    raw_token = self.get_raw_token(header)   # "eyJ0eXAi..."
    if raw_token is None:
        return None

    try:
        # 3. 验证 Token（签名 + 过期 + 算法）
        validated_token = self.get_validated_token(raw_token)
        # validated_token = {'user_id': 1, 'jti': 'abc123', 'exp': 1750000000, ...}

        # 4. 检查黑名单
        jti = validated_token.get("jti")
        if JWTCacheService.is_blacklisted(jti):
            return None                      # 已退出的 Token

        # 5. 获取用户
        user = self.get_user(validated_token)

        # 6. 返回 (user, token) 元组
        return user, validated_token
    except Exception:
        # 任何异常 → 返回 None（而非抛异常）
        return None
```

**关键设计决策**：返回 `None` 而非抛 `AuthenticationFailed`，兼容 `IsAuthenticatedOrReadOnly` 权限类。

| 场景                    | 返回 None            | 抛 AuthenticationFailed |
| ----------------------- | -------------------- | ----------------------- |
| 无 Token                | 未认证（读操作放行） | 未认证（读操作也 401）  |
| Token 无效              | 未认证（读操作放行） | 401                     |
| Token 在黑名单          | 未认证（读操作放行） | 401                     |
| Token 有效 + 用户不存在 | 未认证（读操作放行） | 401                     |

**`get_user()` —— 用户缓存机制**

代码位置：[accounts/authentication.py#L45-L91](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\accounts\authentication.py#L45-L91)

```python
def get_user(self, validated_token):
    user_id = validated_token.get('user_id')
    cache_key = f"user_instance_cache_{user_id}"

    # 1. 查 Redis 缓存（只存 ID）
    cached_user_id = cache.get(cache_key)
    if cached_user_id:
        try:
            return User.objects.get(id=cached_user_id)  # 根据 ID 查 DB
        except User.DoesNotExist:
            return None

    # 2. 缓存未命中：查 DB + 回写缓存
    try:
        user = User.objects.get(id=user_id)
        cache.set(cache_key, user.id, timeout=3600)  # 存 ID，TTL 1 小时
        return user
    except User.DoesNotExist:
        return None
```

**缓存策略详解**：

| 设计决策                      | 原因                                                         |
| ----------------------------- | ------------------------------------------------------------ |
| 只存 ID，不存完整对象         | 减少 Redis 内存占用；避免 User 对象序列化/反序列化开销；保证数据一致性 |
| TTL 1 小时                    | 平衡性能与一致性；用户修改后最多 1 小时生效                  |
| 缓存 ID 后仍查 DB             | ID → DB 查询轻量（主键索引），保证最新数据                   |
| `User.DoesNotExist` 返回 None | Token 有效但用户被删除时，认证失败                           |

**Token 前缀配置**：

```python
SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('Token',),  # 自定义前缀（非默认的 Bearer）
}
```

**JWT 认证完整流程图**：

```
请求 → Authorization: Token eyJ...
  │
  ├─ authenticate(request)
  │   │
  │   ├─ get_header(request) → "Token eyJ..."
  │   │   └─ 无 Token → return None（未认证）
  │   │
  │   ├─ get_raw_token(header) → "eyJ..."
  │   │   └─ 格式错误 → return None
  │   │
  │   ├─ get_validated_token(raw_token)
  │   │   ├─ 验证签名（SECRET_KEY）
  │   │   ├─ 验证过期时间（exp）
  │   │   └─ 解析载荷 → {'user_id': 1, 'jti': 'abc', 'exp': ...}
  │   │   └─ 验证失败 → return None
  │   │
  │   ├─ is_blacklisted(jti)
  │   │   └─ 在黑名单 → return None
  │   │
  │   ├─ get_user(validated_token)
  │   │   ├─ Redis 查 user_instance_cache_1
  │   │   │   ├─ 命中 → User.objects.get(id=1)
  │   │   │   └─ 未命中 → User.objects.get(id=1) + 回写缓存
  │   │   └─ 用户不存在 → return None
  │   │
  │   └─ return (user, validated_token)
  │
  └─ DRF 权限检查
      ├─ IsAuthenticatedOrReadOnly + SAFE_METHODS → 放行
      └─ IsAuthenticated → 未认证时 401
```

##### 深度讲解:Token黑名单机制详解

**为什么需要 Token 黑名单**：JWT 是**无状态**的，一旦签发，在过期前无法主动使其失效。

```
1. 用户登录 → 获得 Token（有效期 2 小时）
2. 用户修改密码 → 旧 Token 应立即失效
3. 用户退出登录 → Token 应立即失效
4. 管理员强制下线 → Token 应立即失效
5. Token 泄露 → 需要立即作废

如果没有黑名单：
  退出登录后，Token 在 2 小时内仍可使用 → 安全隐患
```

**`JWTCacheService` 实现详解**

代码位置：[accounts/services.py#L23-L105](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\accounts\services.py#L23-L105)

**`add_to_blacklist()` —— 加入黑名单**：

```python
@classmethod
def add_to_blacklist(cls, payload: dict):
    con = cls._get_con()

    # 1. 提取 jti（JWT ID，每个 Token 唯一）
    jti = payload.get("jti")
    if not jti:
        return

    # 2. 计算剩余有效期
    exp_timestamp = payload.get("exp")
    now_timestamp = int(datetime.datetime.now(
        datetime.timezone.utc
    ).timestamp())
    remaining_seconds = exp_timestamp - now_timestamp

    # 3. 未过期才加入黑名单
    if remaining_seconds > 0:
        redis_key = f"jwt:blacklist:{jti}"
        con.setex(redis_key, remaining_seconds, 1)  # SETEX: key + TTL + value
```

| 决策                   | 原因                                    |
| ---------------------- | --------------------------------------- |
| 用 `jti` 作为黑名单键  | JWT 规范中 jti 是每个 Token 的唯一标识  |
| TTL = Token 剩余有效期 | Token 过期后自动从黑名单移除，节省内存  |
| `setex` 原子操作       | 设置键 + 过期时间一步完成，避免中间状态 |
| value 存 `1`           | 只需占位符，无需存储实际内容            |
| 已过期的 Token 不加入  | 没有意义，反正会自然过期                |

**`is_blacklisted()` —— 检查黑名单**：

```python
@classmethod
def is_blacklisted(cls, jti: str) -> bool:
    if not jti:
        return True             # jti 为空 → 视为无效
    con = cls._get_con()
    return con.exists(f"jwt:blacklist:{jti}") == 1
```

**登出接口实现**：

代码位置：[accounts/views.py](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\accounts\views.py)

```python
@action(detail=False, methods=['POST'], permission_classes=[IsAuthenticated])
def logout(self, request):
    """用户退出登录"""
    try:
        token = request.auth  # SimpleJWT 自动解析的 token 对象
        if token:
            JWTCacheService.add_to_blacklist(token.payload)
    except Exception:
        pass  # 即使失败也返回成功（前端已退出）

    return APIResponse(msg="退出成功")
```

**对比其他 Token 失效方案**：

| 方案                         | 原理                                             | 优点               | 缺点                       |
| ---------------------------- | ------------------------------------------------ | ------------------ | -------------------------- |
| **Redis 黑名单（本项目）**   | Token 加入黑名单，TTL = 剩余有效期               | 简单高效，自动清理 | 需维护 Redis               |
| **修改密钥**                 | 修改 SECRET_KEY 使所有 Token 失效                | 彻底               | 影响所有用户，无法定向失效 |
| **短有效期 + Refresh Token** | access_token 短（5min），refresh_token 长（7天） | 无需黑名单         | 用户体验差，需频繁刷新     |
| **版本号机制**               | User 模型加 token_version，改密码时 +1           | 简单               | 每次请求需查 DB 验证版本号 |

##### **补充提问**

**缓存击穿/穿透的防护**：

- 当大量并发请求携带同一个失效或不存在的 `user_id` 的 Token 访问时，可能会瞬间穿透 Redis 压向数据库。可以向面试官提及，如果后续要进一步优化，可以在 `User.DoesNotExist` 时给 Redis 写入一个空值（比如特殊的标记或短期的 Null 缓存），防止恶意请求穿透。

**登出黑名单的过期时间设计**：

- 写入 Redis 黑名单的 `jti` 应该设置多长的过期时间？通常可以将其过期时间设置为**与该 Token 剩余的有效时间一致**，这样当 Token 自然过期后，黑名单里的 `jti` 也会自动被 Redis 回收，节省内存空间。

#### 3. 统一响应格式

**文件**: [common_response.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/utils/common_response.py)

**设计要点**:
- `APIResponse(code=100, msg='请求成功', **kwargs)` 统一封装
- 成功码固定为 `100`，前端拦截器以此判断业务成功
- 支持分页响应 `PaginatedResponse`，自动封装 count/next/previous/results

**响应结构**:
```json
{
  "code": 100,
  "msg": "请求成功",
  "data": { ... }
}
```

**业务状态码约定**:

| code | 含义 | 对应 HTTP | 场景 |
|------|------|-----------|------|
| **100** | 请求成功 | 200/201 | 正常响应 |
| **102** | 邮箱或密码错误 | 401 | 登录失败 |
| **400** | 参数错误 | 400 | 参数校验失败 |
| **403** | 权限不足 | 403 | 无权限访问 |
| **404** | 资源不存在 | 404 | 查询的资源不存在 |
| **998** | 业务逻辑错误 | 400/401/403 | 可预期的客户端错误 |
| **999** | 系统内部错误 | 500 | 不可预期的服务端异常 |

##### 深度讲解:APIResponse设计

**为什么需要统一响应格式？**

**问题**：DRF 默认 `Response` 只返回裸数据，前端需要根据不同接口判断响应结构，逻辑混乱。

```
DRF 默认响应（不统一）：
  GET  /users/       → [{id:1, name:'a'}, ...]
  POST /users/       → {id:1, name:'a', email:'a@b.com'}
  GET  /users/1/     → {id:1, name:'a'}
  DELETE /users/1/   → 无内容（204 No Content）
  错误响应            → {detail: 'Not found'}
```

**解决方案**：统一 `{code, msg, data}` 结构，前端只需判断 `code`：

```
统一响应（结构化）：
  成功：{code: 100, msg: '请求成功', data: {...}}
  失败：{code: 998, msg: '参数错误', data: null}
  系统错误：{code: 999, msg: '系统开小差了', data: null}
```

**APIResponse 核心实现**

**位置**：[common_response.py#L29-L73](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\utils\common_response.py#L29-L73)

```python
class APIResponse(Response):
    def __init__(self, code=100, msg='请求成功', status=200, headers={}, **kwargs):
        data = {'code': code, 'msg': msg}
        if kwargs:
            data.update(kwargs)   # 额外字段合并到 data
        super().__init__(data=data, status=status, headers=headers)
```

**使用示例**：

```python
# 基本用法
APIResponse()
# → {"code": 100, "msg": "请求成功"}

# 带业务数据（方式一：data 参数）
APIResponse(data={"user": user_data}, msg="登录成功")
# → {"code": 100, "msg": "登录成功", "data": {"user": {...}}}

# 带业务数据（方式二：kwargs 直接平铺 —— 常用！）
APIResponse(user=serializer.data, token=tokens)
# → {"code": 100, "msg": "请求成功", "user": {...}, "token": "xxx"}

# 业务错误
APIResponse(code=998, msg="参数校验失败", status=400)
# → HTTP 400, {"code": 998, "msg": "参数校验失败"}
```

**kwargs 技巧**：本项目常用 `APIResponse(user=serializer.data)` 而非 `APIResponse(data={...})`，因为：

```python
# accounts/views.py — 登录接口
return APIResponse(user=serializer.data)
# → {"code": 100, "msg": "请求成功", "user": {...}}

# accounts/views.py — 注册接口
return APIResponse(user=serializer.data, status=status.HTTP_201_CREATED)
# → HTTP 201, {"code": 100, "msg": "请求成功", "user": {...}}

# accounts/views.py — 登录失败
return APIResponse(code=102, msg="邮箱或密码错误", status=status.HTTP_401_UNAUTHORIZED)
# → HTTP 401, {"code": 102, "msg": "邮箱或密码错误"}
```

**两层状态码设计**：

| 层级 | 状态码 | 用途 | 处理方 |
|------|--------|------|--------|
| **网络层** | HTTP Status（200/400/401/403/500） | 网络请求成功/失败 | 浏览器/网关/CDN |
| **业务层** | `code`（100/400/403/404/998/999） | 业务逻辑成功/失败 | 前端 JS 代码 |

**前端拦截器配合**

**位置**：[request.js#L56-L81](file:///e:\BH\PyStudy\ICube\cube_front\src\http\request.js#L56-L81)

```javascript
service.interceptors.response.use(
    response => {
        const res = response.data
        // 业务成功：code === 100，直接返回响应数据
        if (res.code !== 100) {
            ElMessage({
                type: 'error',
                message: !res.msg ? '请求服务器异常,请联系管理员' : res.msg
            })
            return Promise.reject(new Error(res.msg || 'Error'))
        } else {
            return res  // {code: 100, msg: '...', data: {...}}
        }
    },
    error => {
        const error_msg = error.response?.data?.msg
        ElMessage({
            type: 'error',
            message: !error_msg ? '请求服务器异常,请联系管理员' : error_msg
        })
        return Promise.reject(error)
    }
)
```

**设计模式总结**：

| 模式 | 实现 | 目的 |
|------|------|------|
| **统一响应** | 继承 `Response` 封装 `code/msg/data` | 前端只需判断 code |
| **分层状态码** | HTTP Status（网络层）+ code（业务层） | 职责分离 |
| **策略模式** | kwargs 动态添加字段 | 灵活适配不同接口 |
| **模板方法** | `get_paginated_response()` 重写 | 统一分页格式 |
| **装饰器模式** | 全局异常处理器 | 零侵入异常处理 |

##### 深度讲解:全局异常处理

**为什么需要全局异常处理？**

DRF 默认异常处理存在三个不足：

| 问题 | 说明 |
|------|------|
| **格式不统一** | 默认返回 `{"detail": "错误信息"}`，与 `APIResponse` 格式不一致 |
| **日志缺失** | 默认不记录业务日志，生产环境排查困难 |
| **敏感信息泄露** | 开发模式下可能暴露堆栈、SQL 语句等敏感信息 |

**配置方式**：

```python
# settings/dev.py#L298
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'utils.common_exception.common_exception_handler',
}
```

**异常处理流程**

**位置**：[common_exception.py#L35-L127](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\utils\common_exception.py#L35-L127)

```
请求 → DRF View
  │
  ├─ 正常返回
  │   └─ APIResponse(code=100) → 前端成功
  │
  ├─ 异常抛出
  │   │
  │   ├─ 情况 A: DRF 已处理异常
  │   │   ├─ ValidationError（参数校验失败）
  │   │   ├─ PermissionDenied（权限不足）
  │   │   ├─ AuthenticationFailed（认证失败）
  │   │   ├─ NotFound（资源不存在）
  │   │   └─ → DRF exception_handler() 返回 Response
  │   │       → common_exception_handler 包装为 code=998
  │   │       → loguru.warning() 记录日志
  │   │
  │   └─ 情况 B: 系统级异常
  │       ├─ DatabaseError（数据库连接失败）
  │       ├─ ValueError / TypeError（代码 bug）
  │       ├─ Redis 连接超时
  │       └─ → DRF exception_handler() 返回 None
  │           → common_exception_handler 返回 code=999
  │           → loguru.error() 记录日志（含堆栈）
  │
  └─ 统一 APIResponse 格式返回前端
```

**核心实现**：

```python
def common_exception_handler(exc, context):
    # ============ 第一步：提取诊断信息 ============
    request = context.get('request')
    view = context.get('view')
    user = getattr(request.user, 'email', 'Anonymous')
    path = request.path
    method = request.method
    view_name = f"{view.__class__.__module__}.{view.__class__.__name__}"

    # ============ 第二步：调用 DRF 原生处理器 ============
    response = drf_exception_handler(exc, context)

    # ============ 第三步：区分异常类型 ============

    # --- 情况 A: DRF 已处理的异常（业务错误） ---
    if response is not None:
        msg = _format_error_message(response.data, exc)
        logger.bind(user=user, path=path, method=method, view=view_name).warning(
            f"Business Error | {msg}"
        )
        return APIResponse(code=998, msg=msg, status=response.status_code)

    # --- 情况 B: 系统级异常 ---
    logger.bind(user=user, path=path, method=method, view=view_name).error(
        f"Internal Server Error | Detail: {str(exc)}"
    )
    return APIResponse(
        code=999,
        msg="系统开小差了，请稍后再试",
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
```

**错误消息格式化**：

DRF 错误响应有三种格式，需要统一提取：

```python
def _format_error_message(data, exc):
    # 类型一：字典格式（如 ValidationError 的字段错误）
    if isinstance(response.data, dict):
        if isinstance(exc, ValidationError):
            first_field = next(iter(response.data))
            first_error = response.data[first_field]
            msg = f"{first_field}: {first_error[0] if isinstance(first_error, list) else first_error}"
        else:
            msg = response.data.get('detail') or str(response.data)
    # 类型二：列表格式
    elif isinstance(response.data, list):
        msg = response.data[0]
    # 类型三：其他格式
    else:
        msg = str(response.data)
    return msg
```

**日志分层策略**：

| 级别 | 适用场景 | 日志内容 | 处理方式 |
|------|----------|----------|----------|
| **WARNING** | 业务错误（code=998） | 用户、路径、方法、错误消息 | 日志文件 + 正常运行 |
| **ERROR** | 系统错误（code=999） | 用户、路径、方法、异常详情 + 堆栈 | 日志文件 + 报警通知 |

##### 深度讲解:自定义分页器

**为什么需要自定义分页器？**

DRF 默认分页响应格式与项目的 `APIResponse` 统一格式不一致：

```
DRF 默认分页响应：
{
    "count": 100,
    "next": "?page=2",
    "previous": null,
    "results": [...]
}

项目统一格式（APIResponse）：
{
    "code": 100,
    "msg": "请求成功",
    "data": {
        "count": 100,
        "next": "?page=2",
        "previous": null,
        "results": [...]
    }
}
```

前端拦截器只认 `code === 100`，如果不重写，分页接口返回的数据会被拦截器当作错误处理。

**DRF 分页机制回顾**：

| 分页器 | 原理 | URL 参数 | 适用场景 |
|--------|------|----------|----------|
| `PageNumberPagination` | 页码分页 | `?page=2&page_size=20` | 通用列表 |
| `LimitOffsetPagination` | 偏移量分页 | `?limit=20&offset=40` | 无限滚动 |
| `CursorPagination` | 游标分页 | `?cursor=abc123` | 大数据集、实时流 |

**UnifiedPagination 核心实现**

**位置**：[common_pagination.py#L33-L125](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\utils\common_pagination.py#L33-L125)

```python
class UnifiedPagination(PageNumberPagination):
    page_size = 20                          # 默认每页 20 条
    page_size_query_param = 'page_size'     # 前端可自定义每页条数
    max_page_size = 100                     # 最大每页 100 条
    page_query_param = 'page'               # 页码参数名

    def get_paginated_response(self, data):
        """重写响应方法，用 APIResponse 包装"""
        return APIResponse(
            data={
                'count': self.page.paginator.count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'results': data
            }
        )
```

**三级分页器继承体系**：

```
UnifiedPagination (page_size=20, max=100)
    │
    ├─ LargeResultsSetPagination (page_size=50, max=500)
    │   → 适用于数据量大的列表页（商品、帖子）
    │
    └─ SmallResultsSetPagination (page_size=10, max=50)
        → 适用于管理后台（订单、用户管理）
```

| 分页器 | page_size | max_page_size | 适用场景 | 继承关系 |
|--------|-----------|---------------|----------|----------|
| `UnifiedPagination` | 20 | 100 | 默认全局分页器 | 继承 `PageNumberPagination` |
| `LargeResultsSetPagination` | 50 | 500 | 商品列表、帖子列表 | 继承 `UnifiedPagination` |
| `SmallResultsSetPagination` | 10 | 50 | 订单管理、用户管理 | 继承 `UnifiedPagination` |

**全局配置与单视图覆盖**：

```python
# 全局配置（settings/dev.py#L295-L296）
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'utils.common_pagination.UnifiedPagination',
    'PAGE_SIZE': 20,
}

# 单视图定制
class PostViewSet(viewsets.ModelViewSet):
    pagination_class = LargeResultsSetPagination  # 每页 50 条

# 禁用分页（如商品分类列表，数据量少）
pagination_class = None
```

#### 4. 权限系统
**文件**: [permissions.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/permissions.py)

**自定义权限类**:
- `IsOwnerOrReadOnly`：适配多种模型（author/user/owner字段），只读请求放行，写请求验证所有者
- `IsSelfOrReadOnly`：用户只能操作自己的资料
- `IsAdminOrReadOnly`：管理员可写，其他只读
- `IsFollowingOrReadOnly`：关注者可见
- `IsAdminOrCustomCreator`：管理员或自定义创建者可写

##### 深度讲解:自定义权限类详解

**DRF 权限系统架构**

DRF 权限类基于 **BasePermission** 基类，两个核心方法：

```python
class BasePermission:
    def has_permission(self, request, view):
        """视图级权限：请求到达视图前调用，无对象"""
        return True  # 允许

    def has_object_permission(self, request, view, obj):
        """对象级权限：获取到对象后调用，针对单个资源"""
        return True  # 允许
```

**权限检查流程**：

```
请求 → dispatch()
  → initial()   ← 认证 + has_permission() 视图级检查
  → get_object()
  → check_object_permissions()  ← has_object_permission() 对象级检查
  → 执行 action
```

**`SAFE_METHODS` —— 只读请求判断**

DRF 将 GET、HEAD、OPTIONS 三种方法标记为"安全方法"（不会修改数据）：

```python
permissions.SAFE_METHODS == ('GET', 'HEAD', 'OPTIONS')
```

**`IsOwnerOrReadOnly` —— 最常用的权限类**

**代码位置**：[accounts/permissions.py#L22-L62](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\accounts\permissions.py#L22-L62)

```python
class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # 1. 读权限：任何人可读
        if request.method in permissions.SAFE_METHODS:
            return True

        # 2. 写权限：只有所有者才能修改
        # 自动适配不同模型的所有者字段
        if hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        else:
            for field_name in ['author', 'user', 'creator', 'owner']:
                if hasattr(obj, field_name):
                    return getattr(obj, field_name) == request.user

        # 3. 找不到所有者字段 → 只有管理员能修改
        return request.user.is_staff
```

**三层判断逻辑**：

```
请求到达 → has_object_permission()
  │
  ├─ SAFE_METHODS? → ✅ 放行
  │
  ├─ 有 author/user/owner 字段?
  │   └─ 是所有者? → ✅ 放行
  │   └─ 不是? → ❌ 拒绝
  │
  └─ 无所有者字段? → 管理员? → ✅ / ❌
```

**`IsAdminOrReadOnly` —— 管理员权限**

```python
class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
```

| 维度       | IsOwnerOrReadOnly                 | IsAdminOrReadOnly          |
| ---------- | --------------------------------- | -------------------------- |
| 检查层级   | 对象级（`has_object_permission`） | 视图级（`has_permission`） |
| 判断依据   | 对象的所有者字段                  | 用户的 `is_staff` 属性     |
| 适用场景   | 单条资源的所有权控制              | 全局资源的管理员控制       |

**`IsAuthenticatedAndOwner` —— 认证 + 所有者双重验证**

```python
class IsAuthenticatedAndOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        return False
```

| 维度           | IsOwnerOrReadOnly  | IsAuthenticatedAndOwner |
| -------------- | ------------------ | ----------------------- |
| 未登录用户     | 可读取             | 无法访问任何接口         |
| 读操作         | 任何人可读         | 必须登录 + 是所有者      |
| 写操作         | 必须是所有者       | 必须登录 + 是所有者      |

#### 5. 限流机制
**文件**: [throttles.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/throttles.py)

**LoginRateThrottle**:
- 针对登录接口的自定义限流，结合 IP 和尝试登录的 Email
- 缓存Key: `throttle_login_scope_{IP}_{email}`
- 限流频率: 3次/分钟 (`login_scope`: '3/min')
- 防止暴力破解攻击

##### 深度讲解:自定义限流类详解

**DRF 限流体系架构**

DRF 限流基于 **Token Bucket（令牌桶）** 算法，核心流程：

```
请求 → 限流检查
  │
  ├─ get_cache_key(request, view) → 生成缓存键
  │   └─ 返回 None → 不限流
  │
  ├─ 检查 Redis 中的请求历史
  │   ├─ 计数未超限 → 允许 + 记录本次
  │   └─ 计数超限 → 拒绝（返回 429 Too Many Requests）
  │
  └─ scope 对应 settings 中的速率配置
```

**`LoginRateThrottle` 实现**

**代码位置**：[accounts/throttles.py#L19-L74](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\accounts\throttles.py#L19-L74)

```python
class LoginRateThrottle(SimpleRateThrottle):
    scope = 'login_scope'  # 对应 settings 中的键

    def get_cache_key(self, request, view):
        # 1. 仅对 login 动作生效
        if view.action != 'login':
            return None

        # 2. 获取尝试登录的邮箱
        user_data = request.data.get('user', {})
        email = user_data.get('email', '')
        if not email:
            return None

        # 3. 获取真实 IP
        ident = self.get_ident(request)

        # 4. 生成 Redis 键
        return self.cache_format % {
            'scope': self.scope,
            'ident': f"{ident}_{email}"
        }
```

**为什么用 IP + 邮箱组合？**

| 方案          | 问题                                     |
| ------------- | ---------------------------------------- |
| 仅按 IP       | 同一 IP 用不同邮箱暴力破解不受限         |
| 仅按邮箱      | 分布式攻击（不同 IP 尝试同一邮箱）不受限 |
| **IP + 邮箱** | 同一 IP 尝试同一邮箱受限，防暴力破解     |

**scope 与速率配置绑定**

```python
# settings/dev.py#L314-L317
'DEFAULT_THROTTLE_RATES': {
    'anon': '100/day',        # 匿名：每天 100 次
    'user': '1000/day',      # 登录：每天 1000 次
    'login_scope': '3/min',  # 登录：每分钟 3 次
}
```

**限流算法 —— 滑动窗口**

```
Redis 存储：
  key: throttle_login_scope_192.168.1.1_test@example.com
  value: [timestamp1, timestamp2, timestamp3]  ← 最近 3 次请求的时间戳
  TTL: 60 秒（1 分钟窗口）

第 4 次请求（1 分钟内）：
  → 已有 3 个时间戳 → 超限 → 返回 429

1 分钟后（timestamp1 过期）：
  → 只剩 2 个时间戳 → 允许
```

**限流叠加效果**：

| 限流类              | 键                                                  | 速率    |
| ------------------- | --------------------------------------------------- | ------- |
| `AnonRateThrottle`  | `throttle_anon_192.168.1.1`                         | 100/day |
| `LoginRateThrottle` | `throttle_login_scope_192.168.1.1_test@example.com` | 3/min   |

**测试模式禁用限流**：

```python
if 'test' in sys.argv:
    'DEFAULT_THROTTLE_CLASSES': [],  # 清空限流类
    'DEFAULT_THROTTLE_RATES': {},    # 清空限流速率
```

#### 6. 事务处理与库存扣减
**文件**: [shop/views.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/shop/views.py#L139)

**订单创建流程**:
- 使用 `@transaction.atomic` 装饰器保证数据一致性
- **并发安全的库存扣减**: 使用 `F('stock') - cart.quantity` 表达式，避免竞态条件
- **销量统计**: `F('sales_count') + cart.quantity` 同步更新
- **事务回滚**: 任一商品库存不足则整个订单回滚

**关键代码**:
```python
cart.product.stock = F('stock') - cart.quantity
cart.product.sales_count = F('sales_count') + cart.quantity
cart.product.save()
```

#### 7. 支付宝支付集成
**文件**: [alipay_config.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/shop/alipay_config.py)

**支付流程**:
1. **扫码支付**: 调用 `api_alipay_trade_precreate` 生成二维码
2. **异步回调**: 支付宝 POST 请求 `notify_url`，验证签名后更新订单状态
3. **同步回调**: 用户支付完成后跳转 `return_url`

**配置要点**:
- 使用 RSA2 签名算法 (SHA256)
- 沙箱环境 `debug=True`，生产环境改为 `False`
- 回调地址使用环境变量 `SERVER_HOST`，支持动态配置
- 金额用 `Decimal`，`total_amount` 为两位小数字符串
- 密钥 `apps/shop/keys/` 禁止提交版本控制

**签名验证**:
```python
def verify_alipay_notify(data):
    alipay = get_alipay_client()
    return alipay.verify(data)
```

#### 8. 数据库设计
**文件**: [forum/models.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/models.py)

**设计亮点**:
- **软删除**: `status` 字段 ('published'/'deleted'/'draft')，`is_deleted` 布尔字段
- **多对多关系**: Post-Tag 通过中间表 `PostTag` 管理，支持额外字段
- **索引优化**:
  - `db_index=True`: title, created_at, author
  - `indexes`: 复合索引 (`author, -created_at`, `status, -created_at`)
- **唯一约束**: `unique_together = ['post', 'user']` 防止重复点赞/收藏

##### 深度讲解:模型设计模式详解

**1. 软删除（Soft Delete）**

**核心思想**：用字段标记删除状态，而非物理 DELETE。

```python
# Post 用 status 字段
class Post(models.Model):
    STATUS_CHOICES = [
        ('published', '已发布'),
        ('deleted', '已删除'),    # 软删除标记
        ('draft', '草稿'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')

    def soft_delete(self):
        self.status = 'deleted'
        self.save(update_fields=['status'])  # 只更新 status 字段

# Comment 用 is_deleted 布尔字段
class Comment(models.Model):
    is_deleted = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)  # 管理员隐藏
```

**两种实现方式对比**：

| 方式              | 字段    | 优点               | 缺点        |
| --------------- | ----- | ---------------- | --------- |
| `status` 字段     | 多状态枚举 | 支持多种状态（草稿/发布/删除） | 查询需过滤多个状态 |
| `is_deleted` 布尔 | 简单二元  | 查询简洁             | 状态扩展性差    |

**软删除的 4 个价值**：

1. **审计追溯**：删除的数据仍可查询，满足合规要求
2. **数据恢复**：误删可还原
3. **避免级联删除**：评论等关联数据不会被连带物理删除
4. **统计完整**：历史数据不影响报表

**2. 自定义中间表（PostTag）**

**核心思想**：用 `through` 参数自定义多对多中间表，替代 Django 默认生成的中间表。

```python
# 自定义中间表
class PostTag(models.Model):
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='post_tags')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='tag_posts')
    created_at = models.DateTimeField(auto_now_add=True)  # 扩展字段：关联时间

    class Meta:
        unique_together = ['post', 'tag']  # 联合唯一约束

class Post(models.Model):
    tags = models.ManyToManyField('Tag', through='PostTag')  # 指定中间表
```

**自定义中间表的 3 个理由**：

1. **扩展字段**：添加 `created_at`（关联时间）、`weight`（排序权重）等
2. **业务约束**：`unique_together` 防止重复关联
3. **反向访问名**：清晰的 `post_tags` / `tag_posts`，而非默认的 `post_set` / `tag_set`

**3. 冗余统计字段**

**核心思想**：把本可聚合计算的字段单独存储，避免频繁 COUNT 查询。

```python
class Post(models.Model):
    # 冗余字段（本可从 PostLike/Comment/PostCollect 表聚合得到）
    view_count = models.IntegerField(default=0)      # 浏览量
    like_count = models.IntegerField(default=0)      # 点赞数
    comment_count = models.IntegerField(default=0)   # 评论数
    collect_count = models.IntegerField(default=0)   # 收藏数
```

**为什么需要冗余？**

```python
# 没有冗余：每次查询都要聚合
Post.objects.annotate(
    like_count=Count('likes'),
    comment_count=Count('comments'),
    collect_count=Count('collects')
)  # 三次 JOIN + COUNT，性能差

# 有冗余：直接读字段
Post.objects.values('title', 'like_count', 'comment_count')  # 单表查询
```

**维护一致性的关键**：

```python
# 点赞时：先创建记录，再用 F() 更新计数
PostLike.objects.create(post=post, user=user)
Post.objects.filter(id=post_id).update(like_count=F('like_count') + 1)  # 原子更新

# 取消点赞：先删记录，再减计数
PostLike.objects.filter(post=post, user=user).delete()
Post.objects.filter(id=post_id).update(like_count=F('like_count') - 1)
```

**4. 自引用树形结构**

**核心思想**：外键指向自身，实现层级数据（如多级评论、分类树）。

```python
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        'self',                  # 指向自身
        on_delete=models.CASCADE,
        null=True,               # 一级评论 parent=None
        blank=True,
        related_name='replies'   # 反向查询：parent.replies 获取子评论
    )
    content = models.TextField(max_length=1000)
```

**数据结构示意**：

```
帖子 #1
├─ 评论 #1 (parent=None)
│  ├─ 评论 #3 (parent=评论#1)
│  │  └─ 评论 #5 (parent=评论#3)
│  └─ 评论 #4 (parent=评论#1)
└─ 评论 #2 (parent=None)
   └─ 评论 #6 (parent=评论#2)
```

**查询策略**：

```python
# 列表查询：只查一级评论（parent=None）
top_comments = Comment.objects.filter(post=post, parent=None)

# 获取子评论：通过 prefetch_related 预加载
top_comments = Comment.objects.filter(
    post=post, parent=None, is_deleted=False
).prefetch_related('replies')  # 一次性加载所有回复
```

**5. 索引优化**

```python
class Meta:
    # 单字段索引
    indexes = [
        models.Index(fields=['author', '-created_at']),  # 作者+时间降序
        models.Index(fields=['status', '-created_at']),  # 状态+时间降序
    ]
    # 联合唯一约束
    unique_together = ['post', 'user']  # 防止重复点赞/收藏
```

#### 9. 日志系统
**文件**: [logger_conf.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/logger_conf.py)

**配置要点**:
- 使用 Loguru 替代 Django 原生 logging
- 通过 `InterceptHandler` 拦截第三方库日志
- 开发环境输出到控制台，生产环境写入文件
- **分级漏斗记录**: 不同级别日志写入不同文件（debug/info/warning/error/critical）

##### 深度讲解:Loguru日志配置详解

**为什么用 Loguru 替代 Django 默认 logging？**

| 特性 | Django logging | Loguru |
|------|---------------|--------|
| 配置复杂度 | 30+ 行 dict 配置 | 一行 `logger.add()` |
| 日志分割 | 需 `RotatingFileHandler` | `rotation="10 MB"` |
| 异步写入 | 不支持 | `enqueue=True` |
| 彩色输出 | 不支持 | `colorize=True` |
| 结构化绑定 | 不支持 | `logger.bind(user=..., path=...)` |
| 异常诊断 | 简单堆栈 | `backtrace=True` + `diagnose=True` |

**三步禁用 Django 默认日志**

**位置**：[settings/dev.py#L416-L424](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\settings\dev.py#L416-L424)

```python
# 1. 禁用 Django 默认的日志配置系统
LOGGING_CONFIG = None

# 2. 显式置空，防止 Django 自动加载默认配置
LOGGING = {}

# 3. 使用自定义的 Loguru 日志配置
from .logger_conf import setup_logging
setup_logging()
```

**InterceptHandler —— 桥接标准 logging 到 Loguru**

**位置**：[settings/logger_conf.py#L36-L71](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\settings\logger_conf.py#L36-L71)

```python
class InterceptHandler(logging.Handler):
    """标准 logging 到 Loguru 的桥接处理器"""

    def emit(self, record):
        # 1. 级别转换：logging → Loguru
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 2. 调整调用深度，显示原始调用位置
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # 3. 转发到 Loguru
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )
```

**为什么需要 InterceptHandler？**

```
Django / DRF / 第三方库 → 标准 logging 模块
  logger = logging.getLogger('django')
  logger.warning('Slow query: ...')

如果不桥接：
  → 日志走 Django 默认 logging → 输出到 Django 配置的 handler
  → Loguru 看不到这些日志 → 日志割裂

桥接后：
  logging.getLogger('django').warning('...')
    → InterceptHandler.emit()
    → logger.opt(depth=...).log('WARNING', 'Slow query: ...')
    → Loguru 统一处理 → 输出到文件/控制台
```

**开发环境 vs 生产环境日志策略**

| 配置项 | 开发环境 | 生产环境 |
|--------|----------|----------|
| **文件格式** | 文本（彩色标记） | JSON（便于 ELK 解析） |
| **文件策略** | 按级别分文件（debug/info/warning/error/critical） | 统一 all.log + error.log |
| **控制台级别** | INFO | WARNING |
| **文件最低级别** | DEBUG | INFO |
| **diagnose** | True（显示变量值） | False（避免泄露敏感信息） |
| **colorize（控制台）** | True | True |

**开发环境日志文件**：

```
log/
├── cube-debug.log       ← DEBUG 及以上
├── cube-info.log        ← INFO 及以上
├── cube-warning.log     ← WARNING 及以上
├── cube-error.log       ← ERROR 及以上
└── cube-critical.log    ← CRITICAL 及以上
```

**生产环境日志文件**：

```
/var/log/icube/
├── cube-all.log         ← INFO 及以上（JSON 格式）
└── cube-error.log       ← ERROR 及以上（JSON 格式）
```

#### 10. 图片上传与URL管理
**文件**: [image_url.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/utils/image_url.py)

**核心函数**: `build_image_url(relative_path, absolute=False)`

**设计要点**:
- **默认返回相对路径**（如 `/media/avatars/user.png`），避免 CORS 和 PNA（Private Network Access）问题
- **`absolute=True` 参数**: 用于生成完整URL（如邮件场景）
- **自动处理 ImageFieldFile 对象**: 用 `isinstance` 检查 `FieldFile`，禁止用 `hasattr(.., 'path')`（会触发 `SuspiciousFileOperation`）
- **统一添加 `/media/` 前缀**: 确保数据库中存储的图片路径前缀一致

**关键代码**:
```python
from django.db.models.fields.files import FieldFile

def build_image_url(relative_path, absolute=False):
    if not relative_path:
        return ''
    
    if isinstance(relative_path, FieldFile):
        relative_path = relative_path.name
    
    if not relative_path.startswith('/media/'):
        relative_path = '/media' + relative_path
    
    if absolute:
        return settings.SITE_DOMAIN.rstrip('/') + relative_path
    
    return relative_path
```

**问题解决**:
- **CORS 问题**: 之前后端返回完整 `http://localhost:8000/media/...` URL，从公网 IP 访问时被浏览器 PNA 策略阻止。修改后返回相对路径，前端通过代理转发。
- **路径不一致问题**: 数据库中存储的图片路径前缀不一致（有无 `/media/`），通过统一添加前缀解决。

##### 深度讲解:图片处理与安全

**为什么不能使用 hasattr 判断文件对象**

从模型实例读取 `ImageField` 时，得到的不是普通字符串，而是 `FieldFile`：

```python
user.image.startswith('/media/')
# AttributeError: 'FieldFile' object has no attribute 'startswith'
```

一种看似可行但存在风险的写法是：

```python
if hasattr(user.image, 'path'):
    image_path = user.image.path
```

`hasattr(obj, 'path')` 并不是只检查属性名称，它会在内部真正执行 `getattr(obj, 'path')`。`FieldFile.path` 又会调用 Storage 计算文件的物理路径。如果数据库中的文件名以 `/` 开头，Django 的 `safe_join` 会认为路径试图逃逸 `MEDIA_ROOT`，从而抛出 `SuspiciousFileOperation`。

正确做法是先进行类型判断，再读取不会触发物理路径计算的 `name`：

```python
from django.db.models.fields.files import FieldFile

if isinstance(relative_path, FieldFile):
    relative_path = relative_path.name
```

**Pillow 图片处理流水线**

**位置**：[image_processor.py#L145-L208](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/utils/image_processor.py#L145-L208)

```
上传文件
  → Pillow 解码
  → 可选中心裁剪
  → 等比例缩放
  → 编码为 WebP 或 JPEG
  → 写入 BytesIO
  → 包装为 InMemoryUploadedFile
  → 交给 Django Storage 保存
```

等比例缩放的核心计算：

```python
ratio = min(max_width / width, max_height / height)
new_width = int(width * ratio)
new_height = int(height * ratio)
```

**项目中的具体策略**：

- **用户头像**：中心裁剪为 `1:1`，最大尺寸 `512 × 512`，WebP 质量为 85
- **帖子图片**：最大尺寸 `1200 × 1200`，支持可选的正方形裁剪，统一转换为 WebP
- **公式缩略图**：根据公式名称和记号自动生成 400×300 缩略图

**安全价值**：

- 帖子图片限制为不超过 5 MB，避免直接上传超大文件
- 使用 MIME 类型白名单，拒绝明显不支持的文件类型
- 使用 Pillow 解码并重新编码，不直接保存用户提交的原始二进制内容
- 限制最终图片尺寸，降低磁盘占用、网络流量和前端渲染压力
- 统一转为 WebP，通常会移除原图中的 EXIF 等元数据
- 使用 `FieldFile.name` 代替 `.path`，避免访问危险的本地物理路径
- 数据库保存相对路径，避免泄漏服务器目录

**仍需注意的边界**：

- MIME 类型可以伪造，应捕获 `UnidentifiedImageError` 并校验 Pillow 实际识别的格式
- 防止图片解压炸弹：限制原图像素总数，处理 `DecompressionBombError`
- 未处理 EXIF 图片方向：应调用 `ImageOps.exif_transpose(img)`

#### 11. 浏览量统计
**文件**: [formula/views.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/views.py)

**实现方式**:
- 使用 Django `F()` 表达式实现原子更新
- 公式详情页访问时自动递增 `view_count`
- 首页精选公式按 `view_count` 降序排列

**关键代码**:
```python
from django.db.models import F

def retrieve(self, request, pk=None):
    instance = self.get_object()
    instance.view_count = F('view_count') + 1
    instance.save()
    instance.refresh_from_db()
    serializer = self.get_serializer(instance)
    return APIResponse(data=serializer.data)
```

**排序逻辑**:
```python
queryset = Formula.objects.order_by('-view_count')[:6]
```

#### 12. 图片处理流水线
**文件**: [image_processor.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/utils/image_processor.py)

**核心功能**:
- **图片压缩**: 使用 Pillow 对上传图片进行自动压缩
  - 大图片预压缩：原图>2048px时先等比例缩小再裁剪
  - 质量优化：默认quality=85，平衡清晰度和文件大小
- **1:1比例裁剪**: 自动裁剪为正方形，支持中心裁剪
- **WebP格式转换**: PNG/JPG自动转换为WebP格式，减小文件体积
- **缩略图生成**: 根据公式名称和记号自动生成缩略图

**关键代码**:
```python
from PIL import Image

def process_image(file, max_width=1200, max_height=1200, quality=85, crop_square=False, convert_webp=False):
    img = Image.open(file)
    
    # 大图片预压缩
    if img.width > 2048 or img.height > 2048:
        ratio = min(2048 / img.width, 2048 / img.height)
        img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
    
    # 1:1比例裁剪
    if crop_square:
        min_side = min(img.width, img.height)
        left = (img.width - min_side) // 2
        top = (img.height - min_side) // 2
        img = img.crop((left, top, left + min_side, top + min_side))
    
    # 格式转换
    if convert_webp:
        output_format = 'WEBP'
    
    return processed_file

def generate_formula_thumbnail(name, notation):
    img = Image.new('RGB', (400, 300), color='#f5f5f5')
    # 绘制公式名称和记号
    ...
```

##### 深度讲解:图片处理与安全(续)

**InMemoryUploadedFile 的作用**

`InMemoryUploadedFile` 本身不负责压缩。它的作用是把 Pillow 生成的 `BytesIO` 重新包装成 Django 能够交给 `ImageField` 和 Storage 保存的上传文件对象。

```python
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO

# 处理后的图片
buffer = BytesIO()
img.save(buffer, format='WEBP', quality=85)
buffer.seek(0)

# 包装为 Django 可识别的文件对象
processed_file = InMemoryUploadedFile(
    buffer, 'ImageField', f'{name}.webp',
    'image/webp', buffer.getbuffer().nbytes, None
)
```

**面试回答要点**

> 项目把图片处理分为 URL 标准化和上传处理两层。读取时通过 `build_image_url` 将字符串或 Django `FieldFile` 统一转换为 `/media/...` 相对地址，避免域名耦合和浏览器 PNA 问题。判断 `FieldFile` 时使用 `isinstance`，因为 `hasattr(obj, 'path')` 会触发属性求值，路径异常时可能抛出 `SuspiciousFileOperation`。上传时使用 Pillow 完成中心裁剪、等比例缩放和 WebP 重编码，再通过 `InMemoryUploadedFile` 接入 Django Storage。安全上还需要同时控制文件字节数、真实格式和解压后的像素总量，不能只相信客户端 MIME。

#### 13. 公式图片双字段设计
**文件**: [formula/serializers.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/serializers.py)

**设计思路**:
- **thumbnail_file**: 用户上传的图片文件，经过压缩裁剪处理
- **thumbnail_path**: 从公式库选择的图片路径引用，直接使用原路径
- 两种字段互斥，根据前端提交数据判断图片来源

**关键代码**:
```python
class FormulaSerializer(serializers.ModelSerializer):
    thumbnail_file = serializers.FileField(write_only=True, required=False)
    thumbnail_path = serializers.CharField(write_only=True, required=False)
    
    def create(self, validated_data):
        thumbnail_file = validated_data.pop('thumbnail_file', None)
        thumbnail_path = validated_data.pop('thumbnail_path', None)
        
        if thumbnail_file:
            # 用户上传：压缩裁剪处理
            processed = process_image(thumbnail_file, crop_square=True, convert_webp=True)
            validated_data['thumbnail'] = processed
        elif thumbnail_path:
            # 公式库选择：直接引用路径
            validated_data['thumbnail'] = thumbnail_path
        
        return super().create(validated_data)
```

#### 14. 目标状态自动绑定
**文件**: [formula/serializers.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/serializers.py)

**实现逻辑**:
- 每个公式分类（F2L/OLL/PLL等）对应一个目标魔方状态
- 创建/编辑公式时，根据 `category_id` 自动查找并绑定对应的 `target_state_id`
- 修改分类时同步更新目标状态

**关键代码**:
```python
def _bind_target_state(self, formula, category_id):
    try:
        category = CubeCategory.objects.get(id=category_id)
        if category.target_state:
            formula.target_state = category.target_state
            formula.save()
    except CubeCategory.DoesNotExist:
        pass
```

#### 15. 作者筛选与权限控制
**文件**: [formula/filters.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/filters.py), [formula/permissions.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/permissions.py)

**作者筛选**:
- 使用 `django-filter` 的 `NumberInFilter` 支持多值筛选
- 作者列表接口返回所有创建过公式的用户

**关键代码**:
```python
class FormulaFilter(django_filters.FilterSet):
    difficulty = django_filters.BaseInFilter(field_name='difficulty', lookup_expr='in')
    created_by = django_filters.NumberInFilter(field_name='created_by', lookup_expr='in')
    
    class Meta:
        model = Formula
        fields = ['category', 'is_custom', 'difficulty', 'created_by']
```

**权限控制**:
- `IsAdminOrCustomCreator`: 管理员可编辑所有公式，普通用户仅可编辑自己上传的公式

```python
class IsAdminOrCustomCreator(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        return obj.created_by == request.user
```

##### 深度讲解:过滤搜索与排序详解

**DRF 过滤系统架构**

DRF 的过滤/搜索/排序基于 **Filter Backends** 机制，在 ViewSet 上声明式配置：

```python
class PostViewSet(viewsets.ModelViewSet):
    filter_backends = [
        filters.SearchFilter,       # 搜索
        filters.OrderingFilter,     # 排序
        DjangoFilterBackend         # 过滤（需 django-filter 库）
    ]
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'view_count', 'like_count', 'comment_count', 'is_pinned', 'is_essence']
    ordering = ['-is_pinned', '-is_essence', '-created_at']
    filterset_fields = ['tags__name', 'is_pinned', 'is_essence', 'created_at']
```

**DjangoFilterBackend —— 精确过滤**

| URL                                      | 对应 SQL                           | 说明                 |
| ---------------------------------------- | ---------------------------------- | -------------------- |
| `/api/posts/?is_pinned=true`             | `WHERE is_pinned = 1`              | 过滤置顶帖子         |
| `/api/posts/?tags__name=魔方`            | `WHERE tags.name = '魔方'`         | 按标签名过滤（跨表） |
| `/api/posts/?created_at__gte=2026-08-01` | `WHERE created_at >= '2026-08-01'` | 日期范围过滤         |

**SearchFilter —— 关键词搜索**

`search_fields = ['title', 'content']` → `/api/posts/?search=魔方`

```sql
-- 默认：OR 连接，大小写不敏感
SELECT * FROM forum_post
WHERE title ILIKE '%魔方%' OR content ILIKE '%魔方%';
```

**OrderingFilter —— 排序**

| URL                                          | 对应 SQL                                  | 说明         |
| -------------------------------------------- | ----------------------------------------- | ------------ |
| `/api/posts/?ordering=-created_at`           | `ORDER BY created_at DESC`                | 按时间倒序   |
| `/api/posts/?ordering=view_count`            | `ORDER BY view_count ASC`                 | 按浏览量升序 |
| `/api/posts/?ordering=-like_count`           | `ORDER BY like_count DESC`                | 按点赞数倒序 |
| `/api/posts/?ordering=is_pinned,-created_at` | `ORDER BY is_pinned ASC, created_at DESC` | 多字段排序   |

**annotate 动态排序 —— 热度排序**

**位置**：[forum/views.py#L99-L109](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\forum\views.py#L99-L109)

```python
def list(self, request, *args, **kwargs):
    queryset = self.filter_queryset(self.get_queryset())

    # 按热度排序（查询参数 hot 存在时启用）
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
    ...
```

**热度公式**：`hot_score = 点赞数 × 3 + 评论数 × 2 + 收藏数 × 1`

#### 16. 自定义公式分类
**文件**: [formula/models.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/models.py), [formula/views.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/views.py)

**设计思路**:
- `CubeCategory` 模型添加 `created_by` 外键和 `is_custom` 布尔字段，支持用户创建自定义分类
- 系统分类 `created_by=None, is_custom=False`，用户自定义分类 `created_by=当前用户, is_custom=True`
- 分类列表接口根据用户权限过滤：未登录仅见系统分类，已登录见系统 + 自己的自定义分类

**关键代码**:
```python
# 模型字段
class CubeCategory(models.Model):
    # ... 现有字段 ...
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    is_custom = models.BooleanField('是否自定义', default=False)

# 视图过滤逻辑
def get_queryset(self):
    user = self.request.user
    if user.is_authenticated:
        return CubeCategory.objects.filter(
            models.Q(created_by__isnull=True) |
            models.Q(created_by=user)
        )
    return CubeCategory.objects.filter(created_by__isnull=True)

# 创建时自动设置
def perform_create(self, serializer):
    serializer.save(created_by=self.request.user, is_custom=True)
```

**前端实现**:
- 公式编辑器中分类选择器分为"系统分类"和"我的自定义分类"两组
- 添加"+ 新建"按钮，点击弹出分类创建弹窗
- 弹窗支持选择阶数、求解方法、阶段（从固定列表选择）

#### 17. 公式编辑逆公式同步
**文件**: [formula/serializers.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/serializers.py)

**问题**: 编辑公式时逆公式没有随公式修改而更新

**解决方案**:
在 `update` 方法中检测 `notation` 是否被修改，如果是则重新生成逆公式

```python
def update(self, instance, validated_data):
    # 当公式记号被修改时，重新生成逆公式
    if 'notation' in validated_data:
        from .services import FormulaService
        validated_data['inverse_notation'] = FormulaService.generate_inverse_notation(validated_data['notation'])
    # ... 其余逻辑 ...
```

#### 18. 公式卡片样式优化
**文件**: [FormulaLibrary.vue](file:///e:/BH/PyStudy/ICube/cube_front/src/components/formula/FormulaLibrary.vue), [CollectionView.vue](file:///e:/BH/PyStudy/ICube/cube_front/src/views/profiles/CollectionView.vue)

**优化内容**:
- 公式卡片布局优化：头部显示公式名称+难度标签，底部显示分类名+作者信息
- 分类名、作者名、分隔符使用统一字体大小和样式，提升视觉一致性
- 作者信息格式："分类名  by 用户名"，中间用两个空格隔开
- 用户自己创建的公式可在"我的公式"页面进行编辑和删除操作

```html
<!-- 卡片头部：公式名 + 难度标签 -->
<div class="formula-header">
  <span class="formula-name">{{ formula.name }}</span>
  <el-tag :type="difficultyTagType(formula.difficulty)" size="small">
    {{ difficultyLabel(formula.difficulty) }}
  </el-tag>
</div>

<!-- 卡片底部：分类名  by 用户名（统一字体） -->
<div class="formula-footer">
  <div class="footer-left">
    <span class="category-tag">{{ formula.category?.name }}</span>
    <span v-if="formula.author" class="author-separator">&nbsp;&nbsp;by&nbsp;</span>
    <span v-if="formula.author" class="author-name">{{ formula.author.username }}</span>
  </div>
  <div class="footer-right">
    <!-- 编辑、删除按钮（仅对自己的自定义公式显示） -->
  </div>
</div>
```

**样式特点**:
- `.formula-name`: 公式名称，加粗显示
- `.category-tag`, `.author-separator`, `.author-name`: 统一字体大小和颜色
- 收藏页面的公式卡片样式与公式库页面保持一致

#### 19. 自定义用户模型与缓存
**文件**: [accounts/models.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/models.py), [accounts/services.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/accounts/services.py)

**核心实现**:
- 继承 `AbstractUser`，重写 `USERNAME_FIELD = "email"`
- 自定义 `UserManager` 实现 `create_user` / `create_superuser`
- 关注关系用 `ManyToManyField("self", symmetrical=False)` 自关联

**管理器（Manager）**

管理器是 Django ORM 的核心机制，是模型与数据库交互的入口。每个模型默认都有 `objects` 管理器。

```python
# accounts/models.py#L24-L95
class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **other_fields) -> User:
        if not email:
            raise ValueError('邮箱必填')
        email = self.normalize_email(email)
        user = self.model(email=email, **other_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

# 第 169 行：用自定义管理器替换默认的
objects = UserManager()
```

**class Meta 内部配置类**

用于定义模型的元数据（表名、排序、索引、权限等）：

```python
class Meta:
    app_label = 'forum'
    db_table = 'forum_post'
    verbose_name = '帖子'
    ordering = ['-is_pinned', '-is_essence', '-created_at']
    indexes = [
        models.Index(fields=['author', '-created_at']),
        models.Index(fields=['status', '-created_at']),
    ]
    unique_together = ['post', 'tag']  # 联合唯一约束
```

**Redis 缓存辅助方法**

```
读请求：Redis 查 → 命中直接返回 → 未命中查 DB → 回写 Redis
写请求：DB 写入 → 同步更新 Redis（双写保证一致）
```

`django_redis` 常用操作：

```python
from django_redis import get_redis_connection
con = get_redis_connection("default")

# String 类型
con.set("key", "value", ex=3600)      # 设置键值 + TTL
con.get("key")                         # 获取值
con.incr("counter")                    # 原子自增

# Set 类型（关注/粉丝集合）
con.sadd("key", 1, 2, 3)              # 添加元素
con.sismember("key", 1)               # 元素是否在集合中
con.scard("key")                      # 获取集合大小

# Pipeline 批量操作
pipe = con.pipeline()
pipe.sadd("key1", 1, 2)
pipe.expire("key1", 600)
pipe.execute()                        # 一次性执行
```

**缓存穿透/击穿/雪崩**

| 问题       | 场景                      | 危害             |
| -------- | ----------------------- | -------------- |
| **缓存穿透** | 查不存在的数据，缓存和 DB 都没有      | 每次都打 DB，缓存完全失效 |
| **缓存击穿** | 某个热点 key 过期瞬间，大量并发请求打过来 | 瞬间 DB 压力暴增     |
| **缓存雪崩** | 大量 key 同时过期             | DB 被流量洪峰冲垮     |

**防穿透实现**：空结果也写入缓存，用 `-1` 占位符：

```python
# accounts/services.py#L182-L186
if following_ids:
    pipe.sadd(key, *following_ids)
else:
    pipe.sadd(key, -1)       # 占位符
    pipe.expire(key, 600)    # 10分钟后重建
```

**防击穿方案**：互斥锁（SETNX）

```python
if con.set(lock_key, 1, ex=10, nx=True):  # 10秒自动过期防死锁
    try:
        data = Post.objects.get(id=post_id)
        con.set(cache_key, data, ex=3600)
        return data
    finally:
        con.delete(lock_key)
```

**防雪崩方案**：过期时间加随机数

```python
import random
expire = 3600 + random.randint(0, 600)  # 1小时 + 0~10分钟随机
con.set(key, value, ex=expire)
```

**记忆口诀**：
- 穿透：查不存在的 → 用空值占位或布隆过滤器
- 击穿：单个热 key 过期 → 用互斥锁或永不过期
- 雪崩：大量 key 同时过期 → 过期时间加随机 + 多级缓存

#### 20. ORM查询优化
**文件**: [forum/views.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/views.py#L53), [forum/services.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/services.py#L83)

**select_related —— 外键预加载（JOIN）**

```python
Post.objects.filter(status='published').select_related('author')
# 对应 SQL：INNER JOIN，单条 SQL 一次性取关联数据
```

```sql
-- 没有 select_related：N+1 查询问题
SELECT * FROM forum_post WHERE status='published';        -- 1 次
SELECT * FROM accounts_user WHERE id = 1;                 -- N 次

-- 有 select_related：1 次查询
SELECT * FROM forum_post
INNER JOIN accounts_user ON forum_post.author_id = accounts_user.id
WHERE forum_post.status = 'published';
```

**prefetch_related —— 多对多预加载（IN 查询）**

```python
Post.objects.filter(status='published').prefetch_related('tags', 'images')
# 多对多 JOIN 会产生笛卡尔积，用 IN 避免
```

**为什么多对多用 prefetch 不用 select？** 1 个帖子有 3 个标签，用 JOIN 会产生 3 行重复的帖子数据。prefetch_related 在 Python 层拼装，避免数据冗余。

**F 表达式 —— 原子更新**

```python
# 错误写法（有竞态条件）
post = Post.objects.get(id=1)
post.like_count = post.like_count + 1   # Python 层计算
post.save()                              # 并发时丢失更新

# F() 表达式（正确）
Post.objects.filter(id=1).update(like_count=F('like_count') + 1)
# SQL: UPDATE ... SET like_count = like_count + 1 WHERE id = 1
# MySQL 行锁保证原子性，并发安全
```

本项目用 F 的场景：浏览量自增、点赞/取消点赞计数、扣库存防超卖、热度分数计算。

**Q 对象 —— 复杂条件组合**

```python
from django.db.models import Q

# OR 条件（filter 默认只能 AND）
CubeCategory.objects.filter(
    Q(created_by__isnull=True) |     # 系统内置分类
    Q(created_by=user)                # 用户自建分类
)
# WHERE created_by_id IS NULL OR created_by_id = 5
```

| 运算符  | 含义  | 对应 SQL | 示例                 |
| ---- | --- | ------ | ------------------ |
| `&`  | AND | `AND`  | `Q(a=1) & Q(b=2)`  |
| `\|` | OR  | `OR`   | `Q(a=1) \| Q(b=2)` |
| `~`  | NOT | `NOT`  | `~Q(a=1)`          |

**annotate + F —— 数据库层计算字段**

```python
Post.objects.filter(
    status='published', created_at__gte=since
).annotate(
    hot_score=F('like_count') * 3 + F('comment_count') * 2 + F('view_count')
).order_by('-hot_score')[:20]
```

```sql
SELECT *, (like_count * 3 + comment_count * 2 + view_count) AS hot_score
FROM forum_post
WHERE status = 'published' AND created_at >= '2026-07-28'
ORDER BY hot_score DESC LIMIT 20;
```

**为什么在 DB 层算而不是 Python 层？** 10 万条帖子在 Python 排序要先全部拉到内存，慢且占内存。DB 层用计算字段 + ORDER BY，只返回 LIMIT 20 条。

**only() —— 字段裁剪** / **update_fields —— 局部更新**

```python
# only()：只取必要字段
post = Post.objects.only('view_count').get(id=post_id)
# SQL: SELECT id, view_count FROM forum_post WHERE id = 1;

# update_fields：只更新变化的字段
self.save(update_fields=['use_count'])
# SQL: UPDATE forum_post SET use_count = 5 WHERE id = 1;
```

**速记对比表**：

| 工具                 | 用途      | 对应 SQL               | 解决的核心问题        |
| ------------------ | ------- | -------------------- | -------------- |
| `F()`              | 引用字段值   | `SET col = col + 1`  | 原子更新、并发安全      |
| `Q()`              | 组合查询条件  | `OR` / `AND` / `NOT` | 复杂条件查询         |
| `select_related`   | 外键预加载   | `JOIN`               | N+1 查询         |
| `prefetch_related` | 多对多预加载  | `IN` 子查询             | N+1 查询（无笛卡尔积）  |
| `annotate`         | 分组/计算字段 | `GROUP BY` / 计算列     | 数据库层聚合         |
| `only`             | 字段裁剪    | 指定列查询                | 减少 IO          |
| `update_fields`    | 局部更新    | 指定列 UPDATE           | 减少 binlog、避免覆盖 |

**记忆口诀**：单数用 select（JOIN），复数用 prefetch（IN）。

#### 21. 序列化器设计
**文件**: [forum/serializers.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/serializers.py)

**核心设计**:
- 多序列化器策略：`get_serializer_class()` 按 action 动态选择
- `SerializerMethodField`：动态计算字段（如 `is_liked`、`is_collected`）
- 嵌套序列化：`author = ProfileListSerializer(read_only=True)`
- `write_only` / `read_only` 分离写入和读取字段
- `Serializer.create / update` 覆写：处理标签关联、图片同步等业务逻辑

**多序列化器策略**

```python
# forum/views.py#L64-L80
def get_serializer_class(self):
    if self.action == 'list':
        return PostListSerializer       # 列表：轻量级
    if self.action in ['create', 'update', 'partial_update']:
        return PostCreateUpdateSerializer  # 写入：含文件上传
    return PostSerializer               # 详情：完整版
```

| 序列化器                         | 对应 Action         | 设计理由                         |
| ---------------------------- | ----------------- | ---------------------------- |
| `PostListSerializer`         | `list`            | 列表页不需要 content 全文，减小 payload |
| `PostSerializer`             | `retrieve`        | 详情页需要完整数据和动态状态               |
| `PostCreateUpdateSerializer` | `create`/`update` | 写入专用，支持文件上传和图片关联             |

**SerializerMethodField —— 动态计算字段**

```python
# forum/serializers.py#L141-L197
class PostSerializer(serializers.ModelSerializer):
    is_liked = serializers.SerializerMethodField()
    is_collected = serializers.SerializerMethodField()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PostLike.objects.filter(post=obj, user=request.user).exists()
        return False
```

**嵌套序列化**

```python
class PostListSerializer(serializers.ModelSerializer):
    author = ProfileListSerializer(read_only=True)   # 嵌套序列化
    tags = TagSerializer(many=True, read_only=True)   # 嵌套 + 多对多
    images = serializers.SerializerMethodField()       # 动态获取前 4 张
```

**write_only / read_only 分离**

```python
# tag_ids：写入时传 [1, 2, 3]，读取时返回 [{id, name}, ...]
tag_ids = serializers.ListField(write_only=True)  # 写入专用
tags = TagSerializer(many=True, read_only=True)   # 读取专用
```

| 属性                | 写入（反序列化） | 读取（序列化） | 典型场景                                 |
| ----------------- | -------- | ------- | ------------------------------------ |
| `write_only=True` | 接受值    | 不输出   | `password`、`tag_ids`（写入用 ID，读取用嵌套对象） |
| `read_only=True`  | 忽略值    | 输出值   | `created_at`、`view_count`、`is_liked` |

**create/update 覆写**

```python
# forum/serializers.py#L199-L246
def create(self, validated_data):
    tag_ids = validated_data.pop('tag_ids', [])       # 提取自定义字段
    validated_data['author'] = self.context['request'].user  # 设置作者
    post = super().create(validated_data)

    if tag_ids:
        tags = Tag.objects.filter(id__in=tag_ids)
        post.tags.set(tags)                           # 关联标签（set 替换原有）
        for tag in tags:
            tag.increment_use_count()                 # 递增使用次数
    return post
```

**validate_\<field\> 单字段验证**

```python
def validate_title(self, value):
    if len(value.strip()) < 3:
        raise serializers.ValidationError("标题至少3个字符")
    return value.strip()

def validate_content_file(self, value):
    if not value.name.endswith('.md'):
        raise serializers.ValidationError("只支持.md格式的文件")
    if value.size > 1024 * 1024 * 5:
        raise serializers.ValidationError("文件大小不能超过5MB")
    return value
```

**知识点速查表**：

| 知识点                        | 作用               | 对应 DRF 机制                |
| -------------------------- | ---------------- | ------------------------ |
| **多序列化器策略**                | 按 action 选不同序列化器 | `get_serializer_class()` |
| **SerializerMethodField**  | 动态计算字段           | `get_{field}` 方法         |
| **嵌套序列化**                  | 外键关联序列化          | 嵌套序列化器                   |
| **write_only/read_only** | 读写分离             | 字段属性                     |
| **create/update 覆写**       | 自定义业务逻辑          | 覆写方法                     |
| **validate\_<field>**      | 单字段验证            | 字段级验证                    |

#### 22. ViewSet与Action

- ModelViewSet 提供 CRUD，`@action` 装饰器添加自定义端点
- detail=True 作用于单个资源，detail=False 作用于集合
- 动态权限：`get_permissions()` / `get_throttles()` 按 action 切换
- 代码位置：[forum/views.py#L232-L266](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\forum\views.py#L232-L266)、[accounts/views.py#L48-L61](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\accounts\views.py#L48-L61)

##### 深度讲解:ViewSet与自定义Action详解

###### 1. ViewSet 家族成员

DRF 提供 4 种 ViewSet 基类，灵活选择：

| 基类                   | 提供的 Action       | 适用场景           | 本项目使用                                       |
| ---------------------- | ------------------- | ------------------ | ------------------------------------------------ |
| `ViewSet`              | 无（纯自定义）      | 完全自定义逻辑     | 不使用                                           |
| `GenericViewSet`       | 无 + 通用 mixin     | 需自定义 CRUD 逻辑 | `AuthViewSet`                                    |
| `ReadOnlyModelViewSet` | `list` + `retrieve` | 只读操作           | `TagViewSet`                                     |
| `ModelViewSet`         | 全部 CRUD           | 标准增删改查       | `PostViewSet`、`CommentViewSet`、`ReportViewSet` |

**本项目的选择**：

```python
class PostViewSet(viewsets.ModelViewSet):      # 帖子：完整 CRUD + 自定义动作
class CommentViewSet(viewsets.ModelViewSet):  # 评论：完整 CRUD + 自定义动作
class ReportViewSet(viewsets.ModelViewSet):   # 举报：完整 CRUD
class AuthViewSet(viewsets.GenericViewSet):  # 认证：自定义 register/login/logout
class TagViewSet(viewsets.ReadOnlyModelViewSet):  # 标签：只读
```

###### 2. `@action` 装饰器 —— 自定义端点

**核心思想**：在 ViewSet 上添加非标准 CRUD 的自定义端点，DRF 自动生成路由。

**参数说明**：

```python
@action(
    detail=True,          # True: /posts/{pk}/like/  False: /posts/like/
    methods=['POST'],     # HTTP 方法
    permission_classes=[IsAuthenticated],  # 该 action 专用权限
    url_path='my-likes'   # 可选：自定义 URL 路径（默认用方法名）
)
def like(self, request, pk=None):
    ...
```

**`detail=True` vs `detail=False`**：

| 参数           | 路由格式              | 方法签名                   | 适用场景     | 本项目示例                                                   |
| -------------- | --------------------- | -------------------------- | ------------ | ------------------------------------------------------------ |
| `detail=True`  | `/posts/{pk}/action/` | `(self, request, pk=None)` | 操作单个资源 | `like`、`collect`、`comments`、`like`(评论)、`dislike`(评论) |
| `detail=False` | `/posts/action/`      | `(self, request)`          | 操作资源集合 | `my_posts`、`collected`、`hot`、`upload_image`、`register`、`login`、`logout` |

**本项目的 action 统计**：

| ViewSet        | Action         | detail | methods | 路由                          |
| -------------- | -------------- | ------ | ------- | ----------------------------- |
| PostViewSet    | `like`         | ✅      | POST    | `/api/posts/{id}/like/`       |
| PostViewSet    | `collect`      | ✅      | POST    | `/api/posts/{id}/collect/`    |
| PostViewSet    | `comments`     | ✅      | GET     | `/api/posts/{id}/comments/`   |
| PostViewSet    | `my_posts`     | ❌      | GET     | `/api/posts/my_posts/`        |
| PostViewSet    | `collected`    | ❌      | GET     | `/api/posts/collected/`       |
| PostViewSet    | `hot`          | ❌      | GET     | `/api/posts/hot/`             |
| PostViewSet    | `upload_image` | ❌      | POST    | `/api/posts/upload_image/`    |
| CommentViewSet | `like`         | ✅      | POST    | `/api/comments/{id}/like/`    |
| CommentViewSet | `dislike`      | ✅      | POST    | `/api/comments/{id}/dislike/` |
| AuthViewSet    | `register`     | ❌      | POST    | `/api/auth/register/`         |
| AuthViewSet    | `login`        | ❌      | POST    | `/api/auth/login/`            |
| AuthViewSet    | `logout`       | ❌      | POST    | `/api/auth/logout/`           |

###### 3. 动态权限 —— `get_permissions()`

**核心思想**：不同 action 需要不同权限，通过重写 `get_permissions()` 动态返回权限列表。

**本项目实现**：[forum/views.py#L232-L233](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\forum\views.py#L232-L233)

```python
@action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
def like(self, request, pk=None):
    ...
```

**两种方式设置 action 权限**：

| 方式                         | 示例                                            | 适用场景               |
| ---------------------------- | ----------------------------------------------- | ---------------------- |
| **装饰器参数**               | `@action(permission_classes=[IsAuthenticated])` | 简单场景，权限固定     |
| **重写 `get_permissions()`** | 按 `self.action` 动态判断                       | 复杂场景，权限逻辑动态 |

**本项目的装饰器方式**：大多数 action 直接在 `@action` 中指定 `permission_classes`，如 `like`/`collect` 用 `[IsAuthenticated]`，`comments` 用 `[IsAuthenticatedOrReadOnly]`。

**`get_permissions()` 方式示例**（AuthViewSet）：

```python
# AuthViewSet 默认 permission_classes = [AllowAny]
# 但 login 操作需要特殊限流（通过 get_throttles）
def get_throttles(self):
    throttles = super().get_throttles()
    if self.action == 'login':
        throttles.append(LoginRateThrottle())  # 仅登录接口加限流
    return throttles
```

###### 4. 动态限流 —— `get_throttles()`

**核心思想**：不同 action 限流策略不同，如登录接口加暴力破解限流，其他接口用默认限流。

**本项目实现**：[accounts/views.py#L48-L61](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\accounts\views.py#L48-L61)

```python
def get_throttles(self):
    throttles = super().get_throttles()          # 获取默认限流
    if self.action == 'login':
        throttles.append(LoginRateThrottle())   # 仅登录加暴力破解限流
    return throttles
```

**限流配置位置**：[accounts/throttles.py#L19-L74](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\accounts\throttles.py#L19-L74)

```python
class LoginRateThrottle(SimpleRateThrottle):
    scope = 'login'

    def get_cache_key(self, request, view):
        # IP + 邮箱双重限流
        if request.data.get('email'):
            return f'throttle_login_{request.data["email"]}'
        return self.get_ident(request)
```

对应 settings 配置：

```python
'DEFAULT_THROTTLE_RATES': {
    'login': '5/minute',   # 登录：每分钟最多 5 次
}
```

###### 5. 动态查询集 —— `get_queryset()`

**核心思想**：不同 action 需要返回不同范围的数据，重写 `get_queryset()` 按 action 过滤。

**本项目实现**：[forum/views.py#L463-L489](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\forum\views.py#L463-L489)

```python
class CommentViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = Comment.objects.filter(
            is_deleted=False, is_hidden=False
        ).select_related('author', 'post')

        # list 动作：只返回一级评论
        if self.action == 'list':
            post_id = self.request.query_params.get('post')
            if post_id:
                queryset = queryset.filter(post_id=post_id)
            return queryset.filter(parent=None).order_by('-created_at')

        # 其他动作：允许查询所有层级（点赞/删除等操作需要）
        return queryset.order_by('-created_at')
```

**ReportViewSet 的 get_queryset**：[forum/views.py#L613-L626](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\forum\views.py#L613-L626)

```python
def get_queryset(self):
    if self.request.user.is_staff:
        return super().get_queryset()              # 管理员看全部
    return super().get_queryset().filter(reporter=self.request.user)  # 普通用户只看自己的
```

###### 6. 序列化器选择 —— `get_serializer_class()`

**已在序列化器章节详述**，此处补充与 ViewSet 的配合：

```python
def get_serializer_class(self):
    if self.action == 'list':
        return PostListSerializer          # 列表用轻量版
    if self.action in ['create', 'update', 'partial_update']:
        return PostCreateUpdateSerializer  # 写入专用
    return PostSerializer                 # 详情用完整版

# 自定义 action 也可以用 get_serializer_class
@action(detail=False)
def my_posts(self, request):
    posts = self.get_queryset().filter(author=request.user)
    serializer = self.get_serializer(posts, many=True)  # 自动用 PostListSerializer
    ...
```

###### 7. Action 中的分页处理

**`@action` 不会自动分页**，需要手动调用分页方法。

**本项目实现**：[forum/views.py#L315-L322](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\forum\views.py#L315-L322)

```python
@action(detail=False, methods=['GET'], permission_classes=[IsAuthenticated])
def my_posts(self, request):
    posts = self.get_queryset().filter(author=request.user)

    # 手动分页
    page = self.paginate_queryset(posts)
    if page is not None:
        serializer = self.get_serializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    # 不分页的降级方案
    serializer = self.get_serializer(posts, many=True, context={'request': request})
    return APIResponse(posts=serializer.data)
```

**分页相关方法**：

| 方法                           | 作用                                                         |
| ------------------------------ | ------------------------------------------------------------ |
| `paginate_queryset(queryset)`  | 对 queryset 执行分页，返回当前页数据（无分页配置时返回 None） |
| `get_paginated_response(data)` | 封装分页响应（自动适配自定义分页器）                         |

###### 8. 知识点速查表

| 知识点                     | 作用                   | 本项目示例                                      |
| -------------------------- | ---------------------- | ----------------------------------------------- |
| **ModelViewSet**           | 完整 CRUD              | PostViewSet、CommentViewSet                     |
| **ReadOnlyModelViewSet**   | 只读 CRUD              | TagViewSet                                      |
| **GenericViewSet**         | 纯自定义               | AuthViewSet（register/login/logout）            |
| **@action(detail=True)**   | 单个资源操作           | like、collect、comments                         |
| **@action(detail=False)**  | 资源集合操作           | my_posts、hot、upload_image                     |
| **action 动态权限**        | 按 action 切换权限     | `@action(permission_classes=[IsAuthenticated])` |
| **get_throttles()**        | 按 action 切换限流     | 登录接口加 LoginRateThrottle                    |
| **get_queryset()**         | 按 action 过滤数据     | CommentViewSet：list 只返回一级评论             |
| **get_serializer_class()** | 按 action 切换序列化器 | list→轻量版，retrieve→完整版                    |
| **手动分页**               | action 中手动调用      | my_posts、collected、hot                        |

**一句话记忆**：
- `detail=True` → 路由带 pk → 操作单个资源
- `detail=False` → 路由不带 pk → 操作资源集合
- `get_*` 系列方法 → 按 action 动态切换行为（权限/限流/查询集/序列化器）

#### 23. Redis缓存与三问

- 用户缓存：只存 ID 不存完整对象（减少序列化开销，保证一致性）
- 浏览量缓存：`incr` 原子操作 + 定时任务批量同步到 DB
- 关注关系缓存：Redis Set + Pipeline 批量操作 + -1 占位符防穿透
- 懒加载重建：缓存未命中时查库并回写
- 代码位置：[accounts/authentication.py#L45-L91](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\accounts\authentication.py#L45-L91)、[forum/services.py#L59-L88](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\forum\services.py#L59-L88)、[accounts/services.py#L145-L188](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\accounts\services.py#L145-L188)

##### 深度讲解:Redis缓存策略详解

本项目共 **5 大 Redis 使用场景**，分布在 3 个模块中：

```
Redis 使用全景
├── accounts/
│   ├── authentication.py    → 用户实例缓存（认证时）
│   ├── services.py          → Token 黑名单 + 关注/粉丝关系缓存
│   └── serializers.py       → 用户更新时清除缓存
└── forum/
    └── services.py          → 帖子浏览量缓存 + 定时同步
```

###### 1. 用户实例缓存

**位置**：[accounts/authentication.py#L45-L91](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\accounts\authentication.py#L45-L91)

**缓存键**：`user_instance_cache_{user_id}`

**缓存策略**：

```
认证请求 → get_user(token)
  │
  ├─ Redis 命中（user_instance_cache_1）
  │   └─ User.objects.get(id=1)  ← 主键查询
  │
  └─ Redis 未命中
      ├─ User.objects.get(id=1)
      ├─ cache.set("user_instance_cache_1", 1, 3600)
      └─ 返回 user
```

**设计决策**：

| 决策                | 原因                                            |
| ------------------- | ----------------------------------------------- |
| 只存 ID（不存对象） | 减少 Redis 内存 + 避免序列化开销 + 保证数据新鲜 |
| TTL 1 小时          | 平衡性能与一致性                                |
| 缓存后仍查 DB       | 主键查询极快，保证数据最新                      |

**缓存失效**：用户更新时主动清除。

###### 2. Token 黑名单

**位置**：[accounts/services.py#L23-L105](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\accounts\services.py#L23-L105)

**缓存键**：`jwt:blacklist:{jti}`

**缓存策略**：

```
登出 → add_to_blacklist(token)
  → SETEX jwt:blacklist:{jti} {剩余秒} 1

认证 → is_blacklisted(jti)
  → EXISTS jwt:blacklist:{jti}
```

**设计决策**：TTL = Token 剩余有效期，过期自动清理。

###### 3. 关注/粉丝关系缓存

**位置**：[accounts/services.py#L108-L333](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\accounts\services.py#L108-L333)

**缓存键**：

| 键                         | 类型      | 内容                 |
| -------------------------- | --------- | -------------------- |
| `user:{user_id}:following` | Redis Set | 用户关注的人 ID 集合 |
| `user:{user_id}:followers` | Redis Set | 用户的粉丝 ID 集合   |

**缓存策略**：

```python
# 读取：懒加载重建
def get_following_ids(user_id):
    key = f"user:{user_id}:following"

    # 1. 缓存命中（含 -1 占位符）
    if con.scard(key) > 0:
        return {int(x) for x in con.smembers(key)}

    # 2. 缓存未命中 → 查库
    user = User.objects.get(id=user_id)
    following_ids = list(user.following.values_list('id', flat=True))

    # 3. Pipeline 回写 Redis
    pipe = con.pipeline()
    if following_ids:
        pipe.sadd(key, *following_ids)
    else:
        pipe.sadd(key, -1)      # 空集合用 -1 占位符
        pipe.expire(key, 600)   # 10 分钟 TTL
    pipe.execute()
    return set(following_ids)

# 写入：双写保证一致
def update_follow_relation(from_id, to_id, is_follow):
    pipe = con.pipeline()
    if is_follow:
        pipe.sadd(f"user:{from_id}:following", to_id)
        pipe.srem(f"user:{from_id}:following", -1)  # 移除占位符
        pipe.sadd(f"user:{to_id}:followers", from_id)
        pipe.srem(f"user:{to_id}:followers", -1)
    else:
        pipe.srem(f"user:{from_id}:following", to_id)
        pipe.srem(f"user:{to_id}:followers", from_id)
    pipe.execute()
```

**Pipeline 批量操作**：

```python
# 一次 Pipeline 执行 4 条命令
pipe = con.pipeline()
pipe.sadd(key1, value1)      # 关注者的 following 集合
pipe.srem(key1, -1)           # 移除占位符
pipe.sadd(key2, value2)       # 被关注者的 followers 集合
pipe.srem(key2, -1)           # 移除占位符
pipe.execute()                # 一次网络往返
```

**-1 占位符防穿透**：

```
场景：新用户没有关注任何人
  → Redis key 不存在
  → 每次 get_following_ids 都查 DB（穿透）

解决方案：空集合写入 -1 占位符
  → scard(key) → 1（包含 -1）
  → smembers(key) → {-1}
  → 检测到 -1 → 返回空集合
  → TTL 10 分钟后重建
```

**防穿透的读取判断**：

```python
# 读取时检查 -1 占位符
if con.sismember(key, -1):
    return 0  # 空集合
```

###### 4. 帖子浏览量缓存

**位置**：[forum/services.py#L28-L177](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\forum\services.py#L28-L177)

**缓存键**：`forum:post:{post_id}:view`

**缓存策略**：

```python
# 1. 增加浏览量：incr 原子操作
def increase_view(post_id):
    try:
        return cache.incr(f"forum:post:{post_id}:view")  # 原子 +1
    except Exception:
        # 降级：直接查库更新
        post = Post.objects.get(id=post_id)
        post.view_count = F('view_count') + 1
        post.save(update_fields=['view_count'])

# 2. 获取浏览量：先查缓存
def get_view_count(post_id):
    count = cache.get(key)
    if count is None:
        post = Post.objects.only('view_count').get(id=post_id)
        count = post.view_count
        cache.set(key, count, timeout=3600)  # 1 小时 TTL
    return count

# 3. 定时同步：批量写入 DB
def sync_all_views():
    keys = con.keys("*forum:post:*:view")
    for key in keys:
        post_id = key.split(':')[-2]
        views = con.get(key)
        Post.objects.filter(id=post_id).update(
            view_count=F('view_count') + int(views)
        )
        con.delete(key)
```

**浏览量缓存的三级策略**：

| 层级   | 操作                                     | 时机                    |
| ------ | ---------------------------------------- | ----------------------- |
| **L1** | `cache.incr(key)`                        | 用户访问帖子时，原子 +1 |
| **L2** | `cache.get(key)`                         | 读取浏览量时，先查缓存  |
| **L3** | `Post.objects.update(view_count=F(...))` | 定时任务批量同步        |

**降级策略**：

```
Redis 可用 → incr 原子操作 → 定时同步 DB
Redis 不可用 → 直接 F() 更新 DB（降级）
```

**性能隐患**：`con.keys("*forum:post:*:view")` 是阻塞操作，生产环境数据量大时可能阻塞 Redis。建议改用 `SCAN` 命令替代。

###### 5. 用户缓存失效

**位置**：[accounts/serializers.py#L149-L150](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\accounts\serializers.py#L149-L150)

```python
# 用户更新时主动清除缓存
cache_key = f"user_instance_cache_{instance.id}"
cache.delete(cache_key)
```

**作用**：用户修改邮箱、头像等信息后，清除 Redis 缓存，下次认证时从 DB 重新加载。

###### 6. Redis 使用总览

| 场景             | 缓存键                     | Redis 类型 | 过期策略                 | 读写模式                  | 代码位置                                                     |
| ---------------- | -------------------------- | ---------- | ------------------------ | ------------------------- | ------------------------------------------------------------ |
| **用户实例**     | `user_instance_cache_{id}` | String     | TTL 1h                   | 认证时读，更新时删        | [authentication.py#L45](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\accounts\authentication.py#L45) |
| **Token 黑名单** | `jwt:blacklist:{jti}`      | String     | TTL=剩余有效期           | 登出时写，认证时查        | [services.py#L56](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\accounts\services.py#L56) |
| **关注集合**     | `user:{id}:following`      | Set        | 空集合 10min             | 关注时双写，读取时懒加载  | [services.py#L146](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\accounts\services.py#L146) |
| **粉丝集合**     | `user:{id}:followers`      | Set        | 空集合 10min             | 关注时双写，读取时懒加载  | [services.py#L215](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\accounts\services.py#L215) |
| **浏览量**       | `forum:post:{id}:view`     | String     | 无 TTL（定时同步后删除） | incr 原子写，定时批量同步 | [forum/services.py#L28](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\forum\services.py#L28) |

###### 7. 缓存模式总结

| 模式              | 本项目实现                     | 解决的问题      |
| ----------------- | ------------------------------ | --------------- |
| **读写分离**      | 浏览量：Redis 写 + 定时同步 DB | 高频写入减压    |
| **懒加载重建**    | 关注关系：缓存未命中查回写     | 冷启动数据加载  |
| **双写保证一致**  | 关注/取关：DB + Redis 同步写   | 数据一致性      |
| **防穿透**        | -1 占位符 + TTL                | 空集合查询      |
| **防击穿**        | 用户缓存 1h TTL                | 热点 key 不过期 |
| **Pipeline 批量** | 关注操作一次 4 条命令          | 减少网络往返    |
| **降级策略**      | Redis 不可用时回退 DB          | 高可用          |
| **主动失效**      | 用户更新时 `cache.delete`      | 数据新鲜        |

##### 深度讲解:缓存穿透/击穿/雪崩详解

###### 三种缓存问题对比

| 问题 | 场景 | 后果 | 本项目对应 |
|------|------|------|----------|
| **穿透** | 查询一个不存在的数据（如用户 id=-1） | 缓存永远 miss，请求全部打到 DB，可能被恶意攻击 | 关注关系缓存的 -1 占位符 |
| **击穿** | 某个热点 key 过期瞬间，大量并发请求同时回源 DB | DB 瞬时压力暴增 | 用户实例缓存（1h TTL）、浏览量缓存 |
| **雪崩** | 大量 key 同时过期（如定时刷新后集体失效） | DB 被一波请求打垮 | 浏览量缓存（定时同步后批量删除） |

###### 1. 缓存穿透

**场景**：用户查询不存在的 id（如 `user_id=99999`），缓存和 DB 都没有，每次请求都会打到 DB。

**本项目解决方案**：`-1` 占位符 + TTL

```python
# accounts/services.py#L179-L186
# 空集合场景：写入 -1 占位符，防止穿透
if following_ids:
    pipe.sadd(key, *following_ids)
else:
    # 空集合：添加 -1 占位符，设置 10 分钟 TTL
    pipe.sadd(key, -1)
    pipe.expire(key, 600)
pipe.execute()
```

**工作原理**：

```
请求：get_following_ids(99999)
  │
  ├─ 首次：Redis miss → 查 DB 返回空 → 写入 SMEMBERS key {-1} EXPIRE 600
  ├─ 第 2~N 次：Redis hit → scard(key)=1（含 -1）→ 返回 {-1} → 过滤 -1 返回空集合
  └─ 600s 后：TTL 过期 → 重新查 DB（此时用户可能有关注了）
```

**读取时的判断**：

```python
# accounts/services.py#L234-L236 — get_followers_count
total = con.scard(key)
if total > 0:
    # 如果集合包含 -1 占位符，说明是空集合，返回 0
    return total - 1 if con.sismember(key, -1) else total
```

**为什么用 -1 而不是空值？**

| 方式 | 问题 |
|------|------|
| 不写任何值 | `scard(key)=0` → 缓存未命中 → 每次查 DB（穿透） |
| 写空标记（如 "null"） | 需要额外的 key 或 value 判断，逻辑复杂 |
| **写 -1 占位符** | `scard(key)>0` 表示"已缓存"，`sismember(key, -1)` 表示"空"，逻辑清晰 |

###### 2. 缓存击穿

**场景**：某个热点 key（如首页热门帖子）过期瞬间，大量并发请求同时回源 DB。

**本项目风险点**：用户实例缓存 `user_instance_cache_{id}` TTL 为 1 小时，过期瞬间大量认证请求会同时查 DB。

**当前缓解措施**：

| 措施 | 说明 |
|------|------|
| TTL 足够长 | 用户缓存 1 小时，浏览量缓存 1 小时 |
| 主键查询快 | `User.objects.get(id=pk)` 走主键索引，极快 |
| 主动失效 | 用户更新时 `cache.delete()`，避免被动过期 |

**可增强方案**（面试加分）：分布式锁（Redis SETNX）

`cache.add()` 底层就是 Redis `SETNX`（SET if Not eXists），key 不存在时设置成功返回 True，存在时返回 False。

```python
import time
import uuid
from django.core.cache import cache
from django_redis import get_redis_connection


class DistributedLock:
    """
    Redis 分布式锁封装

    核心命令：SET key value NX PX milliseconds
      - NX：key 不存在时才设置（等价于 SETNX + EXPIRE 原子操作）
      - PX：设置过期时间（毫秒），防止死锁

    使用场景：缓存击穿防护、定时任务互斥、秒杀库存扣减等
    """

    def __init__(self, lock_key, timeout=10, wait_timeout=3, retry_interval=0.1):
        self.lock_key = lock_key
        self.timeout = timeout
        self.wait_timeout = wait_timeout
        self.retry_interval = retry_interval
        self.lock_value = str(uuid.uuid4())
        self.con = get_redis_connection("default")

    def acquire(self):
        start_time = time.time()
        while True:
            acquired = self.con.set(
                self.lock_key,
                self.lock_value,
                nx=True,
                px=int(self.timeout * 1000)
            )
            if acquired:
                return True
            elapsed = time.time() - start_time
            if elapsed >= self.wait_timeout:
                return False
            time.sleep(self.retry_interval)

    def release(self):
        lua_script = """
        if redis.call('get', KEYS[1]) == ARGV[1] then
            return redis.call('del', KEYS[1])
        else
            return 0
        end
        """
        self.con.eval(lua_script, 1, self.lock_key, self.lock_value)

    def __enter__(self):
        if not self.acquire():
            raise TimeoutError(f"获取锁超时: {self.lock_key}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False


# 使用分布式锁解决缓存击穿
def get_post_with_lock(post_id):
    cache_key = f"forum:post:{post_id}:detail"
    lock_key = f"lock:post:{post_id}"

    cached = cache.get(cache_key)
    if cached:
        return cached

    lock = DistributedLock(lock_key, timeout=5, wait_timeout=2)
    if lock.acquire():
        try:
            cached = cache.get(cache_key)
            if cached:
                return cached
            post = Post.objects.select_related('author').prefetch_related('tags').get(id=post_id)
            post_data = PostSerializer(post).data
            import random
            jitter = random.randint(0, 60)
            cache.set(cache_key, post_data, timeout=300 + jitter)
            return post_data
        finally:
            lock.release()
    else:
        time.sleep(0.2)
        cached = cache.get(cache_key)
        if cached:
            return cached
        post = Post.objects.select_related('author').get(id=post_id)
        return PostSerializer(post).data
```

**分布式锁核心要点**：

| 要点 | 说明 |
|------|------|
| **原子加锁** | `SET key value NX PX timeout` 一条命令完成，防止 SETNX + EXPIRE 之间宕机 |
| **唯一标识** | 用 UUID 作为 value，防止误删其他线程的锁 |
| **原子解锁** | Lua 脚本检查 value 后再 DEL，防止竞态条件 |
| **超时释放** | 设置合理 TTL，防止业务异常导致死锁 |
| **超时等待** | `wait_timeout` 内重试获取锁，超过则降级 |
| **双重检查** | 获取锁后再查一次缓存，防止重复回源 |

###### 3. 缓存雪崩

**场景**：大量 key 同时过期，如浏览量缓存定时同步后批量删除，下一波请求同时回源。

**本项目风险点**：

```
forum/services.py sync_all_views()
  → 定时任务批量同步浏览量到 DB
  → 同步后 con.delete(key_str) 删除所有缓存键
  → 下一波访问帖子的请求全部 miss → 同时查 DB
```

**当前缓解措施**：

| 措施 | 说明 |
|------|------|
| Pipeline 批量操作 | 减少网络往返，降低同步耗时 |
| 异步定时同步 | `sync_all_views` 非实时，浏览量先存 Redis 再批量写 DB |
| 缓存 TTL 错开 | Token 黑名单 TTL = 剩余有效期，天然错开 |

**可增强方案**（面试加分）：

```python
# 方案一：给 TTL 加随机偏移
import random
base_ttl = 3600  # 1 小时
jitter = random.randint(0, 300)  # 0~5 分钟随机
cache.set(key, value, timeout=base_ttl + jitter)

# 方案二：双缓存策略（主缓存 + 备份缓存）
def get_view_count(post_id):
    key = f"forum:post:{post_id}:view"
    backup_key = f"forum:post:{post_id}:view:backup"

    count = cache.get(key)
    if count is not None:
        return count

    count = cache.get(backup_key)
    if count is not None:
        return count

    post = Post.objects.only('view_count').get(id=post_id)
    count = post.view_count
    cache.set(key, count, timeout=3600)
    cache.set(backup_key, count, timeout=3900)  # 备份缓存 65min，比主缓存长
    return count
```

###### 4. 三种问题与解决方案总览

| 问题 | 根因 | 解决方案 | 本项目实现 |
|------|------|----------|----------|
| **穿透** | 查不存在的数据，缓存永远 miss | 空值缓存 + TTL 过期 | `-1` 占位符 + 10min TTL（关注关系） |
| **击穿** | 热点 key 过期，并发回源 | 互斥锁 / 热点数据永不过期 | TTL 足够长 + 主键查询快（用户缓存） |
| **雪崩** | 大量 key 同时过期 | TTL 加随机 / 双缓存 / 集群高可用 | Pipeline 批量 + 定时错开同步 |

**面试关键回答**：
- 穿透 → 不存在的数据 → **布隆过滤器** 或 **空值缓存**
- 击穿 → 热点 key 过期 → **分布式锁** 或 **热点数据永不过期**
- 雪崩 → 大量 key 过期 → **TTL 加随机** 或 **Redis 集群**

#### 24. Django信号

- post_save / post_delete 解耦业务逻辑
- 评论增删自动更新帖子计数
- 代码位置：[forum/signals.py#L20-L62](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\forum\signals.py#L20-L62)

##### 深度讲解:Django Signal详解

**信号**是 Django 的观察者模式实现，允许某些动作在模型操作发生时自动通知到其他部分。

**核心思想**：解耦——当 A 模型变化时需要更新 B 模型，不直接在 A 中写 B 的逻辑，而是通过信号通知。

```
传统方式（耦合）：
  Comment.save() → 手动调用 Post.update_comment_count()
  → 如果有多处创建 Comment 的代码，每处都要写更新逻辑 → 容易遗漏

信号方式（解耦）：
  Comment.save() → 自动触发 post_save 信号 → Signal Handler 更新 Post
  → 无论在哪里创建 Comment，计数都会自动更新
```

###### 1. Django 内置信号一览

| 信号 | 触发时机 | 参数 | 常用场景 |
|------|----------|------|----------|
| `pre_save` | `save()` 之前 | instance, raw, using, update_fields | 数据预处理（如自动生成 slug） |
| **`post_save`** | `save()` 之后 | instance, created, raw, using, update_fields | **创建后更新关联计数** |
| `pre_delete` | `delete()` 之前 | instance, using | 删除前清理关联文件 |
| **`post_delete`** | `delete()` 之后 | instance, using | **删除后更新关联计数** |
| `m2m_changed` | 多对多关系变化时 | instance, action, model, pk_set | 标签关联变化时更新计数 |
| `pre_init` / `post_init` | 模型实例化 | instance, args, kwargs | 很少使用 |

**本项目使用的信号**：

| 信号 | sender | 触发场景 | 作用 |
|------|--------|----------|------|
| `post_save` | `Comment` | 评论创建 | 更新帖子评论数 |
| `post_delete` | `Comment` | 评论删除 | 更新帖子评论数 |
| `post_save` | `Tag` | 标签保存 | 更新标签使用次数 |

###### 2. 评论计数自动更新

**位置**：[forum/signals.py#L20-L62](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\forum\signals.py#L20-L62)

```python
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Comment, Tag


@receiver(post_save, sender=Comment)
def update_post_comment_count(sender, instance, created, **kwargs):
    """评论创建后，重新计算帖子的评论数"""
    if created and not instance.is_deleted:
        post = instance.post
        # 重新计算（排除已删除和隐藏的评论）
        post.comment_count = post.comments.filter(
            is_deleted=False, is_hidden=False
        ).count()
        post.save(update_fields=['comment_count'])


@receiver(post_delete, sender=Comment)
def update_post_comment_count_on_delete(sender, instance, **kwargs):
    """评论删除后，重新计算帖子的评论数"""
    post = instance.post
    post.comment_count = post.comments.filter(
        is_deleted=False, is_hidden=False
    ).count()
    post.save(update_fields=['comment_count'])
```

**工作流程**：

```
用户发表评论
  │
  ├─ Comment.objects.create(post=post, author=user, content='...')
  │
  ├─ Comment.save() 执行
  │
  ├─ 触发 post_save 信号
  │   ├─ sender = Comment（模型类）
  │   ├─ instance = 刚创建的评论对象
  │   └─ created = True（新创建）
  │
  ├─ update_post_comment_count() 被调用
  │   ├─ 检查 created=True 且未删除
  │   ├─ post.comments.filter(is_deleted=False, is_hidden=False).count()
  │   └─ post.save(update_fields=['comment_count'])  # 只更新评论数字段
  │
  └─ 评论数保持一致
```

**设计决策**：

| 决策 | 原因 |
|------|------|
| `recount` 而非 `F('comment_count') + 1` | 防止并发计数不一致，**以实际查询为准** |
| `update_fields=['comment_count']` | 只更新一个字段，避免触发完整的 `save()` |
| `filter(is_deleted=False, is_hidden=False)` | 软删除设计，排除已删除/隐藏的评论 |
| `post_save` 而非 `pre_save` | 确保评论已写入 DB 后再统计 |

###### 3. 标签使用次数更新

```python
@receiver(post_save, sender=Tag)
def update_tag_use_count(sender, instance, **kwargs):
    """标签保存时，重新计算使用次数"""
    instance.use_count = instance.posts.count()
    instance.save(update_fields=['use_count'])
```

**注意**：这里监听的是 `Tag` 模型的 `post_save`，而非 `Post` 模型。标签与帖子是多对多关系，通过中间表 `PostTag` 关联。

###### 4. 信号的注册方式

**方式一：`@receiver` 装饰器（本项目使用）**

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Comment)
def my_handler(sender, instance, created, **kwargs):
    ...
```

**方式二：手动连接**

```python
from django.db.models.signals import post_save
from .models import Comment

def my_handler(sender, instance, created, **kwargs):
    ...

post_save.connect(my_handler, sender=Comment)
```

**方式三：`AppConfig.ready()` 中注册**

```python
# apps.py
class ForumConfig(AppConfig):
    name = 'apps.forum'

    def ready(self):
        # 导入信号处理器，触发 @receiver 装饰器注册
        from . import signals
```

> **本项目注意**：[apps.py](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\forum\apps.py) 中**没有** `ready()` 方法，信号注册依赖 Django 的自动发现机制。当 `INSTALLED_APPS` 包含 `'apps.forum'` 时，Django 会自动导入 `signals.py` 模块（如果存在）。

> **最佳实践**：在 `AppConfig.ready()` 中显式导入 `signals`，确保信号一定被注册。本项目的做法可能在某些 Django 版本下信号不生效。

###### 5. 信号的执行顺序与事务

**执行顺序**：

```
Comment.objects.create(...)
  │
  ├─ 1. pre_save 信号触发
  ├─ 2. SQL INSERT 执行
  ├─ 3. post_save 信号触发
  │   └─ update_post_comment_count() → Post.save(update_fields=['comment_count'])
  │
  └─ 4. 事务提交（如果在 @transaction.atomic 中）
```

**事务注意**：

| 场景 | 行为 | 风险 |
|------|------|------|
| 不在事务中 | 信号在 `save()` 后立即执行 | 正常 |
| 在 `@transaction.atomic` 中 | 信号在 `save()` 后、**事务提交前**执行 | 如果信号中抛异常，整个事务回滚 |
| 事务提交后执行 | 需要使用 `transaction.on_commit()` | 避免信号中的 DB 操作影响主事务 |

**推荐做法**：

```python
from django.db import transaction

@receiver(post_save, sender=Comment)
def update_post_comment_count(sender, instance, created, **kwargs):
    if created:
        # 在事务提交后再执行，避免信号失败导致主操作回滚
        transaction.on_commit(lambda: _update_count(instance.post))

def _update_count(post):
    post.comment_count = post.comments.filter(
        is_deleted=False, is_hidden=False
    ).count()
    post.save(update_fields=['comment_count'])
```

###### 6. 信号 vs 重写 save() vs 业务层调用

三种方式实现"评论创建后更新帖子计数"：

| 方式 | 代码位置 | 优点 | 缺点 |
|------|----------|------|------|
| **信号** | `signals.py` | 完全解耦，自动触发 | 隐式执行，调试困难 |
| **重写 `save()`** | `models.py` | 逻辑集中 | 与模型耦合，`bulk_create` 不触发 |
| **业务层调用** | `views.py` / `services.py` | 显式可控 | 需要每处都写，容易遗漏 |

**选择依据**：

```
是否需要"所有创建操作"都触发？
  ├─ YES → 信号（包括 admin、shell、测试中的创建）
  └─ NO → 业务层调用（只在特定接口中触发）

是否需要在 bulk_create / bulk_update 时触发？
  ├─ 信号和 save() 都不会触发
  └─ 需要业务层手动处理
```

**本项目场景**：评论可以通过 API、Admin、Shell 多种方式创建，用信号保证所有入口都更新计数——合理。

###### 7. 信号的注意事项

| 注意点 | 说明 |
|--------|------|
| **`bulk_create` 不触发信号** | `Comment.objects.bulk_create([...])` 不触发 `post_save` |
| **`update()` 不触发信号** | `Comment.objects.filter(...).update(is_deleted=True)` 不触发 |
| **信号中避免重入** | `post.save()` 可能触发 `Post` 的 `post_save`，形成循环 |
| **测试中可能未注册** | 测试 runner 可能不加载 `AppConfig.ready()` |
| **调试困难** | 信号是隐式的，排查时容易忽略 |

###### 8. 设计模式总结

| 模式 | 实现 | 目的 |
|------|------|------|
| **观察者模式** | `@receiver` 注册监听器 | 模型变化时自动通知 |
| **解耦** | 信号发送方不知道接收方 | 业务逻辑分离 |
| **冗余字段** | `comment_count` 存储在 `Post` 表 | 避免每次列表查询都 `COUNT()` |

**面试关键回答**：
- Django Signal 是什么？→ 观察者模式，模型操作后自动触发回调
- 什么时候用信号？→ 需要解耦、所有创建入口都需要触发的场景
- 信号和重写 `save()` 的区别？→ 信号更解耦但隐式，`save()` 更集中但耦合
- `bulk_create` 会触发信号吗？→ 不会，需要手动处理
- 信号在事务中的行为？→ 默认在事务内执行，`transaction.on_commit()` 可延迟到提交后
- 为什么用 `recount` 而非 `+1`？→ 保证并发安全，以实际查询结果为准

#### 25. 环境与配置

##### 深度讲解:sys.path 注入

- 动态修改 sys.path，使 `apps.xxx` 导入路径成立
- 同时插入配置目录、apps 目录、项目根目录
- 代码位置：[settings/dev.py#L40-L50](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\settings\dev.py#L40-L50)

**什么是 sys.path？**

`sys.path` 是 Python 模块搜索路径列表，`import` 语句会按顺序在这些路径中查找模块。

```python
>>> import sys
>>> sys.path
['',                              # 当前目录
 '/usr/lib/python313',            # 标准库
 '/usr/lib/python313/lib-dynload',
 '/home/user/venv/lib/python3.13/site-packages'  # 第三方包
]
```

**核心规则**：`import apps.forum.models` 时，Python 会在 `sys.path` 的每个路径下查找 `apps/` 目录。

###### 1. 项目目录结构与导入问题

**本项目目录结构**：

```
cube_api/                          ← BASE_DIR（manage.py 所在）
├── manage.py
├── cube_api/                      ← 配置目录（settings/ 所在）
│   ├── settings/
│   │   ├── dev.py                 ← sys.path 注入发生在这里
│   │   └── prod.py
│   ├── utils/                     ← 工具层
│   └── apps/                      ← 应用目录
│       ├── accounts/
│       ├── forum/
│       └── shop/
└── requirements.txt
```

**问题**：Django 默认 `BASE_DIR` 是 `cube_api/`，但 `apps/` 在 `cube_api/cube_api/apps/` 下。

```
默认 sys.path：
  [cube_api/, ...]

import apps.forum.models
  → 在 cube_api/ 下找 apps/ → 找不到！
  → 实际路径是 cube_api/cube_api/apps/
```

###### 2. 三行 sys.path 注入

**位置**：[settings/dev.py#L40-L50](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\settings\dev.py#L40-L50)

```python
# 1. 将配置目录（cube_api/cube_api/）加入路径
#    使 utils、settings 等模块可直接导入
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 2. 将 apps 目录（cube_api/cube_api/apps/）加入路径
#    使 apps.accounts、apps.forum 等应用可直接导入
APPS_DIR = Path(__file__).resolve().parent.parent / 'apps'
if APPS_DIR.exists():
    sys.path.insert(0, str(APPS_DIR))

# 3. 将项目根目录（cube_api/）加入路径
#    方便导入项目级别的包和模块
sys.path.insert(0, str(BASE_DIR))
```

**路径解析过程**：

```
__file__ = cube_api/cube_api/settings/dev.py

Path(__file__).resolve()
  → /e/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py

.parent
  → /e/BH/PyStudy/ICube/cube_api/cube_api/settings/

.parent
  → /e/BH/PyStudy/ICube/cube_api/cube_api/  ← 配置目录

.parent
  → /e/BH/PyStudy/ICube/cube_api/  ← BASE_DIR
```

**注入后的 sys.path**：

```python
sys.path = [
    '/e/BH/PyStudy/ICube/cube_api/cube_api/apps',   # ← 注入 2：apps 目录
    '/e/BH/PyStudy/ICube/cube_api/cube_api',          # ← 注入 1：配置目录
    '/e/BH/PyStudy/ICube/cube_api',                   # ← 注入 3：项目根目录
    '',                                                # 当前目录
    '/usr/lib/python313',                             # 标准库
    '.../site-packages',                              # 第三方包
]
```

###### 3. 为什么用 insert(0, ...) 而非 append()？

| 方式 | 搜索顺序 | 风险 |
|------|----------|------|
| `insert(0, ...)` | **优先搜索**自定义路径 | 可能覆盖同名的第三方包 |
| `append(...)` | 最后搜索自定义路径 | 可能被同名的第三方包覆盖 |

**本项目用 `insert(0, ...)` 的原因**：

```
场景：项目有自定义的 utils 模块
  sys.path.insert(0, 'cube_api/cube_api/')
  → import utils.common_response
  → 优先找到 cube_api/cube_api/utils/common_response.py

如果用 append：
  → 可能先找到 site-packages/utils/（第三方包）
  → 导入了错误的模块
```

###### 4. 注入后的导入效果

| 导入语句 | 搜索路径 | 找到的模块 |
|----------|----------|------------|
| `from apps.forum.models import Post` | 注入 2（apps 目录） | `apps/forum/models.py` |
| `from utils.common_response import APIResponse` | 注入 1（配置目录） | `utils/common_response.py` |
| `from settings.dev import *` | 注入 1（配置目录） | `settings/dev.py` |
| `import rest_framework` | site-packages | 第三方包 |

###### 5. 面试常见追问

**Q：sys.path 注入在什么时候执行？**

```
Django 启动流程：
  1. python manage.py runserver
  2. 加载 settings 模块（dev.py 或 prod.py）
  3. dev.py 执行 → sys.path.insert(...)  ← 此时注入
  4. Django 读取 INSTALLED_APPS → import apps.xxx  ← 注入已生效
  5. 加载 URLconf、中间件、视图等
```

**Q：sys.path 注入有什么风险？**

| 风险 | 说明 | 缓解 |
|------|------|------|
| **模块名冲突** | 自定义 `utils` 可能覆盖第三方 `utils` | 命名时加项目前缀（如 `icube_utils`） |
| **IDE 警告** | PyCharm / VSCode 可能无法识别注入的路径 | 配置 `pythonpath` 或 `sources root` |
| **不可移植** | 换环境后路径可能变化 | 用 `Path(__file__).resolve()` 相对定位 |

**Q：`prod.py` 需要再次注入吗？**

```python
# prod.py 第一行
from .dev import *  # ← 导入 dev.py 时已执行 sys.path 注入
```

不需要。`prod.py` 通过 `from .dev import *` 继承 `dev.py`，注入在导入时已执行。

##### 深度讲解:测试模式自动切换

- `if 'test' in sys.argv` 检测
- SQLite 内存库 + Mock Redis + 禁用限流 + MD5 哈希
- 代码位置：[settings/dev.py#L190-L369](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\settings\dev.py#L190-L369)

**为什么需要测试模式自动切换？**

```
测试环境痛点：
  1. MySQL 建表慢 → 每次测试都要 CREATE TABLE
  2. Redis 状态残留 → 上次测试的数据影响下次
  3. PBKDF2 密码哈希慢 → 创建用户耗时
  4. 限流干扰 → 并发测试触发 429

解决方案：
  if 'test' in sys.argv:
      → SQLite 内存库（无需建表，内存中创建）
      → Mock Redis（用 Django cache 替代）
      → MD5 哈希（比 PBKDF2 快 100 倍）
      → 禁用限流（测试不受限制）
```

###### 1. 检测机制

**位置**：[settings/dev.py#L190](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\settings\dev.py#L190)

```python
if 'test' in sys.argv:
    # 测试模式配置...
```

**原理**：执行 `python manage.py test` 时，`sys.argv` 为 `['manage.py', 'test']`，包含 `'test'` 字符串。

```python
# 开发环境
$ python manage.py runserver
  sys.argv = ['manage.py', 'runserver']  → 'test' not in sys.argv → 正常配置

# 测试环境
$ python manage.py test
  sys.argv = ['manage.py', 'test']       → 'test' in sys.argv → 测试配置

# pytest 环境（兼容）
if 'test' in sys.argv or 'pytest' in sys.modules:
    # 额外检测 pytest 导入
```

**两种检测方式对比**：

| 方式 | 检测对象 | 适用场景 | 本项目使用 |
|------|----------|----------|------------|
| `'test' in sys.argv` | 命令行参数 | `python manage.py test` | ✅ |
| `'pytest' in sys.modules` | 已导入的模块 | `pytest` 运行 | ✅（Redis 配置使用） |

###### 2. SQLite 内存数据库

```python
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # 内存数据库
    }
```

**SQLite 内存库 vs MySQL**：

| 对比项 | SQLite `:memory:` | MySQL |
|--------|-------------------|-------|
| 建表速度 | 极快（内存操作） | 慢（磁盘 I/O） |
| 数据隔离 | 每次测试全新数据库 | 需要手动清理 |
| 并发支持 | 单线程写入 | 多线程 |
| 持久化 | 进程结束自动销毁 | 持久化到磁盘 |
| 适用场景 | 单元测试 | 集成测试、生产 |

**注意**：SQLite 与 MySQL 有 SQL 方言差异，测试通过不代表生产一定没问题。例如：
- `SQLite` 不支持 `SELECT FOR UPDATE` 行锁
- `SQLite` 不区分大小写的 `LIKE` 默认行为不同
- `SQLite` 没有完整的 `FULL OUTER JOIN` 支持

###### 3. Mock Redis

**位置**：[settings/dev.py#L364-L369](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\settings\dev.py#L364-L369)

```python
if 'test' in sys.argv:
    import django_redis

    def mock_get_redis_connection(alias):
        """Mock Redis 连接，返回 Django cache 对象"""
        from django.core.cache import cache
        return cache

    # 替换全局函数
    django_redis.get_redis_connection = mock_get_redis_connection
```

**Mock 原理**：

```
业务代码：
  from django_redis import get_redis_connection
  con = get_redis_connection('default')
  con.incr('forum:post:1:view')     # Redis incr

测试环境（Mock 后）：
  get_redis_connection = mock_get_redis_connection
  con = mock_get_redis_connection('default')
  → return django.core.cache.cache  # 返回 Django 缓存对象

  con.incr('forum:post:1:view')
  → django.core.cache.cache.incr(...)  # 用 Django 缓存模拟 Redis
```

**Mock 的局限性**：

| Redis 特性 | Django cache 是否支持 |
|------------|---------------------|
| `incr()` / `decr()` | ✅ 支持 |
| `sadd()` / `smembers()` | ❌ 不支持（Set 操作） |
| `setex()` | ✅ 支持（`set(key, val, timeout)`） |
| `pipeline()` | ❌ 不支持 |
| `expire()` | ✅ 支持 |

> **本项目注意**：`ProfileCacheService` 使用了 Redis Set 操作（`sadd`/`smembers`/`sismember`），Mock 后这些操作可能报错。测试中可能需要额外 Mock 或跳过相关测试。

###### 4. MD5 密码哈希加速

```python
if 'test' in sys.argv:
    PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ]
```

**性能对比**：

| 哈希器 | 算法 | 迭代次数 | 单次耗时 | 安全性 |
|--------|------|----------|----------|--------|
| PBKDF2 | SHA-256 | 600,000 | ~300ms | 高 |
| Argon2 | Argon2id | - | ~200ms | 最高 |
| **MD5** | MD5 | 1 | <1ms | ❌ 不安全 |

> **注意**：MD5 仅用于测试加速，生产环境**绝对不能**使用。Django 默认的 PBKDF2 通过高迭代次数抵抗暴力破解。

###### 5. 禁用限流

```python
if 'test' in sys.argv:
    REST_FRAMEWORK = {
        'DEFAULT_THROTTLE_CLASSES': [],    # 清空限流类
        'DEFAULT_THROTTLE_RATES': {},      # 清空限流速率
    }
```

**为什么禁用限流？**

```
测试场景：批量请求登录接口
  for i in range(10):
      response = self.client.post('/api/login/', {...})

不禁用限流：
  → 第 4 次请求返回 429 Too Many Requests
  → 测试失败：期望 200，实际 429

禁用限流：
  → 所有请求正常处理
  → 测试关注业务逻辑，不关注限流
```

###### 6. 测试配置全景

| 配置项 | 开发环境 | 测试环境 | 切换原因 |
|--------|----------|----------|----------|
| DB ENGINE | MySQL 8.0 | SQLite `:memory:` | 速度 + 隔离 |
| Redis | `redis://127.0.0.1:6379/1` | Mock → Django cache | 去依赖 |
| 密码哈希 | PBKDF2 (600k 迭代) | MD5 (1 迭代) | 速度 |
| 限流 | anon=100/d, user=1000/d | 禁用 | 不干扰测试 |
| KEY_PREFIX | `icube` | `icube_test` | 数据隔离 |
| 缓存 TTL | 86400s (24h) | 300s (5min) | 测试不需要长 TTL |

**面试关键回答**：
- 如何检测测试环境？→ `if 'test' in sys.argv` 检查命令行参数
- 为什么用 SQLite 内存库？→ 快速、自动销毁、无污染
- 为什么用 MD5 哈希？→ PBKDF2 太慢，测试需要快速创建用户
- 如何 Mock Redis？→ 替换 `django_redis.get_redis_connection` 为返回 Django cache 的函数
- 为什么禁用限流？→ 避免限流干扰测试逻辑，限流应单独测试
- Mock Redis 有什么局限？→ 不支持 Set、Pipeline 等 Redis 特有操作
- SQLite 测试能完全替代 MySQL 吗？→ 不能，SQL 方言有差异，建议补充集成测试

#### 26. Service层模式

Service 层位于 View 与数据访问层之间，用于承载跨模型、缓存、事务和业务规则。它不是 Django 强制要求的层，而是随着业务复杂度增加主动引入的职责边界。

```text
HTTP 请求
  → View：鉴权、解析参数、调用 Service、构造响应
  → Service：执行业务规则、事务、缓存和复杂查询
  → Model / ORM / Redis：持久化与数据访问
```

##### 深度讲解:Service层模式详解

###### 1. 为什么需要 Service 层

如果所有逻辑都直接写在 View 中，View 往往会同时处理：

- 请求参数和权限。
- 多个模型的查询与更新。
- Redis 缓存读写。
- 事务和并发控制。
- 业务状态判断。
- HTTP 响应结构。

这会形成难以复用和测试的"胖 View"。Service 层把与 HTTP 无关的业务流程提取出来，使每层只承担稳定的职责：

| 层 | 主要职责 | 不适合承担的职责 |
|----|----------|------------------|
| View | 权限、参数、调用 Service、返回 `APIResponse` | 复杂事务、跨模型规则 |
| Serializer | 输入校验、序列化与反序列化 | 缓存策略、复杂业务编排 |
| Service | 业务规则、事务、缓存、复杂查询 | 直接依赖 HTTP Request 和 Response |
| Model | 数据结构、约束、简单领域行为 | 请求参数和响应格式 |

###### 2. 项目中的 Service

论坛 Service 集中在 [services.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/services.py)：

| Service | 核心方法 | 职责 |
|---------|----------|------|
| `PostCacheService` | `increase_view()`、`get_view_count()`、`sync_all_views()` | 使用 Redis 聚合浏览量并同步数据库 |
| `PostInteractionService` | `toggle_like()`、`toggle_collect()`、`toggle_comment_reaction()` | 处理点赞、收藏和评论反应 |
| `HotPostService` | `get_hot_posts()` | 按时间范围和热度公式查询热门帖子 |

View 只保留请求层逻辑。例如点赞接口先取得当前帖子，再把业务处理交给 Service：

```python
post = self.get_object()
result = PostInteractionService.toggle_like(post.id, request.user)
return APIResponse(**result)
```

调用位置见 [views.py#L242-L266](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/views.py#L242-L266)。

这样做的直接收益：

- 点赞逻辑可以被 View、管理命令或定时任务复用。
- Service 可以脱离 HTTP 请求单独测试。
- View 不需要了解计数器和关系表如何更新。
- 缓存或热度算法变化时，接口层基本不需要修改。

###### 3. PostCacheService：缓存与降级

浏览量服务位于 [services.py#L28-L178](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/services.py#L28-L178)，缓存键格式为：

```text
forum:post:{post_id}:view
```

设计目标：

1. 浏览请求先通过 Redis `INCR` 更新计数，利用 Redis 单线程命令的原子性承受高并发。
2. 读取时优先访问缓存，减少数据库查询。
3. 定时把 Redis 中的浏览量同步到 MySQL。
4. Redis 异常时使用 Django `F()` 表达式直接更新数据库。

数据库降级使用：

```python
Post.objects.filter(id=post_id).update(
    view_count=F('view_count') + 1
)
```

`F()` 表达式让数据库直接执行 `view_count = view_count + 1`，避免多个请求先读后写造成更新丢失。

###### 4. PostInteractionService：关系记录与冗余计数

点赞和收藏同时维护两类数据：

- **关系表：** 记录哪个用户操作了哪个帖子，用于判断用户状态。
- **冗余计数：** `like_count`、`collect_count` 等字段，用于列表快速展示和排序。

关系表通过唯一约束防止重复记录，例如 `PostLike` 的 `(post, user)` 唯一，见 [models.py#L257-L280](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/models.py#L257-L280)。

评论反应支持三种状态转换：

```text
无记录 → 点赞或点踩
相同操作 → 取消
点赞 ↔ 点踩
```

切换点赞和点踩时，Service 在一条 `UPDATE` 中同时修改两个计数：

```python
Comment.objects.filter(id=comment_id).update(
    like_count=F('like_count') + 1,
    dislike_count=F('dislike_count') - 1
)
```

这种写法保证两个计数字段在同一条 SQL 中完成更新，但关系记录与计数更新仍然是不同 SQL。

###### 5. HotPostService：数据库层计算

热门帖子服务位于 [services.py#L348-L390](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/services.py#L348-L390)，只统计最近 `N` 天已发布的帖子：

```python
hot_score = (
    F('like_count') * 3
    + F('comment_count') * 2
    + F('view_count')
)
```

权重含义：

- 点赞 `×3`：代表用户认可。
- 评论 `×2`：代表用户参与。
- 浏览 `×1`：代表内容曝光。

使用 ORM `annotate()` 在数据库层计算和排序，避免把所有帖子加载到 Python 内存后再处理。不过该计算字段无法直接使用普通索引排序，数据量大时仍可能出现临时表或 filesort。

###### 6. 当前实现需要注意的边界

**toggle 不是严格的幂等接口**

唯一约束能保证同一用户只有一条点赞记录，但 `toggle_like()` 连续调用两次会先点赞再取消，最终状态发生两次变化。因此它是"状态切换接口"，不是严格意义上的幂等接口。

如果业务要求幂等，应该拆分为明确状态：

```text
PUT /posts/{id}/like    → 保证最终为已点赞
DELETE /posts/{id}/like → 保证最终为未点赞
```

**关系记录与计数缺少事务**

当前点赞流程先创建或删除关系记录，再更新冗余计数，中间没有 `transaction.atomic()`。任意一步失败，都可能造成关系表与计数字段不一致。

更稳妥的边界是：

```python
from django.db import transaction

with transaction.atomic():
    post = Post.objects.select_for_update().get(id=post_id)
    # 修改关系记录
    # 更新冗余计数
```

`select_for_update()` 可以串行化同一帖子的并发修改，唯一约束则作为最终防线。

**exists + create 存在并发竞争**

两个并发请求可能同时执行 `exists()` 并都得到 `False`，随后同时创建记录，其中一个请求会触发唯一约束异常。Service 应在事务中处理 `IntegrityError`，或使用带锁的状态判断。

**浏览量缓存的"总量"和"增量"语义混用**

`get_view_count()` 会把数据库总浏览量写入缓存，而 `sync_all_views()` 又把缓存值当作增量累加到数据库。一旦缓存由读取流程初始化，同步时可能重复累加历史总量。

缓存键必须明确选择一种语义：

- **增量模式：** Redis 只保存未落库增量，展示值为数据库总量加 Redis 增量。
- **总量模式：** Redis 保存最终总量，同步时使用覆盖或计算差值，不能直接累加。

**Redis KEYS 会阻塞**

`sync_all_views()` 使用 `KEYS "*forum:post:*:view"`，见 [services.py#L125-L174](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/services.py#L125-L174)。`KEYS` 会一次遍历全部键，生产环境应使用 `SCAN` 分批处理。

**Service 不应返回 HTTP 协议结构**

当前 `toggle_comment_reaction()` 直接返回 `code`、`msg`、`data`，而点赞和收藏返回普通业务字典，接口不一致。更清晰的做法是让 Service 只返回领域结果，由 View 统一包装 `APIResponse`。

###### 7. 面试回答

> 项目在 DRF View 与 ORM 之间增加了 Service 层。View 只负责鉴权、解析参数和返回响应，Service 负责 Redis 缓存、跨模型更新、热度计算和业务状态切换。例如点赞接口只调用 `PostInteractionService.toggle_like()`，具体的关系记录和冗余计数都封装在 Service 中。这样可以降低 View 复杂度，提高复用性和可测试性。但抽到 Service 并不等于天然安全，跨表修改仍要使用事务和数据库约束，缓存也必须明确总量或增量语义。


---

### 前端重点

#### 1. 图片裁剪组件
**文件**: [ImageCropper.vue](file:///e:/BH/PyStudy/ICube/cube_front/src/components/ImageCropper.vue)

**核心实现**:
- **Canvas裁剪**: 使用HTML5 Canvas实现1:1固定比例裁剪框
- **滚轮缩放**: 鼠标滚轮控制图片缩放，支持平滑过渡
- **防抖拖拽**: 使用防抖函数处理拖拽事件，避免频繁重绘
- **实时预览**: 裁剪框内实时显示裁剪结果
- **大图片优化**: 原图>2048px时先缩小再裁剪，提升性能

**关键代码**:
```javascript
const onWheel = (e) => {
  e.preventDefault()
  const delta = e.deltaY > 0 ? -0.1 : 0.1
  scale.value = Math.max(1, Math.min(scale.value + delta, 5))
}

const startDrag = (e) => {
  isDragging.value = true
  lastX.value = e.clientX
  lastY.value = e.clientY
}

// 防抖处理拖拽
const handleDrag = debounce((e) => {
  if (!isDragging.value) return
  const dx = e.clientX - lastX.value
  const dy = e.clientY - lastY.value
  offsetX.value += dx
  offsetY.value += dy
  lastX.value = e.clientX
  lastY.value = e.clientY
}, 16)
```

#### 2. 公式编辑器
**文件**: [FormulaEditor.vue](file:///e:/BH/PyStudy/ICube/cube_front/src/components/formula/FormulaEditor.vue)

**核心功能**:
- **点击式键盘输入**: 模拟魔方键盘，支持R/L/U/D/F/B/r/l/u/d/f/b/M/E/S/x/y/z等所有操作
- **直接字符串输入**: 支持直接输入公式字符串，自动解析格式
- **图片来源选择**: 可从公式库选择图片或自己上传
- **分类/难度选择**: 下拉选择分类和难度等级
- **实时预览**: 编辑时实时显示公式效果

**关键代码**:
```javascript
const notationKeys = [
  ['R', 'L', 'U', 'D', 'F', 'B'],
  ['r', 'l', 'u', 'd', 'f', 'b'],
  ['M', 'E', 'S', 'x', 'y', 'z']
]

const addNotation = (key) => {
  if (shiftPressed.value) {
    formula.value += key + "'"
  } else {
    formula.value += key
  }
}

const handleImageSelect = async (formulaId) => {
  const res = await getFormulaDetail(formulaId)
  if (res.code === 100) {
    form.thumbnail_path = res.data.thumbnail
  }
}
```

#### 3. 公式多重筛选
**文件**: [FormulaLibrary.vue](file:///e:/BH/PyStudy/ICube/cube_front/src/components/formula/FormulaLibrary.vue)

**筛选维度**:
- **分类筛选**: 按公式分类（F2L/OLL/PLL等）
- **难度筛选**: 支持多选难度等级
- **作者筛选**: 下拉选择作者进行筛选
- **搜索**: 按名称/记号关键词搜索

**关键代码**:
```javascript
const filterParams = computed(() => {
  const params = {}
  if (selectedCategory.value) params.category = selectedCategory.value
  if (selectedDifficulty.value.length) params.difficulty = selectedDifficulty.value.join(',')
  if (selectedAuthor.value) params.created_by = selectedAuthor.value
  if (keyword.value) params.search = keyword.value
  return params
})
```

#### 4. 价格筛选优化
**文件**: [ShopView.vue](file:///e:/BH/PyStudy/ICube/cube_front/src/views/ShopView.vue)

**优化内容**:
- **快捷价格区间标签**: 添加5个常用区间（0-50元、50-100元、100-200元、200-500元、500元以上），点击快速筛选
- **输入框优化**: 改为 `type="number"`，只允许输入数字；添加重置按钮；布局改为垂直排列避免小屏幕显示不全
- **交互优化**: 点击快捷标签自动取消手动输入值，手动筛选自动取消选中标签
- **样式优化**: 标签区域使用分隔线与输入框区分，悬停有轻微上浮效果

**关键代码**:
```javascript
const priceTags = ref([
  { key: '0-50', label: '0-50元', min: 0, max: 50 },
  { key: '50-100', label: '50-100元', min: 50, max: 100 },
  { key: '100-200', label: '100-200元', min: 100, max: 200 },
  { key: '200-500', label: '200-500元', min: 200, max: 500 },
  { key: '500+', label: '500元以上', min: 500, max: null },
])

const selectPriceTag = (tag) => {
  if (selectedPriceTag.value === tag.key) {
    resetPriceFilter()
    return
  }
  priceMin.value = tag.min
  priceMax.value = tag.max || ''
  selectedPriceTag.value = tag.key
  currentPage.value = 1
  loadProducts()
}
```

#### 5. 3D魔方可视化
**文件**: [CubeDemo.vue](file:///e:/BH/PyStudy/ICube/cube_front/src/components/formula/CubeDemo.vue)

**核心实现**:
- **Three.js 场景搭建**: Scene + PerspectiveCamera + WebGLRenderer + OrbitControls
- **魔方几何**: 27个小立方体 (3x3x3)，每个面独立材质
- **公式记号解析**: 支持 R/L/U/D/F/B/r/l/u/d/f/b/M/E/S/x/y/z 等标准魔方记号
- **层旋转算法**: 根据记号提取旋转轴、角度、参与旋转的方块条件
- **Tween.js 动画**: 平滑过渡，支持上一步/下一步/自动播放

**内存管理**:
- `onBeforeUnmount` 中执行 `geometry.dispose()`、`material.dispose()`、`renderer.dispose()`
- 取消 `requestAnimationFrame` 和 `autoPlayTimer`

**状态定义**:
```json
{
  "faces": {
    "F": [["blue", "blue", "blue"], ["blue", "blue", "blue"], ["blue", "blue", "blue"]],
    "B": [["green", "green", "green"], ...],
    "U": [["yellow", ...], ...],
    "D": [["white", ...], ...],
    "L": [["orange", ...], ...],
    "R": [["red", ...], ...]
  }
}
```

#### 6. 状态管理 (Pinia)
**文件**: [stores/](file:///e:/BH/PyStudy/ICube/cube_front/src/stores/)

**模块划分**:
- `user.js`: 用户登录状态、token、个人信息
- `menu.js`: 菜单导航状态

**持久化**: token 存储在 `localStorage`，页面刷新后自动恢复

#### 7. 请求拦截器
**文件**: [request.js](file:///e:/BH/PyStudy/ICube/cube_front/src/http/request.js)

**请求拦截**:

- 自动注入 Token: `config.headers['Authorization'] = 'Token ' + token`
- 统一超时设置: 5000ms
- **baseURL**: 设置为 `/`，配合 Vite 代理配置

**响应拦截**:

- 业务错误处理: `code !== 100` 时显示错误消息并 reject
- HTTP错误处理: 401/404/500 等状态码统一提示

#### 8. 路由结构
**文件**: [index.js](file:///e:/BH/PyStudy/ICube/cube_front/src/router/index.js)

**路由设计**:
- **父布局路由**: HomeView 作为根布局，包含 Header/Footer
- **子路由**: 所有业务页面作为 HomeView 的 children
- **认证标记**: 需要登录的路由配置 `meta: { requiresAuth: true }`
- **独立页面**: LoginView/RegisterView 独立于 HomeView，无导航栏
- **教程路由**: 6个教程页面路由（beginner/cfop/oll-essentials/pll-essentials/complete-oll/complete-pll）

**路由参数传递**:
- 通过 query 参数传递 `formula_id`，实现首页精选公式到公式库详情的跳转联动

#### 9. 公式跳转联动
**文件**: [Main.vue](file:///e:/BH/PyStudy/ICube/cube_front/src/components/Main.vue), [FormulaLibrary.vue](file:///e:/BH/PyStudy/ICube/cube_front/src/components/formula/FormulaLibrary.vue)

**实现流程**:
1. **首页跳转**: 点击精选公式卡片，通过路由 query 参数传递公式ID
```javascript
const goToFormula = (id) => {
  router.push({ path: '/formulas', query: { formula_id: id } })
}
```

2. **目标页面接收**: 在 FormulaLibrary.vue 的 `onMounted` 中读取 query 参数并自动打开详情弹窗
```javascript
import { useRoute } from 'vue-router';
const route = useRoute();

const openFormulaById = async (formulaId) => {
  const res = await getFormulaDetail(formulaId);
  if (res.code === 100) {
    selectedFormula.value = res.data;
    showDetailDialog.value = true;
  }
};

onMounted(() => {
  const formulaId = route.query.formula_id;
  if (formulaId) {
    openFormulaById(formulaId);
  }
});
```

#### 10. Vite 代理配置
**文件**: [vite.config.js](file:///e:/BH/PyStudy/ICube/cube_front/vite.config.js)

**配置要点**:
- **开发模式 (server.proxy)**: 配置 `/api` 和 `/media` 代理到 `http://127.0.0.1:8000`
- **预览模式 (preview.proxy)**: 同样配置代理，确保构建后预览时媒体文件能正确访问

**关键代码**:
```javascript
server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
        '/api': {
            target: 'http://127.0.0.1:8000',
            changeOrigin: true,
        },
        '/media': {
            target: 'http://127.0.0.1:8000',
            changeOrigin: true,
        }
    }
},
preview: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
        '/api': {
            target: 'http://127.0.0.1:8000',
            changeOrigin: true,
        },
        '/media': {
            target: 'http://127.0.0.1:8000',
            changeOrigin: true,
        }
    }
}
```

#### 11. 教程页面体系
**文件**: [tutorial/](file:///e:/BH/PyStudy/ICube/cube_front/src/views/tutorial/)

**6个教程页面**:
| 页面 | 路径 | 内容 |
|------|------|------|
| BeginnerTutorial.vue | `/tutorial/beginner` | 层先法教程（7步骤） |
| CFOPTutorial.vue | `/tutorial/cfop` | CFOP教程（十字/F2L/OLL/PLL） |
| OLLEssentials.vue | `/tutorial/oll-essentials` | OLL基础教程（两步OLL：10个算法） |
| PLLEssentials.vue | `/tutorial/pll-essentials` | PLL基础教程（两步PLL：6个算法） |
| CompleteOLL.vue | `/tutorial/complete-oll` | 完整OLL教程（57个算法） |
| CompletePLL.vue | `/tutorial/complete-pll` | 完整PLL教程（21个算法） |

**学习路径**:
- **初学者路径**: 两步OLL（10个算法）+ 两步PLL（6个算法），共16个算法，1-2周学会
- **进阶路径**: 完整OLL（57个算法）+ 完整PLL（21个算法），共78个算法，达到sub-20秒

---

### 部署重点

#### 1. Docker Compose 完整部署方案
**文件**: [docker-compose.yml](file:///e:/BH/PyStudy/ICube/docker-compose.yml)

**服务架构**:
```
浏览器
  → 网关 Nginx :80
      ├─ /api/*    → api:8000（Django + Gunicorn）
      ├─ /media/*  → ./cube_api/media
      ├─ /static/* → collected_static
      └─ /*        → front:80（前端 Nginx → Vue dist）
```

**5个服务详解**:

| 服务 | 镜像 | 端口 | 作用 |
|------|------|------|------|
| **db** | `mysql:8.0` | `127.0.0.1:3306` | 主数据库；远程管理通过 SSH 隧道 |
| **redis** | `redis:7-alpine` | `6379` | JWT 黑名单、缓存和登录限流 |
| **api** | 后端多阶段构建 | 容器内 `8000` | Django + Gunicorn API |
| **front** | 前端多阶段构建 | 容器内 `80` | 前端 Nginx 提供镜像内的 Vue `dist` |
| **nginx** | `nginx:1.28-alpine` | `80/443` | 统一网关；当前站点配置实际监听 HTTP 80 |

**关键配置**:
- **MySQL 健康检查**: `start_period: 45s` 为首次初始化预留时间，API 通过 `condition: service_healthy` 等待数据库可用
- **数据持久化**: MySQL、Redis 使用命名卷，媒体文件使用 `./cube_api/media` 绑定目录
- **静态文件共享**: API 将 `collectstatic` 结果写入 `collected_static`，网关 Nginx 直接提供 `/static/`
- **镜像不可变**: API 代码和前端 `dist` 均写入镜像，更新代码后必须重新构建目标镜像
- **环境变量**: `.env` 向 Compose 注入 `ALLOWED_HOSTS`、`ALLOWED_ORIGIN`、`SERVER_HOST`、`DB_PASSWORD`

**环境变量示例 (.env)**:
```dotenv
ALLOWED_HOSTS=服务器IP或域名,localhost
ALLOWED_ORIGIN=服务器IP或域名
SERVER_HOST=服务器IP或域名
DB_PASSWORD=icube123
```

`ALLOWED_ORIGIN` 和 `SERVER_HOST` 不带协议；包含 `$` 的值使用单引号，避免被 Compose 当作变量插值。

**部署模式**:
```bash
bash deploy.sh full   # 首次部署、Docker 配置变更或全量更新
bash deploy.sh api    # 仅构建后端、执行 migration、重启 Nginx
bash deploy.sh front  # 仅构建前端、重启 Nginx
```

#### 2. 后端Dockerfile详解
**文件**: [Dockerfile](file:///e:/BH/PyStudy/ICube/cube_api/Dockerfile)

后端采用 `python:3.13-slim` 多阶段构建：

1. **builder 阶段**: 安装 `gcc`、`default-libmysqlclient-dev`、`pkg-config`，将 Gunicorn 和项目依赖构建为 wheel
2. **runtime 阶段**: 只安装 `libmariadb3`、wheel 依赖和项目代码，不保留编译工具链
3. **启动流程**: 先执行 `python manage.py collectstatic --noinput`，再以 3 个 worker 启动 Gunicorn
4. **生产约束**: 不使用 `--reload`；API 不挂载宿主机源码，代码更新必须重建镜像

#### 3. 前端Dockerfile详解
**文件**: [Dockerfile](file:///e:/BH/PyStudy/ICube/cube_front/Dockerfile)

前端采用 Node + Nginx 多阶段构建：

1. **builder 阶段**: 基于 `node:20-alpine`，使用 `npm ci` 安装锁定依赖并执行 `npm run build`
2. **runtime 阶段**: 基于 `nginx:1.28-alpine`，只复制 `dist` 和前端 Nginx 配置
3. **SPA 回退**: 前端 Nginx 使用 `try_files $uri $uri/ /index.html`
4. **缓存策略**: `/assets/` 长缓存，`index.html` 禁止缓存

构建产物直接写入镜像，不需要本地生成或提交 `cube_front/dist`。

#### 4. Nginx配置详解
**文件**: [icube.conf](file:///e:/BH/PyStudy/ICube/nginx/conf.d/icube.conf)

**路由规则**:
| 路径 | 处理方式 | 关键配置 |
|------|---------|---------|
| `/api/*` | proxy_pass | 转发到 `http://api:8000`，保留 `/api/` 前缀 |
| `/media/*` | alias | 直接访问绑定目录，30天缓存 |
| `/static/*` | alias | 直接访问 `collected_static`，30天缓存 |
| `/*` | proxy_pass | 转发到 `http://front:80` |

**代理头设置**:
```nginx
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```

**配置要点**:
- **`server_name _`**: 通配符配置，支持任意域名访问
- **双层 Nginx**: 外层负责网关路由，前端容器内 Nginx 负责 `dist` 和 SPA 回退
- **`expires 30d`**: 静态文件设置30天缓存，减少重复请求
- **`proxy_connect_timeout 60s`**: 增加连接超时时间，应对慢请求

#### 5. 生产环境配置
**文件**: [prod.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/prod.py)

**环境变量读取**:
- `ALLOWED_HOSTS`: 通过 `os.getenv('ALLOWED_HOSTS')` 动态获取，支持逗号分隔多个域名
- `CORS_ALLOWED_ORIGINS`: 根据 `ALLOWED_ORIGIN` 自动生成 http/https 地址列表
- `SECRET_KEY`: 从环境变量读取，防止硬编码泄露
- `DB_NAME/DB_USER/DB_PASSWORD/DB_HOST`: 数据库连接参数

**配置特点**:
- **数据库**: 使用 MySQL，通过环境变量配置连接
- **缓存**: 使用 Redis，配置 `django_redis` 缓存后端
- **日志**: 使用 Loguru 统一记录日志
- **DEBUG**: 生产环境设为 `False`，关闭调试模式
- **当前边界**: Compose 尚未将 `SECRET_KEY` 注入 API，生产环境需要补齐

#### 6. Docker网络配置
**自定义网络**: `icube_network`（bridge模式）

**网络隔离**:
- 所有服务连接到同一自定义网络
- 容器间通过 Compose 服务名通信（如 `http://api:8000`）
- MySQL 绑定 `127.0.0.1:3306:3306`，远程连接使用 SSH 隧道
- Redis 当前仍映射 `6379:6379`，生产环境无宿主机直连需求时应移除或限制到回环地址

**卷挂载策略**:
| 卷名 | 用途 | 宿主路径 | 容器路径 |
|------|------|---------|---------|
| `mysql_data` | MySQL数据持久化 | 自动 | `/var/lib/mysql` |
| `redis_data` | Redis数据持久化 | 自动 | `/data` |
| `collected_static` | 静态文件共享 | 自动 | `/app/collected_static` / `/usr/share/nginx/html/static` |
| `./cube_api/media` | 媒体文件共享 | 仓库目录 | `/app/media` / `/usr/share/nginx/html/media` |

MySQL 字符集、排序规则和监听地址通过 Compose `command` 参数设置，不再 bind mount `mysql.conf`。

#### 7. 完整部署流程
```bash
# 1. 上传项目到服务器
git clone <项目仓库>
cd ICube

# 2. 在项目根目录创建并编辑 .env
# 配置 ALLOWED_HOSTS、ALLOWED_ORIGIN、SERVER_HOST、DB_PASSWORD

# 3. 首次全量部署
bash deploy.sh full

# 4. 创建超级管理员（可选）
docker compose exec api python manage.py createsuperuser

# 5. 检查服务状态和日志
docker compose ps
docker compose logs -f api nginx
```

`deploy.sh` 会执行 `git pull --ff-only`、按模式构建镜像、等待数据库、执行 migration、启动服务、重启 Nginx 并验证 HTTP/MySQL/Redis。使用普通部署用户运行，不执行 `sudo bash deploy.sh`，也禁止执行会删除数据卷的 `docker compose down -v`。

**验证部署**:
1. 访问 `http://your-server-ip/admin/` 验证后台管理界面
2. 访问 `http://your-server-ip/` 验证前端页面
3. 测试 API: `curl http://your-server-ip/api/formulas/`

#### 8. CORS配置

CORS（Cross-Origin Resource Sharing，跨源资源共享）是浏览器的安全机制。服务器通过响应头声明哪些来源可以读取响应，从而有条件地放宽同源策略。

##### 深度讲解:CORS配置详解

**1. 什么是"同源"**

浏览器判断两个 URL 是否同源，需要同时比较：

```text
协议（scheme）+ 主机（host）+ 端口（port）
```

| 前端地址 | API 地址 | 是否同源 |
|----------|----------|----------|
| `http://localhost:5173` | `http://localhost:8000` | 否，端口不同 |
| `http://localhost:5173` | `http://127.0.0.1:5173` | 否，主机不同 |
| `https://icube.example.com` | `https://icube.example.com/api/` | 是 |
| `https://www.example.com` | `https://api.example.com` | 否，子域不同 |

CORS 限制的是浏览器中的跨源 JavaScript 请求。`curl`、Postman 和服务器之间的 HTTP 调用不受浏览器同源策略限制。

**2. 简单请求与预检请求**

满足特定方法、请求头和 Content-Type 条件的请求属于简单请求，浏览器直接发送，再根据响应中的 CORS 头决定是否允许前端读取。

携带 `Authorization`、使用 `application/json` 或非简单方法时，浏览器通常先发送预检请求：

```http
OPTIONS /api/forum/posts/
Origin: http://localhost:5173
Access-Control-Request-Method: POST
Access-Control-Request-Headers: authorization, content-type
```

服务器允许后返回：

```http
Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Methods: POST, OPTIONS
Access-Control-Allow-Headers: authorization, content-type
```

预检通过后，浏览器才发送真正的业务请求。

**3. CorsMiddleware 为什么要靠前**

项目在 [dev.py#L101-L115](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L101-L115) 中把：

```python
'corsheaders.middleware.CorsMiddleware',
```

放在 `MIDDLEWARE` 第一位。

Django 中间件按声明顺序处理请求，按反向顺序处理响应。`CorsMiddleware` 需要：

- 拦截并响应预检 `OPTIONS` 请求。
- 给正常响应和错误响应添加 CORS 响应头。

因此它应尽可能靠前，至少位于 `CommonMiddleware`、WhiteNoise 或其他可能提前返回响应的中间件之前。否则某些 301、404 或异常响应可能缺少 CORS 头，浏览器只显示模糊的 CORS 错误。

**4. 开发环境配置**

开发配置见 [dev.py#L510-L519](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L510-L519)：

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

CORS_ALLOW_ALL_ORIGINS = True
```

当 `CORS_ALLOW_ALL_ORIGINS = True` 时，所有来源都会被允许，`CORS_ALLOWED_ORIGINS` 不再起限制作用。开发环境这样配置便于联调，但不适合生产环境。

前端 Axios 使用相对路径，Vite 又把 `/api` 代理到 Django，见 [request.js#L41-L50](file:///e:/BH/PyStudy/ICube/cube_front/src/http/request.js#L41-L50) 和 [vite.config.js#L31-L56](file:///e:/BH/PyStudy/ICube/cube_front/vite.config.js#L31-L56)。浏览器实际请求的是 Vite 自己的地址，因此正常开发链路通常表现为同源；CORS 主要用于前端直接访问后端端口或其他独立客户端场景。

**5. 生产环境配置**

生产配置从 `dev.py` 全量继承，再根据环境变量生成允许来源：

```python
_allowed_origin = os.getenv('ALLOWED_ORIGIN', '')
CORS_ALLOWED_ORIGINS = [
    f"{scheme}://{_allowed_origin}"
    for scheme in ['http', 'https']
    if _allowed_origin
]
CORS_ALLOW_CREDENTIALS = True
```

对应位置：[prod.py#L38-L52](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/prod.py#L38-L52)。

这里的 `ALLOWED_ORIGIN` 预期是纯主机名，例如：

```env
ALLOWED_ORIGIN=icube.example.com
```

如果传入 `https://icube.example.com`，代码会拼出无效的 `https://https://icube.example.com`。环境变量格式必须与配置代码的约定一致。

**6. 当前生产配置存在继承漏洞**

`prod.py` 使用：

```python
from .dev import *
```

这会把开发环境的：

```python
CORS_ALLOW_ALL_ORIGINS = True
```

一起继承到生产环境。`prod.py` 虽然设置了 `CORS_ALLOWED_ORIGINS`，却没有把全开放开关改回 `False`，因此生产白名单实际上不会形成限制。

生产环境必须显式覆盖：

```python
CORS_ALLOW_ALL_ORIGINS = False
```

当 `CORS_ALLOW_CREDENTIALS = True` 时，这个问题更需要重视，因为服务器会允许跨源请求携带凭证。不能依赖浏览器默认行为代替明确的来源白名单。

**7. CORS、ALLOWED_HOSTS 与 CSRF 的区别**

| 配置 | 防护对象 | 判断依据 |
|------|----------|----------|
| `ALLOWED_HOSTS` | 非法 Host 头、DNS Rebinding | 请求的 `Host` |
| CORS | 浏览器跨源读取响应 | 请求的 `Origin` |
| CSRF | 冒用 Cookie 身份提交状态修改请求 | CSRF Token、Origin、Referer |

三者不能互相替代：

- `ALLOWED_HOSTS` 放行某个域名，不等于允许该来源跨域。
- CORS 允许某个来源，不等于关闭 CSRF 防护。
- CORS 不是认证和权限控制，后端仍需校验 JWT、用户身份和对象权限。

如果跨源请求使用 Session Cookie，除 CORS 外还要正确配置 `CSRF_TRUSTED_ORIGINS`、Cookie 的 `SameSite` 与 `Secure` 属性。使用 `Authorization` 请求头时，仍需要允许该请求头通过预检。

**8. 为什么生产环境通常不触发 CORS**

当前 Nginx 同时提供前端页面和 `/api/`：

```text
https://icube.example.com/      → Vue
https://icube.example.com/api/  → Django
```

浏览器看到的协议、主机和端口完全一致，所以属于同源请求。此时 CORS 配置主要作为以下场景的兼容能力：

- 独立部署到其他域名的前端。
- 第三方浏览器应用调用 API。
- 本地前端直接访问生产或测试 API。

如果系统明确只允许同域前端访问，可以进一步缩小 CORS 范围，而不是默认开放所有来源。

**9. 面试回答**

> CORS 是浏览器对同源策略的受控放宽，判断来源时协议、主机和端口必须全部一致。项目使用 `django-cors-headers`，把 `CorsMiddleware` 放在中间件最前面，使预检请求、正常响应和错误响应都能带上 CORS 头。开发环境允许所有来源方便联调，生产环境应使用精确白名单。当前 `prod.py` 继承了开发环境的 `CORS_ALLOW_ALL_ORIGINS = True`，但没有显式关闭，导致生产白名单失效，应覆盖为 `False`。同时要区分 CORS、`ALLOWED_HOSTS` 和 CSRF：它们分别处理跨源读取、Host 头校验和 Cookie 身份冒用，不能互相替代。

---

## 已优化项

以下问题已在近期迭代中修复，展示项目持续改进能力：

1. **生产配置硬编码IP** → 已改为环境变量读取 (`ALLOWED_HOSTS`, `ALLOWED_ORIGIN`, `SERVER_HOST`)
2. **prod.py不规范LOGGING配置** → 已删除 Django 原生 LOGGING dict，统一使用 Loguru
3. **支付宝回调地址硬编码** → 已改为 `os.getenv('SERVER_HOST')` 动态配置
4. **Nginx server_name硬编码** → 已改为通配符 `_`，支持任意域名访问
5. **图片URL存储完整地址** → 已改为存储相对路径，通过 `build_image_url()` 函数统一生成，默认返回相对路径避免CORS问题
6. **CORS/PNA问题** → 通过修改图片URL生成函数返回相对路径，并配置Vite代理，解决了从公网IP访问时的跨域问题
7. **Vite预览模式不支持proxy** → 已配置 `preview.proxy`，确保构建后预览时媒体文件能正确访问
8. **公式浏览量排序错误** → 前端排序字段从 `-views` 修正为 `-view_count`，匹配后端字段名
9. **公式详情浏览量不更新** → 后端 `retrieve` 方法使用 `F('view_count') + 1` 实现原子更新
10. **首页精选公式点击无跳转** → 实现公式跳转联动，通过路由 query 参数传递公式ID，目标页面自动打开详情弹窗
11. **无用魔方阶数导航卡片** → 已移除首页中的2x2/3x3/4x4/5x5导航卡片
12. **图片压缩裁剪缺失** → 实现图片处理流水线：Pillow压缩、1:1裁剪、WebP转换、自动缩略图生成
13. **公式上传图片预览错误** → 后端新增thumbnail_file/thumbnail_path双字段，分别处理上传文件和路径引用
14. **公式分类未绑定目标状态** → 创建/编辑时根据category_id自动绑定target_state_id
15. **3D演示重置视角未复原** → 添加相机位置和目标点Tween动画，重置时平滑恢复
16. **帖子图片预览问题** → 实现图片全量同步，帖子列表支持1:1比例图片预览
17. **公式筛选维度不足** → 新增作者筛选，支持分类/难度/作者三维联合筛选
18. **图片裁剪组件问题** → 重写ImageCropper组件，支持Canvas裁剪、滚轮缩放、防抖拖拽
19. **公式卡片样式优化** → 优化卡片布局：头部显示公式名+难度标签，底部显示"分类名  by 用户名"，统一字体样式
20. **自定义公式分类** → 支持用户创建、管理个人公式分类，权限控制分类访问范围
21. **公式编辑逆公式不同步** → 编辑公式时检测notation变化，自动重新生成逆公式
22. **自定义公式无删除功能** → 前端添加删除按钮，支持用户删除自己创建的自定义公式
23. **前端缺少路由守卫** → 已添加全局 router.beforeEach 守卫，根据 requiresAuth 和 Token 状态拦截未登录访问并跳转登录页。
24. **公式库匿名访问触发收藏接口 401** → 已增加登录态判断，未登录可正常浏览公式，仅点击收藏时提示“请先登录”。
25. **页面路由切换缺少加载反馈** → 已新增全局路由加载动画与错误兜底，加载时显示进度条和遮罩，失败时显示错误卡片并支持重新加载，避免等待生硬或页面白屏。

---

## 项目不足与改进建议

### 严重问题（面试必问）

1. **前端缺少错误边界**
   - 组件异常未处理，可能导致白屏
   - **改进方案**: 使用 Vue 3 的 `errorCaptured` 生命周期或 `onErrorCaptured` 组合式 API

### 性能优化问题

3. **HotPostService 缺少预加载 + 无缓存**
   
   - **位置**: [forum/services.py#L363-L389](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\forum\services.py#L363-L389)
   - **问题**: 无 `select_related('author')` / `prefetch_related('tags', 'images')`，序列化时 N+1 查询；`order_by('-hot_score')` 走 filesort（计算字段无法建索引），7 天数据量大时性能下降
   - **改进方案**: Redis 缓存 TOP 20 ID 列表（5 分钟 TTL）+ 补全预加载
   
   ```python
   @staticmethod
   def get_hot_posts(days=7, limit=20):
       cache_key = f"hot_posts:{days}:{limit}"
       con = get_redis_connection("default")
   
       # 1. 先查缓存
       cached = con.lrange(cache_key, 0, -1)
       if cached:
           post_ids = [int(id) for id in cached]
           return Post.objects.filter(id__in=post_ids).select_related('author').prefetch_related('tags', 'images')
   
       # 2. 缓存未命中：查 DB + 回写 Redis
       since = timezone.now() - timedelta(days=days)
       posts = list(Post.objects.filter(
           status='published',
           created_at__gte=since
       ).select_related('author').prefetch_related('tags', 'images').annotate(
           hot_score=F('like_count') * 3 + F('comment_count') * 2 + F('view_count')
       ).order_by('-hot_score')[:limit])
   
       # 3. 写入缓存
       if posts:
           pipe = con.pipeline()
           pipe.delete(cache_key)
           pipe.rpush(cache_key, *[p.id for p in posts])
           pipe.expire(cache_key, 300)  # 5 分钟 TTL
           pipe.execute()
   
       return posts
   ```
   
4. **PostViewSet.list 跨表聚合性能差**
   - **位置**: [forum/views.py#L99-L109](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\forum\views.py#L99-L109)
   - **问题**: 3 个 `Count` 触发 3 次 LEFT JOIN + GROUP BY，产生笛卡尔积，必须用 `COUNT(DISTINCT)`；分页时每页都要全量聚合计算，无法利用冗余字段
   - **改进方案**: 改用 `F()` 走 Post 表已有冗余字段（`like_count`/`comment_count`/`collect_count`）

   ```python
   if hot:
       queryset = queryset.annotate(
           hot_score=F('like_count') * 3 + F('comment_count') * 2 + F('collect_count')
       ).order_by('-hot_score')
   ```

   | 维度 | 现状（Count 跨表聚合） | 优化后（F 单表计算） |
   | ---- | ----------------------------------- | ------------------ |
   | SQL 复杂度 | 3 表 LEFT JOIN + GROUP BY + DISTINCT | 单表 + 计算列 |
   | 性能 | 慢（笛卡尔积 + 临时表） | 快（无 JOIN） |
   | 数据一致性 | 实时准确 | 依赖冗余字段同步（可接受短暂不一致） |

5. **sync_all_views 使用阻塞 KEYS 命令**
   - **位置**: [forum/services.py#L147](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\forum\services.py#L147)
   - **问题**: `sync_all_views` 定时同步浏览量时使用 `con.keys("*forum:post:*:view")` 遍历所有缓存键。`KEYS` 命令是阻塞操作，会扫描 Redis 所有键，数据量大时可能阻塞 Redis 主线程，影响其他请求响应
   - **改进方案**: 改用 `SCAN` 游标命令，分批遍历，每次只返回少量键，不阻塞 Redis

   | 维度 | KEYS | SCAN |
   |------|------|------|
   | 阻塞性 | 阻塞 Redis 主线程 | 非阻塞，分批遍历 |
   | 内存占用 | 一次性返回所有键 | 每次只返回少量键 |
   | 适用数据量 | 少量键（<1万） | 任意数量 |
   | 复杂度 | O(N) 一次 | O(N) 分多次 |

### 中等问题

6. **测试覆盖不完整**
   - forum 模块有较完整测试（models/serializers/services/views/api）
   - accounts、formula、shop、timer 模块测试较少或缺失
   - **改进方案**: 为关键业务流程（登录、下单、支付回调、计时）补充单元测试和集成测试

7. **图片压缩已实现，但头像裁剪组件待完善**
   - 已实现公式图片的压缩裁剪功能
   - 头像上传裁剪功能需进一步优化交互体验
   - **改进方案**: 统一头像和公式图片的裁剪组件，提升用户体验

8. **缺少接口文档访问**
   - drf-spectacular 已配置，但缺少访问入口说明
   - **改进方案**: 在首页添加 API 文档链接（默认访问 `/api/schema/swagger-ui/`）

9. **缺少HTTPS配置**
   - Nginx 配置了 443 端口但无 SSL 证书配置
   - **改进方案**: 使用 Let's Encrypt 配置免费 SSL 证书

10. **缺少性能监控**
    - 无 APM、无日志轮转、无慢查询监控
    - **改进方案**: 集成 Prometheus + Grafana，配置日志轮转

11. **缺少密码强度提示**
    - 注册时无密码强度校验
    - **改进方案**: 添加密码复杂度校验（长度、大小写、数字、特殊字符）

### 代码质量问题

12. **validate_title 边界条件缺失**
    - **位置**: [forum/serializers.py#L286-L303](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\forum\serializers.py#L286-L303)
    - **问题**: 最大长度检查与返回值不一致（最小长度用 `len(value.strip())`，最大长度用 `len(value)`，但返回 `value.strip()`）；未处理 `None` 值；未过滤不可见控制字符；未处理全角空格
    - **改进方案**: 统一 strip + 控制字符过滤 + None 防御

    | 边界条件 | 现状处理 | 风险 | 修复后处理 |
    |---------|---------|------|-----------|
    | `None` 值 | 抛 `AttributeError` | 500 错误 | 转为空字符串 |
    | 前后空格 | 最小检查 strip，最大检查不 strip | 逻辑矛盾 | 统一用 strip 后长度 |
    | 控制字符 | 未过滤 | 注入风险 | 正则移除 |
    | 全角空格 | 未处理 | 用户体验差 | 额外 strip |
    | 纯空白字符串 | 被拒 | 无 | 不变 |

13. **信号未在 AppConfig.ready() 中显式注册**
    - **位置**: [forum/apps.py](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\forum\apps.py)
    - **问题**: `ForumConfig` 缺少 `ready()` 方法，信号注册依赖 Django 自动发现机制。跨版本不可靠，测试环境可能失效，排查困难
    - **改进方案**: 在 `apps.py` 添加 `ready()` 方法显式导入信号

    | 场景 | 现状 | 修复后 |
    |------|------|--------|
    | 生产环境 | 可能正常（Django 自动加载） | 一定正常（显式导入） |
    | 测试环境 | 信号可能未注册，计数不更新 | 显式注册，测试可靠 |
    | Django 版本升级 | 行为可能变化 | 不依赖自动发现，稳定 |

### 轻微问题

14. **容器健康检查不完整**
    - 当前只有 MySQL 配置 Compose healthcheck，Redis、API、front 尚未配置
    - **改进方案**: 增加 Redis PING、API 健康接口和前端 HTTP healthcheck

15. **前端缺少TypeScript**
    - 纯 JavaScript 项目，类型安全不足

16. **缺少404页面**
    - 路由未匹配时无友好提示

### 优化优先级总览

| 优先级 | 分类 | 位置 | 问题 | 方案 | 是否优化 |
| ---- | -- | ---------------- | -------------------- | ----------------------------- | ---- |
| 严重 | 前端 | 路由守卫 | 未实现全局路由守卫 | 添加 `router.beforeEach` | 是 |
| 严重 | 前端 | 错误边界 | 组件异常白屏 | 使用 `onErrorCaptured` |  |
| 高 | 性能 | HotPostService | 缺少预加载 + filesort 无缓存 | Redis 缓存 + 补全 select\_related |  |
| 高 | 性能 | PostViewSet.list | Count 跨表聚合笛卡尔积 | 改用 F() 走冗余字段 |  |
| 高 | 性能 | sync_all_views | KEYS 阻塞 Redis 主线程 | 改用 SCAN 游标分批遍历 |  |
| 中 | 测试 | 全项目 | 测试覆盖不完整 | 补充关键业务流程测试 |  |
| 中 | 安全 | HTTPS | 无 SSL 证书 | Let's Encrypt |  |
| 中 | 安全 | 密码强度 | 无密码强度校验 | 添加复杂度校验 |  |
| 中 | 代码质量 | validate\_title | 边界条件缺失 | 统一 strip + 控制字符过滤 + None 防御 |  |

---

## 面试回答技巧

### 被问到"项目不足"时的回答模板

> "项目整体架构清晰，但在安全和健壮性方面有改进空间。比如前端缺少路由守卫，虽然路由配置了 requiresAuth 元信息，但没有实现全局守卫来拦截未登录请求；测试覆盖也需要加强，目前主要集中在论坛模块。不过近期已经做了一些优化，比如生产环境配置从硬编码 IP 改为环境变量读取，图片URL从完整地址改为相对路径解决CORS问题，公式跳转联动也已实现，这些都是持续改进的方向。"

### 项目亮点总结

> "这个项目最让我满意的是**自定义JWT认证**、**图片处理流水线**和**公式库系统**。认证方面实现了 Redis 缓存用户实例和 JWT 黑名单机制；图片处理方面使用 Pillow 实现了压缩、1:1裁剪、WebP格式转换、自动缩略图生成的完整流水线，前端配合Canvas裁剪组件提供良好的交互体验；公式库系统支持用户自定义上传公式、按作者筛选、多重筛选（分类/难度/作者）、自定义公式分类创建与管理，并能自动根据分类绑定目标状态，编辑时逆公式同步更新。此外，浏览量统计使用 F 表达式实现原子更新，公式跳转联动通过路由参数实现无缝衔接，3D演示重置时通过Tween动画平滑恢复视角，公式卡片经过样式优化后展示更加统一美观。"

### 被问到"技术难点"时的回答模板

> "最大的挑战是**并发库存扣减**、**图片处理流水线**和**3D魔方旋转算法**。库存扣减方面，使用了 Django 的 `F()` 表达式保证原子性，避免了并发下单时的超卖问题；图片处理方面，需要实现完整的流水线——大图预压缩、1:1裁剪、WebP格式转换、自动缩略图生成，还要区分用户上传和公式库选择两种图片来源，通过双字段设计解决了这个问题；魔方旋转方面，需要解析标准魔方记号（如 R/U/F/B 等），计算旋转轴和参与旋转的方块，使用 Tween.js 实现平滑动画。此外，还需要解决从公网IP访问时的CORS和PNA问题，通过修改URL生成函数返回相对路径解决。"

### 被问到"生产环境部署"时的回答模板

> "使用 Docker Compose 编排了 5 个服务：MySQL、Redis、Django API、Vue 前端、Nginx。Nginx 作为反向代理，处理 API 请求转发、静态文件服务和 SPA 路由回退。生产环境通过 `.env` 文件配置服务器 IP、域名等信息，MySQL 配置了健康检查确保启动顺序正确。媒体文件通过 Nginx 的 alias 配置直接访问。部署时只需在服务器上创建 `.env` 文件，执行 `docker compose up -d --build` 即可完成。"

---

## 面试常见问题预测

### 一、后端基础问题

#### Q1: django-unfold是什么？和原生Django Admin有什么区别？

**回答要点**:
- **django-unfold**: 基于 Tailwind CSS 的现代化后台管理框架，替代原生 Django Admin
- **核心区别**:
  - 原生 Admin: Bootstrap 风格，功能有限
  - Unfold: Tailwind CSS 风格，提供更丰富的组件和自定义能力
- **主要特性**:
  - `@display` 装饰器: 自定义列表页列，支持 Badge、图片预览
  - `@action` 装饰器: 定义批量操作
  - Fieldsets: 编辑页字段分组，支持 Tab 布局
  - 侧边栏自定义: 支持中文标题、可折叠分组、自定义排序
- **继承方式**: 所有 Admin 类继承 `unfold.admin.ModelAdmin` 而非 `admin.ModelAdmin`

#### Q2: @display 和 @action 装饰器有什么作用？

**回答要点**:
- **@display**: 将方法注册为列表页展示列，替代原生 `admin.display`
  - 支持 `description` 参数设置列标题
  - 支持 `ordering` 参数设置排序字段
  - 支持 `boolean` 参数渲染为图标或自定义 HTML
- **@action**: 将方法注册为批量操作，替代原生 `admin.action`
  - 支持 `description` 参数设置操作名称
  - 接收 `request` 和 `queryset` 参数
  - 使用 `self.message_user()` 向管理员反馈操作结果
- **示例**: 状态 Badge、头像预览、批量禁用用户

#### Q3: 后台侧边栏如何自定义？

**回答要点**:
- **配置位置**: 在 `UNFOLD` 字典的 `SIDEBAR.navigation` 中配置
- **配置项**:
  - `title`: 分组标题（中文）
  - `icon`: Material Icons 图标名称
  - `collapsible`: 是否可折叠（`True`）
  - `items`: 子菜单项列表（`title` + `link`）
- **自定义排序**: 按需求顺序排列分组
- **模板覆盖**: 通过项目 `templates/unfold/helpers/app_list.html` 覆盖模板，修改样式

#### Q3a: 轮播图系统如何设计？

**回答要点**:
- **后端模型**: `Banner` 模型包含 title(标题)、description(描述)、image(图片)、link(跳转链接)、sort_order(排序)、is_active(状态)、created_at(创建时间)
- **API设计**: GET `/api/home/banners/` 返回启用状态的轮播图，按 sort_order 排序
- **后台管理**: `BannerAdmin` 支持图片预览、状态Badge、列表页可编辑排序和状态、批量启用/禁用
- **前端组件**: 支持渐变遮罩层显示标题和描述、悬停暂停、图片加载占位符、点击跳转（支持内部路由和外部链接）、指示器美化

**关键代码**:
```python
# 模型定义
class Banner(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='banners/')
    link = models.URLField(max_length=500, blank=True)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
```

#### Q3b: 教程系统有哪些优化？

**回答要点**:
- **教程列表页优化**: 添加学习路径流程图、热门教程卡片、CFOP进阶课程分类
- **导航链路**: 各教程页面之间互相导航，形成完整的学习链路
- **返回导航**: 教程页面底部返回按钮指向教程列表页（`/tutorials`）而非首页
- **学习路径**: 初学者路径（两步OLL 10个算法 + 两步PLL 6个算法，共16个算法）和进阶路径（完整OLL 57个算法 + 完整PLL 21个算法，共78个算法）

**教程导航页面结构**:
- 学习路径流程图：层先法入门 → CFOP速拧 → 两步OLL/PLL → 完整OLL/PLL
- 热门教程卡片：三阶魔方入门、CFOP速拧高级法、两步OLL基础
- 常规正阶魔方：2x2、3x3、4x4、5x5（部分开发中）
- 三阶魔方专项进阶：层先法、CFOP、桥式解法
- CFOP进阶课程：两步OLL、两步PLL、完整OLL、完整PLL

#### Q4: JWT如何实现注销？
**回答要点**:
- 标准JWT是无状态的，无法直接注销
- 本项目实现了**Redis黑名单机制**:
  - 注销时将JWT的`jti`(JWT ID)存入Redis，设置过期时间等于token剩余有效期
  - 认证时检查`JWTCacheService.is_blacklisted(jti)`
  - 防止token被复用
- 同时配合**用户缓存策略**: 用户缓存Key为`user_instance_cache_{user_id}`，TTL为1小时，注销时清除用户缓存

#### Q5: 如何防止并发超卖？
**回答要点**:
- 使用**Django F()表达式**实现原子更新，避免竞态条件
- 结合**@transaction.atomic**装饰器保证事务一致性
- **关键代码**:
  ```python
  cart.product.stock = F('stock') - cart.quantity
  cart.product.sales_count = F('sales_count') + cart.quantity
  cart.product.save()
  cart.product.refresh_from_db()  # 刷新数据
  ```
- F表达式直接在数据库层面执行计算，避免先查后改的竞争窗口

#### Q6: Redis缓存策略是什么？
**回答要点**:
- **用户实例缓存**: Key为`user_instance_cache_{user_id}`，TTL为1小时
- **JWT黑名单**: Key为`jwt_blacklist_{jti}`，TTL等于token剩余有效期
- **登录限流**: Key为`throttle_login_scope_{IP}_{email}`，TTL为1分钟
- **缓存内容**: 用户缓存仅存储用户ID，避免序列化开销，查询时根据ID获取完整对象

#### Q7: 为什么用Loguru而不是Django原生logging？
**回答要点**:
- **API更简洁**: 无需复杂配置，一行代码即可完成日志记录
- **自动格式化**: 时间戳、日志级别、文件名、行号等自动添加
- **分级漏斗记录**: 不同级别日志写入不同文件（debug/info/warning/error/critical）
- **更好的性能**: 异步写入，支持多进程安全
- **拦截第三方库日志**: 通过`InterceptHandler`统一接管Django、Gunicorn等库的日志

#### Q8: 自定义权限类有哪些？如何实现？
**回答要点**:
- **IsOwnerOrReadOnly**: 适配多种模型（author/user/owner字段），只读请求放行，写请求验证所有者
- **IsSelfOrReadOnly**: 用户只能操作自己的资料
- **IsAdminOrReadOnly**: 管理员可写，其他只读
- **IsFollowingOrReadOnly**: 关注者可见
- **IsAdminOrCustomCreator**: 管理员或自定义创建者可写
- **实现方式**: 继承`BasePermission`，重写`has_object_permission`方法

#### Q8a: 管理器（Manager）是什么？Django 独有的吗？

**回答要点**:
- **管理器是 Django ORM 的核心机制**，它是模型与数据库交互的入口。每个 Django 模型默认都有一个 `objects` 管理器（类型为 `models.Manager`），通过它才能调用 `.filter()`、`.get()`、`.create()` 等方法
- **不是 Django 独有的**，但 Django 的管理器模式非常系统化：
  - SQLAlchemy 有类似的 `session.query()` 机制
  - ORM 框架普遍存在"数据访问层"概念，但 Django 把它直接绑定到模型类上
- **本项目示例**: [accounts/models.py#L24-L95](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\accounts\models.py#L24-L95) 定义了 `UserManager`，继承 `BaseUserManager`，重写了 `create_user` 和 `create_superuser`。`objects = UserManager()` 用自定义管理器替换默认的

#### Q8b: 方法参数后面的 `-> User` 是什么意思？

**回答要点**:
- 这是 **Python 类型注解（Type Hints）**，表示该函数的**返回值类型**
- `email: str` → 参数 `email` 是字符串
- `password: str | None = None` → 参数 `password` 可以是字符串或 `None`，默认值 `None`
- `-> User` → 函数返回一个 `User` 实例
- **作用**: 给 IDE 提供类型推断（自动补全、类型检查），给阅读代码的人明确返回值类型。**运行时不影响任何行为**，Python 不会强制检查

#### Q8c: `class Meta` 是什么？每个类都有吗？

**回答要点**:
- **`class Meta`** 是 Django 模型的"内部配置类"，用于定义模型的元数据（数据库表名、排序、索引、权限等）。它不是 Python 语法要求，是 Django ORM 的约定
- **每个 Django Model 都可以有（也可以没有）**，没有时 Django 用默认值
- 常见配置项:

| 配置项 | 作用 | 本项目示例 |
| ----------------- | ------ | ------------------------------------------------ |
| `db_table` | 数据库表名 | `db_table = 'forum_post'` |
| `ordering` | 默认排序 | `ordering = ['-is_pinned', '-created_at']` |
| `indexes` | 复合索引优化 | `models.Index(fields=['author', '-created_at'])` |
| `unique_together` | 联合唯一约束 | `unique_together = ['post', 'tag']` |

- 本项目示例：[forum/models.py#L148-L162](file:///e:\BH\PyStudy\ICube\cube_api\cube_api\apps\forum\models.py#L148-L162)

### 二、数据库相关问题

#### Q9: 软删除如何实现？有什么注意事项？
**回答要点**:
- **实现方式**: 添加`is_deleted`布尔字段，删除操作实际是更新`is_deleted=True`
- **配合status字段**: 'published'/'deleted'/'draft'多状态管理
- **注意事项**:
  - 查询时需过滤`is_deleted=False`的记录
  - 信号监听需处理更新操作（非仅创建）
  - 后台管理界面需重写`get_queryset`排除已删除记录

#### Q10: 索引如何优化？
**回答要点**:
- **单字段索引**: `db_index=True`用于高频查询字段（title, created_at, author）
- **复合索引**: `indexes = [models.Index(fields=['author', '-created_at'])]`
- **唯一约束**: `unique_together = ['post', 'user']`防止重复点赞/收藏
- **索引使用原则**:
  - 外键字段自动创建索引
  - 避免过多索引影响写入性能
  - 常用查询条件应创建索引

#### Q11: 如何处理N+1查询问题？
**回答要点**:
- **select_related**: 一次性加载一对一/多对一关联对象
- **prefetch_related**: 批量预加载一对多/多对多关联对象
- **评论扁平化优化**: 一次性查询所有评论，在内存中组装树状结构
- **示例**:
  ```python
  # 优化前：N+1查询
  posts = Post.objects.all()
  for post in posts:
      author = post.author  # 每次循环都触发查询
  
  # 优化后：1次查询
  posts = Post.objects.select_related('author').prefetch_related('tags').all()
  ```

#### Q12: 事务如何使用？有什么注意事项？
**回答要点**:
- **装饰器方式**: `@transaction.atomic`
- **上下文管理器方式**: `with transaction.atomic():`
- **商城订单创建流程**:
  1. 验证购物车商品
  2. F表达式扣减库存和增加销量
  3. 删除购物车
  4. 创建订单和订单项
- **注意事项**:
  - 任一操作失败自动回滚
  - 避免在事务中执行耗时操作
  - 使用F表达式保证并发安全

### 三、前端相关问题

#### Q13: Three.js如何管理内存？
**回答要点**:
- **geometry.dispose()**: 释放几何体内存
- **material.dispose()**: 释放材质内存
- **renderer.dispose()**: 释放渲染器资源
- **取消动画**: `cancelAnimationFrame(animationId)`
- **清理定时器**: `clearInterval(autoPlayTimer)`
- **执行时机**: 在`onBeforeUnmount`钩子中执行所有清理操作

#### Q14: Pinia状态管理如何设计？
**回答要点**:
- **模块划分**:
  - `user.js`: 用户登录状态、token、个人信息
  - `menu.js`: 菜单导航状态
- **持久化**: token存储在`localStorage`，页面刷新后自动恢复
- **数据流向**: API响应 → Store → 组件
- **响应式**: 使用`defineStore`定义状态，组件通过`useStore()`访问

#### Q15: 请求拦截器如何设计？
**回答要点**:
- **请求拦截**:
  - 自动注入Token: `config.headers['Authorization'] = 'Token ' + token`
  - 统一超时设置: 5000ms
  - baseURL设置为`/`，配合Vite代理配置
- **响应拦截**:
  - 业务错误处理: `code !== 100`时显示错误消息并reject
  - HTTP错误处理: 401/404/500等状态码统一提示
- **Token前缀**: 使用`Token`而非标准`Bearer`

#### Q16: Vite代理配置有什么特点？
**回答要点**:
- **开发模式**: `server.proxy`配置`/api`和`/media`代理到`http://127.0.0.1:8000`
- **预览模式**: `preview.proxy`同样配置，确保构建后预览时媒体文件能正确访问
- **changeOrigin**: 设置为`true`，解决跨域问题
- **host**: 设置为`0.0.0.0`，允许外部访问

#### Q17: 公式跳转联动如何实现？
**回答要点**:
- **首页跳转**: 点击精选公式卡片，通过路由query参数传递公式ID
  ```javascript
  router.push({ path: '/formulas', query: { formula_id: id } })
  ```
- **目标页面接收**: 在`onMounted`中读取query参数并自动打开详情弹窗
  ```javascript
  const formulaId = route.query.formula_id;
  if (formulaId) {
      openFormulaById(formulaId);
  }
  ```
- **无缝衔接**: 用户体验如同点击列表项打开详情

### 四、部署与运维问题

#### Q18: Docker服务启动顺序如何保证？
**回答要点**:
- **depends_on**: 定义服务依赖关系
- **healthcheck**: MySQL配置健康检查，`start_period: 45s`确保初始化完成
- **服务依赖链**: api依赖db(healthy) + redis(started)
- **关键配置**:
  ```yaml
  icube_api:
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
  ```

#### Q19: Nginx如何处理SPA路由？
**回答要点**:
- **try_files指令**: `try_files $uri $uri/ /index.html`
- **原理**: 当请求路径在服务器上找不到对应文件时，回退到`index.html`
- **API代理**: `/api/*`通过`proxy_pass`转发到Django服务
- **静态文件**: `/media/*`和`/static/*`通过`alias`直接访问
- **代理头设置**: 传递真实IP和协议（X-Real-IP, X-Forwarded-For, X-Forwarded-Proto）

#### Q20: 支付宝回调如何验证？
**回答要点**:
- **签名验证**: 使用支付宝SDK的`verify`方法验证回调数据签名
- **签名算法**: RSA2 (SHA256)
- **验证流程**:
  1. 获取回调POST数据
  2. 调用`alipay.verify(data)`验证签名
  3. 验证通过后更新订单状态
- **回调地址**: 使用环境变量`SERVER_HOST`动态配置，避免硬编码

#### Q21: 生产环境配置如何管理？
**回答要点**:
- **环境变量**: 通过`.env`文件注入配置（ALLOWED_HOSTS, ALLOWED_ORIGIN, SERVER_HOST）
- **动态读取**: `os.getenv('ALLOWED_HOSTS')`
- **CORS配置**: 根据`ALLOWED_ORIGIN`自动生成http/https地址
- **SECRET_KEY**: 从环境变量读取，防止硬编码泄露
- **SITE_DOMAIN**: 用于生成完整图片URL

#### Q21a: sys.path 注入是什么？为什么要修改？

**回答要点**:
- `sys.path` 是 Python 模块搜索路径列表，`import` 语句会按顺序在这些路径中查找模块
- **为什么要修改**: 项目目录结构非标准，`apps/` 不在默认搜索路径下。Django 默认 `BASE_DIR` 是 `cube_api/`，但 `apps/` 在 `cube_api/cube_api/apps/` 下
- **三行注入**: 位置 [settings/dev.py#L40-L50](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L40-L50)
  - 注入配置目录（`cube_api/cube_api/`），使 `utils`、`settings` 等模块可直接导入
  - 注入 apps 目录（`cube_api/cube_api/apps/`），使 `apps.accounts`、`apps.forum` 等应用可直接导入
  - 注入项目根目录（`cube_api/`），方便导入项目级别的包和模块
- **为什么用 `insert(0, ...)` 而非 `append()`**: `insert(0, ...)` 插到列表头部优先搜索，避免被同名的第三方包覆盖
- **`prod.py` 需要重复注入吗**: 不需要，`from .dev import *` 时已执行
- **风险**: 模块名冲突、IDE 无法识别、不可移植

#### Q21b: 测试模式自动切换是如何实现的？

**回答要点**:
- **核心问题**: 测试时依赖 MySQL + Redis 会拖慢速度，且存在数据污染风险
- **检测机制**: `if 'test' in sys.argv` 检测命令行参数，或 `'pytest' in sys.modules` 检测 pytest 导入
- **自动切换内容**:
  - **SQLite 内存库**: `:memory:` 无需建表，内存中创建，进程结束自动销毁
  - **Mock Redis**: 用 Django cache 替代真实 Redis，避免状态残留
  - **MD5 哈希**: 比 PBKDF2 快 100 倍，加速测试用户创建
  - **禁用限流**: 测试不受 429 限制干扰
- **注意**: SQLite 与 MySQL 有 SQL 方言差异（如不支持 `SELECT FOR UPDATE` 行锁），测试通过不代表生产一定没问题

### 五、安全相关问题

#### Q22: 如何防止暴力破解攻击？
**回答要点**:
- **自定义限流**: `LoginRateThrottle`针对登录接口限流
- **限流策略**: 结合IP和尝试登录的Email，Key为`throttle_login_scope_{IP}_{email}`
- **限流频率**: 3次/分钟
- **原理**: 防止攻击者通过大量请求猜测密码

#### Q23: CORS/PNA问题如何解决？
**回答要点**:
- **图片URL处理**: 修改`build_image_url()`函数默认返回相对路径
- **Vite代理**: 配置`/media`代理到后端
- **Nginx配置**: 生产环境通过Nginx的`alias`配置直接访问媒体文件
- **PNA问题**: 避免返回完整`http://localhost:8000/...`URL，从公网IP访问时被浏览器PNA策略阻止

#### Q24: 为什么不用Bearer前缀？
**回答要点**:
- **项目约定**: 使用`Token`前缀而非标准`Bearer`
- **历史原因**: 早期版本使用Token认证方式
- **兼容性**: 前端和后端保持一致即可
- **自定义认证**: `CachedJWTAuthentication`中提取Token时使用`Token `前缀

#### Q24a: 什么是CORS预检请求？

**回答要点**:
- 满足特定方法、请求头和 Content-Type 条件的请求属于**简单请求**，浏览器直接发送
- 携带 `Authorization`、使用 `application/json` 或非简单方法时，浏览器先发送**预检请求**（OPTIONS）:

```http
OPTIONS /api/forum/posts/
Origin: http://localhost:5173
Access-Control-Request-Method: POST
Access-Control-Request-Headers: authorization, content-type
```

- 服务器允许后返回:

```http
Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Methods: POST, OPTIONS
Access-Control-Allow-Headers: authorization, content-type
```

- 预检通过后，浏览器才发送真正的业务请求
- **CorsMiddleware 要靠前**: 放在 `MIDDLEWARE` 第一位，确保预检请求、正常响应和错误响应都能带上 CORS 头

### 六、性能优化问题

#### Q25: 公式浏览量如何统计？
**回答要点**:
- **F表达式原子更新**: `F('view_count') + 1`
- **实现位置**: 在`retrieve`方法中执行
- **排序逻辑**: 首页精选公式按`view_count`降序排列
- **关键代码**:
  ```python
  instance.view_count = F('view_count') + 1
  instance.save()
  instance.refresh_from_db()  # 刷新数据
  ```

#### Q26: 图片URL为什么返回相对路径？
**回答要点**:
- **避免CORS问题**: 完整URL可能触发跨域限制
- **避免PNA问题**: 从公网IP访问时，`http://localhost:8000/...`被浏览器PNA策略阻止
- **前端代理**: 通过Vite代理或Nginx配置转发媒体请求
- **统一管理**: `build_image_url()`函数统一处理，支持`absolute=True`参数用于邮件场景

#### Q26a: 游标分页和传统分页有什么区别？

**回答要点**:
- DRF 提供三种分页器:

| 分页器 | 原理 | URL 参数 | 适用场景 |
|--------|------|----------|----------|
| `PageNumberPagination` | 页码分页 | `?page=2&page_size=20` | 通用列表 |
| `LimitOffsetPagination` | 偏移量分页 | `?limit=20&offset=40` | 无限滚动 |
| `CursorPagination` | 游标分页 | `?cursor=abc123` | 大数据集、实时流 |

- **深分页性能对比**:

```python
# 传统分页（深分页慢）
GET /api/posts/?page=10000
→ SELECT * FROM forum_post LIMIT 20 OFFSET 199980  # 扫描 20 万行

# 游标分页（深分页快）
GET /api/posts/?cursor=eyJpZCI6IDEyMzQ1fQ==
→ SELECT * FROM forum_post WHERE id > 12345 ORDER BY id LIMIT 20  # 索引扫描
```

- **本项目选择 `PageNumberPagination`**: 前端友好（page 参数直观）、SEO 友好、兼容 admin
- **深分页优化**: 游标分页或 `WHERE id > last_id` 替代 `OFFSET`

### 七、架构设计问题

#### Q27: 项目模块划分原则是什么？
**回答要点**:
- **按功能模块划分**: accounts(认证)、forum(论坛)、formula(公式库)、shop(商城)、home(首页)、timer(计时器)
- **模块化设计**: 每个模块独立，通过API交互
- **共享组件**: utils(工具函数)、libs(第三方库扩展)、settings(配置文件)
- **MVS架构**: Django的Model-View-Serializer架构

#### Q28: 教程系统有哪些学习路径？
**回答要点**:
- **初学者路径**: 两步OLL（10个算法）+ 两步PLL（6个算法），共16个算法，1-2周学会
- **进阶路径**: 完整OLL（57个算法）+ 完整PLL（21个算法），共78个算法，达到sub-20秒
- **6个教程页面**: BeginnerTutorial、CFOPTutorial、OLLEssentials、PLLEssentials、CompleteOLL、CompletePLL

### 八、项目亮点与不足

#### Q29: 项目最大的技术亮点是什么？
**回答要点**:
- **自定义JWT认证**: Redis缓存用户实例 + JWT黑名单机制
- **图片URL统一管理**: `build_image_url()`函数解决CORS和PNA问题
- **教程系统**: 完整学习路径，6个教程页面
- **并发安全**: F表达式原子更新库存
- **3D魔方可视化**: Three.js实现公式状态可视化

#### Q30: 项目有哪些不足？如何改进？
**回答要点**:
- **前端缺少路由守卫**: 实现`router.beforeEach`钩子检查token
- **前端缺少错误边界**: 使用`onErrorCaptured`组合式API
- **测试覆盖不完整**: 为关键业务流程补充单元测试和集成测试
- **头像裁剪待完善**: 统一头像和公式图片的裁剪组件，优化交互体验
- **缺少HTTPS配置**: 使用Let's Encrypt配置免费SSL证书

#### Q31: 近期做了哪些优化？
**回答要点**:
1. 生产配置硬编码IP → 改为环境变量读取
2. 图片URL存储完整地址 → 改为存储相对路径
3. CORS/PNA问题 → 通过相对路径和代理配置解决
4. Vite预览模式不支持proxy → 添加preview.proxy配置
5. 公式浏览量排序错误 → 修正排序字段名
6. 公式详情浏览量不更新 → 使用F表达式原子更新
7. 首页精选公式点击无跳转 → 实现公式跳转联动
8. **图片处理流水线** → 实现压缩、裁剪、WebP转换、自动缩略图
9. **公式图片双字段** → 区分用户上传和公式库选择两种来源
10. **目标状态自动绑定** → 根据分类自动绑定目标状态
11. **3D演示视角重置** → 添加Tween动画平滑恢复
12. **公式多重筛选** → 新增作者筛选，支持三维联合筛选

### 九、开放性问题

#### Q32: 如果要支持百万级用户，你会如何优化？
**回答要点**:
- **数据库**: 读写分离、分库分表、增加缓存层
- **后端**: 使用Celery异步处理、增加负载均衡、使用Gunicorn多进程
- **前端**: CDN加速、代码分割、图片懒加载
- **Redis**: 主从复制、集群模式
- **部署**: Kubernetes编排、自动扩缩容

#### Q33: 如果让你重新设计这个项目，你会怎么做？
**回答要点**:
- **前端**: 使用TypeScript、添加路由守卫和错误边界
- **后端**: 添加更多测试、使用缓存预热、实现消息队列
- **数据库**: 添加慢查询监控、优化索引、使用读写分离
- **安全**: 添加HTTPS、实现更严格的权限控制
- **运维**: 集成Prometheus + Grafana监控、配置日志轮转

---

## 后端深度面试问题扩展

### 一、Django基础与架构

#### Q34: Django的MTV架构是什么？和MVC有什么区别？
**回答要点**:
- **MTV架构**: Model(模型)、Template(模板)、View(视图)
- **MVC架构**: Model(模型)、View(视图)、Controller(控制器)
- **对应关系**:
  - Django的Model → MVC的Model（数据层）
  - Django的View → MVC的Controller（业务逻辑）
  - Django的Template → MVC的View（展示层）
- **区别**:
  - Django的View负责处理请求和业务逻辑，而非渲染
  - Template负责渲染HTML，与数据分离
  - URL配置起到了Controller的路由分发作用

#### Q35: Django中间件的执行顺序是什么？常用中间件有哪些？
**回答要点**:
- **执行顺序**:
  - 请求阶段: 按`MIDDLEWARE`列表顺序执行`process_request`和`process_view`
  - 响应阶段: 按`MIDDLEWARE`列表逆序执行`process_exception`、`process_template_response`、`process_response`
- **常用中间件**:
  - `SecurityMiddleware`: 安全相关（XSS防护、HTTPS重定向）
  - `SessionMiddleware`: 会话管理
  - `AuthenticationMiddleware`: 用户认证
  - `CsrfViewMiddleware`: CSRF防护
  - `MessageMiddleware`: 消息框架
  - `CorsMiddleware`: CORS跨域支持（django-cors-headers）

#### Q36: Django的ORM有什么优缺点？
**回答要点**:
- **优点**:
  - **代码可读性高**: 使用Python代码操作数据库，无需编写SQL
  - **数据库抽象**: 支持多种数据库（MySQL、PostgreSQL、SQLite等），切换方便
  - **安全性**: 自动防止SQL注入
  - **迁移系统**: 数据库schema版本管理
- **缺点**:
  - **性能开销**: 复杂查询时ORM生成的SQL可能不够优化
  - **学习曲线**: 复杂查询需要学习ORM语法
  - **灵活性受限**: 某些复杂SQL难以用ORM表达，需使用`raw()`或`extra()`

#### Q37: Django的QuerySet是什么？有什么特点？
**回答要点**:
- **定义**: QuerySet是Django ORM对数据库查询的封装，是一个可迭代对象
- **特点**:
  - **惰性求值**: 只有在真正需要数据时才执行数据库查询
  - **链式调用**: 支持多个filter、exclude、order_by等方法链式调用
  - **可切片**: 支持Python切片语法，转换为LIMIT/OFFSET
  - **缓存机制**: 首次迭代后结果缓存到内存
- **示例**:
  ```python
  # 惰性求值，此时不执行查询
  posts = Post.objects.filter(status='published')
  
  # 链式调用，仍不执行查询
  posts = posts.order_by('-created_at')[:10]
  
  # 迭代时执行查询，结果缓存
  for post in posts:
      print(post.title)
  ```

#### Q38: Django的信号机制是什么？如何使用？
**回答要点**:
- **定义**: Django信号是一种观察者模式，用于在特定事件发生时通知相关的监听器
- **常用信号**:
  - `pre_save`/`post_save`: 保存前后
  - `pre_delete`/`post_delete`: 删除前后
  - `m2m_changed`: 多对多关系变更
  - `user_logged_in`/`user_logged_out`: 用户登录/注销
- **使用方式**:
  ```python
  from django.db.models.signals import post_save
  from django.dispatch import receiver
  from .models import Comment, Post
  
  @receiver(post_save, sender=Comment)
  def update_post_comment_count(sender, instance, created, **kwargs):
      post = instance.post
      post.comment_count = post.comments.filter(is_deleted=False).count()
      post.save(update_fields=['comment_count'])
  ```

### 二、Django REST Framework

#### Q39: DRF的序列化器有什么作用？如何自定义序列化器？
**回答要点**:
- **作用**:
  - **数据序列化**: 将模型实例转换为JSON格式
  - **数据反序列化**: 将JSON数据转换为模型实例
  - **数据验证**: 验证输入数据的合法性
- **自定义序列化器**:
  ```python
  from rest_framework import serializers
  from .models import Post
  
  class PostSerializer(serializers.ModelSerializer):
      author_name = serializers.CharField(source='author.username', read_only=True)
      
      class Meta:
          model = Post
          fields = ['id', 'title', 'content', 'author', 'author_name', 'created_at']
          read_only_fields = ['id', 'author', 'created_at']
      
      def validate_title(self, value):
          if len(value) < 3:
              raise serializers.ValidationError('标题至少3个字符')
          return value
  ```

#### Q40: DRF的视图有哪些类型？各有什么特点？
**回答要点**:
- **APIView**: 最基础的视图类，手动处理请求和响应
- **GenericAPIView**: 提供了通用的CRUD操作，需配合Mixin使用
- **ViewSet**: 将多个相关视图组合在一起，通过router自动生成URL
- **ModelViewSet**: 完整的CRUD操作，最常用
- **ReadOnlyModelViewSet**: 只读版本，适用于公开数据
- **使用场景**:
  - 简单API用`APIView`
  - 标准CRUD用`ModelViewSet`
  - 公开只读数据用`ReadOnlyModelViewSet`

#### Q41: DRF的认证机制有哪些？如何自定义认证？
**回答要点**:
- **内置认证**:
  - `SessionAuthentication`: 会话认证
  - `BasicAuthentication`: HTTP基本认证
  - `TokenAuthentication`: Token认证
- **第三方认证**:
  - `JWTAuthentication`: JWT认证（djangorestframework-simplejwt）
- **自定义认证**:
  ```python
  from rest_framework.authentication import BaseAuthentication
  from rest_framework.exceptions import AuthenticationFailed
  
  class CustomAuthentication(BaseAuthentication):
      def authenticate(self, request):
          token = request.headers.get('Authorization')
          if not token:
              return None
          
          # 验证token逻辑
          user = self.validate_token(token)
          if not user:
              raise AuthenticationFailed('Token无效')
          
          return (user, None)
  ```

#### Q42: DRF的权限机制有哪些？如何自定义权限？
**回答要点**:
- **内置权限**:
  - `AllowAny`: 允许所有用户
  - `IsAuthenticated`: 仅登录用户
  - `IsAdminUser`: 仅管理员
  - `IsAuthenticatedOrReadOnly`: 登录用户可写，其他只读
- **自定义权限**:
  ```python
  from rest_framework.permissions import BasePermission
  
  class IsOwnerOrReadOnly(BasePermission):
      def has_object_permission(self, request, view, obj):
          # 只读请求放行
          if request.method in ['GET', 'HEAD', 'OPTIONS']:
              return True
          
          # 写请求验证所有者
          return obj.author == request.user
  ```

#### Q43: DRF的限流机制有哪些？如何自定义限流？
**回答要点**:
- **内置限流**:
  - `AnonRateThrottle`: 匿名用户限流
  - `UserRateThrottle`: 登录用户限流
  - `ScopedRateThrottle`: 基于scope的限流
- **自定义限流**:
  ```python
  from rest_framework.throttling import SimpleRateThrottle
  
  class LoginRateThrottle(SimpleRateThrottle):
      scope = 'login'
      
      def get_cache_key(self, request, view):
          email = request.data.get('email', '')
          if email:
              return f'{self.scope}_{self.get_ident(request)}_{email}'
          return f'{self.scope}_{self.get_ident(request)}'
  ```

### 三、数据库与性能优化

#### Q44: MySQL的存储引擎有哪些？InnoDB和MyISAM有什么区别？
**回答要点**:
- **常用存储引擎**: InnoDB、MyISAM、Memory、Archive
- **InnoDB vs MyISAM**:
  | 特性 | InnoDB | MyISAM |
  |------|--------|--------|
  | 事务支持 | 支持 | 不支持 |
  | 行级锁 | 支持 | 表级锁 |
  | 外键约束 | 支持 | 不支持 |
  | 全文索引 | 5.6+支持 | 支持 |
  | 崩溃恢复 | 支持 | 不支持 |
  | 并发性能 | 高 | 低 |
- **选择建议**: 生产环境优先使用InnoDB

#### Q45: MySQL索引的类型有哪些？如何选择合适的索引？
**回答要点**:
- **索引类型**:
  - **B+Tree索引**: 最常用，支持范围查询、排序
  - **Hash索引**: 精确匹配，不支持范围查询
  - **Full-text索引**: 全文搜索
  - **R-tree索引**: 空间数据查询
- **索引选择原则**:
  - **高频查询字段**: WHERE条件、JOIN条件、ORDER BY字段
  - **区分度高的字段**: 如邮箱、用户名（不适合性别等低区分度字段）
  - **避免过多索引**: 索引影响写入性能
  - **复合索引**: 遵循最左前缀原则

#### Q46: 什么是数据库事务？ACID原则是什么？
**回答要点**:
- **事务定义**: 一组不可分割的数据库操作，要么全部成功，要么全部失败
- **ACID原则**:
  - **Atomicity（原子性）**: 事务是一个原子操作，不可分割
  - **Consistency（一致性）**: 事务前后数据完整性保持一致
  - **Isolation（隔离性）**: 事务之间相互隔离，互不干扰
  - **Durability（持久性）**: 事务提交后，数据永久保存

#### Q47: MySQL的事务隔离级别有哪些？各有什么特点？
**回答要点**:
- **隔离级别**:
  - **READ UNCOMMITTED（读未提交）**: 允许读取未提交的数据，可能出现脏读、不可重复读、幻读
  - **READ COMMITTED（读已提交）**: 只能读取已提交的数据，避免脏读，可能出现不可重复读、幻读
  - **REPEATABLE READ（可重复读）**: MySQL默认，同一事务内多次读取同一数据结果一致，避免脏读、不可重复读，可能出现幻读
  - **SERIALIZABLE（串行化）**: 最高隔离级别，事务串行执行，避免所有并发问题，但性能最低

#### Q48: 什么是缓存雪崩、缓存击穿、缓存穿透？如何解决？
**回答要点**:
- **缓存雪崩**:
  - **问题**: 大量缓存同时过期，请求全部打到数据库
  - **解决方案**: 设置不同过期时间、缓存预热、多级缓存
- **缓存击穿**:
  - **问题**: 热点数据缓存过期，大量请求同时访问该数据
  - **解决方案**: 互斥锁、永不过期（后台异步更新）、分布式锁
- **缓存穿透**:
  - **问题**: 请求不存在的数据，缓存和数据库都查不到
  - **解决方案**: 缓存空值、布隆过滤器、参数校验

#### Q49: 什么是MVCC？它是如何实现的？
**回答要点**:
- **定义**: Multi-Version Concurrency Control，多版本并发控制，让读写操作不互相阻塞，提升并发性能
- **核心思想**: 每行数据维护多个版本，读操作读取快照版本，写操作创建新版本
- **实现机制**（InnoDB）:
  - **隐藏字段**: 每行包含 `DB_TRX_ID`（事务ID）、`DB_ROLL_PTR`（回滚指针）、`DB_ROW_ID`（行ID）
  - **Undo Log**: 旧版本数据通过回滚指针串联成版本链
  - **Read View**: 事务发起时生成快照，决定能看到哪些版本
- **Read View 可见性判断**:
  - 若 `DB_TRX_ID < min_trx_id`：已提交，可见
  - 若 `DB_TRX_ID >= max_trx_id`：未来事务，不可见
  - 若在活跃事务列表中：未提交，不可见，沿版本链找上一个版本
- **与隔离级别的关系**:
  - **RC（读已提交）**: 每次SELECT都生成新的Read View → 可能不可重复读
  - **RR（可重复读）**: 仅第一次SELECT生成Read View → 可重复读
- **本项目应用**: Django ORM 的 `select_for_update()` 会使用当前读（读最新版本），绕过MVCC

#### Q50: MySQL的锁机制有哪些？行锁、间隙锁、临键锁的区别？
**回答要点**:
- **锁粒度**:
  - **表锁**: 锁整张表，并发低（MyISAM）
  - **行锁**: 锁单行记录，并发高（InnoDB）
  - **页锁**: 锁数据页，介于两者之间
- **InnoDB行锁类型**:
  - **Record Lock（记录锁）**: 锁定索引上的单条记录
  - **Gap Lock（间隙锁）**: 锁定索引区间，但不包含记录本身，防止插入
  - **Next-Key Lock（临键锁）**: Record Lock + Gap Lock，锁定记录及其前方的间隙
- **共享锁与排他锁**:
  - **S锁（共享锁）**: `SELECT ... LOCK IN SHARE MODE`，允许多个读
  - **X锁（排他锁）**: `SELECT ... FOR UPDATE`、`UPDATE`、`DELETE`，独占
- **意向锁**: 表级标记锁（IS、IX），快速判断表中是否有行锁
- **本项目应用**: 订单创建时 `select_for_update()` 对购物车记录加排他锁，防止并发下单

#### Q51: 聚簇索引和非聚簇索引有什么区别？
**回答要点**:
- **聚簇索引**:
  - 数据行按索引顺序物理存储，叶子节点直接存储完整数据行
  - 一张表只能有一个聚簇索引（通常是主键）
  - 查询主键非常快（一次IO即可）
- **非聚簇索引（二级索引）**:
  - 叶子节点存储索引列值 + 主键值
  - 查询需要**回表**：先查二级索引得到主键，再查聚簇索引得到完整数据
- **覆盖索引**: 查询列全部被索引覆盖，无需回表
  ```sql
  -- 联合索引 (a, b, c)
  SELECT a, b FROM t WHERE a = 1;  -- 覆盖索引，无需回表
  SELECT * FROM t WHERE a = 1;     -- 需要回表
  ```
- **索引下推（ICP）**: MySQL 5.6+，在存储引擎层先过滤索引条件，减少回表次数

#### Q52: MySQL的日志系统有哪些？binlog、redo log、undo log 的区别？
**回答要点**:
- **Redo Log（重做日志）**:
  - 存储引擎层（InnoDB），保证**崩溃恢复**（持久性）
  - 记录数据页的物理修改（哪个页偏移量改了什么）
  - 先写日志（WAL），再写数据页，循环写
  - `innodb_flush_log_at_trx_commit=1` 保证每次事务提交都刷盘
- **Undo Log（回滚日志）**:
  - 存储引擎层（InnoDB），保证**事务回滚**（原子性）和 MVCC
  - 记录修改前的旧值
  - 用于事务回滚和快照读
- **Binlog（二进制日志）**:
  - Server层，保证**主从复制**和**数据恢复**
  - 记录所有DDL和DML操作（逻辑日志）
  - 三种格式：STATEMENT（语句）、ROW（行变更）、MIXED（混合）
  - `sync_binlog=1` 保证每次事务提交都刷盘
- **两阶段提交**: 保证 redo log 和 binlog 的一致性
  ```
  1. 写入 redo log（prepare状态）
  2. 写入 binlog
  3. 提交 redo log（commit状态）
  ```

#### Q53: 如何进行慢查询优化？EXPLAIN各字段含义？
**回答要点**:
- **定位慢查询**:
  ```sql
  -- 开启慢查询日志
  SET GLOBAL slow_query_log = ON;
  SET GLOBAL long_query_time = 1;  -- 超过1秒记录
  ```
- **EXPLAIN关键字段**:
  | 字段 | 含义 | 优化关注点 |
  |------|------|-----------|
  | `type` | 访问类型 | `ALL`（全表扫描）最差，`const`/`eq_ref`/`ref`较好 |
  | `key` | 实际使用的索引 | NULL表示未用索引 |
  | `rows` | 预估扫描行数 | 越小越好 |
  | `Extra` | 额外信息 | `Using filesort`（文件排序）、`Using temporary`（临时表）需优化 |
  | `possible_keys` | 可能用的索引 | 判断是否漏建索引 |
  | `key_len` | 索引使用长度 | 判断复合索引用了几个字段 |
- **常见优化手段**:
  - 避免 `SELECT *`，只查需要的列（利用覆盖索引）
  - 避免 `LIKE '%xxx'`（前导通配符无法用索引）
  - 避免 `WHERE` 对索引列使用函数或类型转换
  - 大分页优化：`WHERE id > last_id LIMIT 10` 替代 `OFFSET 10000 LIMIT 10`
- **本项目应用**: 帖子列表查询添加 `(status, created_at)` 联合索引，避免全表扫描

#### Q54: 什么是数据库范式？什么时候需要反范式？
**回答要点**:
- **范式（Normal Form）**:
  - **1NF**: 字段不可再分（原子性）
  - **2NF**: 非主键字段完全依赖主键（消除部分依赖）
  - **3NF**: 非主键字段直接依赖主键（消除传递依赖）
  - **BCNF**: 每个决定因素都是候选键
- **反范式**: 为提升查询性能，适度增加冗余字段，牺牲空间换时间
- **何时反范式**:
  - 高频查询需要多表JOIN，性能瓶颈明显
  - 统计/报表场景，冗余字段避免实时计算
- **本项目应用**:
  - `Post` 模型冗余了 `view_count`、`like_count`、`comment_count` 字段，避免每次查询都COUNT
  - `Formula` 模型冗余了 `view_count`，用 `F('view_count') + 1` 原子更新
  - `Order` 模型存储了 `address` JSON 快照而非外键引用，防止地址修改影响历史订单

#### Q55: MySQL主从复制原理是什么？如何实现读写分离？
**回答要点**:
- **复制原理**:
  1. **主库**执行事务，写入 binlog
  2. **IO线程**（从库）拉取主库 binlog，写入 relay log
  3. **SQL线程**（从库）读取 relay log，回放SQL，同步数据
- **复制方式**:
  - **异步复制**: 主库不等从库确认，可能丢数据（默认）
  - **半同步复制**: 主库等至少一个从库确认收到 binlog
  - **组复制（MGR）**: 多主一致性复制
- **读写分离**:
  - 写操作走主库，读操作走从库
  - Django通过数据库路由实现:
    ```python
    class MasterSlaveRouter:
        def db_for_read(self, model, **hints):
            return 'slave'
        def db_for_write(self, model, **hints):
            return 'default'
    ```
- **主从延迟问题**:
  - **原因**: 单线程回放SQL、大事务、网络延迟
  - **解决**: 关键读操作强制走主库（`using('default')`）

#### Q56: 什么情况下需要分库分表？有哪些策略？
**回答要点**:
- **分表时机**:
  - 单表数据量超过千万级，查询性能明显下降
  - 单表数据文件超过10GB，维护困难
- **分库时机**:
  - 单库并发量过高，CPU/IO/连接数成为瓶颈
  - 业务模块需要物理隔离
- **分片策略**:
  - **水平分片（Sharding）**: 按行拆分到多张表
    - **范围分片**: 按ID范围（1-10000在表A，10001-20000在表B）
    - **哈希分片**: `table_no = hash(id) % N`
    - **一致性哈希**: 减少节点变动时的数据迁移
  - **垂直分片**: 按列拆分（热门字段和冷门字段分开）
- **分库分表带来的问题**:
  - **跨库JOIN**: 应用层组装或冗余字段
  - **分布式事务**: 2PC、TCC、Saga模式
  - **全局唯一ID**: 雪花算法、号段模式
  - **分页查询**: 需要多次查询后合并
- **中间件**: ShardingSphere、MyCAT、Vitess

#### Q57: Django ORM如何优化查询性能？N+1问题如何解决？
**回答要点**:
- **N+1问题**:
  - **现象**: 查询N条主表记录，再逐条查询关联表，共执行 N+1 次SQL
  - **示例（错误）**:
    ```python
    posts = Post.objects.all()  # 1次查询
    for post in posts:
        print(post.author.username)  # N次查询（每条帖子查一次作者）
    ```
- **解决方案**:
  - **select_related（外键/一对一）**: JOIN查询，一次获取
    ```python
    posts = Post.objects.select_related('author', 'category').all()
    ```
  - **prefetch_related（多对多/反向外键）**: 额外一次IN查询
    ```python
    posts = Post.objects.prefetch_related('tags', 'comments').all()
    ```
- **其他优化手段**:
  - **only()**: 只查需要的字段
    ```python
    Post.objects.only('title', 'created_at')
    ```
  - **defer()**: 排除大字段
    ```python
    Post.objects.defer('content')  # 不查content字段
    ```
  - **bulk_create**: 批量插入
    ```python
    Tag.objects.bulk_create([Tag(name='t1'), Tag(name='t2')])
    ```
  - **bulk_update**: 批量更新（Django 2.2+）
  - **Iterator()**: 大数据集流式处理，不缓存QuerySet
    ```python
    for post in Post.objects.iterator():
        process(post)
    ```
- **本项目应用**:
  - 帖子列表: `select_related('author').prefetch_related('tags')`
  - 公式列表: `select_related('category', 'target_state')`

#### Q58: 本项目中事务是如何使用的？有哪些注意事项？
**回答要点**:
- **事务使用场景**:
  - **订单创建**: 购物车删除 + 订单创建 + 库存扣减必须在同一事务
  - **订单取消**: 状态更新 + 库存回滚必须在同一事务
  - **支付宝回调**: 订单状态更新 + 库存扣减必须幂等且原子
- **Django事务用法**:
  ```python
  from django.db import transaction
  
  # 方式1：装饰器
  @transaction.atomic
  def create_order(request):
      cart = Cart.objects.select_for_update().get(id=cart_id)
      order = Order.objects.create(...)
      Product.objects.filter(id=pid).update(stock=F('stock') - qty)
      cart.delete()
  
  # 方式2：上下文管理器
  with transaction.atomic():
      # 事务代码块
      pass
  
  # 方式3：保存点（部分回滚）
  with transaction.atomic():
      try:
          with transaction.atomic():
              # 可能失败的操作
              pass
      except:
          pass  # 仅回滚保存点，外层事务继续
  ```
- **注意事项**:
  - **不要在事务中调用外部服务**（如HTTP请求、支付宝API），避免长事务
  - **select_for_update()必须在事务内使用**，否则无效
  - **F表达式保证原子性**: `F('stock') - 1` 在数据库层面计算，不受Python竞争影响
  - **幂等性处理**: 支付宝回调用 `select_for_update()` 锁定订单，检查状态防止重复处理

### 四、安全与认证

#### Q59: 什么是JWT？JWT的结构是什么？
**回答要点**:
- **定义**: JSON Web Token，一种用于身份认证的令牌
- **结构**: 三部分用`.`分隔
  - **Header**: 声明类型和算法
    ```json
    {"alg": "HS256", "typ": "JWT"}
    ```
  - **Payload**: 存储用户信息（如user_id、username、过期时间）
    ```json
    {"user_id": 1, "username": "test", "exp": 1234567890}
    ```
  - **Signature**: 签名，用于验证token完整性
    ```
    HMACSHA256(base64UrlEncode(header) + "." + base64UrlEncode(payload), secret)
    ```

#### Q60: JWT和Session有什么区别？各自的优缺点是什么？
**回答要点**:
- **存储位置**:
  - JWT: 存储在客户端（localStorage/cookie）
  - Session: 存储在服务端
- **状态管理**:
  - JWT: 无状态，服务端无需存储会话
  - Session: 有状态，服务端需要维护会话
- **优缺点**:
  | 特性 | JWT | Session |
  |------|-----|---------|
  | 分布式部署 | 友好（无需共享Session） | 需要Session共享（Redis等） |
  | 过期管理 | 客户端判断，服务端黑名单 | 服务端控制 |
  | 安全性 | 需防止token泄露 | 需防止Session劫持 |
  | 大小 | 较大（包含用户信息） | 较小（仅Session ID） |

#### Q61: 什么是CSRF攻击？如何防范？
**回答要点**:
- **定义**: Cross-Site Request Forgery，跨站请求伪造，攻击者诱导用户在已登录的情况下执行非预期操作
- **防范措施**:
  - **CSRF Token**: 表单中加入随机token，服务端验证
  - **SameSite Cookie**: 设置Cookie的SameSite属性（Strict/Lax）
  - **验证Referer**: 验证请求来源
  - **使用JWT**: 无状态认证天然防CSRF（需配合Authorization头）

#### Q62: 什么是XSS攻击？如何防范？
**回答要点**:
- **定义**: Cross-Site Scripting，跨站脚本攻击，攻击者在网页中注入恶意脚本
- **类型**:
  - **存储型XSS**: 恶意脚本存储在数据库中
  - **反射型XSS**: 恶意脚本通过URL参数传递
  - **DOM型XSS**: 恶意脚本在客户端执行
- **防范措施**:
  - **输入过滤**: 对用户输入进行过滤和转义
  - **输出编码**: 渲染数据时进行HTML编码
  - **使用安全的模板引擎**: Django模板自动转义
  - **Content-Security-Policy**: 设置CSP头限制脚本来源

#### Q63: 密码如何安全存储？
**回答要点**:
- **绝对禁止**: 明文存储密码
- **推荐方式**: 使用单向哈希函数加密
- **常用算法**:
  - **bcrypt**: 推荐，自动加盐，可配置成本因子
  - **Argon2**: 更安全，但计算成本高
  - **scrypt**: 内存密集型，防ASIC攻击
- **Django实现**:
  ```python
  from django.contrib.auth.hashers import make_password, check_password
  
  # 创建密码哈希
  hashed_password = make_password('password123')
  
  # 验证密码
  is_valid = check_password('password123', hashed_password)
  ```

### 五、Redis与缓存

#### Q64: Redis支持哪些数据类型？各有什么用途？
**回答要点**:
- **String（字符串）**:
  - 用途: 缓存、计数器、分布式锁
  - 示例: 缓存用户信息、页面访问次数
- **Hash（哈希）**:
  - 用途: 存储对象、用户资料
  - 示例: `hset user:1 name "test" email "test@example.com"`
- **List（列表）**:
  - 用途: 消息队列、最新列表
  - 示例: 论坛帖子列表、任务队列
- **Set（集合）**:
  - 用途: 去重、交集并集
  - 示例: 用户关注列表、共同关注
- **Sorted Set（有序集合）**:
  - 用途: 排行榜、带权重的队列
  - 示例: 热门帖子排行、积分排名
- **Bitmap（位图）**:
  - 用途: 布尔状态存储、统计
  - 示例: 用户签到、活跃用户统计

#### Q65: Redis的持久化机制有哪些？各有什么特点？
**回答要点**:
- **RDB（Redis Database）**:
  - **原理**: 定期将内存数据快照写入磁盘
  - **优点**: 恢复速度快、文件体积小
  - **缺点**: 可能丢失最近的数据
  - **配置**: `save 60 1000`（60秒内1000次修改则快照）
- **AOF（Append Only File）**:
  - **原理**: 记录所有写操作命令
  - **优点**: 数据完整性高、可配置同步策略
  - **缺点**: 文件体积大、恢复速度慢
  - **配置**: `appendonly yes`、`appendfsync everysec`
- **混合持久化**: Redis 4.0+支持，结合RDB和AOF的优点

#### Q66: Redis的主从复制是什么？如何配置？
**回答要点**:
- **定义**: 将主节点的数据同步到从节点，实现数据备份和读写分离
- **配置**:
  ```bash
  # 从节点配置文件
  slaveof 192.168.1.100 6379  # 主节点IP和端口
  ```
- **复制流程**:
  1. 从节点连接主节点
  2. 主节点执行BGSAVE生成RDB文件
  3. 主节点发送RDB文件到从节点
  4. 从节点加载RDB文件
  5. 主节点发送增量命令到从节点
- **作用**:
  - 数据备份
  - 读写分离（主写从读）
  - 负载均衡

#### Q67: 什么是Redis分布式锁？如何实现？
**回答要点**:
- **定义**: 在分布式系统中，多个进程/线程对共享资源的互斥访问
- **实现方式**:
  ```python
  import redis
  
  client = redis.Redis()
  
  def acquire_lock(key, timeout=10):
      # 设置锁，NX表示不存在才设置，PX表示过期时间（毫秒）
      result = client.set(key, '1', nx=True, px=timeout * 1000)
      return result is not None
  
  def release_lock(key):
      client.delete(key)
  ```
- **注意事项**:
  - 设置合理的过期时间，避免死锁
  - 使用Lua脚本保证原子性
  - 考虑锁的重入性

### 六、部署与运维

#### Q68: Django项目如何部署到生产环境？
**回答要点**:
- **容器编排**: 项目使用 Docker Compose v2 编排 `db`、`redis`、`api`、`front`、`nginx` 五个服务
- **后端镜像**: Python 多阶段构建依赖 wheel，运行阶段启动 3 个 Gunicorn worker，不使用 `--reload`
- **前端镜像**: Node 阶段执行 `npm ci` 和 `npm run build`，运行阶段由 Nginx 提供镜像内的 `dist`
- **公网入口**: 网关 Nginx 将 `/api/` 转发到 `api:8000`，将其他页面请求转发到 `front:80`
- **静态与媒体**: API 启动时自动执行 `collectstatic`；Django 静态文件使用 `collected_static` 卷，媒体文件使用 `./cube_api/media` 绑定目录
- **数据库启动**: API 通过 `depends_on: condition: service_healthy` 等待 MySQL 健康检查通过
- **发布流程**: `deploy.sh` 支持 `full`、`api`、`front` 三种模式，负责拉取代码、构建镜像、执行 migration、重启 Nginx 和健康验证

#### Q69: Docker和虚拟机有什么区别？
**回答要点**:
- **隔离级别**:
  - Docker: 操作系统级隔离，共享内核
  - 虚拟机: 硬件级隔离，有独立内核
- **资源消耗**:
  - Docker: 轻量级，启动快，资源占用少
  - 虚拟机: 重量级，启动慢，资源占用多
- **性能**:
  - Docker: 接近原生性能
  - 虚拟机: 有虚拟化开销
- **使用场景**:
  - Docker: 微服务、容器化部署
  - 虚拟机: 需要完全隔离的环境

#### Q70: Nginx的作用是什么？常用配置有哪些？
**回答要点**:
- **作用**:
  - **反向代理**: 将客户端请求转发到后端服务器
  - **负载均衡**: 分发请求到多个后端服务器
  - **静态文件服务**: 直接提供静态文件
  - **SSL终止**: 处理HTTPS请求
- **常用配置**:
  ```nginx
  server {
      listen 80;
      server_name _;
      
      location /api/ {
          proxy_pass http://api:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
      }
  
      location /media/ {
          alias /usr/share/nginx/html/media/;
          expires 30d;
      }
  
      location /static/ {
          alias /usr/share/nginx/html/static/;
          expires 30d;
      }
      
      location / {
          proxy_pass http://front:80;
      }
  }
  ```
- **项目中的双层 Nginx**: 外层 Nginx 是统一网关；前端容器内的 Nginx 提供 `dist`，并通过 `try_files $uri $uri/ /index.html` 完成 Vue Router 的 SPA 回退

#### Q71: 什么是Docker Compose？如何使用？
**回答要点**:
- **定义**: 使用声明式 YAML 统一定义和运行多容器应用
- **规范**: Docker Compose v2 使用 Compose Specification，顶层不再需要 `version`
- **项目配置**:
  ```yaml
  services:
    db:
      image: mysql:8.0
      volumes:
        - mysql_data:/var/lib/mysql
      healthcheck:
        test: ["CMD-SHELL", "MYSQL_PWD=... mysqladmin ping -h localhost -uroot"]
        start_period: 45s
  
    api:
      build: ./cube_api
      depends_on:
        db:
          condition: service_healthy
  
    front:
      build: ./cube_front
  
    nginx:
      image: nginx:1.28-alpine
      ports:
        - "80:80"
  ```
- **常用命令**:
  ```bash
  bash deploy.sh full     # 首次或全量部署
  bash deploy.sh api      # 仅更新后端并执行迁移
  bash deploy.sh front    # 仅更新前端
  docker compose ps       # 查看服务状态
  docker compose logs -f  # 查看日志
  ```
- **数据安全**: `docker compose down` 默认保留命名卷，`docker compose down -v` 会删除 MySQL 和 Redis 数据卷，生产环境禁止使用

### 七、设计模式与架构

#### Q72: 什么是RESTful API？有什么设计原则？
**回答要点**:
- **定义**: Representational State Transfer，一种软件架构风格
- **设计原则**:
  - **无状态**: 每个请求都包含所有必要信息，服务端不保存会话状态
  - **统一接口**: 使用标准HTTP方法（GET/POST/PUT/DELETE）
  - **资源标识**: 使用URL标识资源（如`/api/posts/1`）
  - **资源表现**: 支持多种格式（JSON/XML）
  - **超媒体驱动**: 返回的资源包含链接到其他资源的URI
- **HTTP方法语义**:
  - GET: 获取资源
  - POST: 创建资源
  - PUT: 更新资源（全量）
  - PATCH: 更新资源（部分）
  - DELETE: 删除资源

#### Q73: 什么是微服务架构？和单体架构有什么区别？
**回答要点**:
- **微服务**: 将应用拆分为多个独立的小型服务，每个服务专注于一个业务领域
- **单体架构**: 所有功能集中在一个应用中
- **区别**:
  | 特性 | 微服务 | 单体架构 |
  |------|--------|----------|
  | 部署 | 独立部署 | 整体部署 |
  | 技术栈 | 可多样化 | 统一技术栈 |
  | 扩展性 | 按需扩展 | 整体扩展 |
  | 复杂度 | 高（分布式） | 低 |
  | 可靠性 | 部分故障不影响整体 | 单点故障 |
- **选择建议**: 小型项目用单体，大型项目用微服务

#### Q74: 什么是MVC/MVT架构？有什么优缺点？
**回答要点**:
- **MVC**: Model-View-Controller
- **MVT**: Model-View-Template（Django）
- **优点**:
  - **职责分离**: 各层职责清晰，易于维护
  - **代码复用**: 视图和模板可复用
  - **可测试性**: 各层独立，易于单元测试
- **缺点**:
  - **学习曲线**: 需要理解各层之间的交互
  - **简单项目过度设计**: 小型项目可能显得复杂

#### Q75: 什么是ORM？和直接写SQL有什么区别？
**回答要点**:
- **ORM**: Object-Relational Mapping，对象关系映射，将数据库表映射为对象
- **区别**:
  | 特性 | ORM | 原生SQL |
  |------|-----|---------|
  | 可读性 | 高（Python代码） | 低（SQL语句） |
  | 开发效率 | 高（无需编写SQL） | 低（需手写SQL） |
  | 性能 | 可能较低（复杂查询） | 高（可优化SQL） |
  | 数据库兼容性 | 高（自动适配） | 低（SQL方言差异） |
  | 安全性 | 高（防SQL注入） | 低（需手动防护） |
- **选择建议**: 常规操作使用ORM，复杂查询使用原生SQL

### 八、Python基础

#### Q76: Python的GIL是什么？有什么影响？
**回答要点**:
- **定义**: Global Interpreter Lock，全局解释器锁，Python解释器中用于控制多线程执行的锁
- **影响**:
  - **多线程性能**: 同一时刻只有一个线程执行Python字节码，CPU密集型任务无法利用多核
  - **多进程**: 绕过GIL的方式，每个进程有独立的解释器和GIL
- **适用场景**:
  - **I/O密集型**: 多线程有效（等待时释放GIL）
  - **CPU密集型**: 建议使用多进程或异步

#### Q77: Python的装饰器是什么？如何实现？
**回答要点**:
- **定义**: 一种语法糖，用于修改函数或类的行为
- **实现方式**:
  ```python
  # 简单装饰器
  def my_decorator(func):
      def wrapper(*args, **kwargs):
          print('Before')
          result = func(*args, **kwargs)
          print('After')
          return result
      return wrapper
  
  @my_decorator
  def hello():
      print('Hello')
  
  # 带参数的装饰器
  def repeat(times):
      def decorator(func):
          def wrapper(*args, **kwargs):
              results = []
              for _ in range(times):
                  results.append(func(*args, **kwargs))
              return results
          return wrapper
      return decorator
  
  @repeat(3)
  def say_hi():
      return 'Hi'
  ```

#### Q78: Python的生成器是什么？有什么特点？
**回答要点**:
- **定义**: 使用`yield`关键字定义的函数，返回一个迭代器
- **特点**:
  - **惰性求值**: 每次迭代时生成一个值，不一次性生成所有值
  - **内存效率**: 节省内存，适合处理大数据集
  - **无限序列**: 可以生成无限序列
- **示例**:
  ```python
  def fibonacci():
      a, b = 0, 1
      while True:
          yield a
          a, b = b, a + b
  
  # 使用生成器
  fib = fibonacci()
  for _ in range(10):
      print(next(fib))
  ```

#### Q79: Python的异步编程是什么？如何实现？
**回答要点**:
- **定义**: 非阻塞编程，在等待I/O操作时可以执行其他任务
- **实现方式**:
  ```python
  import asyncio
  
  async def fetch_data(url):
      print(f'Start fetching {url}')
      # 模拟网络请求
      await asyncio.sleep(1)
      print(f'Finished fetching {url}')
      return f'Data from {url}'
  
  async def main():
      # 并发执行多个任务
      results = await asyncio.gather(
          fetch_data('https://example.com'),
          fetch_data('https://google.com')
      )
      print(results)
  
  asyncio.run(main())
  ```
- **适用场景**: I/O密集型任务（网络请求、文件读写）

#### Q80: Python的列表推导式是什么？和循环有什么区别？
**回答要点**:
- **定义**: 一种简洁的创建列表的方式
- **示例**:
  ```python
  # 列表推导式
  squares = [x**2 for x in range(10) if x % 2 == 0]
  
  # 等价于循环
  squares = []
  for x in range(10):
      if x % 2 == 0:
          squares.append(x**2)
  ```
- **区别**:
  - **代码简洁**: 一行代码完成，可读性高
  - **性能**: 通常比显式循环更快
  - **功能**: 支持条件过滤和嵌套

### 九、项目实战问题

#### Q81: 在本项目中，如何实现用户关注功能？
**回答要点**:
- **模型设计**: 使用ManyToManyField实现用户之间的关注关系
  ```python
  class User(AbstractUser):
      following = models.ManyToManyField(
          'self',
          symmetrical=False,
          related_name='followers',
          blank=True
      )
  ```
- **API实现**:
  - 关注: `user.following.add(target_user)`
  - 取消关注: `user.following.remove(target_user)`
  - 获取关注列表: `user.following.all()`
  - 获取粉丝列表: `user.followers.all()`
- **权限控制**: 使用`IsFollowingOrReadOnly`权限类，关注者可见特定内容

#### Q82: 在本项目中，论坛模块的帖子状态如何管理？
**回答要点**:
- **状态字段**:
  ```python
  STATUS_CHOICES = [
      ('published', '已发布'),
      ('draft', '草稿'),
      ('deleted', '已删除')
  ]
  status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')
  is_deleted = models.BooleanField(default=False)
  ```
- **状态流转**:
  - 草稿 → 已发布: 用户发布帖子
  - 已发布 → 草稿: 用户编辑后保存草稿
  - 已发布 → 已删除: 用户或管理员删除（软删除）
- **查询过滤**:
  ```python
  # 获取所有活跃帖子
  Post.objects.filter(status='published', is_deleted=False)
  ```

#### Q83: 在本项目中，如何实现图片上传功能？
**回答要点**:
- **模型字段**: 使用`ImageField`
  ```python
  from django.db import models
  
  class Post(models.Model):
      image = models.ImageField(upload_to='forum/posts/%Y/%m/', blank=True, null=True)
  ```
- **图片处理流水线**: 使用Pillow自动处理
  ```python
  from cube_api.utils.image_processor import process_image
  
  # 压缩、裁剪、WebP转换
  processed = process_image(
      file, 
      max_width=1200, 
      quality=85, 
      crop_square=True,  # 1:1比例裁剪
      convert_webp=True  # WebP格式转换
  )
  ```
- **公式图片双字段**: 区分上传文件和路径引用
  ```python
  class FormulaSerializer(serializers.ModelSerializer):
      thumbnail_file = serializers.FileField(write_only=True)
      thumbnail_path = serializers.CharField(write_only=True)
  ```
- **URL管理**: 使用`build_image_url()`函数统一生成图片URL
- **前端上传**: 使用FormData发送文件
  ```javascript
  const formData = new FormData();
  formData.append('image', file);
  formData.append('title', title);
  formData.append('content', content);
  ```
- **前端裁剪组件**: Canvas实现1:1裁剪，支持滚轮缩放和防抖拖拽

#### Q84: 在本项目中，如何实现浏览量统计？
**回答要点**:
- **模型字段**:
  ```python
  class Formula(models.Model):
      view_count = models.IntegerField(default=0)
  ```
- **原子更新**: 使用`F()`表达式
  ```python
  from django.db.models import F
  
  def retrieve(self, request, pk=None):
      instance = self.get_object()
      instance.view_count = F('view_count') + 1
      instance.save()
      instance.refresh_from_db()
      serializer = self.get_serializer(instance)
      return APIResponse(data=serializer.data)
  ```
- **排序展示**: 按`view_count`降序排列精选公式
  ```python
  Formula.objects.order_by('-view_count')[:6]
  ```

#### Q85: 在本项目中，如何实现搜索功能？
**回答要点**:
- **数据库查询**: 使用`icontains`进行模糊搜索
  ```python
  keyword = request.query_params.get('keyword', '')
  if keyword:
      queryset = queryset.filter(Q(title__icontains=keyword) | Q(content__icontains=keyword))
  ```
- **进阶搜索**:
  - 使用`django-haystack`结合Elasticsearch
  - 支持全文搜索、分词、高亮
- **搜索优化**:
  - 添加全文索引
  - 使用缓存减少数据库查询

#### Q86: 在本项目中，如何实现邮件发送功能？
**回答要点**:
- **配置**: 在`settings.py`中配置邮件后端
  ```python
  EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
  EMAIL_HOST = 'smtp.example.com'
  EMAIL_PORT = 587
  EMAIL_USE_TLS = True
  EMAIL_HOST_USER = 'noreply@example.com'
  EMAIL_HOST_PASSWORD = 'password'
  ```
- **发送邮件**:
  ```python
  from django.core.mail import send_mail
  
  send_mail(
      subject='Welcome to ICube',
      message='Thank you for registering.',
      from_email='noreply@example.com',
      recipient_list=['user@example.com'],
      fail_silently=False
  )
  ```
- **模板邮件**:
  ```python
  from django.core.mail import EmailMultiAlternatives
  from django.template.loader import render_to_string
  
  html_content = render_to_string('email/welcome.html', {'user': user})
  msg = EmailMultiAlternatives(subject, plain_text, from_email, [email])
  msg.attach_alternative(html_content, 'text/html')
  msg.send()
  ```

### 十、开放性问题

#### Q87: 如何设计一个高并发的秒杀系统？
**回答要点**:
- **限流**: 使用Redis或Nginx限流，控制请求速率
- **库存预减**: 在Redis中预减库存，避免直接操作数据库
- **异步处理**: 使用消息队列（如Celery）处理下单请求
- **数据库优化**: 使用F表达式原子更新，添加索引
- **缓存**: 使用Redis缓存商品信息和库存
- **降级**: 高并发时降级非核心功能

#### Q88: 如何设计一个分布式ID生成器？
**回答要点**:
- **UUID**: 简单但无序，不适合数据库主键
- **雪花算法**: 64位ID，包含时间戳、机器ID、序列号
- **数据库自增**: 多库多表，设置不同起始值和步长
- **Redis**: 使用`INCR`命令生成唯一ID
- **方案选择**: 根据业务需求选择合适的方案

#### Q89: 如何设计一个消息队列系统？
**回答要点**:
- **消息模型**: 点对点、发布/订阅
- **消息持久化**: 确保消息不丢失
- **消息确认**: ACK机制，处理失败重试
- **消息顺序**: 保证消息顺序消费
- **消息积压**: 监控队列长度，动态扩容
- **常用队列**: RabbitMQ、Kafka、Redis Streams

#### Q90: 如何进行代码Review？有哪些要点？
**回答要点**:
- **代码风格**: 符合PEP8规范，命名清晰
- **逻辑正确性**: 业务逻辑是否正确
- **性能**: 是否有优化空间（N+1查询、冗余计算）
- **安全性**: 是否有SQL注入、XSS等风险
- **可读性**: 代码是否易于理解，是否有必要的注释
- **测试覆盖**: 是否有单元测试，覆盖率是否足够
- **设计模式**: 是否合理使用设计模式

#### Q91: 如何进行性能测试？有哪些工具？
**回答要点**:
- **性能指标**:
  - 响应时间（RT）
  - 吞吐量（TPS/QPS）
  - 并发数
  - 错误率
- **测试工具**:
  - **JMeter**: 功能强大，支持多种协议
  - **Locust**: Python编写，易于扩展
  - **k6**: JavaScript编写，适合开发人员
- **测试步骤**:
  1. 确定测试目标和场景
  2. 编写测试脚本
  3. 执行测试并监控
  4. 分析结果并优化

#### Q92: 如何处理线上问题？有哪些步骤？
**回答要点**:
- **应急响应**:
  1. **发现问题**: 通过监控告警发现异常
  2. **定位问题**: 查看日志、分析堆栈、排查原因
  3. **临时修复**: 紧急修复或降级处理
  4. **彻底修复**: 分析根本原因，制定修复方案
  5. **验证修复**: 测试验证，确保问题解决
  6. **复盘总结**: 记录问题、原因、解决方案，避免重复发生

#### Q93: 作为后端开发者，你认为最重要的技能是什么？
**回答要点**:
- **扎实的计算机基础**: 数据结构、算法、操作系统、网络
- **深入理解框架**: 不仅会用，还要理解原理
- **数据库设计与优化**: 索引、查询优化、事务处理
- **安全意识**: 了解常见攻击手段和防范方法
- **问题排查能力**: 快速定位和解决问题
- **代码质量**: 可读性、可维护性、测试覆盖
- **持续学习**: 关注新技术、新趋势

#### Q94: 项目中图片处理流水线是如何设计的？
**回答要点**:
- **处理流程**: 上传 → 大图预压缩 → 1:1裁剪 → WebP转换 → 质量优化
- **关键技术**: 使用Pillow库进行图片处理
  - 大图预压缩: 原图>2048px时先等比例缩小
  - 1:1裁剪: 中心裁剪为正方形
  - WebP转换: PNG/JPG自动转换为WebP格式，体积减小50%+
  - 质量优化: 默认quality=85，平衡清晰度和大小
- **双字段设计**: 区分用户上传（thumbnail_file）和公式库选择（thumbnail_path）
- **自动缩略图**: 无图片时根据公式名称和记号生成缩略图

**关键代码**:
```python
def process_image(file, max_width=1200, quality=85, crop_square=False, convert_webp=False):
    img = Image.open(file)
    # 大图预压缩
    if img.width > 2048:
        ratio = 2048 / img.width
        img = img.resize((int(img.width * ratio), int(img.height * ratio)))
    # 1:1裁剪
    if crop_square:
        min_side = min(img.width, img.height)
        left = (img.width - min_side) // 2
        img = img.crop((left, top, left + min_side, top + min_side))
    # WebP转换
    if convert_webp:
        img.save(output_path, 'WEBP', quality=quality)
```

#### Q95: 公式上传功能是如何实现的？
**回答要点**:
- **前端公式编辑器**: 
  - 点击式键盘输入（R/L/U/D/F/B等所有魔方记号）
  - 支持直接输入字符串
  - 图片来源可选：公式库选择或自己上传
  - 分类/难度/作者选择
- **后端处理逻辑**:
  - 图片上传：压缩裁剪→WebP转换→存储
  - 图片选择：直接引用公式库图片路径
  - 自动绑定目标状态：根据分类查找并绑定
  - 自动生成缩略图：无图片时生成
- **权限控制**: 管理员可编辑所有公式，普通用户仅可编辑自己上传的
- **筛选支持**: 分类、难度、作者三维联合筛选

**关键代码**:
```python
def create(self, validated_data):
    thumbnail_file = validated_data.pop('thumbnail_file', None)
    thumbnail_path = validated_data.pop('thumbnail_path', None)
    # 处理图片
    if thumbnail_file:
        processed = process_image(thumbnail_file, crop_square=True, convert_webp=True)
        validated_data['thumbnail'] = processed
    elif thumbnail_path:
        validated_data['thumbnail'] = thumbnail_path
    # 绑定目标状态
    self._bind_target_state(formula, category_id)
```



# Git相关

## 企业开发提交信息

企业开发中的提交信息（commit message）有严格的规范，好的提交信息能大幅提升团队协作效率。以下是业界通用的最佳实践：

### 一、提交信息格式（常规规范）

```
<type>(<scope>): <subject>
<空行>
<body>
<空行>
<footer>
```

#### 实际示例

```
feat(user): 添加用户登录功能

实现JWT token认证，包含登录接口和token刷新机制
添加登录状态缓存到Redis

Closes #123
```

### 二、Type 类型（必须）

| Type         | 说明                          | 示例                                      |
| ------------ | ----------------------------- | ----------------------------------------- |
| **feat**     | 新功能                        | `feat(order): 添加订单导出功能`           |
| **fix**      | 修复bug                       | `fix(cart): 修复购物车数量计算错误`       |
| **docs**     | 文档修改                      | `docs(readme): 更新部署文档`              |
| **style**    | 代码格式（不影响功能）        | `style(user): 格式化代码缩进`             |
| **refactor** | 重构（不是新功能也不是修bug） | `refactor(payment): 重构支付接口调用逻辑` |
| **perf**     | 性能优化                      | `perf(query): 优化数据库查询性能`         |
| **test**     | 测试相关                      | `test(api): 添加用户接口单元测试`         |
| **chore**    | 构建/工具变动                 | `chore(deps): 升级Django到4.2`            |
| **revert**   | 回滚提交                      | `revert: 回滚feat(user)提交`              |
| **ci**       | CI配置修改                    | `ci(github): 添加自动化部署流程`          |

### 三、Scope 范围（可选但推荐）

Django 项目中常见的 scope：

```
feat(models): 添加用户模型字段
feat(views): 实现文章列表API
feat(admin): 自定义后台管理界面
feat(serializers): 添加数据验证逻辑
feat(templates): 更新首页模板
feat(utils): 添加日期处理工具函数
fix(settings): 修复时区配置错误
chore(migrations): 合并迁移文件
```

### 四、Subject 主题（必须）

**规范要求：**

- 不超过50个字符
- 使用祈使句（动词开头）
- 首字母小写
- 结尾不加句号

**正确示例：**

```
✅ feat(user): add login validation
✅ fix(order): fix price calculation bug
✅ docs(api): update swagger documentation
```

**错误示例：**

```
❌ 更新代码（太模糊）
❌ feat(user): Added login.（过去式且大写）
❌ fix bug（缺少type和scope）
❌ feat: 修改了很多东西（不具体）
```

### 五、Body 正文（复杂修改时写）

**规范要求：**

- 每行不超过72字符
- 说明"为什么改"和"怎么改的"
- 可以多行

**示例：**

```
fix(payment): fix WeChat payment callback issue

- Add signature verification to prevent tampering
- Add idempotent processing to avoid duplicate deductions
- Improve error logging for troubleshooting

Previously, missing signature verification could lead to forged callbacks.
Now all callbacks require valid WeChat signature before processing.
```

### 六、Footer 脚注（可选）

主要用于：

1. **关联 Issue**
2. **破坏性变更说明**

```
feat(api): redesign user API interface

BREAKING CHANGE: The /user/info endpoint has been moved to /api/v1/user/profile

Closes #456, #789
```

### 七、企业常用模板

#### 模板 1：简单但规范（适合日常）

```
<type>: <subject>

- 修改点1
- 修改点2

关联单号: TASK-123
```

**示例：**

```
feat: 添加用户导出功能

- 新增导出Excel接口
- 添加导出权限控制
- 记录导出日志

关联单号: PROJ-456
```

#### 模板 2：详细版（适合重要修改）

```
<type>(<scope>): <subject>

【修改原因】
...

【修改内容】
- 修改点1
- 修改点2

【影响范围】
...

【测试情况】
- 测试点1
- 测试点2

关联Issue: #123
```

### 八、实际 Django 项目示例

#### 示例 1：新功能

```
feat(order): add order cancellation feature

- Add cancel button in order detail page
- Implement cancel_order view and URL routing
- Add order status check before cancellation (only pending orders can be cancelled)
- Send email notification after cancellation

Closes #234
```

#### 示例 2：修复 Bug

```
fix(cart): fix cart total price display error

Problem:
Cart total price doesn't update when quantity changes from 1 to 0

Solution:
Add validation to remove item when quantity becomes 0
Recalculate total after each quantity update

Affected files:
- cart/views.py
- cart/static/js/cart.js

Closes #456
```

#### 示例 3：重构

```
refactor(serializers): extract common validation logic

- Create BaseSerializer with common validators
- Reduce code duplication in UserSerializer and OrderSerializer
- Add custom validator for phone number format

No functional changes, only code organization improvement
```

#### 示例 4：性能优化

```
perf(query): optimize dashboard data query

- Add select_related to reduce N+1 queries
- Add index on order.created_at field
- Cache dashboard data for 5 minutes

Query time reduced from 3.2s to 0.8s
```

### 九、团队协作建议

#### 1. 统一使用工具

```bash
# 安装 commitizen
pip install commitizen

# 使用 cz commit 交互式填写
cz commit

# 或使用 git cz（需要安装）
git cz
```

#### 2. 配置 Git 钩子验证

```bash
# .git/hooks/commit-msg
#!/bin/bash
# 验证提交信息格式
```

#### 3. 分支命名规范

```
feature/user-login    # 新功能分支
bugfix/cart-error     # 修复分支
hotfix/payment-crash  # 紧急修复
release/v1.2.0        # 发布分支
```

#### 4. Pull Request 标题规范

PR 标题使用相同格式，方便生成 Changelog：

```
feat(user): add email verification
```

### 十、快速参考表

| 场景         | Type  | 示例                                      |
| ------------ | ----- | ----------------------------------------- |
| 新增接口     | feat  | `feat(api): add user register endpoint`   |
| 修数据库模型 | feat  | `feat(models): add user profile model`    |
| 修bug        | fix   | `fix(auth): fix token expiration`         |
| 改配置       | chore | `chore(settings): update CORS settings`   |
| 改文档       | docs  | `docs(readme): update installation guide` |
| 优化性能     | perf  | `perf(query): add database index`         |
| 加测试       | test  | `test(user): add login test cases`        |

### 十一、工具推荐

1. **Commitizen** - 交互式提交工具
2. **Commitlint** - 提交信息检查工具
3. **Standard Version** - 自动生成 CHANGELOG
4. **GitMoji** - 使用 emoji 增强可读性（非正式但流行）

---

## 部署

### Docker Compose 部署

项目使用根目录的 `docker-compose.yml` 和 `deploy.sh` 完成生产部署。Docker Compose v2 直接使用 Compose Specification，文件不再声明已过时的 `version` 字段。

#### 服务构成

| 服务    | 镜像或构建方式      | 端口                  | 说明                                                  |
| ------- | ------------------- | --------------------- | ----------------------------------------------------- |
| `db`    | `mysql:8.0`         | `127.0.0.1:3306:3306` | MySQL 数据库，仅允许宿主机直连；远程管理通过 SSH 隧道 |
| `redis` | `redis:7-alpine`    | `6379`                | 缓存、JWT 黑名单和 Session                            |
| `api`   | `./cube_api`        | 容器内 `8000`         | Django + Gunicorn API                                 |
| `front` | `./cube_front`      | 容器内 `80`           | 内置 Nginx，提供 Vue 构建产物                         |
| `nginx` | `nginx:1.28-alpine` | `80/443`              | 公网网关；当前站点配置监听 HTTP 80                    |

API 通过 `condition: service_healthy` 等待 MySQL 健康检查通过后启动；`start_period: 45s` 为首次数据库初始化预留时间。

所有服务加入 `icube_network`，容器之间使用 Compose 服务名通信：

```text
浏览器
  ├─ /api/*    → nginx → api:8000
  ├─ /media/*  → nginx → ./cube_api/media
  ├─ /static/* → nginx → collected_static
  └─ /*        → nginx → front:80 → Vue SPA
```

#### 镜像构建

- 后端采用多阶段构建：builder 阶段将 Python 依赖构建为 wheel；runtime 阶段只安装运行库、依赖和项目代码。
- API 容器启动时先执行 `collectstatic`，再以 3 个 worker 启动 Gunicorn，生产环境不使用 `--reload`。
- 前端采用 Node + Nginx 多阶段构建：Node 阶段执行 `npm ci`、`npm run build`，Nginx 运行阶段只保留 `dist`。
- 前端 `dist` 直接写入镜像，不使用 `front_dist` 卷，也不需要本地构建或提交 `cube_front/dist`。

#### 数据持久化

| 卷或目录           | 用途                                    |
| ------------------ | --------------------------------------- |
| `mysql_data`       | MySQL `/var/lib/mysql` 数据             |
| `redis_data`       | Redis `/data` 数据                      |
| `collected_static` | API 与网关 Nginx 共享的 Django 静态文件 |
| `./cube_api/media` | API 与网关 Nginx 共享的宿主机媒体目录   |

`init_data.sql` 挂载到 `/docker-entrypoint-initdb.d/02_init_data.sql`，只在 `mysql_data` 为空时执行。已有数据库的结构升级由 Django migration 完成。

#### 生产环境变量

服务器根目录 `.env` 至少配置：

```env
ALLOWED_HOSTS=服务器IP或域名,localhost
ALLOWED_ORIGIN=服务器IP或域名
SERVER_HOST=服务器IP或域名
DB_PASSWORD=icube123
```

`ALLOWED_ORIGIN` 和 `SERVER_HOST` 不包含协议。Compose 使用 `${DB_PASSWORD:-icube123}`，未设置时继续使用默认密码。`.env` 中包含 `$` 的值应使用单引号，避免被 Compose 当作变量插值。

#### 一键部署

```bash
# 首次部署或 Docker 配置、前后端同时更新
bash deploy.sh full

# 仅更新后端：构建 API、执行 migration、启动 API、重启 Nginx
bash deploy.sh api

# 仅更新前端：构建 front、启动 front、重启 Nginx
bash deploy.sh front
```

不传参数时默认使用 `full`。`api` 和 `front` 只适用于已经完成过全量部署的服务器。脚本使用普通部署用户运行，不要执行 `sudo bash deploy.sh`。

脚本主要流程：

1. 检查 Git、Docker、Compose、`.env` 和健康检查主机。
2. 执行 `git pull --ff-only`，本地已跟踪文件存在冲突修改时由 Git 拒绝覆盖。
3. 按模式构建镜像；`api` 不构建前端，`front` 不停止 API、不执行 migration。
4. `full` 和 `api` 等待 MySQL 健康检查通过后执行 migration。
5. 重建目标容器后重启网关 Nginx，刷新上游容器地址。
6. 检查容器状态、HTTP、MySQL healthcheck 和 Redis PING；失败时输出最近日志。

#### 运维命令

```bash
docker compose ps
docker compose logs -f api nginx
# 仅重启现有 API 容器，不会加载新代码
docker compose restart api
docker compose exec api python manage.py createsuperuser
```

禁止执行 `docker compose down -v`，该命令会删除 `mysql_data` 和 `redis_data`。当前 Redis 仍映射到宿主机 `6379`；生产环境若无需宿主机直连，应移除端口映射或限制为 `127.0.0.1:6379:6379`。



## gitleaks

Gitleaks 是一款用于扫描 Git 仓库和文件系统中硬编码密钥、密码等敏感信息的工具。它通过正则表达式和熵值分析来识别潜在的秘密。

下面是它的基本用法：

### 📥 1. 安装 Gitleaks

根据你的操作系统，可以使用包管理器或直接下载二进制文件进行安装。

| 操作系统                  | 安装命令 / 方法                                              |
| :------------------------ | :----------------------------------------------------------- |
| **macOS**                 | `brew install gitleaks`                                      |
| **Linux (Ubuntu/Debian)** | `sudo apt install gitleaks`                                  |
| **Linux (其他发行版)**    | 可以从 [GitHub Releases](https://github.com/gitleaks/gitleaks/releases) 下载二进制文件，或使用 `wget` 下载并解压到 `PATH` 中，例如： `wget https://github.com/gitleaks/gitleaks/releases/download/v8.21.2/gitleaks_8.21.2_linux_x64.tar.gz` `tar -xzf gitleaks_8.21.2_linux_x64.tar.gz` `sudo mv gitleaks /usr/local/bin/` |
| **Windows**               | 使用 Chocolatey: `choco install gitleaks` 使用 Scoop: `scoop install gitleaks` |
| **Docker**                | `docker pull ghcr.io/gitleaks/gitleaks:latest`               |

可直接github下载对应安装包解压并配置环境，安装后，可以用 `gitleaks --version` 命令验证是否成功。

### 🎯 2. 核心使用场景与命令

Gitleaks 支持扫描 Git 历史记录、本地目录或管道输入。根据场景选择对应命令即可。

#### 扫描整个 Git 仓库的历史记录

这是最常用的场景，会检查仓库所有提交历史中是否泄露过秘密。

bash

```
gitleaks git /path/to/your/repo
# 或者，如果你已经位于仓库根目录
gitleaks git .
```



**注意**：在较新的版本中，`gitleaks detect` 命令已被弃用，推荐使用 `gitleaks git` 。

#### 扫描本地文件夹（不包含 Git 历史）

如果你只想扫描当前工作目录的文件，而不想追溯历史，可以使用 `dir` 命令。

bash

```
gitleaks dir /path/to/your/folder
```

#### 在 Pre-commit Hook 中扫描暂存区

为了防止将秘密提交到仓库，可以在 `pre-commit` 钩子中，将 `git` 的暂存区内容通过管道传给 Gitleaks 进行扫描。

bash

```
git diff --cached | gitleaks stdin --no-banner
```



如果扫描出问题，这个钩子会阻止本次提交。

### ⚙️ 3. 常用选项与配置

你可以通过以下参数来控制扫描行为和输出结果。

| 参数                                | 说明                                                         |
| :---------------------------------- | :----------------------------------------------------------- |
| `--config`                          | 指定一个自定义的 TOML 格式配置文件，用于定义更精准的规则或忽略特定内容。配置文件可以继承默认规则。 |
| `--report-format` & `--report-path` | 将扫描结果导出为文件，支持 `json`、`csv`、`sarif` 等格式。例如：`--report-format json --report-path report.json` 。 |
| `--redact`                          | 在终端输出中隐藏匹配到的秘密内容，用 `***` 代替，防止在屏幕上泄露敏感信息。 |
| `--log-opts`                        | 传递给 `git log` 的参数，用于限制扫描的提交范围。例如，`--log-opts="--since=2024-01-01"` 只扫描今年以来的提交。 |
| `--no-git`                          | 强制将扫描目录视为普通文件夹，不读取 Git 历史，等同于 `dir` 命令的效果。 |
| `--exit-code`                       | 当发现秘密时，Gitleaks 默认返回非零退出码（`1`），这会导致 CI/CD 任务失败。你可以通过此参数修改退出码，例如 `--exit-code 2` 。 |

### ⚠️ 4. 发现秘密后怎么办

如果 Gitleaks 在历史记录中发现了秘密，单纯删除当前文件是不够的，因为秘密依然存在于 Git 历史中。

1. **立即处理**：使用 **BFG Repo-Cleaner** 或 `git filter-repo` 等工具，从整个 Git 历史中彻底清除该秘密文件或字符串。
2. **强制推送**：清理完成后，需要强制推送到远程仓库（`git push --force --all`）。
3. **更换密钥**：因为信息可能已被公开，最佳实践是立即在服务端更换/作废这个密钥，确保安全。

### ⚙️ 5. 进阶配置

Gitleaks 的强大之处在于其高度可定制的配置（`.gitleaks.toml`）。

- **自定义规则**：你可以为特定的内部 API 密钥或令牌格式添加规则。

  toml

  ```
  [[rules]]
  id = "my-custom-rule"
  description = "My company's secret key"
  regex = '''MY_SECRET_[a-zA-Z0-9]{20}'''
  ```

  

- **忽略误报（False Positives）**：可以在全局或在特定规则内添加 `allowlists`，来忽略特定的路径、文件或提交。

  toml

  ```
  [[allowlists]]
  description = "Ignore test files"
  paths = ['''**/*_test\.go''', '''test/.*\.json''']
  ```

  

  配置文件的更完整说明可以参考官方默认配置。

无论是日常开发还是将仓库公开前的审计，将 Gitleaks 集成到工作流中（特别是`pre-commit`钩子）都是一个很好的习惯，能从源头避免敏感信息泄露。
