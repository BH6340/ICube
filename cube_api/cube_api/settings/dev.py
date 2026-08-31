# -*- coding: utf-8 -*-
"""
开发环境配置文件

该文件包含项目的所有开发环境配置，生产环境配置在 prod.py 中通过继承此文件并覆盖部分配置实现。

文件结构：
    1. 路径配置（BASE_DIR、sys.path）
    2. 安全配置（SECRET_KEY、DEBUG、ALLOWED_HOSTS）
    3. 应用配置（INSTALLED_APPS）
    4. 中间件配置（MIDDLEWARE）
    5. 数据库配置（DATABASES）
    6. 缓存配置（CACHES、Redis）
    7. DRF 配置（REST_FRAMEWORK）
    8. JWT 配置（SIMPLE_JWT）
    9. 其他业务配置（FORUM_CONFIG、SPECTACULAR_SETTINGS）
    10. 日志配置（LOGGING）
    11. CORS 配置

设计特点：
    - 通过环境变量动态获取敏感配置（数据库密码、Redis 地址等）
    - 测试环境自动切换为 SQLite 内存数据库和专用 Redis 数据库
    - 禁用 Django 默认日志，使用 Loguru 作为日志框架
    - 自定义用户模型（AUTH_USER_MODEL）
    - 统一响应格式、统一异常处理、统一分页器
"""
import sys, os

from pathlib import Path
from datetime import timedelta

# 测试环境检测：manage.py test 或 pytest 运行时均为 True
_IS_TEST = 'test' in sys.argv or 'pytest' in sys.modules

# ==================== 路径配置 ====================

# 项目根目录（包含 manage.py 的 cube_api/ 目录）
# 基于当前文件位置解析，避免依赖进程启动目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 将项目包目录（cube_api/cube_api/）加入 Python 模块搜索路径
# 支持直接导入 utils、settings 等项目级模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 将 apps 目录加入 Python 模块搜索路径
# 保留应用模块的直接导入兼容性
APPS_DIR = Path(__file__).resolve().parent.parent / 'apps'
if APPS_DIR.exists():
    sys.path.insert(0, str(APPS_DIR))

# 将项目根目录加入 Python 模块搜索路径
# 确保 manage.py 与服务进程使用一致的导入行为
sys.path.insert(0, str(BASE_DIR))

# ==================== 安全配置 ====================

# Django 加密签名密钥，用于 Session、密码重置令牌和消息等签名场景
# 开发环境使用固定值；生产环境必须通过环境变量覆盖
SECRET_KEY = 'django-insecure-t_8fu67t$62)5i7d#zrkbtv4n+fft8e#szjw8*2%wx-x#+j#3a'

# 调试模式：开发环境开启，生产环境必须关闭
# DEBUG = True 会暴露详细错误信息，不可用于生产环境
DEBUG = True

# 开发环境接受任意 Host；生产环境必须改为明确的域名或 IP 列表
ALLOWED_HOSTS = ['*']

# 生成图片、邮件等绝对 URL 时使用的站点地址
# 开发环境默认指向本地服务，生产环境通过 SITE_DOMAIN 覆盖
SITE_DOMAIN = os.getenv('SITE_DOMAIN', 'http://localhost:8000')

# ==================== 应用配置 ====================

INSTALLED_APPS = [
    # django-unfold 必须在 Django 内置应用之前注册
    # 基于 Tailwind CSS 重构 Django Admin 界面
    'unfold',                        # Unfold 核心应用
    'unfold.contrib.filters',        # Unfold 扩展过滤器（提供更丰富的侧边栏筛选组件）

    # Django 内置应用
    'django.contrib.admin',          # 后台管理系统
    'django.contrib.auth',           # 认证系统
    'django.contrib.contenttypes',   # 内容类型框架
    'django.contrib.sessions',       # 会话管理
    'django.contrib.messages',       # 消息框架
    'django.contrib.staticfiles',    # 静态文件管理
    # 第三方应用
    'corsheaders',                   # CORS 跨域支持
    'rest_framework',                # Django REST Framework
    'rest_framework_simplejwt',      # JWT 认证支持
    'drf_spectacular',               # OpenAPI 文档生成
    # 自定义应用
    'apps.home',                     # 首页导航模块
    'apps.accounts',                 # 用户认证模块
    'apps.forum',                    # 论坛模块
    'apps.formula',                  # 公式库模块
    'apps.shop',                     # 商城模块
    'apps.timer'                     # 计时器模块
]

# ==================== 中间件配置 ====================

MIDDLEWARE = [
    # 尽可能靠前，确保短路响应和错误响应也能附加 CORS 响应头
    'corsheaders.middleware.CorsMiddleware',
    # 安全中间件：处理安全相关的 HTTP 头
    'django.middleware.security.SecurityMiddleware',
    # 会话中间件：管理用户会话
    'django.contrib.sessions.middleware.SessionMiddleware',
    # 通用中间件：处理 URL 重写、内容类型等
    'django.middleware.common.CommonMiddleware',
    # CSRF 中间件：防止跨站请求伪造
    'django.middleware.csrf.CsrfViewMiddleware',
    # 认证中间件：将用户信息附加到请求对象
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 消息中间件：管理消息框架
    'django.contrib.messages.middleware.MessageMiddleware',
    # 点击劫持防护中间件
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 路由配置：指定项目的根 URL 配置文件
ROOT_URLCONF = 'cube_api.urls'

# 模板配置：项目使用 Django 模板引擎
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # 自定义模板目录
        'APP_DIRS': True,  # 自动查找各应用下的 templates 目录
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',  # 模板中可访问 request 对象
                'django.contrib.auth.context_processors.auth',  # 模板中可访问用户信息
                'django.contrib.messages.context_processors.messages',  # 模板中可访问消息
            ],
        },
    },
]

# ==================== 缓存配置 ====================

# 兼容保留的初始缓存声明
# 下方“Redis 配置”会根据测试或非测试环境重新赋值 CACHES
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",  # Redis 地址和数据库编号
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Session 数据存入 default 缓存，多个应用实例可共享登录状态
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# Session 配置
SESSION_COOKIE_AGE = 3600 * 24  # Session 有效期：1 天
SESSION_SAVE_EVERY_REQUEST = True  # 每次请求刷新 Session 过期时间

# WSGI 应用配置：指定 WSGI 入口文件
WSGI_APPLICATION = 'cube_api.wsgi.application'

# ==================== 数据库配置 ====================

# 优先读取环境变量，未配置时使用本地开发默认值
DB_NAME = os.getenv('DB_NAME', 'icube')           # 数据库名称
DB_USER = os.getenv('DB_USER', 'icube_api')       # 数据库用户名
DB_PASSWORD = os.getenv('DB_PASSWORD', 'icube123?') # 数据库密码
DB_HOST = os.getenv('DB_HOST', 'localhost')       # 数据库主机
DB_PORT = os.getenv('DB_PORT', '3306')            # 数据库端口

# 使用 MySQL 作为数据库引擎
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # MySQL 数据库引擎
        'NAME': DB_NAME,                       # 数据库名称
        'USER': DB_USER,                       # 用户名
        'PASSWORD': DB_PASSWORD,               # 密码
        'HOST': DB_HOST,                       # 主机地址
        'PORT': DB_PORT,                       # 端口
    }
}

# manage.py test / pytest 使用 SQLite 内存数据库
# 数据库随测试进程销毁，不会写入本地 MySQL
if _IS_TEST:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # 内存数据库，速度最快
    }

# ==================== Redis 配置 ====================

# Redis 公共选项，由开发、测试及 prod.py 复用
REDIS_BASE_OPTIONS = {
    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    # 连接池满时等待空闲连接，避免立即抛出连接池耗尽异常
    'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
    'CONNECTION_POOL_CLASS_KWARGS': {
        'max_connections': 50,  # 连接池最多维护 50 个连接
        'timeout': 20,          # 获取空闲连接最多等待 20 秒，不是网络连接超时
    },
    # 缓存值必须是 JSON 可序列化的数据
    'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
}

# 测试与开发环境使用不同 Redis 数据库和键前缀
if _IS_TEST:
    # 测试环境：cache 用 LocMemCache（内存实现），Redis 直连用 fakeredis 模拟
    # 两者配合覆盖所有缓存场景，无需真实 Redis 服务
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'icube_test_cache',
            'KEY_PREFIX': 'icube_test',
            'TIMEOUT': 300,
        }
    }
    # 仅为缩短测试耗时；MD5PasswordHasher 不可用于真实用户密码
    PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ]
else:
    # 非测试环境默认值；生产环境会在 prod.py 中覆盖地址和键前缀
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/1',  # 使用数据库 1
            'OPTIONS': REDIS_BASE_OPTIONS,
            'KEY_PREFIX': 'icube',       # 缓存键前缀
            'TIMEOUT': 86400,           # 默认缓存有效期：24 小时
        }
    }



# ==================== 密码验证配置 ====================

AUTH_PASSWORD_VALIDATORS = [
    # 验证密码与用户属性（如用户名、邮箱）的相似度
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    # 验证密码最小长度
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    # 验证密码不在常见密码列表中
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    # 验证密码不全是数字
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ==================== 国际化配置 ====================

LANGUAGE_CODE = 'zh-hans'       # 默认语言：简体中文
TIME_ZONE = 'Asia/Shanghai'     # 默认时区：Asia/Shanghai
USE_I18N = True                 # 启用国际化翻译
USE_TZ = False                  # 使用本地时间，不启用时区感知 datetime

# ==================== 静态文件与媒体文件配置 ====================

# 静态文件 URL 前缀（当前为相对路径）
STATIC_URL = 'static/'

# 项目级静态文件目录（存放自定义 admin 静态资源等）
STATICFILES_DIRS = [BASE_DIR / 'static']

# 媒体文件配置（用户上传的文件，如头像、商品图片等）
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # 媒体文件在服务器上的物理存储路径
MEDIA_URL = '/media/'                         # 媒体文件的访问 URL 前缀

# 启动时确保媒体文件目录存在
if not os.path.exists(MEDIA_ROOT):
    os.makedirs(MEDIA_ROOT)

# 默认主键字段类型：使用 BigAutoField（自增大整数）
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 自定义用户模型：指定使用 accounts 应用的 User 模型
# 格式：应用标签.模型名
AUTH_USER_MODEL = 'accounts.User'

# ==================== DRF 配置 ====================

# 配置项总览；下方分支会完全覆盖该字典并生成最终配置
REST_FRAMEWORK = {
    # 统一分页器：使用自定义的 UnifiedPagination，返回统一格式
    'DEFAULT_PAGINATION_CLASS': 'utils.common_pagination.UnifiedPagination',
    'PAGE_SIZE': 20,  # 默认每页 20 条
    # 统一异常处理：使用自定义的 common_exception_handler
    'EXCEPTION_HANDLER': 'utils.common_exception.common_exception_handler',
    # 过滤器后端：支持字段过滤查询
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend'
    ],
    # 认证类：使用自定义的 CachedJWTAuthentication（带 Redis 缓存）
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.accounts.authentication.CachedJWTAuthentication',
    ],
    # API 文档生成：使用 drf-spectacular
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # 限流策略：防止接口被滥用
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',  # 针对匿名用户
        'rest_framework.throttling.UserRateThrottle',  # 针对登录用户
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',       # 匿名用户每天最多 100 次请求
        'user': '1000/day',      # 登录用户每天最多 1000 次请求
        'login_scope': '3/min',  # LoginRateThrottle 使用的登录频率，登录接口每分钟最多 3 次请求（防止暴力破解）
    }
}

# 根据运行环境生成最终 DRF 配置
if _IS_TEST:
    # 测试环境保留限流类但设超大限流，确保限流代码路径被测试但不会真正拦截
    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'apps.accounts.authentication.CachedJWTAuthentication',
        ],
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.IsAuthenticatedOrReadOnly',
        ],
        'DEFAULT_THROTTLE_CLASSES': [
            'rest_framework.throttling.AnonRateThrottle',
            'rest_framework.throttling.UserRateThrottle',
        ],
        'DEFAULT_THROTTLE_RATES': {
            'anon': '10000/minute',
            'user': '10000/minute',
            'login_scope': '10000/minute',
            'send_code_scope': '10000/minute',
        },
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
        'PAGE_SIZE': 20,
        'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    }
else:
    # 非测试环境默认配置，生产环境直接继承
    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'apps.accounts.authentication.CachedJWTAuthentication',
        ],
        # 默认权限：认证用户可读写，匿名用户只读
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.IsAuthenticatedOrReadOnly',
        ],
        'DEFAULT_THROTTLE_CLASSES': [
            'rest_framework.throttling.AnonRateThrottle',
            'rest_framework.throttling.UserRateThrottle',
        ],
        'DEFAULT_THROTTLE_RATES': {
            'anon': '100/day',
            'user': '1000/day',
            'login_scope': '5/minute',  # LoginRateThrottle 每分钟最多尝试 5 次
            'send_code_scope': '10/min',  # 验证码发送限流：开发环境放宽到每分钟10次
        },
        'DEFAULT_PAGINATION_CLASS': 'utils.common_pagination.UnifiedPagination',
        'PAGE_SIZE': 20,
        'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    }

# 兼容测试代码对原生 Redis 连接的访问
# 返回 fakeredis.FakeRedis 实例，使 .exists()/.sadd()/.scard() 等方法可用
if _IS_TEST:
    import django_redis
    import fakeredis

    _fake_redis = fakeredis.FakeRedis()

    def mock_get_redis_connection(alias):
        return _fake_redis

    django_redis.get_redis_connection = mock_get_redis_connection

# ==================== 邮件 SMTP 配置 ====================

# 使用 QQ 邮箱 SMTP 服务发送验证码邮件
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.qq.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 465))
EMAIL_USE_SSL = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_DISPLAY_NAME = os.getenv('EMAIL_DISPLAY_NAME', 'ICube魔方平台')
DEFAULT_FROM_EMAIL = f'"{EMAIL_DISPLAY_NAME}" <{EMAIL_HOST_USER}>' if EMAIL_HOST_USER else EMAIL_HOST_USER

# 测试环境使用内存后端，不实际发送邮件
if _IS_TEST:
    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# 开发环境假邮箱后缀列表：匹配这些后缀的邮箱直接返回固定验证码 999999，不实际发送
EMAIL_TEST_SUFFIXES = ['@test.com', '@example.com', '@fake.com']

# SMTP 发送开关：False 时所有邮箱都用 999999 固定验证码（服务器端口被封时使用）
EMAIL_SMTP_ENABLED = os.getenv('EMAIL_SMTP_ENABLED', 'True') == 'True'

# ==================== 业务配置 ====================

# 论坛模块配置
FORUM_CONFIG = {
    'POST_MIN_TITLE_LENGTH': 5,                    # 帖子标题最小长度
    'POST_MAX_TITLE_LENGTH': 200,                  # 帖子标题最大长度
    'POST_MIN_CONTENT_LENGTH': 10,                 # 帖子内容最小长度
    'COMMENT_MIN_CONTENT_LENGTH': 2,               # 评论内容最小长度
    'HOT_POST_DAYS': 7,                            # 热门帖子统计天数
    'HOT_POST_LIMIT': 20,                          # 热门帖子数量限制
    'MAX_FILE_SIZE': 5 * 1024 * 1024,              # 最大文件大小（5 MB）
    'ALLOWED_FILE_EXTENSIONS': ['.md'],             # 允许的文件扩展名
}

# ==================== JWT 配置 ====================

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),     # Access Token 有效期：7 天
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),    # Refresh Token 有效期：7 天
    'ROTATE_REFRESH_TOKENS': True,                 # 刷新 Access Token 时签发新的 Refresh Token
    'UPDATE_LAST_LOGIN': True,                     # 更新最后登录时间
    'AUTH_HEADER_TYPES': ('Token',)                 # Authorization 格式：Token <token>
}

# ==================== OpenAPI 文档配置 ====================

SPECTACULAR_SETTINGS = {
    'TITLE': 'ICube API',                              # API 标题
    'DESCRIPTION': '项目接口文档',                      # API 描述
    'VERSION': '1.0.0',                                # API 版本号
    'SERVE_INCLUDE_SCHEMA': False,                     # 不在文档中包含 Schema 自身
    'AUTHENTICATION_WHITELIST': [],                    # 兼容保留项，drf-spectacular 不读取此键
    'SCHEMA_PATH_PREFIX': '/api/',                     # API 路径前缀
    'TAGS': [                                          # 接口分类标签
        {'name': 'users', 'description': '用户管理'},
        {'name': 'profiles', 'description': '用户资料浏览'},
        {'name': 'forum', 'description': '论坛帖子管理'},
        {'name': 'comments', 'description': '评论系统'},
        {'name': 'tags', 'description': '标签管理'},
        {'name': 'reports', 'description': '举报管理'},
    ],
}

# ==================== 日志配置 ====================

# 禁用 Django 默认 dictConfig，统一交由 Loguru 配置
LOGGING_CONFIG = None

# 保留空配置，避免其他模块读取 LOGGING 时缺少设置
LOGGING = {}

# 初始化项目 Loguru 日志处理器
from .logger_conf import setup_logging
setup_logging()

# ==================== django-unfold 后台主题配置 ====================

# 允许同源页面嵌入管理后台，满足 Unfold 组件需求
X_FRAME_OPTIONS = 'SAMEORIGIN'

UNFOLD = {
    "SITE_TITLE": "ICube",
    "SITE_HEADER": "ICube 管理后台",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "认证和授权",
                "icon": "lock",
                "collapsible": True,
                "items": [
                    {"title": "用户组", "link": "/admin/auth/group/"},
                    {"title": "权限", "link": "/admin/auth/permission/"},
                ],
            },
            {
                "title": "Home",
                "icon": "home",
                "collapsible": True,
                "items": [
                    {"title": "导航菜单", "link": "/admin/home/navigationmenu/"},
                ],
            },
            {
                "title": "Accounts",
                "icon": "people",
                "collapsible": True,
                "items": [
                    {"title": "用户列表", "link": "/admin/accounts/user/"},
                ],
            },
            {
                "title": "论坛",
                "icon": "message",
                "collapsible": True,
                "items": [
                    {"title": "标签", "link": "/admin/forum/tag/"},
                    {"title": "帖子", "link": "/admin/forum/post/"},
                    {"title": "评论", "link": "/admin/forum/comment/"},
                    {"title": "举报记录", "link": "/admin/forum/report/"},
                    {"title": "帖子图片", "link": "/admin/forum/postimage/"},
                ],
            },
            {
                "title": "魔方公式",
                "icon": "cube",
                "collapsible": True,
                "items": [
                    {"title": "魔方分类", "link": "/admin/formula/cubecategory/"},
                    {"title": "魔方状态", "link": "/admin/formula/cubestate/"},
                    {"title": "公式", "link": "/admin/formula/formula/"},
                    {"title": "公式标签", "link": "/admin/formula/formulatag/"},
                    {"title": "公式收藏", "link": "/admin/formula/formulacollection/"},
                ],
            },
            {
                "title": "Timer",
                "icon": "timer",
                "collapsible": True,
                "items": [
                    {"title": "计时记录", "link": "/admin/timer/timerrecord/"},
                ],
            },
            {
                "title": "商城",
                "icon": "shopping_cart",
                "collapsible": True,
                "items": [
                    {"title": "商品分类", "link": "/admin/shop/productcategory/"},
                    {"title": "商品", "link": "/admin/shop/product/"},
                    {"title": "购物车", "link": "/admin/shop/cart/"},
                    {"title": "订单", "link": "/admin/shop/order/"},
                    {"title": "订单明细", "link": "/admin/shop/orderitem/"},
                ],
            },
        ],
    },
}

# ==================== CORS 配置 ====================

# 开发环境常用来源；全开放开关启用时该列表不参与限制
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",    # Vite 默认端口
    "http://127.0.0.1:5173",
]

# 仅用于开发联调。prod.py 继承本文件后必须显式覆盖为 False，
# 否则生产环境的 CORS_ALLOWED_ORIGINS 白名单不会生效
CORS_ALLOW_ALL_ORIGINS = True

