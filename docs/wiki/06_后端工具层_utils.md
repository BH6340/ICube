## 6. 后端工具层（utils）

### 6.1 common\_response.py — 统一响应（[common\_response.py](/code/cube_api/cube_api/utils/common_response.py)）

| 类                              | 继承             | 用途                       |
| ------------------------------ | -------------- | ------------------------ |
| `APIResponse`                  | DRF `Response` | 通用响应 `{code, msg, data}` |
| `PaginatedResponse`            | APIResponse    | 适配分页器实例                  |
| `PageNumberPaginationResponse` | APIResponse    | 适配 page 对象               |

**状态码约定**：

| code | 含义              | HTTP status |
| ---- | --------------- | ----------- |
| 100  | 请求成功（默认）        | 200         |
| 400  | 请求参数错误          | 200         |
| 403  | 权限不足            | 200         |
| 404  | 资源不存在           | 200         |
| 503  | 服务不可用（如支付宝配置异常） | 200         |
| 998  | 业务逻辑错误          | 跟随 DRF      |
| 999  | 系统内部错误          | 500         |

**响应格式**：

```json
{"code": 100, "msg": "请求成功", "data": {...}}
```

分页响应：

```json
{"code": 100, "msg": "success", "data": {"count": 100, "next": "?page=2", "previous": null, "results": [...]}}
```

前端拦截器将 `code !== 100` 视为错误。

### 6.2 common\_exception.py — 统一异常处理（[common\_exception.py](/code/cube_api/cube_api/utils/common_exception.py)）

核心函数 `common_exception_handler(exc, context)`（[L35](/code/cube_api/cube_api/utils/common_exception.py#L35-L127)）：

1. 提取上下文（user email/Anonymous、path、method、view 类名）
2. 调用 DRF 原生 `drf_exception_handler` 获取初步 response
3. **情况 A：DRF 已处理**（业务错误）：
   - `ValidationError` → 取第一个字段第一个错误，格式 `field: error`
   - 其他 dict → 取 detail；list → 取 `[0]`；其他 → str()
   - `logger.warning` + 结构化上下文 → `APIResponse(code=998, msg, status=response.status_code)`
4. **情况 B：未捕获异常**（系统错误）：
   - `logger.error` + 上下文 → `APIResponse(code=999, msg="系统开小差了，请稍后再试", status=500)`
   - 屏蔽敏感堆栈，仅返回友好提示

**DRF 原生 `exception_handler` 已处理的异常类型**（情况 A 范围）

DRF 的 `exception_handler`（`rest_framework/views.py` L72）通过 `isinstance` 判断异常类型并构造响应，处理链路如下：

1. **类型转换**：Django 内置的 `Http404` 被转换为 DRF `NotFound`，Django `PermissionDenied` 被转换为 DRF `PermissionDenied`，统一走 DRF 异常分支
2. **`APIException` 及其子类**：根据异常实例的 `status_code` 属性返回对应 HTTP 状态码；detail 为 list/dict 时原样返回，其他包装为 `{'detail': ...}`；附带 `WWW-Authenticate`（认证异常）或 `Retry-After`（限流异常）响应头
3. **认证异常预处理**（在 `APIView.handle_exception` 中）：`NotAuthenticated`/`AuthenticationFailed` 若视图未提供 `WWW-Authenticate` 头，状态码会被强制改为 403（避免浏览器弹出 HTTP Basic 认证框）
4. **其他异常**：返回 `None`，由 `raise_uncaught_exception` 重新抛出，最终落入情况 B

DRF 内置的 11 个 `APIException` 子类（`rest_framework/exceptions.py`）：

| 异常类                    | HTTP     | default\_code           | 触发场景                                              |
| ---------------------- | -------- | ----------------------- | ------------------------------------------------- |
| `ParseError`           | 400      | parse\_error            | 请求体解析失败（如非法 JSON、缺字段）                             |
| `ValidationError`      | 400      | invalid                 | 序列化器/字段校验失败（`is_valid(raise_exception=True)`）      |
| `AuthenticationFailed` | 401/403  | authentication\_failed  | 认证凭据无效（无 `WWW-Authenticate` 头则降级 403）             |
| `NotAuthenticated`     | 401/403  | not\_authenticated      | 未提供认证凭据（无 `WWW-Authenticate` 头则降级 403）            |
| `PermissionDenied`     | 403      | permission\_denied      | 已认证但无权限访问该资源（如 `IsOwnerOrReadOnly` 校验失败）          |
| `NotFound`             | 404      | not\_found              | 路由匹配失败或 `get_object_or_404` 未找到对象                 |
| `MethodNotAllowed`     | 405      | method\_not\_allowed    | 视图不支持该 HTTP 方法（如 POST 到 `ReadOnlyModelViewSet`）   |
| `NotAcceptable`        | 406      | not\_acceptable         | 请求 `Accept` 头无法被任一 renderer 满足                    |
| `UnsupportedMediaType` | 415      | unsupported\_media\_type | `Content-Type` 不被任一 parser 支持（如纯文本提交 JSON 接口）     |
| `Throttled`            | 429      | throttled               | 请求频率超过限流阈值，响应头附带 `Retry-After`                    |
| `APIException`（基类）     | 500      | error                   | 自定义异常基类，子类未指定 `status_code` 时默认 500               |

此外 Django 内置的两类异常会被转换为 DRF 异常后再处理：

- `django.http.Http404` → DRF `NotFound`（404）
- `django.core.exceptions.PermissionDenied` → DRF `PermissionDenied`（403）

**项目异常分支表**：

| 异常类型                              | 分支 | code | HTTP status | 日志级别    | 处理说明                                       |
| --------------------------------- | -- | ---- | ----------- | ------- | ------------------------------------------ |
| `ValidationError`                 | A  | 998  | 400         | warning | 取首个字段首个错误，格式 `field: error`               |
| `ParseError`                      | A  | 998  | 400         | warning | 请求体解析失败                                    |
| `AuthenticationFailed`/`NotAuthenticated` | A  | 998  | 401/403     | warning | 认证失败，状态码由 DRF 决定                           |
| `PermissionDenied`                | A  | 998  | 403         | warning | 权限不足（含 Django `PermissionDenied` 转换）       |
| `NotFound`                        | A  | 998  | 404         | warning | 资源不存在（含 Django `Http404` 转换）               |
| `MethodNotAllowed`                | A  | 998  | 405         | warning | HTTP 方法未被 Router 绑定到 action（详见下方场景表）       |
| `NotAcceptable`                   | A  | 998  | 406         | warning | Accept 头协商失败                               |
| `UnsupportedMediaType`            | A  | 998  | 415         | warning | Content-Type 不支持                           |
| `Throttled`                       | A  | 998  | 429         | warning | 限流触发，响应头附带 `Retry-After`                   |
| `APIException` 其他子类               | A  | 998  | 跟随 DRF      | warning | 自定义 API 异常                                 |
| 其他 Python 异常                      | B  | 999  | 500         | error   | 未捕获异常，屏蔽堆栈，返回友好提示                          |

**`MethodNotAllowed` 常见触发场景**（结合本项目 ViewSet）

DRF ViewSet 通过 `ViewSetMixin.as_view(actions={...})` 把 HTTP 方法绑定到 action 方法名（`viewsets.py` L116-L118）。Router 根据 ViewSet 继承的 Mixin 自动生成 list/detail 两份绑定；**未被绑定的 HTTP 方法属性不存在，dispatch 会走 `http_method_not_allowed` → 抛 `MethodNotAllowed` → 405**。

| 场景 | 触发请求 | 结果 | 原因 / 正确写法 |
| --- | --- | --- | --- |
| 1. ReadOnlyModelViewSet 上发写操作 | `POST /api/forum/tags/` | 405 | `TagViewSet`([forum/views.py#L580](/code/cube_api/cube_api/apps/forum/views.py#L580)) 无 CreateModelMixin；同类还有 `ProductCategoryViewSet`/`ProductViewSet`/`BannerViewSet`/`NavigationMenuViewSet`/`ProfileDetailView` |
| 1. ReadOnlyModelViewSet 上发写操作 | `DELETE /api/home/banners/1/` | 405 | 无 DestroyModelMixin |
| 1. ReadOnlyModelViewSet 上发写操作 | `PUT /api/shop/products/123/` | 405 | 无 UpdateModelMixin |
| 2. 写请求漏掉 `/{id}`（发到 list 路由） | `PUT /api/timer/records/` | 405 | 应 `PUT /api/timer/records/123/`（PUT/PATCH/DELETE 只绑 detail 路由） |
| 2. 写请求漏掉 `/{id}`（发到 list 路由） | `PATCH /api/forum/posts/` | 405 | 应 `PATCH /api/forum/posts/123/` |
| 2. 写请求漏掉 `/{id}`（发到 list 路由） | `DELETE /api/shop/cart/` | 405 | 应 `DELETE /api/shop/cart/789/` |
| 3. list 接口用错 method | `POST /api/shop/products/` | 405 | `ProductViewSet` 为 ReadOnly，应 `GET`；对比 `POST /api/timer/records/` ✅（`TimerRecordViewSet` 为 ModelViewSet） |
| 4. GenericViewSet 无标准 action | `GET /api/users/` / `POST /api/users/` | 405 | `AuthViewSet`([accounts/views.py#L33](/code/cube_api/cube_api/apps/accounts/views.py#L33)) 只含自定义 @action，应走 `POST /api/users/login` 等 |
| 5. 自定义 `http_method_names` | `DELETE /api/formula/formulas/1/`（假设限定 `['get','post']`） | 405 | ViewSet 上 `http_method_names` 未列出该方法 |
| 6. `@action(methods=[...])` 限定 | `GET /api/formula/formulas/1/bookmark`（假设 `methods=['post']`） | 405 | @action 装饰器未允许 GET，应 `POST` |

**排查 checklist**：

1. 查 ViewSet 基类：是否用了 `ReadOnlyModelViewSet`（看 `apps/<module>/views.py` 类继承）
2. 查 URL 是 list 还是 detail：PUT/PATCH/DELETE 必须带 `/{id}/`
3. 查 Router 注册：`urls.py` 中 `router.register(...)` 的 prefix 与 trailing slash（accounts 用 `trailing_slash=False`，见 [accounts/urls.py#L8](/code/cube_api/cube_api/apps/accounts/urls.py#L8)）
4. 查 `@action` 装饰器：`methods=[...]` 是否漏写
5. 查 `http_method_names`：是否在 ViewSet 上被覆盖
6. 查 `@permission_classes` / `@method_decorator` 是否拦截后误返回 405

### 6.3 common\_pagination.py — 统一分页（[common\_pagination.py](/code/cube_api/cube_api/utils/common_pagination.py)）

| 类                           | page\_size | max\_page\_size | 用途    |
| --------------------------- | ---------- | --------------- | ----- |
| `UnifiedPagination`         | 20         | 100             | 默认分页器 |
| `LargeResultsSetPagination` | 50         | 500             | 大数据集  |
| `SmallResultsSetPagination` | 10         | 50              | 小数据集  |

重写 `get_paginated_response(data)` 返回 `APIResponse(data={count, next, previous, results})`，与统一响应格式一致。同时提供 `get_paginated_response_schema(schema)` 为 drf-spectacular 生成正确 schema。

### 6.4 image\_url.py — 图片 URL 标准化（[image\_url.py](/code/cube_api/cube_api/utils/image_url.py)）

```python
def build_image_url(relative_path, absolute=False)
```

**处理逻辑**（[L57-L102](/code/cube_api/cube_api/utils/image_url.py#L57-L102)）：

1. 空路径 → 返回 `''`
2. `isinstance(relative_path, FieldFile)` → 取 `.name`（**避免触发 .path 属性计算**）；`ImportError` 与其他异常分离捕获，`ImportError` 走字符串转换兜底，非 `ImportError` 在确认类型后再转换
3. 完整 URL（http/https 开头）→ 原样返回
4. 补 `/` 前缀
5. 补 `/media/` 前缀（已存在则跳过）
6. `absolute=True` 时拼接 `settings.SITE_DOMAIN`

**关键约束**（项目规则）：

- **禁止** **`hasattr(relative_path, 'path')`** —— 头像路径以 `/` 开头时会触发 `SuspiciousFileOperation`
- 改用 `isinstance(FieldFile)` 检查后访问 `.name`

**默认返回相对路径**的原因：浏览器 Private Network Access (PNA) 会阻止公网域名直接访问 localhost 图片资源。

**浏览器 PNA 策略，可以理解为一道由浏览器设置的“防火墙”，目的是为了防止公共网站偷偷访问你家里的路由器、打印机等内网设备。**

PNA 是 **Private Network Access** 的缩写。它的核心目的是**保护用户免受跨站请求伪造（CSRF）攻击**，防止恶意网站利用你的浏览器作为跳板，去访问和控制你内网中的设备。简单来说，就是避免“请君入瓮”式的攻击。

**💡 为什么需要 PNA？**

想象一下，你同时打开了银行网站和一个恶意网页。如果没有 PNA，这个恶意网页就可以发送请求给你的路由器（IP 通常是 `192.168.1.1`），试图用默认密码登录并篡改你的DNS设置。PNA 策略就是为了阻断这种来自“公共网络”对“私有网络”的非法访问

**🔧 PNA 是怎么工作的**？

当浏览器（如Chrome、Edge）发现一个来自公共网站的请求，要访问一个私有IP地址（如 `192.168.x.x`）或本地地址（如 `127.0.0.1`）时，就会启动 PNA 检查。

它主要通过**预检请求（Preflight Request）** 来验证权限：

1. 浏览器会在发送真实请求前，先发送一个 `OPTIONS` 预检请求，并带上一个特殊头部：`Access-Control-Request-Private-Network: true`。
2. 目标服务器必须明确同意这个请求，在响应中返回头部：`Access-Control-Allow-Private-Network: true`。
3. 如果服务器没有返回这个头，或者返回错误，浏览器就会拦截这个请求，并在开发者工具的控制台里报错，就像我们在搜索结果里看到的真实案例一样。

**🧭 PNA 如何判断“公共”和“私有”？**

浏览器根据 IP 地址范围来判断一个请求是否属于私有网络访问，它把IP地址空间分为了三类：

| IP 地址空间        | 典型示例                          | 隐私级别 |
| :----------------- | :-------------------------------- | :------- |
| **公共 (Public)**  | 全球互联网上的任何公网IP          | 最低     |
| **私有 (Private)** | `192.168.0.0/16`, `10.0.0.0/8` 等 | 中等     |
| **本地 (Local)**   | `127.0.0.1` (localhost), `::1`    | 最高     |

PNA 规则的核心就是：**一个网站只能访问与其隐私级别相同或更低级别的网络资源**。

### 6.5 image\_processor.py — 图像处理（[image\_processor.py](/code/cube_api/cube_api/utils/image_processor.py)）

依赖 Pillow。

| 函数                           | 签名                                                                                           | 功能                               |
| ---------------------------- | -------------------------------------------------------------------------------------------- | -------------------------------- |
| `compress_image`             | `(file, max_width=1200, max_height=1200, quality=85, output_format='JPEG')`                  | 缩放压缩；RGBA/LA 转 JPEG 填白；LANCZOS   |
| `convert_to_webp`            | `(file, quality=85)`                                                                         | 转 WebP（有损）                       |
| `crop_to_square`             | `(file)`                                                                                     | 中心裁剪 1:1；透明输出 PNG，否则 JPEG        |
| `process_image`              | `(file, max_width=1200, max_height=1200, quality=85, crop_square=False, convert_webp=False)` | 统一入口                             |
| `generate_formula_thumbnail` | `(formula_name, formula_notation, size=512)`                                                 | 无上传图时自动生成文字缩略图：白底+公式名+记号，输出 WebP |

所有函数返回 `BytesIO`，调用方负责 `seek(0)` 后写入文件存储。

**🆚 WebP vs JPEG vs PNG（实战对比）**

| 对比维度          | JPEG                   | PNG                | WebP                                   |
| :---------------- | :--------------------- | :----------------- | :------------------------------------- |
| **照片场景**      | 基准（100% 体积）      | 体积过大（5~10倍） | **约 75% 体积**，画质几乎一样          |
| **图标/截图场景** | 不支持透明，有压缩噪点 | 基准（100% 体积）  | **约 50% 体积**，完全无损              |
| **透明背景**      | ❌ 不支持               | ✅ 支持             | ✅ 支持（体积更小）                     |
| **动画**          | ❌ 不支持               | ❌ 不支持           | ✅ 支持（体积比 GIF 小 60%+）           |
| **浏览器兼容性**  | 100% 所有浏览器        | 100% 所有浏览器    | **95%+**（IE 不支持，Safari 14+ 支持） |

***

| 图片类型                                       | 推荐质量        | 原因                                 |
| :--------------------------------------------- | :-------------- | :----------------------------------- |
| **公式缩略图**（`generate_formula_thumbnail`） | `quality=85`    | 文字清晰，体积小，完美适配           |
| **用户上传的公式图**（`process_image`）        | `quality=82-85` | 公式通常有文字和线条，需要较高清晰度 |
| **用户上传的头像/封面图**                      | `quality=80`    | 照片对压缩容忍度高，80 足够          |
| **后台管理的预览缩略图**                       | `quality=75`    | 仅用于列表预览，加载速度优先         |
| **前端展示的大图（详情页）**                   | `quality=85`    | 用户会细看，需要保证清晰度           |

`buffer.seek(0)` 的意思就是**把“文件指针”拨回到开头**。

你可以把它想象成一个**磁带或者播放进度条**：

- 当你往 `buffer` 里写入数据（比如保存了一张图片）后，这个“播放头”会停在数据的**末尾**。
- 此时如果有人（比如 Django）去读取这个 `buffer`，他会从末尾开始读，结果什么都读不到，或者读到一堆空白。
- `buffer.seek(0)` 就是把这个“播放头”**重置到开头**，这样后续的读取操作就能从头开始拿到完整的数据了。
