## 5. 后端配置层（settings）

### 5.1 dev.py — 基础配置（[dev.py](/code/cube_api/cube_api/settings/dev.py)）

`prod.py` 通过 `from .dev import *` 继承此文件并覆盖部分配置，dev.py 是所有运行环境的**基础配置**。文件按 11 个段落组织（顶部注释 [L7-L18](/code/cube_api/cube_api/settings/dev.py#L7-L18) 已列出），每段由独立的 `# =====` 分隔。

#### 路径配置（[L32-L50](/code/cube_api/cube_api/settings/dev.py#L32-L50)）

| 配置项                                  | 行号     | 作用                                                              |
| ------------------------------------ | ------ | --------------------------------------------------------------- |
| `BASE_DIR`                           | L36    | `Path(__file__).resolve().parent.parent.parent` → `cube_api/`（含 manage.py） |
| `sys.path.insert(cube_api/cube_api/)` | L40    | 让 `import utils`、`from settings.xxx` 可直接导入                     |
| `APPS_DIR + sys.path.insert`         | L44-L46 | 让 `apps.xxx` 也能以 apps 子目录方式被识别（双导入路径）                          |
| `sys.path.insert(BASE_DIR)`          | L50    | 统一 manage.py 与服务进程的导入行为                                         |

#### 安全配置（[L52-L67](/code/cube_api/cube_api/settings/dev.py#L52-L67)）

| 配置项             | 开发值                                              | 说明                                       |
| --------------- | ------------------------------------------------ | ---------------------------------------- |
| `SECRET_KEY`    | `django-insecure-...`（固定值）                       | 生产环境必须由 `os.getenv('SECRET_KEY')` 覆盖    |
| `DEBUG`         | `True`                                           | 开发暴露详细错误页；生产必须 `False`                   |
| `ALLOWED_HOSTS` | `['*']`                                          | 开发接受任意 Host；prod 改为白名单                   |
| `SITE_DOMAIN`   | `os.getenv('SITE_DOMAIN', 'http://localhost:8000')` | 生成图片、邮件等绝对 URL 时使用，prod 覆盖              |

#### 应用配置（[L71-L96](/code/cube_api/cube_api/settings/dev.py#L71-L96)）

`INSTALLED_APPS` 注册顺序：

1. **`unfold` + `unfold.contrib.filters`** —— 必须置于 Django 内置应用之前，否则 Tailwind 主题覆盖失效
2. Django 内置：`admin/auth/contenttypes/sessions/messages/staticfiles`
3. 第三方：`corsheaders/rest_framework/rest_framework_simplejwt/drf_spectacular`
4. 业务应用：`apps.home/accounts/forum/formula/shop/timer`（6 个业务模块）

#### 中间件配置（[L100-L117](/code/cube_api/cube_api/settings/dev.py#L100-L117)）

| 顺序 | 中间件                                  | 作用                                       |
| -- | ------------------------------------ | ---------------------------------------- |
| 1  | `corsheaders.middleware.CorsMiddleware` | **必须靠前**，确保短路响应和错误响应也能附加 CORS 头         |
| 2  | `SecurityMiddleware`                  | 安全相关 HTTP 头                              |
| 3  | `SessionMiddleware`                   | 会话管理                                     |
| 4  | `CommonMiddleware`                    | URL 重写、内容类型                              |
| 5  | `CsrfViewMiddleware`                  | 防 CSRF                                   |
| 6  | `AuthenticationMiddleware`            | 将 user 附加到 request                       |
| 7  | `MessageMiddleware`                   | 消息框架                                     |
| 8  | `XFrameOptionsMiddleware`             | 点击劫持防护                                   |

> `X_FRAME_OPTIONS` 在 [L424](/code/cube_api/cube_api/settings/dev.py#L424) 被覆盖为 `'SAMEORIGIN'`，允许 Unfold 同源嵌入。

#### 模板与会话（[L123-L161](/code/cube_api/cube_api/settings/dev.py#L123-L161)）

**模板**（[L123-L136](/code/cube_api/cube_api/settings/dev.py#L123-L136)）：`DIRS=[BASE_DIR/'templates']`、`APP_DIRS=True`、context_processors 为 `request/auth/messages` 三件套。

**Session**（[L153-L158](/code/cube_api/cube_api/settings/dev.py#L153-L158)）：

| 配置项                          | 值                  | 作用                              |
| ---------------------------- | ------------------ | ------------------------------- |
| `SESSION_ENGINE`             | `backends.cache`   | Session 存入 default 缓存（Redis）     |
| `SESSION_CACHE_ALIAS`        | `default`          | 多实例可共享登录态                       |
| `SESSION_COOKIE_AGE`         | `3600 * 24`（1 天）   | Session 有效期                     |
| `SESSION_SAVE_EVERY_REQUEST` | `True`             | 每次请求刷新过期时间（滑动过期）                |

#### 数据库配置（[L163-L190](/code/cube_api/cube_api/settings/dev.py#L163-L190)）

环境变量优先（[L166-L170](/code/cube_api/cube_api/settings/dev.py#L166-L170)），未设置时使用本地默认值：

| 变量           | 默认值          |
| ------------ | ------------ |
| `DB_NAME`    | `icube`      |
| `DB_USER`    | `icube_api`  |
| `DB_PASSWORD`| `icube123?`  |
| `DB_HOST`    | `localhost`  |
| `DB_PORT`    | `3306`       |

**测试模式自动切换 SQLite 内存库**（[L186-L190](/code/cube_api/cube_api/settings/dev.py#L186-L190)）：

```python
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # 内存数据库，速度最快
    }
```

数据库随测试进程销毁，不写入本地 MySQL。

#### Redis 配置（[L192-L233](/code/cube_api/cube_api/settings/dev.py#L192-L233)）

**公共连接选项 `REDIS_BASE_OPTIONS`**（[L195-L205](/code/cube_api/cube_api/settings/dev.py#L195-L205)）：

| 选项                       | 值                                              | 作用                          |
| ------------------------- | ---------------------------------------------- | --------------------------- |
| `CLIENT_CLASS`            | `django_redis.client.DefaultClient`            | 默认客户端                       |
| `CONNECTION_POOL_CLASS`  | `redis.BlockingConnectionPool`                 | 连接池满时等待空闲连接                 |
| `max_connections`         | 50                                             | 连接池上限                       |
| `timeout`                 | 20                                             | 获取空闲连接最多等待 20 秒（非网络超时）      |
| `SERIALIZER`              | `django_redis.serializers.json.JSONSerializer` | 缓存值必须 JSON 可序列化             |

> 上方 `CACHES`（[L142-L150](/code/cube_api/cube_api/settings/dev.py#L142-L150)）是兼容保留的初始声明，会被下方分支完全覆盖。

**测试分支**（[L208-L222](/code/cube_api/cube_api/settings/dev.py#L208-L222)）—— `'test' in sys.argv or 'pytest' in sys.modules`：

| 配置项                | 值                              |
| ------------------ | ------------------------------ |
| `LOCATION`         | `redis://127.0.0.1:6379/3`    |
| `KEY_PREFIX`       | `icube_test`                   |
| `TIMEOUT`          | 300（5 分钟）                      |
| `PASSWORD_HASHERS` | `[MD5PasswordHasher]`（仅测试用）   |

**非测试分支**（[L225-L233](/code/cube_api/cube_api/settings/dev.py#L225-L233)）：

| 配置项          | 值                              |
| ------------ | ------------------------------ |
| `LOCATION`   | `redis://127.0.0.1:6379/1`    |
| `KEY_PREFIX` | `icube`                        |
| `TIMEOUT`    | 86400（24 小时）                   |

> 测试环境（`_IS_TEST = 'test' in sys.argv or 'pytest' in sys.modules`）使用 `LocMemCache`（Django 内置内存缓存）替代 RedisCache，无需真实 Redis 服务；`get_redis_connection` 返回 `fakeredis.FakeRedis()` 实例模拟 Redis 直连命令；`MD5PasswordHasher` 不可用于真实用户密码。

#### 密码验证（[L237-L256](/code/cube_api/cube_api/settings/dev.py#L237-L256)）

`AUTH_PASSWORD_VALIDATORS` 启用 4 个内置验证器：`UserAttributeSimilarityValidator`、`MinimumLengthValidator`、`CommonPasswordValidator`、`NumericPasswordValidator`。

#### 国际化与静态/媒体（[L258-L279](/code/cube_api/cube_api/settings/dev.py#L258-L279)）

**国际化**：

| 配置项            | 值               | 说明                              |
| -------------- | --------------- | ------------------------------- |
| `LANGUAGE_CODE`| `zh-hans`       | 简体中文                            |
| `TIME_ZONE`    | `Asia/Shanghai` | 默认时区                            |
| `USE_I18N`     | `True`          | 启用国际化翻译                         |
| `USE_TZ`       | **`False`**     | **使用本地时间**，不启用时区感知 datetime     |

> ⚠️ `USE_TZ=False` 是项目显式选择，与 Django 6 默认推荐相反；改回 `True` 需同时排查所有 `datetime.now()` 与 `auto_now_add` 兼容性。

**静态/媒体**：

| 配置项           | 值                  | 说明              |
| -------------- | ------------------ | --------------- |
| `STATIC_URL`   | `'static/'`        | 静态文件 URL 前缀     |
| `STATICFILES_DIRS` | `[BASE_DIR / 'static']` | 项目级静态文件目录（自定义 admin 资源等） |
| `MEDIA_ROOT`   | `BASE_DIR/media`  | 媒体文件物理存储路径      |
| `MEDIA_URL`    | `'/media/'`        | 媒体文件访问 URL 前缀   |

**启动时自动创建 media 目录**（[L275-L276](/code/cube_api/cube_api/settings/dev.py#L275-L276)）：`if not os.path.exists(MEDIA_ROOT): os.makedirs(MEDIA_ROOT)`。

`DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'`（[L279](/code/cube_api/cube_api/settings/dev.py#L279)）—— 自增大整数主键。

**自定义用户模型**：`AUTH_USER_MODEL = 'accounts.User'`（[L283](/code/cube_api/cube_api/settings/dev.py#L283)）。

#### DRF 配置（[L285-L354](/code/cube_api/cube_api/settings/dev.py#L285-L354)）

文件中存在**三段** `REST_FRAMEWORK`：

1. **初始声明**（[L288-L314](/code/cube_api/cube_api/settings/dev.py#L288-L314)）—— 仅作注释说明，下方分支会**完全覆盖**该字典
2. **测试分支**（[L317-L331](/code/cube_api/cube_api/settings/dev.py#L317-L331)）：限流保留但设超大速率（`10000/minute`）确保代码路径被测试但不拦截；改用 DRF 默认 `PageNumberPagination`
3. **非测试分支**（[L334-L354](/code/cube_api/cube_api/settings/dev.py#L334-L354)）：生产环境直接继承

**非测试分支完整配置**：

| 配置项                              | 值                                              |
| -------------------------------- | ---------------------------------------------- |
| `DEFAULT_AUTHENTICATION_CLASSES` | `[CachedJWTAuthentication]`                    |
| `DEFAULT_PERMISSION_CLASSES`     | `[IsAuthenticatedOrReadOnly]`                  |
| `DEFAULT_THROTTLE_CLASSES`       | `[AnRateThrottle, UserRateThrottle]`           |
| `DEFAULT_THROTTLE_RATES`         | `anon=100/day`、`user=1000/day`、`login_scope=5/minute` |
| `DEFAULT_PAGINATION_CLASS`        | `utils.common_pagination.UnifiedPagination`    |
| `PAGE_SIZE`                       | 20                                             |
| `DEFAULT_SCHEMA_CLASS`            | `drf_spectacular.openapi.AutoSchema`           |

**测试分支差异**：`DEFAULT_THROTTLE_RATES` 设为 `10000/minute`（保留限流类，确保代码路径被测试但不会真正拦截）；`DEFAULT_PAGINATION_CLASS` 改为 DRF 默认 `PageNumberPagination`；其余与非测试一致。

> ⚠️ 初始声明的 `login_scope=3/min` 与非测试分支的 `5/minute` 不一致；实际生效的是后者（覆盖语义）。

#### 测试模式 Mock Redis（[L356-L364](/code/cube_api/cube_api/settings/dev.py#L356-L364)）

```python
if _IS_TEST:
    import django_redis, fakeredis
    _fake_redis = fakeredis.FakeRedis()
    def mock_get_redis_connection(alias):
        return _fake_redis
    django_redis.get_redis_connection = mock_get_redis_connection
```

**关键约定**：mock 返回 `fakeredis.FakeRedis` 实例，使 `.exists()/.sadd()/.scard()` 等 Redis 直连命令在测试中可用，无需真实 Redis 服务。测试缓存改用 `LocMemCache`（Django 内置），两者配合覆盖所有缓存场景。

#### 业务配置 FORUM\_CONFIG（[L366-L378](/code/cube_api/cube_api/settings/dev.py#L366-L378)）

| 字段                            | 值             | 含义                |
| ----------------------------- | ------------- | ----------------- |
| `POST_MIN_TITLE_LENGTH`        | 5             | 帖子标题最小长度          |
| `POST_MAX_TITLE_LENGTH`        | 200           | 帖子标题最大长度          |
| `POST_MIN_CONTENT_LENGTH`      | 10            | 帖子正文最小长度          |
| `COMMENT_MIN_CONTENT_LENGTH`   | 2             | 评论正文最小长度          |
| `HOT_POST_DAYS`                | 7             | 热门帖子统计天数          |
| `HOT_POST_LIMIT`               | 20            | 热门帖子数量上限          |
| `MAX_FILE_SIZE`                | 5×1024×1024    | 上传文件大小上限（5 MB）    |
| `ALLOWED_FILE_EXTENSIONS`      | `['.md']`     | 允许的文件扩展名          |

#### JWT 配置 SIMPLE\_JWT（[L380-L388](/code/cube_api/cube_api/settings/dev.py#L380-L388)）

| 配置项                       | 值                    | 说明                                       |
| ------------------------- | -------------------- | ---------------------------------------- |
| `ACCESS_TOKEN_LIFETIME`   | `timedelta(days=7)`  | Access Token 有效期：7 天                     |
| `REFRESH_TOKEN_LIFETIME`  | `timedelta(days=7)`  | Refresh Token 有效期：7 天                    |
| `ROTATE_REFRESH_TOKENS`   | `True`               | 刷新 Access 时签发新的 Refresh                 |
| `UPDATE_LAST_LOGIN`       | `True`               | 更新 `last_login` 字段                       |
| `AUTH_HEADER_TYPES`       | `('Token',)`         | **Token 前缀为** **`Token`** **而非** **`Bearer`** |

> Access 与 Refresh 均为 7 天，Token 一旦泄漏需依赖黑名单机制（见 [JWTCacheService](#76-服务层servicespy)）主动注销才能失效。

#### OpenAPI 文档 SPECTACULAR\_SETTINGS（[L390-L407](/code/cube_api/cube_api/settings/dev.py#L390-L407)）

| 配置项                       | 值                                |
| ------------------------- | -------------------------------- |
| `TITLE`                   | `'ICube API'`                    |
| `DESCRIPTION`             | `'项目接口文档'`                       |
| `VERSION`                 | `'1.0.0'`                        |
| `SERVE_INCLUDE_SCHEMA`    | `False`（不在文档中包含 Schema 自身）       |
| `SCHEMA_PATH_PREFIX`      | `'/api/'`                        |
| `AUTHENTICATION_WHITELIST`| `[]`（兼容保留项，drf-spectacular 不读）   |
| `TAGS`                    | 7 个分类标签：users/profiles/forum/comments/tags/reports |

#### 日志配置（[L409-L419](/code/cube_api/cube_api/settings/dev.py#L409-L419)）

```python
LOGGING_CONFIG = None   # 禁用 Django 默认日志配置
LOGGING = {}            # 防止自动加载默认配置
from .logger_conf import setup_logging
setup_logging()
```

详细 Loguru 配置见 [5.3 logger\_conf.py](#53-logger_confpy--loguru-配置logger_confpy)。

#### django-unfold 后台主题（[L421-L504](/code/cube_api/cube_api/settings/dev.py#L421-L504)）

- `X_FRAME_OPTIONS = 'SAMEORIGIN'`（[L424](/code/cube_api/cube_api/settings/dev.py#L424)）—— 允许同源页面嵌入管理后台
- `UNFOLD` 字典配置：站点标题、Logo、侧边栏导航

**侧边栏导航分组**（[L432-L502](/code/cube_api/cube_api/settings/dev.py#L432-L502)）：

| 分组       | 图标              | 子菜单                          |
| -------- | --------------- | ---------------------------- |
| 认证和授权    | `lock`          | 用户组、权限                        |
| Home     | `home`          | 导航菜单                          |
| Accounts | `people`        | 用户列表                          |
| 论坛       | `message`       | 标签、帖子、评论、举报记录、帖子图片            |
| 魔方公式     | `cube`          | 魔方分类、魔方状态、公式、公式标签、公式收藏        |
| Timer    | `timer`         | 计时记录                          |
| 商城       | `shopping_cart` | 商品分类、商品、购物车、订单、订单明细           |

每个分组可折叠（`collapsible: True`），`show_search=True` 启用全局搜索。

#### CORS 配置（[L506-L516](/code/cube_api/cube_api/settings/dev.py#L506-L516)）

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",    # Vite 默认端口
    "http://127.0.0.1:5173",
]
CORS_ALLOW_ALL_ORIGINS = True   # 仅开发联调
```

> ⚠️ `CORS_ALLOW_ALL_ORIGINS=True` 会让 `CORS_ALLOWED_ORIGINS` 白名单失效；`prod.py` 必须显式覆盖为 `False`，否则生产 CORS 白名单不生效。

### 5.2 prod.py — 生产配置（[prod.py](/code/cube_api/cube_api/settings/prod.py)）

`from .dev import *` 后覆盖：

| 配置项                      | 生产值                                                        |
| ------------------------ | ---------------------------------------------------------- |
| DEBUG                    | False                                                      |
| SECRET\_KEY              | `os.getenv('SECRET_KEY', SECRET_KEY)`                      |
| ALLOWED\_HOSTS           | 环境变量 + `localhost,127.0.0.1,icube_api,api`                 |
| CORS\_ALLOWED\_ORIGINS   | `http://` + `https://` + `ALLOWED_ORIGIN` 环境变量 + localhost |
| CORS\_ALLOW\_CREDENTIALS | True                                                       |
| DATABASES HOST           | `db`（Docker 服务名）                                           |
| CACHES LOCATION          | `redis://redis:6379/1`，KEY\_PREFIX=`icube_prod`            |
| STATIC\_ROOT             | `BASE_DIR/collected_static`                                |

### 5.3 logger\_conf.py — Loguru 配置（[logger\_conf.py](/code/cube_api/cube_api/settings/logger_conf.py)）

**核心机制**：

- `InterceptHandler`：继承 `logging.Handler`，将标准 logging 的 LogRecord 转发到 Loguru，调整调用栈深度确保显示原始位置
- `setup_logging()`：通过 `logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)` 全局接管

**日志目录**：

- Docker（`RUNNING_IN_DOCKER=true`）→ `/var/log/icube/`
- 本地 → `<BASE_DIR>/log/`

**环境策略**：

| 配置项         | 开发（`DJANGO_ENV != prod`） | 生产（`DJANGO_ENV=prod`）                |
| ----------- | ------------------------ | ------------------------------------ |
| 控制台级别       | INFO（彩色）                 | WARNING（彩色）                          |
| 文件最低级别      | DEBUG                    | INFO                                 |
| 文件 sink     | 按级别分文件                   | 统一 `cube-all.log` + `cube-error.log` |
| 文件格式        | 文本                       | JSON（便于日志分析）                         |
| rotation    | 10 MB                    | 10 MB                                |
| retention   | 30 days                  | 30 days                              |
| diagnose    | True                     | **False**（避免暴露敏感信息）                  |
| enqueue（异步） | True（文件）/ False（控制台）     | True（文件）/ False（控制台）                 |

显式接管 `django`、`django.server`、`django.db.backends`、`django.utils.autoreload`、`gunicorn`、`uvicorn` logger，全部 `propagate=False` 防重复。

***
