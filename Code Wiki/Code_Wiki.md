# ICube 魔方学习平台 — Code Wiki

> 仓库根：`e:\BH\PyStudy\ICube`
> 后端实际路径：`cube_api/cube_api/apps/`（因 `sys.path` 注入，导入为 `apps.xxx`）
> 本文档聚焦后端，前端仅突出与后端交互部分。

***

## 目录

- [1. 项目概述](#1-项目概述)
- [2. 整体架构与服务拓扑](#2-整体架构与服务拓扑)
- [3. 技术栈与依赖](#3-技术栈与依赖)
- [4. 后端架构总览](#4-后端架构总览)
- [5. 后端配置层（settings）](#5-后端配置层settings)
- [6. 后端工具层（utils）](#6-后端工具层utils)
- [7. accounts 模块](#7-accounts-模块)
- [8. forum 模块](#8-forum-模块)
- [9. formula 模块](#9-formula-模块)
- [10. shop 模块](#10-shop-模块)
- [11. home 模块](#11-home-模块)
- [12. timer 模块](#12-timer-模块)
- [13. 前端架构（重点：与后端交互）](#13-前端架构重点与后端交互)
- [14. 部署与运维](#14-部署与运维)
- [15. 关键设计模式与约定](#15-关键设计模式与约定)
- [16. 已知问题与优化点](#16-已知问题与优化点)
- [17. 常用命令速查](#17-常用命令速查)

***

## 1. 项目概述

ICube 是一个魔方学习与交流平台，前后端分离架构，涵盖：

- **公式库**：CFOP/F2L/OLL/PLL 公式分类体系、魔方状态匹配、3D 渲染、用户自定义公式与收藏
- **论坛**：Markdown 帖子、图片延迟关联、树形评论、点赞/点踩、收藏、举报、热度排行
- **商城**：商品分类树、购物车、订单全生命周期、支付宝沙箱支付、收货地址管理
- **计时器**：用户魔方还原计时记录、分组统计与趋势分析
- **认证**：自定义 email 登录 + JWT（带 Redis 缓存与黑名单注销）+ 关注/粉丝关系（数据库 + Redis 双写）
- **首页**：动态导航菜单 + 轮播图（后端驱动）

***

## 2. 整体架构与服务拓扑

### 2.1 请求流转（生产）

```
浏览器
  ├─ /api/*    → 网关 Nginx → api:8000（Django/DRF，保留 /api/ 前缀）
  ├─ /media/*  → 网关 Nginx → alias ./cube_api/media（30 天缓存）
  ├─ /static/* → 网关 Nginx → alias collected_static（30 天缓存）
  └─ /*        → 网关 Nginx → front:80 → 前端 Nginx（SPA 回退）
```

本地开发：Vite dev server 接管前端，`/api` 与 `/media` 经 `vite.config.js` proxy → `127.0.0.1:8000`。

### 2.2 Docker 服务拓扑

```
                        ┌─────────────────────────────────────┐
                        │  浏览器 http://<server>/             │
                        └─────────────────┬───────────────────┘
                                          ▼
                ┌──────────────────────────────────────────────┐
                │  nginx (icube_nginx) :80                     │
                │  /api/* → api:8000                           │
                │  /media/*、/static/* → alias                 │
                │  /* → front:80                               │
                └──────────────┬────────────────┬──────────────┘
                               ▼                ▼
                 ┌────────────────────┐  ┌────────────────────┐
                 │ api (icube_api)    │  │ front (icube_front)│
                 │ Django + Gunicorn  │  │ Nginx + Vue dist   │
                 │ 镜像内业务代码 :8000 │  │ 镜像内静态资源 :80   │
                 └─────────┬──────────┘  └────────────────────┘
                  depends_on│
          ┌─────────────────┴─────────────────┐
          ▼                                   ▼
   ┌──────────────────┐              ┌──────────────────┐
   │ db (MySQL 8.0)   │              │ redis (7-alpine) │
   │ healthcheck      │              │ redis_data       │
   │ start_period 45s │              └──────────────────┘
   └──────────────────┘
```

### 2.3 数据卷

| 卷或目录                 | 用途                   | 挂载点                                                                |
| ---------------------- | -------------------- | ------------------------------------------------------------------ |
| `mysql_data`           | MySQL 持久化            | `db:/var/lib/mysql`                                                |
| `redis_data`           | Redis 持久化            | `redis:/data`                                                      |
| `collected_static`     | collectstatic 产物     | `api:/app/collected_static` ↔ `nginx:/usr/share/nginx/html/static` |
| `./cube_api/media`     | 受 Git 管理及用户上传的媒体文件 | `api:/app/media` ↔ `nginx:/usr/share/nginx/html/media`             |

前端 `dist` 在 Docker 构建阶段写入 `front` 镜像，不再使用 `front_dist` 卷。所有服务共用自定义桥接网络 `icube_network`。

***

## 3. 技术栈与依赖

### 3.1 后端核心依赖

| 包                             | 版本      | 用途                       |
| ----------------------------- | ------- | ------------------------ |
| Django                        | 6.0.5   | Web 框架                   |
| djangorestframework           | 3.17.1  | DRF                      |
| djangorestframework-simplejwt | 5.5.1   | JWT 认证（Token 前缀 `Token`） |
| django-filter                 | 25.2    | 过滤器后端                    |
| django-cors-headers           | 4.9.0   | CORS 跨域                  |
| django-redis                  | 6.0.0   | Redis 缓存后端               |
| redis                         | 7.4.0   | Redis Python 客户端         |
| drf-spectacular               | 0.29.0  | OpenAPI 文档生成             |
| django-unfold                 | 0.101.0 | 后台管理主题（Tailwind）         |
| mysqlclient                   | 2.2.8   | MySQL 驱动                 |
| pillow                        | 12.2.0  | 图像处理                     |
| openpyxl                      | 3.1.5   | Excel 导入（公式数据）           |
| python-alipay-sdk             | 3.4.0   | 支付宝支付                    |
| loguru                        | 0.7.3   | 日志框架（项目唯一允许的日志库）         |

> `gunicorn` 未写入 `requirements.txt`，在 Dockerfile 中单独 pip install。

### 3.2 前端核心依赖

| 包                       | 版本       | 用途                        |
| ----------------------- | -------- | ------------------------- |
| vue                     | ^3.5.32  | Vue 3 框架                  |
| vue-router              | ^5.0.6   | 路由                        |
| pinia                   | ^3.0.4   | 状态管理                      |
| element-plus            | ^2.14.0  | UI 组件库                    |
| axios                   | ^1.16.0  | HTTP 客户端                  |
| three                   | ^0.184.0 | 3D 魔方渲染                   |
| @tweenjs/tween.js       | ^25.0.0  | 3D 动画补间                   |
| echarts                 | ^6.1.0   | 数据图表                      |
| marked                  | ^18.0.4  | Markdown 渲染               |
| cropperjs               | ^2.1.1   | 图片裁剪                      |
| vite                    | ^8.0.8   | 构建工具                      |
| unplugin-auto-import    | ^21.0.0  | 自动导入 Vue/Router/Pinia API |
| unplugin-vue-components | ^32.0.0  | 自动导入 Element Plus 组件      |

Node 版本要求：`^20.19.0 || >=22.12.0`（与 Dockerfile `node:20-alpine` 匹配）。

***

## 4. 后端架构总览

### 4.1 目录结构

```
cube_api/
├── manage.py
├── requirements.txt
├── Dockerfile
├── mysql.conf                    # 历史配置文件，当前 Compose 不再挂载
└── cube_api/
    ├── __init__.py
    ├── settings/
    │   ├── dev.py                 # 基础配置（开发）
    │   ├── prod.py                # 生产配置（from .dev import * 后覆盖）
    │   └── logger_conf.py         # Loguru 日志配置
    ├── urls.py                    # 顶层路由
    ├── wsgi.py / asgi.py
    ├── utils/                     # 工具层（响应/异常/分页/图片）
    │   ├── common_response.py
    │   ├── common_exception.py
    │   ├── common_pagination.py
    │   ├── image_url.py
    │   └── image_processor.py
    └── apps/                      # 业务应用（sys.path 注入，导入为 apps.xxx）
        ├── accounts/              # 认证与社交关系
        ├── forum/                 # 论坛
        ├── formula/               # 公式库
        ├── shop/                  # 商城
        ├── home/                  # 首页导航
        └── timer/                 # 计时器
```

每个 app 标准结构：`models.py / views.py / serializers.py / services.py / urls.py / admin.py / permissions.py / filters.py（可选）/ signals.py（可选）/ tests/`。

### 4.2 顶层路由（[urls.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/urls.py)）

| 路径前缀                      | 模块              | 说明             |
| ------------------------- | --------------- | -------------- |
| `/admin/`                 | Django Admin    | Unfold 主题      |
| `/api/schema/`            | drf-spectacular | OpenAPI Schema |
| `/api/schema/swagger-ui/` | drf-spectacular | Swagger UI     |
| `/api/schema/redoc/`      | drf-spectacular | Redoc          |
| `/api/home/`              | home            | 导航菜单、轮播图       |
| `/api/`                   | accounts        | 登录、注册、用户信息、关注  |
| `/api/forum/`             | forum           | 帖子、评论、标签、举报    |
| `/api/formula/`           | formula         | 公式、分类、状态、收藏    |
| `/api/shop/`              | shop            | 商品、购物车、订单、支付   |
| `/api/timer/`             | timer           | 计时记录、统计        |

开发环境（DEBUG=True）下挂载 `MEDIA_URL` 提供媒体文件服务。

***

## 5. 后端配置层（settings）

### 5.1 dev.py — 基础配置（[dev.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py)）

`prod.py` 通过 `from .dev import *` 继承此文件并覆盖部分配置，dev.py 是所有运行环境的**基础配置**。文件按 11 个段落组织（顶部注释 [L7-L18](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L7-L18) 已列出），每段由独立的 `# =====` 分隔。

#### 路径配置（[L32-L50](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L32-L50)）

| 配置项                                  | 行号     | 作用                                                              |
| ------------------------------------ | ------ | --------------------------------------------------------------- |
| `BASE_DIR`                           | L36    | `Path(__file__).resolve().parent.parent.parent` → `cube_api/`（含 manage.py） |
| `sys.path.insert(cube_api/cube_api/)` | L40    | 让 `import utils`、`from settings.xxx` 可直接导入                     |
| `APPS_DIR + sys.path.insert`         | L44-L46 | 让 `apps.xxx` 也能以 apps 子目录方式被识别（双导入路径）                          |
| `sys.path.insert(BASE_DIR)`          | L50    | 统一 manage.py 与服务进程的导入行为                                         |

#### 安全配置（[L52-L67](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L52-L67)）

| 配置项             | 开发值                                              | 说明                                       |
| --------------- | ------------------------------------------------ | ---------------------------------------- |
| `SECRET_KEY`    | `django-insecure-...`（固定值）                       | 生产环境必须由 `os.getenv('SECRET_KEY')` 覆盖    |
| `DEBUG`         | `True`                                           | 开发暴露详细错误页；生产必须 `False`                   |
| `ALLOWED_HOSTS` | `['*']`                                          | 开发接受任意 Host；prod 改为白名单                   |
| `SITE_DOMAIN`   | `os.getenv('SITE_DOMAIN', 'http://localhost:8000')` | 生成图片、邮件等绝对 URL 时使用，prod 覆盖              |

#### 应用配置（[L71-L96](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L71-L96)）

`INSTALLED_APPS` 注册顺序：

1. **`unfold` + `unfold.contrib.filters`** —— 必须置于 Django 内置应用之前，否则 Tailwind 主题覆盖失效
2. Django 内置：`admin/auth/contenttypes/sessions/messages/staticfiles`
3. 第三方：`corsheaders/rest_framework/rest_framework_simplejwt/drf_spectacular`
4. 业务应用：`apps.home/accounts/forum/formula/shop/timer`（6 个业务模块）

#### 中间件配置（[L100-L117](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L100-L117)）

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

> `X_FRAME_OPTIONS` 在 [L424](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L424) 被覆盖为 `'SAMEORIGIN'`，允许 Unfold 同源嵌入。

#### 模板与会话（[L123-L161](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L123-L161)）

**模板**（[L123-L136](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L123-L136)）：`DIRS=[BASE_DIR/'templates']`、`APP_DIRS=True`、context_processors 为 `request/auth/messages` 三件套。

**Session**（[L153-L158](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L153-L158)）：

| 配置项                          | 值                  | 作用                              |
| ---------------------------- | ------------------ | ------------------------------- |
| `SESSION_ENGINE`             | `backends.cache`   | Session 存入 default 缓存（Redis）     |
| `SESSION_CACHE_ALIAS`        | `default`          | 多实例可共享登录态                       |
| `SESSION_COOKIE_AGE`         | `3600 * 24`（1 天）   | Session 有效期                     |
| `SESSION_SAVE_EVERY_REQUEST` | `True`             | 每次请求刷新过期时间（滑动过期）                |

#### 数据库配置（[L163-L190](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L163-L190)）

环境变量优先（[L166-L170](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L166-L170)），未设置时使用本地默认值：

| 变量           | 默认值          |
| ------------ | ------------ |
| `DB_NAME`    | `icube`      |
| `DB_USER`    | `icube_api`  |
| `DB_PASSWORD`| `icube123?`  |
| `DB_HOST`    | `localhost`  |
| `DB_PORT`    | `3306`       |

**测试模式自动切换 SQLite 内存库**（[L186-L190](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L186-L190)）：

```python
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # 内存数据库，速度最快
    }
```

数据库随测试进程销毁，不写入本地 MySQL。

#### Redis 配置（[L192-L233](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L192-L233)）

**公共连接选项 `REDIS_BASE_OPTIONS`**（[L195-L205](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L195-L205)）：

| 选项                       | 值                                              | 作用                          |
| ------------------------- | ---------------------------------------------- | --------------------------- |
| `CLIENT_CLASS`            | `django_redis.client.DefaultClient`            | 默认客户端                       |
| `CONNECTION_POOL_CLASS`  | `redis.BlockingConnectionPool`                 | 连接池满时等待空闲连接                 |
| `max_connections`         | 50                                             | 连接池上限                       |
| `timeout`                 | 20                                             | 获取空闲连接最多等待 20 秒（非网络超时）      |
| `SERIALIZER`              | `django_redis.serializers.json.JSONSerializer` | 缓存值必须 JSON 可序列化             |

> 上方 `CACHES`（[L142-L150](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L142-L150)）是兼容保留的初始声明，会被下方分支完全覆盖。

**测试分支**（[L208-L222](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L208-L222)）—— `'test' in sys.argv or 'pytest' in sys.modules`：

| 配置项                | 值                              |
| ------------------ | ------------------------------ |
| `LOCATION`         | `redis://127.0.0.1:6379/3`    |
| `KEY_PREFIX`       | `icube_test`                   |
| `TIMEOUT`          | 300（5 分钟）                      |
| `PASSWORD_HASHERS` | `[MD5PasswordHasher]`（仅测试用）   |

**非测试分支**（[L225-L233](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L225-L233)）：

| 配置项          | 值                              |
| ------------ | ------------------------------ |
| `LOCATION`   | `redis://127.0.0.1:6379/1`    |
| `KEY_PREFIX` | `icube`                        |
| `TIMEOUT`    | 86400（24 小时）                   |

> 测试环境**仍依赖本地 Redis**，仅通过数据库编号 + 键前缀隔离；`MD5PasswordHasher` 不可用于真实用户密码。

#### 密码验证（[L237-L256](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L237-L256)）

`AUTH_PASSWORD_VALIDATORS` 启用 4 个内置验证器：`UserAttributeSimilarityValidator`、`MinimumLengthValidator`、`CommonPasswordValidator`、`NumericPasswordValidator`。

#### 国际化与静态/媒体（[L258-L279](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L258-L279)）

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
| `MEDIA_ROOT`   | `BASE_DIR/media`  | 媒体文件物理存储路径      |
| `MEDIA_URL`    | `'/media/'`        | 媒体文件访问 URL 前缀   |

**启动时自动创建 media 目录**（[L275-L276](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L275-L276)）：`if not os.path.exists(MEDIA_ROOT): os.makedirs(MEDIA_ROOT)`。

`DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'`（[L279](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L279)）—— 自增大整数主键。

**自定义用户模型**：`AUTH_USER_MODEL = 'accounts.User'`（[L283](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L283)）。

#### DRF 配置（[L285-L354](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L285-L354)）

文件中存在**三段** `REST_FRAMEWORK`：

1. **初始声明**（[L288-L314](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L288-L314)）—— 仅作注释说明，下方分支会**完全覆盖**该字典
2. **测试分支**（[L317-L331](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L317-L331)）：清空限流、改用 DRF 默认 `PageNumberPagination`
3. **非测试分支**（[L334-L354](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L334-L354)）：生产环境直接继承

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

**测试分支差异**：`DEFAULT_THROTTLE_*` 清空为 `[]`/`{}`；`DEFAULT_PAGINATION_CLASS` 改为 DRF 默认 `PageNumberPagination`；其余与非测试一致。

> ⚠️ 初始声明的 `login_scope=3/min` 与非测试分支的 `5/minute` 不一致；实际生效的是后者（覆盖语义）。

#### 测试模式 Mock Redis（[L356-L364](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L356-L364)）

```python
if 'test' in sys.argv:
    import django_redis
    def mock_get_redis_connection(alias):
        from django.core.cache import cache
        return cache
    django_redis.get_redis_connection = mock_get_redis_connection
```

**关键约定**：mock 返回的是 **Django RedisCache 包装对象**，并非内存缓存；调用方需通过 `.client.get_client()` 取得 `redis-py` 客户端。Service 层（如 `JWTCacheService._get_con`）已实现这一穿透逻辑。

#### 业务配置 FORUM\_CONFIG（[L366-L378](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L366-L378)）

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

#### JWT 配置 SIMPLE\_JWT（[L380-L388](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L380-L388)）

| 配置项                       | 值                    | 说明                                       |
| ------------------------- | -------------------- | ---------------------------------------- |
| `ACCESS_TOKEN_LIFETIME`   | `timedelta(days=7)`  | Access Token 有效期：7 天                     |
| `REFRESH_TOKEN_LIFETIME`  | `timedelta(days=7)`  | Refresh Token 有效期：7 天                    |
| `ROTATE_REFRESH_TOKENS`   | `True`               | 刷新 Access 时签发新的 Refresh                 |
| `UPDATE_LAST_LOGIN`       | `True`               | 更新 `last_login` 字段                       |
| `AUTH_HEADER_TYPES`       | `('Token',)`         | **Token 前缀为** **`Token`** **而非** **`Bearer`** |

> Access 与 Refresh 均为 7 天，Token 一旦泄漏需依赖黑名单机制（见 [JWTCacheService](#76-服务层servicespy)）主动注销才能失效。

#### OpenAPI 文档 SPECTACULAR\_SETTINGS（[L390-L407](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L390-L407)）

| 配置项                       | 值                                |
| ------------------------- | -------------------------------- |
| `TITLE`                   | `'ICube API'`                    |
| `DESCRIPTION`             | `'项目接口文档'`                       |
| `VERSION`                 | `'1.0.0'`                        |
| `SERVE_INCLUDE_SCHEMA`    | `False`（不在文档中包含 Schema 自身）       |
| `SCHEMA_PATH_PREFIX`      | `'/api/'`                        |
| `AUTHENTICATION_WHITELIST`| `[]`（兼容保留项，drf-spectacular 不读）   |
| `TAGS`                    | 7 个分类标签：users/profiles/forum/comments/tags/reports |

#### 日志配置（[L409-L419](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L409-L419)）

```python
LOGGING_CONFIG = None   # 禁用 Django 默认日志配置
LOGGING = {}            # 防止自动加载默认配置
from .logger_conf import setup_logging
setup_logging()
```

详细 Loguru 配置见 [5.3 logger\_conf.py](#53-logger_confpy--loguru-配置logger_confpy)。

#### django-unfold 后台主题（[L421-L504](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L421-L504)）

- `X_FRAME_OPTIONS = 'SAMEORIGIN'`（[L424](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L424)）—— 允许同源页面嵌入管理后台
- `UNFOLD` 字典配置：站点标题、Logo、侧边栏导航

**侧边栏导航分组**（[L432-L502](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L432-L502)）：

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

#### CORS 配置（[L506-L516](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/dev.py#L506-L516)）

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",    # Vite 默认端口
    "http://127.0.0.1:5173",
]
CORS_ALLOW_ALL_ORIGINS = True   # 仅开发联调
```

> ⚠️ `CORS_ALLOW_ALL_ORIGINS=True` 会让 `CORS_ALLOWED_ORIGINS` 白名单失效；`prod.py` 必须显式覆盖为 `False`，否则生产 CORS 白名单不生效。

### 5.2 prod.py — 生产配置（[prod.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/prod.py)）

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

### 5.3 logger\_conf.py — Loguru 配置（[logger\_conf.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/settings/logger_conf.py)）

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

## 6. 后端工具层（utils）

### 6.1 common\_response.py — 统一响应（[common\_response.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/utils/common_response.py)）

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

### 6.2 common\_exception.py — 统一异常处理（[common\_exception.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/utils/common_exception.py)）

核心函数 `common_exception_handler(exc, context)`（[L35](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/utils/common_exception.py#L35-L127)）：

1. 提取上下文（user email/Anonymous、path、method、view 类名）
2. 调用 DRF 原生 `drf_exception_handler` 获取初步 response
3. **情况 A：DRF 已处理**（业务错误）：
   - `ValidationError` → 取第一个字段第一个错误，格式 `field: error`
   - 其他 dict → 取 detail；list → 取 `[0]`；其他 → str()
   - `logger.warning` + 结构化上下文 → `APIResponse(code=998, msg, status=response.status_code)`
4. **情况 B：未捕获异常**（系统错误）：
   - `logger.error` + 上下文 → `APIResponse(code=999, msg="系统开小差了，请稍后再试", status=500)`
   - 屏蔽敏感堆栈，仅返回友好提示

| 异常类型             | 分支 | code | HTTP status | 日志      |
| ---------------- | -- | ---- | ----------- | ------- |
| ValidationError  | A  | 998  | 400         | warning |
| PermissionDenied | A  | 998  | 403         | warning |
| NotFound         | A  | 998  | 404         | warning |
| APIException 子类  | A  | 998  | 跟随 DRF      | warning |
| 其他 Python 异常     | B  | 999  | 500         | error   |

### 6.3 common\_pagination.py — 统一分页（[common\_pagination.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/utils/common_pagination.py)）

| 类                           | page\_size | max\_page\_size | 用途    |
| --------------------------- | ---------- | --------------- | ----- |
| `UnifiedPagination`         | 20         | 100             | 默认分页器 |
| `LargeResultsSetPagination` | 50         | 500             | 大数据集  |
| `SmallResultsSetPagination` | 10         | 50              | 小数据集  |

重写 `get_paginated_response(data)` 返回 `APIResponse(data={count, next, previous, results})`，与统一响应格式一致。同时提供 `get_paginated_response_schema(schema)` 为 drf-spectacular 生成正确 schema。

### 6.4 image\_url.py — 图片 URL 标准化（[image\_url.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/utils/image_url.py)）

```python
def build_image_url(relative_path, absolute=False)
```

**处理逻辑**（[L57-L102](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/utils/image_url.py#L57-L102)）：

1. 空路径 → 返回 `''`
2. `isinstance(relative_path, FieldFile)` → 取 `.name`（**避免触发 .path 属性计算**）
3. 完整 URL（http/https 开头）→ 原样返回
4. 补 `/` 前缀
5. 补 `/media/` 前缀（已存在则跳过）
6. `absolute=True` 时拼接 `settings.SITE_DOMAIN`

**关键约束**（项目规则）：

- **禁止** **`hasattr(relative_path, 'path')`** —— 头像路径以 `/` 开头时会触发 `SuspiciousFileOperation`
- 改用 `isinstance(FieldFile)` 检查后访问 `.name`

**默认返回相对路径**的原因：浏览器 Private Network Access (PNA) 会阻止公网域名直接访问 localhost 图片资源。

### 6.5 image\_processor.py — 图像处理（[image\_processor.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/utils/image_processor.py)）

依赖 Pillow。

| 函数                           | 签名                                                                                           | 功能                               |
| ---------------------------- | -------------------------------------------------------------------------------------------- | -------------------------------- |
| `compress_image`             | `(file, max_width=1200, max_height=1200, quality=85, output_format='JPEG')`                  | 缩放压缩；RGBA/LA 转 JPEG 填白；LANCZOS   |
| `convert_to_webp`            | `(file, quality=85)`                                                                         | 转 WebP（有损）                       |
| `crop_to_square`             | `(file)`                                                                                     | 中心裁剪 1:1；透明输出 PNG，否则 JPEG        |
| `process_image`              | `(file, max_width=1200, max_height=1200, quality=85, crop_square=False, convert_webp=False)` | 统一入口                             |
| `generate_formula_thumbnail` | `(formula_name, formula_notation, size=512)`                                                 | 无上传图时自动生成文字缩略图：白底+公式名+记号，输出 WebP |

所有函数返回 `BytesIO`，调用方负责 `seek(0)` 后写入文件存储。

***

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

## 8. forum 模块

### 8.1 模块职责

论坛核心：帖子发布（Markdown + 图片延迟关联）、树形评论（点赞/点踩）、标签、收藏、举报、热度排行、统计字段冗余 + Redis 浏览量缓存。

### 8.2 数据模型（[models.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/models.py)）

| 模型              | db\_table          | 核心设计                                                                                   |
| --------------- | ------------------ | -------------------------------------------------------------------------------------- |
| **Tag**         | `forum_tag`        | name unique、color、use\_count 冗余计数                                                      |
| **PostTag**     | `forum_post_tags`  | 自定义中间表，`unique_together=['post','tag']`                                                |
| **Post**        | `forum_post`       | 软删除（status='deleted'）、冗余统计（view\_count/like\_count/comment\_count/collect\_count）、复合索引 |
| **Comment**     | `forum_comment`    | 树形 parent 自关联、软删除（is\_deleted）、is\_hidden 管理员隐藏                                        |
| **PostLike**    | —                  | `unique_together=['post','user']`（幂等）                                                  |
| **CommentLike** | —                  | `unique_together=['comment','user']`、`is_like` Bool 区分赞/踩                              |
| **PostCollect** | —                  | `unique_together=['post','user']`                                                      |
| **Report**      | —                  | 通用举报：content\_type CharField + object\_id（不用 ContentType）                              |
| **PostImage**   | `forum_post_image` | **post 允许 null（延迟关联）**、`upload_to='forum/posts/%Y/%m/'`                                |

#### Post 字段（[L81-L178](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/models.py#L81-L178)）

| 字段                                                          | 类型             | 说明                               |
| ----------------------------------------------------------- | -------------- | -------------------------------- |
| title                                                       | CharField(200) | db\_index, MinLengthValidator(3) |
| content / content\_md                                       | TextField      | 正文 + Markdown 源码                 |
| author                                                      | FK→User        | CASCADE, related\_name='posts'   |
| view\_count / like\_count / comment\_count / collect\_count | IntegerField   | **冗余统计字段**（用 F 表达式原子更新）          |
| is\_pinned / is\_essence / is\_closed                       | BooleanField   | 置顶/精华/关闭评论                       |
| status                                                      | CharField(20)  | choices: published/deleted/draft |
| tags                                                        | M2M(Tag)       | through='PostTag'                |
| report\_count                                               | IntegerField   | 举报数                              |
| created\_at / updated\_at                                   | DateTimeField  | <br />                           |

- **软删除**：`soft_delete()` → `save(update_fields=['status'])`
- **Meta ordering**：`['-is_pinned', '-is_essence', '-created_at']`
- **复合索引**：`[author, -created_at]`、`[-created_at]`、`[status, -created_at]`

### 8.3 URL 路由表（[urls.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/urls.py)）

`DefaultRouter` 注册：

| 路由                        | 视图                         | 方法                   | 权限                        | 功能                               |
| ------------------------- | -------------------------- | -------------------- | ------------------------- | -------------------------------- |
| `/posts/`                 | PostViewSet                | GET                  | IsAuthenticatedOrReadOnly | 帖子列表（search/ordering/filter/hot） |
| `/posts/{id}/`            | PostViewSet                | GET/PUT/PATCH/DELETE | + IsOwnerOrReadOnly       | 详情（retrieve 自动 +1 浏览量）           |
| `/posts/{id}/like/`       | PostViewSet\@like          | POST                 | IsAuthenticated           | 切换点赞                             |
| `/posts/{id}/collect/`    | PostViewSet\@collect       | POST                 | IsAuthenticated           | 切换收藏                             |
| `/posts/{id}/comments/`   | PostViewSet\@comments      | GET                  | IsAuthenticatedOrReadOnly | 帖子一级评论                           |
| `/posts/my_posts/`        | PostViewSet\@my\_posts     | GET                  | IsAuthenticated           | 当前用户帖子                           |
| `/posts/collected/`       | PostViewSet\@collected     | GET                  | —                         | 当前用户收藏                           |
| `/posts/hot/`             | PostViewSet\@hot           | GET                  | —                         | 热门帖子                             |
| `/posts/upload_image/`    | PostViewSet\@upload\_image | POST                 | IsAuthenticated           | 上传图片（post=None 延迟关联）             |
| `/comments/`              | CommentViewSet             | GET                  | IsAuthenticatedOrReadOnly | 一级评论列表                           |
| `/comments/{id}/like/`    | CommentViewSet\@like       | POST                 | —                         | 评论点赞                             |
| `/comments/{id}/dislike/` | CommentViewSet\@dislike    | POST                 | —                         | 评论点踩                             |
| `/tags/`                  | TagViewSet                 | GET                  | IsAuthenticatedOrReadOnly | 标签（只读）                           |
| `/reports/`               | ReportViewSet              | GET/POST             | IsAuthenticated           | 举报（管理员看全部）                       |

### 8.4 视图说明（[views.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/views.py)）

#### PostViewSet（[L31-L441](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/views.py#L31-L441)）

- 继承 `ModelViewSet`
- queryset：`Post.objects.filter(status='published').select_related('author').prefetch_related('tags', 'images')`
- permission：`[IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]`

**过滤器配置**：

- `filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]`
- `search_fields = ['title', 'content']`
- `ordering_fields = ['created_at', 'view_count', 'like_count', 'comment_count', 'is_pinned', 'is_essence']`
- `ordering = ['-is_pinned', '-is_essence', '-created_at']`
- `filterset_fields = ['tags__name', 'is_pinned', 'is_essence', 'created_at']`

**关键方法**：

- `get_serializer_class()`：list → PostListSerializer；create/update → PostCreateUpdateSerializer；其他 → PostSerializer
- `list()`（[L82-L118](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/views.py#L82-L118)）：`hot` 参数存在时 `annotate(hot_score=Count('likes')*3 + Count('comments')*2 + Count('collects'))` + `order_by('-hot_score')`
- `retrieve()`：调 `PostCacheService.increase_view(id)`
- `destroy()`：`instance.soft_delete()`
- `update()`：手动检查 `instance.author != request.user` → 403
- `like` action：`PostInteractionService.toggle_like` → `{liked, like_count}`
- `collect` action：`toggle_collect`
- `comments` action：**只返回一级评论**（`parent=None`）
- `hot` action：支持 days（默认7）、limit（默认20）→ `HotPostService.get_hot_posts`
- `upload_image` action（[L378-L441](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/views.py#L378-L441)）：
  - 校验 content\_type（jpeg/jpg/png/gif/webp）+ 大小 ≤ 5MB
  - `process_image(max_width=1200, max_height=1200, quality=85, crop_square=, convert_webp=True)`
  - 创建 `PostImage(post=None)` **延迟关联**

#### CommentViewSet（[L444-L577](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/views.py#L444-L577))

- 继承 `ModelViewSet`
- `get_queryset()`：list 动作 → `filter(parent=None)` **只返回一级评论** + `order_by('-created_at')`
- `create/destroy`：手动重算 `post.comment_count`
- `like`/`dislike` action：`PostInteractionService.toggle_comment_reaction(comment_id, user, is_like=True/False)`

### 8.5 序列化器（[serializers.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/serializers.py)）

| 序列化器                         | 用途      | 关键设计                                                  |
| ---------------------------- | ------- | ----------------------------------------------------- |
| `TagSerializer`              | 标签      | id/name/color/use\_count                              |
| `PostImageSerializer`        | 帖子图片    | `image_url` SerializerMethodField → `build_image_url` |
| `PostListSerializer`         | 帖子列表    | 嵌套 author/tags，`get_images` 最多 4 张预览图                 |
| `PostSerializer`             | 帖子详情    | 动态字段 `is_liked`/`is_collected`，write\_only `tag_ids`  |
| `PostCreateUpdateSerializer` | 创建/更新   | 支持 .md 文件上传；`_sync_post_images` 全量同步图片                |
| `ReplySerializer`            | 子评论（轻量） | 不含 replies 避免递归；`liked`/`disliked`/`reply_to_name`    |
| `CommentSerializer`          | 一级评论    | `get_replies` **深度优先递归扁平化**所有子孙；`reply_count`         |
| `ReportSerializer`           | 举报      | reporter 自动设当前用户                                      |

#### \_sync\_post\_images 全量同步逻辑（[L389-L436](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/serializers.py#L389-L436)）

1. `re.findall(r'!\[.*?\]\((.*?)\)', content)` 解析 Markdown 所有图片 URL
2. 收集当前 `post.images.all()` 的 `image.name` → `existing_images`
3. 筛选 URL 包含 `/media/forum/posts/` 或 `/media/formulas/` 的，提取 `image_path = url.split('/media/')[-1]` → `required_images`
4. **删除多余**：已关联但不在 Markdown 中的 → `img.delete()`
5. **补齐缺失**：Markdown 中存在但未关联且文件存在的 → `PostImage.objects.create`

### 8.6 服务层（[services.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/services.py)）

> ⚠️ **违反项目规则**：[L16, L23-25](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/services.py#L16-L25) 使用内置 `logging` 模块，应改用 loguru。

#### PostCacheService（[L28-L177](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/services.py#L28-L177)）

**缓存键**：`forum:post:{post_id}:view`

| 方法                        | 逻辑                                                                                                                                        |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `increase_view(post_id)`  | 优先 `cache.incr(key)`；异常降级查库 + `F('view_count')+1` + `save(update_fields=['view_count'])`                                                  |
| `get_view_count(post_id)` | `cache.get` 命中返回；未命中查库 + `cache.set(key, count, 3600)`                                                                                    |
| `sync_all_views()`        | ⚠️ **使用 KEYS 命令** `con.keys("*forum:post:*:view")`（阻塞风险，建议改 SCAN）；解析 post\_id 后 `update(view_count=F('view_count')+int(views))`；删除已同步 key |

#### PostInteractionService（[L180-L345](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/services.py#L180-L345)）

| 方法                                                   | 逻辑                                                              |
| ---------------------------------------------------- | --------------------------------------------------------------- |
| `toggle_like(post_id, user)`                         | 已赞：delete + `F('like_count')-1`；未赞：create + `F('like_count')+1` |
| `toggle_collect(post_id, user)`                      | 对称收藏切换                                                          |
| `toggle_comment_reaction(comment_id, user, is_like)` | 三态：新建反应 / 取消反应 / 切换反应（赞↔踩）                                      |

#### HotPostService（[L348-L389](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/services.py#L348-L389)）

`get_hot_posts(days=7, limit=20)`：

- **热度算法**：`hot_score = F('like_count')*3 + F('comment_count')*2 + F('view_count')`
- 权重：点赞×3（认可度）、评论×2（参与度）、浏览×1（防刷量）
- `annotate + order_by('-hot_score')[:limit]`

### 8.7 权限类（[permissions.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/permissions.py)）

| 权限类                        | 逻辑                                                                         |
| -------------------------- | -------------------------------------------------------------------------- |
| `IsPostOwnerOrReadOnly`    | 读放行；写检查 `obj.author == request.user`                                       |
| `IsCommentOwnerOrReadOnly` | 同上                                                                         |
| `CanModeratePost`          | has\_permission: is\_staff or is\_moderator；has\_object\_permission: 放宽至作者 |

> 注：PostViewSet 实际复用 accounts 的 `IsOwnerOrReadOnly`，未使用 forum 自身权限类（预留）。

### 8.8 信号（[signals.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/signals.py)）

| 信号           | sender  | 接收器                                   | 逻辑                                                    |
| ------------ | ------- | ------------------------------------- | ----------------------------------------------------- |
| post\_save   | Comment | `update_post_comment_count`           | `created and not is_deleted` 时重算 `post.comment_count` |
| post\_delete | Comment | `update_post_comment_count_on_delete` | 物理删除时重算 comment\_count                                |
| post\_save   | Tag     | `update_tag_use_count`                | `use_count = instance.posts.count()`                  |

> ⚠️ CommentViewSet.create/destroy 也手动更新 comment\_count，与信号存在重复。

### 8.9 帖子图片关联机制

采用**全量同步模式**：

```
用户上传图片(upload_image action)
    ↓ PostImage(post=None) 延迟关联存储
用户提交帖子(content 含 Markdown)
    ↓ _sync_post_images(post, content)
    ├── 解析 Markdown ![](url) 提取 required_images
    ├── 删除 post.images 中不在 required_images 的
    └── 为 required_images 中未关联的创建 PostImage(post=post)
```

支持两类图片来源：用户上传 `/media/forum/posts/` + 公式库 `/media/formulas/`（跨模块引用 formula 应用图片）。

***

## 9. formula 模块

### 9.1 模块职责

魔方公式库：公式分类体系、魔方状态定义、公式 CRUD/匹配/收藏、逆公式自动生成与状态推导。

### 9.2 数据模型（[models.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/models.py)）

| 模型                     | db\_table                      | 核心设计                                                                  |
| ---------------------- | ------------------------------ | --------------------------------------------------------------------- |
| **CubeCategory**       | `formula_cube_category`        | 三维分类：order(阶数)→method(求解方法)→phase(阶段)；系统/自定义（is\_custom, created\_by） |
| **CubeState**          | `formula_cube_state`           | JSON 存储魔方状态（order/blocks/pos/faces）                                   |
| **Formula**            | `formula_formula`              | 核心；thumbnail ImageField、inverse\_notation 自动生成、view\_count 原子递增       |
| **FormulaTag**         | `formula_formula_tag`          | name unique、color                                                     |
| **FormulaTagRelation** | `formula_formula_tag_relation` | 中间表，`unique_together=['formula','tag']`                               |
| **FormulaCollection**  | `formula_formula_collection`   | 收藏，`unique_together=['user','formula']`（幂等）                           |

#### Formula 字段（[L124-L233](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/models.py#L124-L233)）

| 字段                     | 类型              | 说明                                                           |
| ---------------------- | --------------- | ------------------------------------------------------------ |
| category               | FK→CubeCategory | CASCADE                                                      |
| name                   | CharField(200)  | <br />                                                       |
| notation               | TextField       | 公式记号                                                         |
| inverse\_notation      | TextField       | blank（自动生成）                                                  |
| target\_state          | FK→CubeState    | SET\_NULL                                                    |
| pre\_state\_definition | JSONField       | null（前置状态）                                                   |
| thumbnail              | ImageField      | upload\_to='formula\_thumbnails/'（**模型层只有此一个 thumbnail 字段**） |
| difficulty             | IntegerField    | default=1                                                    |
| view\_count            | IntegerField    | default=0（**字段名是 view\_count，不是 views**）                     |
| is\_custom             | BooleanField    | default=False                                                |
| created\_by            | FK→User         | SET\_NULL                                                    |

- `save()`：notation 存在且 inverse\_notation 为空时调用 `FormulaService.generate_inverse_notation`
- `get_pre_state()`：优先 `pre_state_definition`；否则返回 `{derive_from_target, target_state, inverse_notation}` 供推导

### 9.3 URL 路由表（[urls.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/urls.py)）

| 路由                           | 视图                              | 方法             | 权限                                                 | 功能                          |
| ---------------------------- | ------------------------------- | -------------- | -------------------------------------------------- | --------------------------- |
| `/categories/`               | CubeCategoryViewSet             | GET            | AllowAny                                           | 分类列表（未登录仅系统分类）              |
| `/categories/{id}/`          | CubeCategoryViewSet             | GET/PUT/DELETE | IsAuthenticated                                    | 详情/更新/删除（仅创建者）              |
| `/categories/my_custom/`     | CubeCategoryViewSet\@my\_custom | GET            | IsAuthenticated                                    | 我的自定义分类                     |
| `/states/`                   | CubeStateViewSet                | CRUD           | IsAdminOrReadOnly                                  | 魔方状态管理                      |
| `/formulas/`                 | FormulaViewSet                  | GET/POST       | IsAuthenticatedOrReadOnly + IsAdminOrCustomCreator | 公式列表/创建（retrieve 自动 +1 浏览量） |
| `/formulas/{id}/`            | FormulaViewSet                  | GET/PUT/DELETE | 同上                                                 | 详情/更新/删除                    |
| `/formulas/match/`           | FormulaViewSet\@match           | POST           | IsAuthenticated                                    | 按状态匹配公式                     |
| `/formulas/my_custom/`       | FormulaViewSet\@my\_custom      | GET            | IsAuthenticated                                    | 我的自定义公式                     |
| `/formulas/authors/`         | FormulaViewSet\@authors         | GET            | IsAuthenticatedOrReadOnly                          | 公式作者列表（distinct）            |
| `/formulas/simple_list/`     | FormulaViewSet\@simple\_list    | GET            | IsAuthenticatedOrReadOnly                          | 精简列表（帖子编辑器用）                |
| `/tags/`                     | FormulaTagViewSet               | CRUD           | IsAdminOrReadOnly                                  | 标签管理                        |
| `/collections/`              | FormulaCollectionViewSet        | GET/POST       | IsAuthenticated                                    | 收藏列表/添加（get\_or\_create 幂等） |
| `/collections/{formula_id}/` | FormulaCollectionViewSet        | DELETE         | IsAuthenticated                                    | 取消收藏（按公式ID）                 |

### 9.4 视图说明（[views.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/views.py)）

#### FormulaViewSet（[L289-L589](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/views.py#L289-L589)）

- queryset：`Formula.objects.select_related('category','target_state').prefetch_related('tag_relations__tag')`
- permission：`[IsAuthenticatedOrReadOnly, IsAdminOrCustomCreator]`
- **过滤器**：SearchFilter + OrderingFilter + DjangoFilterBackend
  - search\_fields=`['name','notation','description']`
  - ordering\_fields=`['category','difficulty','created_at','view_count']`
  - filterset\_class=`FormulaFilter`
- `get_serializer_class()`：list → FormulaListSerializer；其他 → FormulaSerializer
- **retrieve**：`F('view_count')+1` 原子递增 + `refresh_from_db`
- **自定义 action**：match/my\_custom/authors/simple\_list

### 9.5 序列化器（[serializers.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/serializers.py)）

#### FormulaSerializer（详情，[L252-L599](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/serializers.py#L252-L599)）

**thumbnail\_file 与 thumbnail\_path 的区分点**（仅序列化器层）：

- `thumbnail`（只读 SerializerMethodField → `build_image_url`）
- `thumbnail_file`（write\_only FileField，用户上传文件）
- `thumbnail_path`（write\_only CharField，公式库图片引用路径）
- `tag_ids`（write\_only ListField）

**create（[L377-L485](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/serializers.py#L377-L485)）**：

- 非 staff 已登录用户 → `is_custom=True, created_by=user`
- 缩略图三态处理：
  1. 文件 → `process_image(max_width=512, max_height=512, quality=85, crop_square=True, convert_webp=True)`
  2. 路径 → 剥离 `/media/` 前缀后赋给 `formula.thumbnail.name`
  3. 都无 → `generate_formula_thumbnail(name, notation)` 自动生成
- **target\_state\_id 自动绑定**：category 存在且无 target\_state 时，取该分类下第一个 CubeState
- 标签关联：`FormulaTagRelation.objects.get_or_create`

**update（[L487-L599](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/serializers.py#L487-L599)）**：

- notation 修改时重新生成 inverse\_notation
- **改分类时同步更新 target\_state**：旧 target\_state 不属于新 category 则置空，再绑定新分类下首个状态
- 标签全量同步：先 delete 再 get\_or\_create

### 9.6 服务层（[services.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/services.py)）

#### FormulaService（[L17-L87](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/services.py#L17-L87)）

- `generate_inverse_notation(notation)`：按空格分割 → reversed → `NOTATION_INVERSE_MAP` 取逆 → 拼接
- 覆盖 R/L/U/D/F/B/M/E/S/x/y/z 等正向/逆向/180度三种变体

#### CubeStateService（[L90-L436](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/services.py#L90-L436)）

- `validate_state_definition(state_def)`：多层验证（结构→order→blocks→单块→中心块→相邻块颜色）
- 中心块标准配色 `CENTER_COLORS`：Y/W/B/G/O/R
- 颜色支持 `Y/W/B/G/O/R/-/?`（`-` 不关心，`?` 未知）

#### FormulaMatchService（[L439-L563](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/services.py#L439-L563)）

- `match_formulas(user_state)`：前置状态匹配 + 目标状态匹配
- `_is_state_match`：公式状态中 `-` 跳过，部分匹配
- ⚠️ `_execute_formula` 为占位（转动模拟未实现，退化为原状态比较）

### 9.7 过滤器（[filters.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/filters.py)）

`FormulaFilter`：

- `difficulty = BaseInFilter(lookup_expr='in')` — 支持逗号分隔多值
- `created_by = BaseInFilter(lookup_expr='in')` — 多作者ID
- 示例：`/api/formulas/?difficulty=1,2,3&is_custom=true&created_by=1,2`

### 9.8 权限类（[permissions.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/permissions.py)）

| 权限类                      | 逻辑                                                                                                 |
| ------------------------ | -------------------------------------------------------------------------------------------------- |
| `IsAdminOrReadOnly`      | 读放行；写要求 is\_staff                                                                                  |
| `IsOwnerOrReadOnly`      | 读放行；写检查 created\_by（未使用）                                                                           |
| `IsAdminOrCustomCreator` | has\_permission：SAFE 放行，写需登录；has\_object\_permission：`obj.is_custom and obj.created_by==user` 或管理员 |

### 9.9 management/commands

| 命令                   | 功能                                                |
| -------------------- | ------------------------------------------------- |
| `import_formulas`    | 从 Excel 导入 CFOP 公式（F2L/OLL/PLL），依赖 openpyxl，硬编码路径 |
| `insert_cube_states` | 插入 F2L/OLL/PLL 三个目标状态 + 批量更新公式 target\_state      |

***

## 10. shop 模块

### 10.1 模块职责

魔方商城：商品分类树、购物车、订单全生命周期、支付宝集成、收货地址管理。

### 10.2 数据模型（[models.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/shop/models.py)）

| 模型                  | db\_table               | 核心设计                                                                                               |
| ------------------- | ----------------------- | -------------------------------------------------------------------------------------------------- |
| **ProductCategory** | `shop_product_category` | parent FK→self(`SET_NULL`)，树形分类                                                                    |
| **Product**         | `shop_product`          | price/original\_price DecimalField、stock Int、images JSONField、thumbnail ImageField、specs JSONField |
| **Cart**            | `shop_cart`             | user+product 双 FK                                                                                  |
| **Order**           | `shop_order`            | order\_no unique、total\_amount Decimal(12,2)、status 状态机、address JSONField（快照）                      |
| **OrderItem**       | `shop_order_item`       | **price 下单时快照**、quantity、selected\_spec                                                            |
| **Address**         | `shop_address`          | is\_default 唯一性、`full_address` property                                                            |

**订单状态机**（[L156](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/shop/models.py#L156-L162)）：

```
pending（待付款）→ paid（已付款）→ shipped（已发货）→ completed（已完成）
                  ↘ cancelled（已取消）
        paid → cancelled
```

**关键设计**：

- 订单号 `Order.generate_order_no()`：`ORD` + 时间戳(14) + UUID 前 8 位大写
- **库存并发控制**：`F` 表达式原子扣减
- **价格快照**：OrderItem.price 记录下单时价格
- 无软删除，物理删除 + 事务保证

### 10.3 URL 路由表（[urls.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/shop/urls.py)）

| 路由                             | 视图                           | 方法                  | 权限              | 功能                                |
| ------------------------------ | ---------------------------- | ------------------- | --------------- | --------------------------------- |
| `/categories/`                 | ProductCategoryViewSet       | GET                 | AllowAny        | 分类树                               |
| `/products/`                   | ProductViewSet               | GET                 | AllowAny        | 商品列表（category/price/keyword/sort） |
| `/cart/`                       | CartViewSet                  | GET/POST/PUT/DELETE | IsAuthenticated | 购物车                               |
| `/orders/`                     | OrderViewSet                 | GET/POST            | IsAuthenticated | 订单 CRUD                           |
| `/orders/{id}/pay/`            | OrderViewSet\@pay            | PUT                 | IsAuthenticated | 获取支付宝支付链接                         |
| `/orders/{id}/cancel/`         | OrderViewSet\@cancel         | PUT                 | IsAuthenticated | 取消（库存回滚）                          |
| `/orders/{id}/complete/`       | OrderViewSet\@complete       | PUT                 | IsAuthenticated | 确认收货                              |
| `/orders/notify/`              | OrderViewSet\@alipay\_notify | POST                | **AllowAny**    | 支付宝异步回调                           |
| `/addresses/`                  | AddressViewSet               | GET/POST/PUT/DELETE | IsAuthenticated | 地址 CRUD                           |
| `/addresses/{id}/set_default/` | AddressViewSet\@set\_default | POST                | IsAuthenticated | 设默认                               |

### 10.4 视图说明（[views.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/shop/views.py)）

#### OrderViewSet（[L192-L426](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/shop/views.py#L192-L426)）

- `get_queryset`：过滤当前用户 + status 筛选
- `retrieve`：支持 order\_no 或 id 双查询
- **create** **`@transaction.atomic`**（[L240-L307](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/shop/views.py#L240-L307)）：F 表达式扣库存/加销量、删购物车、生成订单与明细
- `pay` action：调 `generate_alipay_url`，失败 `code=503`
- `alipay_notify` action（[L377-L426](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/shop/views.py#L377-L426)）：
  - `permission_classes=[AllowAny]`
  - 先读 `request.body` 再读 `request.data`
  - `verify_alipay_notify` **双重验签**
  - `select_for_update` 锁定订单（幂等）
  - 仅 pending→paid
  - 返回纯文本 `'success'`/`'fail'`

#### CartViewSet（[L112-L189](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/shop/views.py#L112-L189)）

- `get_queryset` 过滤当前用户
- create：相同商品+相同规格用 `F('quantity')+quantity` 合并
- update：quantity≤0 自动删除；>stock 返回 `code=400`

#### AddressViewSet（[L429-L530](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/shop/views.py#L429-L530)）

- create/update 保证同用户仅一个默认地址
- destroy 删默认地址时自动将首地址设为默认

### 10.5 支付宝集成（[alipay\_config.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/shop/alipay_config.py)）

基于 `python-alipay-sdk`。

| 函数/配置                                                  | 位置                                                                                              | 关键点                                                                                                                           |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `ALIPAY_CONFIG`                                        | [L25-L38](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/shop/alipay_config.py#L25-L38)     | app\_id、私钥/公钥路径 `os.path.join(BASE_DIR,'keys',...)`、notify\_url=`http://{SERVER_HOST}/api/shop/orders/notify/`、debug=True（沙箱） |
| `get_alipay_client()`                                  | [L153-L206](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/shop/alipay_config.py#L153-L206) | 文件存在性检查；sign\_type=`RSA2`；启动打印公钥 modulus 指纹                                                                                   |
| `generate_alipay_url(order_no, total_amount, subject)` | [L209-L250](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/shop/alipay_config.py#L209-L250) | `total_amount=str(total_amount)` 强制两位小数字符串；沙箱/生产网关切换                                                                          |
| `verify_alipay_notify(data, raw_body)`                 | [L295-L355](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/shop/alipay_config.py#L295-L355) | **双重验签**：SDK verify + 失败时手动 RSA2 验签；验签 message/sign 落盘便于核对                                                                    |

**密钥路径**：`apps/shop/keys/app_private_key.pem` + `alipay_public_key.pem`，已 `.gitignore`，**禁止提交版本控制**。

### 10.6 management/commands

`init_shop_data`：初始化商品分类（6 个顶级）与 12 个示例商品，`get_or_create` 幂等。

***

## 11. home 模块

### 11.1 模块职责

首页导航菜单与轮播图只读查询，支撑前端动态渲染。

### 11.2 数据模型（[models.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/home/models.py)）

| 模型                 | 核心设计                                                                                                                             |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| **NavigationMenu** | index unique、label、path、category(choices: main/profile)、sort\_order、match\_paths JSONField(list)。**无父级自关联**——靠 category 字段区分两组导航 |
| **Banner**         | title、description、image ImageField(upload\_to='banners/')、link URLField、sort\_order、is\_active                                   |

> 注：本模块**无层级菜单父级自关联**，与常见设计不同。`match_paths` 用于前端路由高亮匹配。

### 11.3 URL 路由表

| 路由                   | 视图                    | 方法  | 权限       | 功能           |
| -------------------- | --------------------- | --- | -------- | ------------ |
| `/navigation/menus/` | NavigationMenuViewSet | GET | AllowAny | 导航菜单（无分页）    |
| `/banners/`          | BannerViewSet         | GET | AllowAny | 启用中的轮播图（无分页） |

### 11.4 management/commands

`init_menus`：⚠️ **危险操作** `NavigationMenu.objects.all().delete()` 先清空再 `bulk_create`（重置语义，非幂等）。main 6 项 + profile 5 项。

***

## 12. timer 模块

### 12.1 模块职责

用户魔方还原计时记录的 CRUD 与统计/趋势分析，**单用户隔离查询**。

### 12.2 数据模型（[models.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/timer/models.py)）

#### TimerRecord（[L20-L91](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/timer/models.py#L20-L91)）

| 字段          | 类型            | 约束                                      |
| ----------- | ------------- | --------------------------------------- |
| user        | FK→User       | CASCADE, related\_name='timer\_records' |
| cube\_type  | CharField(10) | choices: 2x2/3x3/4x4/5x5/other          |
| method      | CharField(20) | choices: layer/cfop/roux/zbll/other     |
| time\_ms    | IntegerField  | **毫秒级精度，避免浮点**                          |
| scramble    | TextField     | blank，打乱公式                              |
| created\_at | DateTimeField | auto\_now\_add                          |

### 12.3 URL 路由表

| 路由                | 视图                        | 方法         | 权限              | 功能                   |
| ----------------- | ------------------------- | ---------- | --------------- | -------------------- |
| `/records/`       | TimerRecordViewSet        | GET/POST   | IsAuthenticated | 记录列表/创建              |
| `/records/{id}/`  | TimerRecordViewSet        | GET/DELETE | IsAuthenticated | 详情/删除（校验 user 一致）    |
| `/records/stats/` | TimerRecordViewSet\@stats | GET        | IsAuthenticated | 分组统计（best/avg/count） |
| `/records/trend/` | TimerRecordViewSet\@trend | GET        | IsAuthenticated | 按日期趋势（默认30天）         |

### 12.4 视图说明（[views.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/timer/views.py)）

#### TimerRecordViewSet（[L29-L200](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/timer/views.py#L29-L200)）

- 继承 `ModelViewSet`，permission=`[IsAuthenticated]`
- **无 filter\_backends**，过滤逻辑全在 `get_queryset` 与 action 内手动解析
- **get\_queryset 单用户隔离**（[L49-L75](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/timer/views.py#L49-L75)）：`filter(user=request.user)` + cube\_type/method/start\_date/end\_date
- **stats action**（[L105-L155](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/timer/views.py#L105-L155)）：`values('cube_type','method').annotate(total_count=Count('id'), best_time=Min('time_ms'), avg_time=Avg('time_ms'))`
- **trend action**（[L157-L200](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/timer/views.py#L157-L200)）：参数 days（默认30），按 `created_at__date` 分组

***

## 13. 前端架构（重点：与后端交互）

### 13.1 构建配置（[vite.config.js](file:///e:/BH/PyStudy/ICube/cube_front/vite.config.js)）

**双 Proxy**（dev 和 preview 完全镜像，均监听 `0.0.0.0:5173`）：

- `/api` → `http://127.0.0.1:8000`，`changeOrigin: true`
- `/media` → `http://127.0.0.1:8000`，`changeOrigin: true`

**自动导入**：

```js
AutoImport({ resolvers: [ElementPlusResolver()], imports: ['vue', 'vue-router', 'pinia'] })
Components({ resolvers: [ElementPlusResolver()] })
```

对应约定：业务代码无需 `import { ref } from 'vue'` 或手动注册 EP 组件。

**别名**：`'@'` → `./src`。

### 13.2 应用入口（[main.js](file:///e:/BH/PyStudy/ICube/cube_front/src/main.js) + [App.vue](file:///e:/BH/PyStudy/ICube/cube_front/src/App.vue)）

挂载流程：`createApp(App)` → 注册 EP 图标 → `use(createPinia())` → `use(ElementPlus)` → `use(router)` → 注册全局 errorHandler → `mount('#app')`。

App.vue 极简：仅 `<router-view />` + 清零 body 边距。

### 13.3 HTTP 请求层（[request.js](file:///e:/BH/PyStudy/ICube/cube_front/src/http/request.js)）— 重点

**axios 实例**：

- `baseURL: ''`（**空字符串**，`/api` 前缀在每个 api 模块的 `url` 字段中硬编码）
- `timeout: 5000`

**请求拦截器**（[L37-L46](file:///e:/BH/PyStudy/ICube/cube_front/src/http/request.js#L37-L46)）：

```js
const token = localStorage.getItem('token')
if (token) config.headers['Authorization'] = `Token ${token}`
```

- **直接从 localStorage 取 Token**，未通过 user store（与 store 共享 key 但绕过 Pinia）
- Token 前缀 `Token`（与后端 `CachedJWTAuthentication` 约定一致，非 `Bearer`）

**响应拦截器**（[L56-L81](file:///e:/BH/PyStudy/ICube/cube_front/src/http/request.js#L56-L81)）：

- 成功：`res.code === 100` → `return res`（完整响应体，含 code/msg/data）
- 业务失败：`res.code !== 100` → `ElMessage.error(res.msg || '请求服务器异常,请联系管理员')` + `Promise.reject(new Error(res.msg))`
- HTTP 错误：取 `error.response?.data?.msg`，同样 ElMessage + reject
- ⚠️ **未发现 401 自动跳转登录**，登录态过期依赖组件层 catch

### 13.4 路由系统（[router/index.js](file:///e:/BH/PyStudy/ICube/cube_front/src/router/index.js)）

`createWebHistory` 模式，去除 `#`。

**路由结构**：

- `/`（HomeView，静态 import，父布局）承载所有功能子路由
- `/login`、`/register` 独立页面（无导航栏）

**HomeView 子路由**（节选）：

| path                        | name             | requiresAuth | 用途           |
| --------------------------- | ---------------- | ------------ | ------------ |
| `''`                        | home             | 否            | 首页（Main.vue） |
| `tutorials`                 | tutorials        | 否            | 教程总览         |
| `tutorial/beginner`         | beginnerTutorial | 否            | 新手层先法        |
| `tutorial/cfop`             | cfopTutorial     | 否            | CFOP         |
| `tutorial/oll-essentials` 等 | —                | 否            | CFOP 子页      |
| `formulas`                  | formulas         | 否            | 公式库          |
| `timer`                     | timer            | 否            | 计时器          |
| `forum`                     | forum            | 否            | 论坛           |
| `forum/post/:id`            | postDetail       | 否            | 帖子详情         |
| `forum/create`              | createPost       | **是**        | 创建帖子         |
| `forum/edit/:id`            | editPost         | **是**        | 编辑帖子         |
| `shop`                      | shop             | 否            | 商城           |
| `shop/cart`                 | shopCart         | **是**        | 购物车          |
| `shop/checkout`             | shopCheckout     | **是**        | 结算           |
| `shop/pay/:orderNo`         | shopPay          | **是**        | 支付页          |
| `profiles/*`                | —                | 部分           | 个人中心子页       |

**教程链路**：`/tutorials` → `/tutorial/beginner` / `/tutorial/cfop` → CFOP 子页（oll-essentials/pll-essentials/complete-oll/complete-pll）。

**懒加载**：除 HomeView 外全部 `() => import('@/views/...')`。

⚠️ **路由守卫缺失**：`meta.requiresAuth` 已标记，但 index.js 中**无** **`beforeEach`** **读取该字段**，登录保护实际未在路由层强制，依赖组件层或后端 401 兜底。

### 13.5 状态管理（Pinia stores）

#### user store（[stores/user.js](file:///e:/BH/PyStudy/ICube/cube_front/src/stores/user.js)）

**state**（4 个 ref，初始化时全部从 localStorage 读取）：token / username / bio / image

**actions**：

- `setInfo(data)`：登录后整体写入 4 字段 + 同步 localStorage
- `updateInfo(data)`：局部更新，按字段 `undefined` 判断逐项写
- `clearInfo()`：清空 + `localStorage.clear()`

**持久化**：手动 `localStorage.setItem`，未用 pinia-persistedstate。

⚠️ store 未封装 `login/logout/getUserInfo` action，登录/登出逻辑分散在组件层（Header.vue 直接调 api + store 方法）。

#### cart store（[stores/cart.js](file:///e:/BH/PyStudy/ICube/cube_front/src/stores/cart.js)）

**非传统购物车数据 store**，而是**轻量版本号刷新机制**：

- `cartVersion = ref(0)`（模块级，全局共享）
- `bumpCartVersion()`：`cartVersion.value++`
- Header.vue 通过 `watch(cartVersion, loadCartCount)` 自动重新拉取购物车数量
- 购物车真实数据每次从后端 `getCart()` 拉取，前端不缓存

#### menu store（[stores/menu.js](file:///e:/BH/PyStudy/ICube/cube_front/src/stores/menu.js)）

- state：`allMenus` / `isLoaded`
- getters：`mainMenus`（category==='main'）/ `profileMenus`（category==='profile'）
- `fetchMenus()`：调 `getMenusApi()`，已加载时直接 return

### 13.6 API 模块清单

所有 api 模块统一 `import request from '@/http/request'`，调用形式 `request({ url, method, data/params })`。响应体统一 `{ code, msg, data }`。

#### home.js

| 函数              | 方法  | URL                           | 用途   |
| --------------- | --- | ----------------------------- | ---- |
| `getMenusApi`   | GET | `/api/home/navigation/menus/` | 导航菜单 |
| `getBannersApi` | GET | `/api/home/banners/`          | 轮播图  |

#### user.js（节选）

| 函数                          | 方法     | URL                               | 后端接口                     |
| --------------------------- | ------ | --------------------------------- | ------------------------ |
| `loginApi(data)`            | POST   | `/api/users/login`                | accounts 登录              |
| `registerApi(data)`         | POST   | `/api/users/register`             | accounts 注册              |
| `logoutApi()`               | POST   | `/api/users/logout`               | accounts 登出（jti 黑名单）     |
| `getProfileApi(username)`   | GET    | `/api/profiles/{username}`        | accounts 个人资料            |
| `followUserApi(username)`   | POST   | `/api/profiles/{username}/follow` | 关注                       |
| `unfollowUserApi(username)` | DELETE | `/api/profiles/{username}/follow` | 取关                       |
| `updateProfileApi(data)`    | PATCH  | `/api/users/info`                 | 更新资料（含 File 时 multipart） |

#### posts.js（节选）

| 函数                   | 方法   | URL                              | 用途             |
| -------------------- | ---- | -------------------------------- | -------------- |
| `getPosts(params)`   | GET  | `/api/forum/posts/`              | 分页+分类+关键词      |
| `getPost(id)`        | GET  | `/api/forum/posts/{id}/`         | 详情             |
| `createPost(data)`   | POST | `/api/forum/posts/`              | multipart 上传封面 |
| `likePost(id)`       | POST | `/api/forum/posts/{id}/like/`    | 点赞（data:{}）    |
| `collectPost(id)`    | POST | `/api/forum/posts/{id}/collect/` | 收藏             |
| `getMyPosts(params)` | GET  | `/api/forum/posts/my_posts/`     | 我的帖子           |
| `uploadImage(file)`  | POST | `/api/forum/posts/upload_image/` | 编辑器上传图片        |

#### formula.js（节选）

| 函数                               | 方法     | URL                              | 用途   |
| -------------------------------- | ------ | -------------------------------- | ---- |
| `getFormulaCategories()`         | GET    | `/api/formula/categories/`       | 分类列表 |
| `getFormulaList(params)`         | GET    | `/api/formula/formulas/`         | 公式列表 |
| `matchFormula(data)`             | POST   | `/api/formula/formulas/match/`   | 状态匹配 |
| `addCollection(formulaId)`       | POST   | `/api/formula/collections/`      | 收藏   |
| `removeCollection(collectionId)` | DELETE | `/api/formula/collections/{id}/` | 取消收藏 |

#### shop.js（节选）

| 函数                    | 方法   | URL                          | 用途           |
| --------------------- | ---- | ---------------------------- | ------------ |
| `getProducts(params)` | GET  | `/api/shop/products/`        | 商品列表         |
| `addToCart(data)`     | POST | `/api/shop/cart/`            | 加入购物车        |
| `createOrder(data)`   | POST | `/api/shop/orders/`          | 创建订单（扣库存）    |
| `payOrder(id)`        | PUT  | `/api/shop/orders/{id}/pay/` | 支付（返回支付宝URL） |
| `getAddresses()`      | GET  | `/api/shop/addresses/`       | 地址列表         |

#### timer.js

| 函数                        | 方法   | URL                         | 用途   |
| ------------------------- | ---- | --------------------------- | ---- |
| `createTimerRecord(data)` | POST | `/api/timer/records/`       | 创建记录 |
| `getTimerStats(params)`   | GET  | `/api/timer/records/stats/` | 分组统计 |
| `getTimerTrend(params)`   | GET  | `/api/timer/records/trend/` | 趋势统计 |

### 13.7 布局组件

#### Header.vue（[components/Header.vue](file:///e:/BH/PyStudy/ICube/cube_front/src/components/Header.vue)）

- `el-menu mode="horizontal"` + 动态菜单项（根据路由切换 mainMenus/profileMenus）
- 深度路径匹配 `findActiveMenu`：优先 `match_paths` 前缀匹配，回退精确 `path`
- 购物车角标：`el-badge :value="cartCount"` + `watch(cartVersion, loadCartCount)` 响应式刷新
- 退出登录：`await logoutApi()` → `userStore.clearInfo()` → `router.push('/')`

#### Main.vue（[components/Main.vue](file:///e:/BH/PyStudy/ICube/cube_front/src/components/Main.vue)）

首页主内容区：

- 轮播图（`getBannersApi`，支持内外跳转）
- 热门帖子（`getPosts({ ordering: '-view_count', created_at__gte: 30天前 })`）+ 精选公式（`getFormulaList({ ordering: '-view_count' })`）
- 魔方教程入口三列卡片
- 公式分类标签（`getFormulaCategories()` → `el-tag`）

***

## 14. 部署与运维

### 14.1 docker-compose.yml（[docker-compose.yml](file:///e:/BH/PyStudy/ICube/docker-compose.yml)）

5 服务架构：

| 服务        | image/build          | 关键配置 |
| --------- | -------------------- | -------- |
| **db**    | `mysql:8.0`          | `mysql_data` 持久化；挂载 `init_data.sql`；`mysqladmin ping` 健康检查，`start_period: 45s`；宿主机仅监听 `127.0.0.1:3306` |
| **redis** | `redis:7-alpine`     | `redis_data` 持久化；当前发布宿主机 `6379` |
| **api**   | build `./cube_api`   | 业务代码写入镜像；挂载 `./cube_api/media` 与 `collected_static`；等待 db `service_healthy`、redis `service_started` |
| **front** | build `./cube_front` | Vue `dist` 写入运行镜像，由容器内 Nginx 在 80 端口提供 |
| **nginx** | `nginx:1.28-alpine`  | 发布 80/443；挂载网关配置、证书目录、媒体目录和 `collected_static`；依赖 api、front |

Compose v2 使用 Compose Specification，顶层 `version` 字段已经删除。后端与前端均采用多阶段构建且不挂载源码，容器运行的是构建时写入镜像的代码。

### 14.2 后端 Dockerfile（[cube\_api/Dockerfile](file:///e:/BH/PyStudy/ICube/cube_api/Dockerfile)）

| 阶段 | 配置 |
| ---- | ---- |
| builder | `python:3.13-slim`；安装 gcc、`default-libmysqlclient-dev`、pkg-config；将 gunicorn 和 `requirements.txt` 全部构建为 wheel |
| runtime | `python:3.13-slim`；只安装 `libmariadb3` 和 builder 生成的 wheel，再复制项目代码 |
| 启动 | 先执行 `python manage.py collectstatic --noinput`，再 `exec gunicorn ... --workers 3` |

编译工具不会进入最终镜像。生产启动命令不包含 `--reload`；数据库 migration 不放在容器启动命令中，而由 `deploy.sh` 在服务切换前显式执行。

### 14.3 前端 Dockerfile（[cube\_front/Dockerfile](file:///e:/BH/PyStudy/ICube/cube_front/Dockerfile)）

| 阶段 | 配置 |
| ---- | ---- |
| builder | `node:20-alpine`；`npm ci` 严格使用锁文件；执行 `npm run build` 生成 `/app/dist` |
| runtime | `nginx:1.28-alpine`；复制前端站点配置和 builder 的 `dist`；监听 80 |

运行镜像不包含 Node.js、源码或 npm 依赖。`dist` 位于 `/usr/share/nginx/html`，不再使用 `npm run preview` 或 `front_dist` 卷。

### 14.4 Nginx 配置（[nginx/conf.d/icube.conf](file:///e:/BH/PyStudy/ICube/nginx/conf.d/icube.conf)）

| 路径         | 网关处理方式 |
| ---------- | ------------ |
| `/api/`    | `proxy_pass http://api:8000;`，保留 `/api/` 前缀，透传代理头，连接与读取超时 60s |
| `/media/`  | `alias /usr/share/nginx/html/media/; expires 30d;` |
| `/static/` | `alias /usr/share/nginx/html/static/; expires 30d;` |
| `/`        | `proxy_pass http://front:80;` |

前端容器的 [nginx.conf](file:///e:/BH/PyStudy/ICube/cube_front/nginx.conf) 再负责静态资源：

- `/assets/` 设置一年不可变缓存。
- `index.html` 使用 `no-cache`。
- `try_files $uri $uri/ /index.html` 完成 Vue Router history 模式 SPA 回退。

当前未配置 gzip、`client_max_body_size` 和 HTTPS server 块。Compose 虽映射 443 并挂载证书目录，但站点配置只监听 80。

### 14.5 环境变量清单

| 变量 | Compose 注入值 | 说明 |
| ---- | -------------- | ---- |
| `DJANGO_SETTINGS_MODULE` | `cube_api.settings.prod` | 固定使用生产配置 |
| `DB_NAME` / `DB_USER` / `DB_HOST` / `DB_PORT` | `icube_db` / `icube_api` / `db` / `3306` | 容器网络内使用服务名 `db` |
| `DB_PASSWORD` | `${DB_PASSWORD:-icube123}` | `.env` 优先，未设置时使用默认值 |
| `ALLOWED_HOSTS` | `${ALLOWED_HOSTS:-}` | 逗号分隔主机名，不带协议 |
| `ALLOWED_ORIGIN` | `${ALLOWED_ORIGIN:-}` | 单个主机名或 IP，不带协议 |
| `SERVER_HOST` | `${SERVER_HOST:-localhost}` | 支付宝回调主机，不带协议 |
| `REDIS_URL` | 未显式注入 | `prod.py` 默认使用 `redis://redis:6379/1` |

`prod.py` 支持读取 `SECRET_KEY`，但当前 Compose 尚未把宿主机 `SECRET_KEY` 传入 API。仅写入 `.env` 不会进入容器，需要同时在 `api.environment` 中映射。`.env` 值包含 `$` 时应使用单引号，避免 Compose 变量插值警告。

MySQL 使用固定 root 密码，业务用户密码为 `${DB_PASSWORD:-icube123}`。生产环境应继续将 root 密码和 Django `SECRET_KEY` 外部化。

### 14.6 数据库初始化

MySQL 字符集和监听地址通过 Compose `command` 传入：

```yaml
command:
  - --character-set-server=utf8mb4
  - --collation-server=utf8mb4_unicode_ci
  - --bind-address=0.0.0.0
```

`mysql.conf` 不再 bind mount，避免 Windows Docker Desktop 把文件映射为 `0777` 后被 MySQL 以 world-writable 为由忽略。

- `init_data.sql` 只在 `mysql_data` 为空时由 `/docker-entrypoint-initdb.d/02_init_data.sql` 自动执行。
- 已有数据库不会重复导入初始化脚本。
- 每次 `full` 或 `api` 发布由 `deploy.sh` 执行 `python manage.py migrate --noinput`。
- MySQL 宿主机端口绑定为 `127.0.0.1:3306:3306`；服务器远程管理使用 SSH 隧道，不直接开放公网 3306。

#### Navicat 通过 SSH 隧道连接

当前服务器 SSH 用户为 `bh`，公网 IP 为 `103.100.211.146`。SSH 账号只负责建立加密隧道，MySQL 账号负责数据库认证，两组凭据不能混用。

首次使用公钥认证时，在本地 Windows PowerShell 执行：

```powershell
Get-Content "$env:USERPROFILE\.ssh\id_rsa.pub" |
ssh bh@103.100.211.146 "umask 077; mkdir -p ~/.ssh; cat >> ~/.ssh/authorized_keys; chmod 700 ~/.ssh; chmod 600 ~/.ssh/authorized_keys"
```

公钥会写入服务器的 `/home/bh/.ssh/authorized_keys`。私钥 `C:\Users\Administrator\.ssh\id_rsa` 必须保留在本机，不能上传到服务器或提交 Git。配置完成后可测试：

```powershell
ssh -i "$env:USERPROFILE\.ssh\id_rsa" bh@103.100.211.146
```

Navicat 的「常规」页填写 MySQL 连接信息：

| 配置项 | 值 |
| ------ | -- |
| 主机 | `127.0.0.1` |
| 端口 | `3306` |
| 用户名 | `icube_api` |
| 密码 | 服务器 `.env` 中的 `DB_PASSWORD` |
| 数据库 | `icube_db` |

Navicat 的「SSH」页勾选 SSH 隧道并填写：

| 配置项 | 值 |
| ------ | -- |
| 主机 | `103.100.211.146` |
| 端口 | `22` |
| 用户名 | `bh` |
| 验证方式 | 公钥 |
| 私钥 | `C:\Users\Administrator\.ssh\id_rsa` |
| 通行短语 | 创建私钥时未设置则留空 |

Navicat 中的「公钥」表示使用密钥对认证，但客户端实际选择的是本机私钥 `id_rsa`；`id_rsa.pub` 只放入服务器的 `authorized_keys`。如果出现 `1045 Access denied for user 'root' ... (using password: NO)`，说明 SSH 隧道已经建立，但 MySQL「常规」页错误使用了 `root` 且未发送密码，应改为 `icube_api` 和对应的 `DB_PASSWORD`。

### 14.7 媒体文件夹注意事项

- **`cube_api/media` 必须纳入 Git 版本控制并上传服务器**（项目规则明确要求）
- 包含公式库图片（`formulas/F2L_Images/`、`OLL_Images/`、`PLL_Images/`）、轮播图（`banners/`）、默认头像（`avatars/*.svg`）等业务必需资源
- 生产环境使用宿主机绑定目录：`./cube_api/media:/app/media` 与 `./cube_api/media:/usr/share/nginx/html/media`
- `deploy.sh full` 会在迁移历史根目录 `media/` 前备份新旧目录
- 脚本不执行 `docker compose down -v`；生产环境也禁止手工执行，避免删除 MySQL 和 Redis 数据卷

### 14.8 deploy.sh 发布流程

```bash
bash deploy.sh full   # 首次、全量或基础设施变更
bash deploy.sh api    # 仅后端，包含 migration
bash deploy.sh front  # 仅前端，不停止 API、不操作数据库
```

共同步骤：检查环境 → `git pull --ff-only` → 按模式构建 → 启动目标服务 → 重启网关 Nginx → 验证容器和 HTTP。`full`、`api` 还会等待 MySQL healthy、执行 migration，并检查 MySQL 与 Redis；`api`、`front` 要求服务器已经存在完整部署。

目标容器重建后必须重启网关 Nginx，防止其继续使用旧容器 IP。脚本失败时会输出服务状态及最近 100 行日志。脚本由普通 Docker 用户运行，禁止 `sudo bash deploy.sh`。

***

## 15. 关键设计模式与约定

### 15.1 响应格式约定

所有视图必须用 `utils/common_response.py` 的 `APIResponse`：

```python
return APIResponse(data=serializer.data)                    # 成功
return APIResponse(data=cart, msg='添加成功')               # 成功带消息
return APIResponse(code=400, msg='库存不足')                 # 参数错误
return APIResponse(code=503, msg='支付宝配置异常')           # 服务不可用
```

前端拦截器将 `code !== 100` 视为错误。

### 15.2 认证与 Token 约定

- **Token 前缀**：`Token`（非 `Bearer`）
- **用户实例缓存**：Redis key `user_instance_cache_{user_id}`，TTL 1h
- **注销**：jti 入黑名单（key `jwt:blacklist:{jti}`，TTL = Token 剩余有效期）
- **修改用户状态后需清理 JWT 缓存**

### 15.3 图片处理约定

- **存储相对路径**，禁止硬编码 `http://localhost:8000`
- **URL 生成统一走** `utils/image_url.py` 的 `build_image_url` 添加 `/media/` 前缀
- **ImageFieldFile 处理**：先 `isinstance` 检查 `FieldFile`，再转字符串调用方法；**禁止** **`hasattr(.., 'path')`**（触发 `SuspiciousFileOperation`）
- **公式图片两字段区分**：`thumbnail_file`（用户上传）与 `thumbnail_path`（公式库图片引用）

### 15.4 缓存策略

| 场景        | 缓存键                                 | 策略                                 |
| --------- | ----------------------------------- | ---------------------------------- |
| 用户实例      | `user_instance_cache_{user_id}`     | TTL 1h，只存 ID                       |
| Token 黑名单 | `jwt:blacklist:{jti}`               | TTL = Token 剩余有效期                  |
| 关注关系      | `user:{id}:following` / `followers` | 懒加载 + -1 占位符防穿透（600s）+ Pipeline 批量 |
| 帖子浏览量     | `forum:post:{id}:view`              | `incr` 原子操作 + 1h TTL               |

### 15.5 业务字段约定

- 公式列表排序字段：`view_count`（不是 `views`）
- 公式缩略图路径匹配：`/media/formulas/`（不是 `/media/formula_thumbnails/`）
- 新增/修改公式：按 `category_id` 自动绑定 `target_state_id`，改分类时同步更新
- 公式卡片显示：头部=公式名+难度标签，底部=分类名  by  用户名（中间两个空格）
- 帖子图片关联：全量同步模式（解析 Markdown 所有 `![](url)`，删除多余、补齐缺失）
- 帖子列表布局：flex 左右结构，左侧内容自适应，右侧图片固定 140px，垂直居中；图片 1:1、`object-fit: contain`

### 15.6 DRF 视图约定

- 优先 `ModelViewSet`，复杂逻辑拆到 `services.py`
- 自定义权限类放 `permissions.py`（如 `IsOwnerOrReadOnly`）
- Redis 操作统一封装在 `services.py`（如 `ProfileCacheService`、`PostCacheService`）
- **严禁使用内置** **`logging`** **模块**，只能 `from loguru import logger`

### 15.7 前端约定

- 自动导入：无需 `import { ref } from 'vue'` 或手动注册 EP 组件
- API 请求统一通过 `src/http/request.js`；api 模块导入用 `@/http/request`（**禁止** **`@/utils/request`**）
- Composition API + `<script setup>`
- 禁止硬编码 `localhost:8000`：API 走 `/api` 代理，媒体走 `/media/`
- Three.js 清理（CubeDemo.vue）：`onBeforeUnmount` 中必须 `geometry.dispose()` / `material.dispose()` / `renderer.dispose()` / `cancelAnimationFrame` / 停止 `TWEEN`

***

## 16. 已知问题与优化点

### 16.1 后端

| #  | 位置                                                                                                            | 问题                                                                        | 建议                             |
| -- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------ |
| 1  | [forum/services.py L16, L23-25](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/services.py#L16-L25) | 使用内置 `logging` 模块，违反"只能用 loguru"规则                                        | 改为 `from loguru import logger` |
| 2  | forum/services.py HotPostService                                                                              | 热度算法双实现（Count 版 vs F 表达式版）且权重不一致                                          | 统一为一处实现                        |
| 3  | forum/views.py CommentViewSet                                                                                 | create/destroy 与 signals.py 的 post\_save/post\_delete 重复更新 comment\_count | 移除一处                           |
| 4  | forum/permissions.py                                                                                          | `IsPostOwnerOrReadOnly` 等三个权限类实际未被 PostViewSet 引用（预留代码）                   | 评估删除或启用                        |
| 5  | forum/services.py sync\_all\_views                                                                            | 使用 KEYS 命令阻塞 Redis 主线程                                                    | 改用 SCAN 游标分批遍历                 |
| 6  | accounts/authentication.py                                                                                    | 缓存命中仍需一次 DB 查询（只存 user\_id）                                               | 评估缓存完整对象（注意敏感信息）               |
| 7  | formula/services.py \_execute\_formula                                                                        | 魔方转动模拟未实现，match 退化为原状态比较                                                  | 实现真实转动模拟                       |
| 8  | formula import\_formulas                                                                                      | 硬编码绝对路径 `E:\BH\PyStudy\web_projects\ICube\files\...`                      | 改为相对路径或环境变量                    |
| 9  | timer/serializers.py                                                                                          | TimerTrendSerializer 字段（times）与视图返回（best\_time）不一致                        | 对齐字段                           |
| 10 | formula insert\_cube\_states                                                                                  | 状态格式（faces 矩阵）与 CubeStateService 验证（blocks 列表）不兼容                         | 统一格式                           |

### 16.2 前端

| # | 位置                                                                                           | 问题                                           | 建议              |
| - | -------------------------------------------------------------------------------------------- | -------------------------------------------- | --------------- |
| 1 | [http/request.js](file:///e:/BH/PyStudy/ICube/cube_front/src/http/request.js#L37-L46)        | 请求拦截器绕过 Pinia 直接读 localStorage               | 改为通过 user store |
| 2 | [http/request.js](file:///e:/BH/PyStudy/ICube/cube_front/src/http/request.js#L56-L81)        | 响应拦截器无 401 自动跳登录                             | 增加 401 路由跳转     |
| 3 | [router/index.js](file:///e:/BH/PyStudy/ICube/cube_front/src/router/index.js)                | `meta.requiresAuth` 标记存在但无 `beforeEach` 守卫   | 补全全局守卫          |
| 4 | [api/comments.js L24-30](file:///e:/BH/PyStudy/ICube/cube_front/src/api/comments.js#L24-L30) | getComments 用 `data` 传分页参数（GET 应该用 `params`） | 改为 `params`     |

### 16.3 部署

| # | 位置 | 当前问题 | 建议 |
| - | ---- | -------- | ---- |
| 1 | docker-compose.yml api environment | `prod.py` 支持 `SECRET_KEY`，但 Compose 未将该变量传入 API | 增加 `SECRET_KEY=${SECRET_KEY}` 并在服务器安全配置 |
| 2 | docker-compose.yml db environment | `MYSQL_ROOT_PASSWORD` 仍硬编码 | 改为受保护的环境变量或 Secret |
| 3 | docker-compose.yml redis ports | Redis 使用 `6379:6379`，可能暴露到公网网卡 | 无宿主机访问需求时移除；否则绑定 `127.0.0.1` |
| 4 | nginx 配置 | 未配置 `client_max_body_size`，默认 1MB 可能小于后端上传限制 | 增加合适的上传大小限制 |
| 5 | nginx 配置 | Compose 映射 443，但没有 HTTPS server 块 | 配置证书、TLS 和 HTTP 跳转 |
| 6 | redis/api/front | 缺少 Compose healthcheck，Nginx `depends_on` 只保证启动顺序 | 增加 Redis PING、API `/health/` 和前端 HTTP 检查 |
| 7 | init\_data.sql | 表 collation `utf8mb4_0900_ai_ci` 与 Compose 的 `utf8mb4_unicode_ci` 不一致 | 统一排序规则 |

***

## 17. 常用命令速查

### 17.1 本地开发

```bash
# 后端（固定 Python 解释器）
cd cube_api
E:\software\python\python313\env\cube_api\Scripts\python.exe manage.py runserver 8000 --settings=cube_api.settings.dev

# 前端（/api → 127.0.0.1:8000）
cd cube_front
npm run dev
```

### 17.2 生产部署

```bash
# 首次部署或全量更新
bash deploy.sh full

# 仅更新后端（自动 migration）
bash deploy.sh api

# 仅更新前端
bash deploy.sh front

# 查看状态和日志
docker compose ps
docker compose logs -f api nginx

# 创建超级用户（服务已运行）
docker compose exec api python manage.py createsuperuser
```

API 代码位于镜像内，代码更新后仅执行 `docker compose restart api` 不会加载新代码，必须重新构建镜像。API 容器启动时自动 `collectstatic`，数据库 migration 由 `deploy.sh full/api` 执行。

### 17.3 测试

```bash
# 全部测试（自动切 SQLite 内存库 + Mock Redis + 禁用限流 + MD5）
docker compose exec api python manage.py test

# 单测试模块
docker compose exec api python manage.py test apps.forum.tests.test_models
```

### 17.4 数据初始化

```bash
# 初始化首页导航菜单（⚠️ 先 delete 再 insert，非幂等）
docker compose exec api python manage.py init_menus

# 初始化商城商品（get_or_create，幂等）
docker compose exec api python manage.py init_shop_data

# 从 Excel 导入 CFOP 公式（硬编码路径）
docker compose exec api python manage.py import_formulas

# 插入 F2L/OLL/PLL 目标状态
docker compose exec api python manage.py insert_cube_states
```

### 17.5 API 文档

- Swagger UI：`http://<server>/api/schema/swagger-ui/`
- Redoc：`http://<server>/api/schema/redoc/`
- OpenAPI Schema：`http://<server>/api/schema/`

***

## 附录：模块依赖关系图

```
                    ┌──────────────────────────────────┐
                    │         accounts (认证核心)      │
                    │  User / JWT / 关注粉丝缓存        │
                    └────────┬─────────────────────────┘
                             │ FK→User
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
    forum              formula                shop
   (帖子/评论)        (公式库)             (商城/支付)
        │                    │                    │
        │   forum._sync_post_images 引用           │
        │   /media/formulas/ 公式库图片            │
        └───────────────────►│                    │
                             │                    │
                             │  accounts.ProfileCacheService
                             │  .get_collection_count
                             │  反向引用 FormulaCollection
                             ◄────────────────────┘
                                                    │
                                                    │ shop 支付宝
                                                    ▼
                                               alipay_config
                                                    │
                                                    ▼
                                          apps/shop/keys/ (禁止提交)

    独立模块：
    home   (导航/轮播，纯只读，无业务耦合)
    timer  (计时记录，单用户隔离，无缓存层)

    工具层被所有模块依赖：
    utils.common_response   →  统一响应
    utils.common_exception  →  统一异常处理
    utils.common_pagination →  统一分页
    utils.image_url         →  图片 URL 标准化
    utils.image_processor   →  图像处理
    settings.logger_conf    →  Loguru 日志接管
```

***

> 文档生成日期：2026-08-06
> 基于代码库实际状态分析，所有引用均使用可点击的 `file://` 链接格式。
