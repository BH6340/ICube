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

# ==================== 路径配置 ====================

# 项目根目录（cube_api/ 目录，包含 manage.py）
# 通过 __file__ 逐层向上解析，确保路径正确
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 将项目配置根目录（cube_api/cube_api/）加入 Python 路径
# 这样可以直接导入 utils、settings 等模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 将 apps 目录加入环境变量
# 使用 pathlib 的 / 运算符拼接路径，比 os.path.join 更简洁直观
APPS_DIR = Path(__file__).resolve().parent.parent / 'apps'
if APPS_DIR.exists():
    sys.path.insert(0, str(APPS_DIR))

# 将项目根目录加入环境变量
# 方便导入项目级别的包和模块
sys.path.insert(0, str(BASE_DIR))

# ==================== 安全配置 ====================

# 密钥：用于 Django 的密码加密、CSRF 保护、会话签名等
# 开发环境使用固定密钥，生产环境必须通过环境变量配置
SECRET_KEY = 'django-insecure-t_8fu67t$62)5i7d#zrkbtv4n+fft8e#szjw8*2%wx-x#+j#3a'

# 调试模式：开发环境开启，生产环境必须关闭
# DEBUG=True 时会显示详细的错误堆栈信息，存在安全风险
DEBUG = True

# 允许访问的主机列表
# 开发环境使用 '*' 允许所有主机访问，生产环境应严格限制
ALLOWED_HOSTS = ['*']

# 站点域名配置，用于生成绝对URL（如图片链接、邮件中的链接等）
# 开发环境使用本地地址，生产环境通过环境变量 SITE_DOMAIN 配置
SITE_DOMAIN = os.getenv('SITE_DOMAIN', 'http://localhost:8000')

# ==================== 应用配置 ====================

INSTALLED_APPS = [
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
    # CORS 中间件：必须放在最前面，确保 CORS 响应头在其他中间件之前设置
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

# 使用 Redis 作为缓存后端
# 开发环境使用本地 Redis，数据库编号为 1
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",  # Redis 地址和数据库编号
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# 让 Session 使用缓存后端（Redis）
# 这样 Session 数据存储在 Redis 中，支持分布式部署
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# Session 配置
SESSION_COOKIE_AGE = 3600 * 24  # Session 过期时间：1天（秒）
SESSION_SAVE_EVERY_REQUEST = True  # 每次请求刷新 Session 过期时间

# WSGI 应用配置：指定 WSGI 入口文件
WSGI_APPLICATION = 'cube_api.wsgi.application'

# ==================== 数据库配置 ====================

# 动态获取数据库连接参数
# 通过环境变量配置，默认值用于开发环境
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

# 测试环境自动切换为 SQLite 内存数据库
# 当命令行参数包含 'test' 时（如 python manage.py test），使用 SQLite 内存数据库
# 内存数据库速度快，测试完成后自动销毁，不会污染开发数据库
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # 内存数据库，速度最快
    }

# ==================== Redis 配置 ====================

# Redis 基础配置模板，避免代码冗余
# 定义公共配置后，开发、测试、生产环境可复用
REDIS_BASE_OPTIONS = {
    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    # 使用阻塞连接池，防止连接耗尽
    'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
    'CONNECTION_POOL_CLASS_KWARGS': {
        'max_connections': 50,  # 最大连接数
        'timeout': 20,          # 连接超时时间（秒）
    },
    # 使用 JSON 序列化器，方便存储复杂数据结构
    'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
}

# 根据环境动态配置缓存
if 'test' in sys.argv or 'pytest' in sys.modules:
    # 测试环境配置
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/3',  # 使用数据库 3，与开发环境隔离
            'OPTIONS': REDIS_BASE_OPTIONS,
            'KEY_PREFIX': 'icube_test',  # 添加测试前缀，防止污染开发数据
            'TIMEOUT': 300,  # 测试环境缓存超时时间短（5分钟）
        }
    }
    # 测试环境使用更快的密码哈希器（MD5），加速测试
    # 注意：生产环境必须使用强哈希算法（如 PBKDF2）
    PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ]
else:
    # 开发/生产环境配置
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/1',  # 使用数据库 1
            'OPTIONS': REDIS_BASE_OPTIONS,
            'KEY_PREFIX': 'icube',       # 缓存键前缀
            'TIMEOUT': 86400,           # 默认缓存超时时间：24小时（秒）
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

LANGUAGE_CODE = 'zh-hans'       # 使用简体中文
TIME_ZONE = 'Asia/Shanghai'     # 使用上海时区
USE_I18N = True                 # 启用国际化
USE_TZ = False                  # 不使用时区感知时间（数据库存储本地时间）

# ==================== 静态文件与媒体文件配置 ====================

# 静态文件 URL 前缀
STATIC_URL = 'static/'

# 媒体文件配置（用户上传的文件，如头像、商品图片等）
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # 媒体文件在服务器上的物理存储路径
MEDIA_URL = '/media/'                         # 媒体文件的访问 URL 前缀

# 确保 media 目录存在，项目启动时自动创建
if not os.path.exists(MEDIA_ROOT):
    os.makedirs(MEDIA_ROOT)

# 默认主键字段类型：使用 BigAutoField（自增大整数）
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 自定义用户模型：指定使用 accounts 应用的 User 模型
# 格式：应用标签.模型名
AUTH_USER_MODEL = 'accounts.User'

# ==================== DRF 配置 ====================

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
        'login_scope': '3/min',  # 登录接口每分钟最多 3 次请求（防止暴力破解）
    }
}

# 根据环境重新配置 DRF
if 'test' in sys.argv:
    # 测试环境：禁用限流，加速测试
    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'apps.accounts.authentication.CachedJWTAuthentication',
        ],
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.IsAuthenticatedOrReadOnly',
        ],
        'DEFAULT_THROTTLE_CLASSES': [],  # 清空限流类
        'DEFAULT_THROTTLE_RATES': {},    # 清空限流速率
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
        'PAGE_SIZE': 20,
        'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    }
else:
    # 开发/生产环境完整配置
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
            'login_scope': '5/minute',  # 登录接口限流
        },
        'DEFAULT_PAGINATION_CLASS': 'utils.common_pagination.UnifiedPagination',
        'PAGE_SIZE': 20,
        'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    }

# 测试环境 Mock Redis 连接
# 将 django_redis.get_redis_connection 替换为返回 cache 对象
# 这样测试时可以使用 Django 的测试缓存（内存缓存）而不需要真实的 Redis
if 'test' in sys.argv:
    import django_redis
    def mock_get_redis_connection(alias):
        from django.core.cache import cache
        return cache
    django_redis.get_redis_connection = mock_get_redis_connection

# ==================== 业务配置 ====================

# 论坛模块配置
FORUM_CONFIG = {
    'POST_MIN_TITLE_LENGTH': 5,                    # 帖子标题最小长度
    'POST_MAX_TITLE_LENGTH': 200,                  # 帖子标题最大长度
    'POST_MIN_CONTENT_LENGTH': 10,                 # 帖子内容最小长度
    'COMMENT_MIN_CONTENT_LENGTH': 2,               # 评论内容最小长度
    'HOT_POST_DAYS': 7,                            # 热门帖子统计天数
    'HOT_POST_LIMIT': 20,                          # 热门帖子数量限制
    'MAX_FILE_SIZE': 5 * 1024 * 1024,              # 最大文件大小（5MB）
    'ALLOWED_FILE_EXTENSIONS': ['.md'],             # 允许的文件扩展名
}

# ==================== JWT 配置 ====================

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),     # Access Token 有效期：7天
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),    # Refresh Token 有效期：7天
    'ROTATE_REFRESH_TOKENS': True,                 # 启用 Token 轮换
    'UPDATE_LAST_LOGIN': True,                     # 更新最后登录时间
    'AUTH_HEADER_TYPES': ('Token',)                 # 认证头类型：Token <token>
}

# ==================== OpenAPI 文档配置 ====================

SPECTACULAR_SETTINGS = {
    'TITLE': 'ICube API',                              # API 标题
    'DESCRIPTION': '项目接口文档',                      # API 描述
    'VERSION': '1.0.0',                                # API 版本号
    'SERVE_INCLUDE_SCHEMA': False,                     # 不在文档中包含 Schema 自身
    'AUTHENTICATION_WHITELIST': [],                    # 忽略认证警告
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

# 1. 禁用 Django 默认的日志配置系统
LOGGING_CONFIG = None

# 2. 显式置空，防止 Django 自动加载默认配置
LOGGING = {}

# 3. 使用自定义的 Loguru 日志配置
from .logger_conf import setup_logging
setup_logging()

# ==================== CORS 配置 ====================

# 允许的前端来源（开发环境）
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",    # Vite 默认端口
    "http://127.0.0.1:5173",
]

# 允许所有来源（开发环境方便调试，生产环境应关闭）
CORS_ALLOW_ALL_ORIGINS = True

