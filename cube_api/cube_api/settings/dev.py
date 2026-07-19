import sys, os

from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 2. 将 apps 目录加入环境变量
# 使用 / 运算符是 pathlib 的标准用法，比 os.path.join 更简洁
APPS_DIR = Path(__file__).resolve().parent.parent / 'apps'
if APPS_DIR.exists():
    sys.path.insert(0, str(APPS_DIR))

# 3. 将项目根目录加入环境变量（通常是为了方便导入内部包）
sys.path.insert(0, str(BASE_DIR))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-t_8fu67t$62)5i7d#zrkbtv4n+fft8e#szjw8*2%wx-x#+j#3a'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# 站点域名配置，用于生成绝对URL（图片、文件等）
# 开发环境使用本地地址，生产环境通过环境变量配置
SITE_DOMAIN = os.getenv('SITE_DOMAIN', 'http://localhost:8000')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third Party Apps
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    # My Apps
    'apps.home',
    'apps.accounts',
    'apps.forum',
    'apps.formula',
    'apps.shop',
    'apps.timer'
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # 必须放在最前面
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cube_api.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# 配置 Redis 作为缓存
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",  # 使用 1 号数据库
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# 让 Session 使用缓存后端
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# 可选：Session 配置
SESSION_COOKIE_AGE = 3600 * 24  # 1天过期
SESSION_SAVE_EVERY_REQUEST = True  # 每次请求刷新过期时间

WSGI_APPLICATION = 'cube_api.wsgi.application'

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

# 动态获取用户名和密码
DB_NAME = os.getenv('DB_NAME', 'icube')
DB_USER = os.getenv('DB_USER', 'icube_api')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'icube123?')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
    }
}

# 测试时使用 SQLite
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # 使用内存数据库，速度更快
        # 或者使用文件数据库
        # 'NAME': BASE_DIR / 'test_db.sqlite3',
    }

# 基础 Redis 配置模板（为了避免代码冗余，我们先定义好公共配置）
REDIS_BASE_OPTIONS = {
    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
    'CONNECTION_POOL_CLASS_KWARGS': {
        'max_connections': 50,
        'timeout': 20,
    },
    'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
}

if 'test' in sys.argv or 'pytest' in sys.modules:
    # 测试环境配置
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/3',
            'OPTIONS': REDIS_BASE_OPTIONS,
            # 💡 极其重要：前缀加上 test_ 区分
            'KEY_PREFIX': 'icube_test',
            'TIMEOUT': 300,  # 测试环境保持短一点的超时即可
        }
    }
    # 使用更快的密码哈希器
    PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ]
else:
    # ==================== 生产/开发环境配置 ====================
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/1',  # 使用 db 1
            'OPTIONS': REDIS_BASE_OPTIONS,
            'KEY_PREFIX': 'icube',
            'TIMEOUT': 86400,  # 24小时
        }
    }



# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'

# 2. 💡 新增：媒体文件配置（用户上传的头像、文件流）
# MEDIA_ROOT 规定了上传的文件在服务器上的实际物理存放路径
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# MEDIA_URL 规定了用户在前端浏览器访问该文件的网络前缀
MEDIA_URL = '/media/'

# 💡 新增：让项目启动时自动检测并强行创建 media 文件夹
if not os.path.exists(MEDIA_ROOT):
    os.makedirs(MEDIA_ROOT)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 必须使用 "应用标签.模型名" 的格式
AUTH_USER_MODEL = 'accounts.User'

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'utils.common_pagination.UnifiedPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'utils.common_exception.common_exception_handler',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend'
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # 'rest_framework_simplejwt.authentication.JWTAuthentication',
        'apps.accounts.authentication.CachedJWTAuthentication',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # 全局配置 DRF 的限流策略
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',  # 针对匿名用户
        'rest_framework.throttling.UserRateThrottle',  # 针对登录用户
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
        'login_scope': '3/min',  # 我们单独为登录接口定义的限流频率：1分钟最多3次
    }
}

# 测试环境限流配置
# 测试环境配置
if 'test' in sys.argv:
    # 测试时完全禁用限流
    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'apps.accounts.authentication.CachedJWTAuthentication',
        ],
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.IsAuthenticatedOrReadOnly',
        ],
        'DEFAULT_THROTTLE_CLASSES': [],  # 清空限流
        'DEFAULT_THROTTLE_RATES': {},     # 清空限流速率
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
        'PAGE_SIZE': 20,
        'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    }
else:
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
            'anon': '100/day',
            'user': '1000/day',
            'login_scope': '5/minute',  # 添加 login_scope 配置
        },
        # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
        'DEFAULT_PAGINATION_CLASS': 'utils.common_pagination.UnifiedPagination',
        'PAGE_SIZE': 20,
        'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    }

# 测试环境 Mock Redis
if 'test' in sys.argv:
    import django_redis
    def mock_get_redis_connection(alias):
        from django.core.cache import cache
        return cache
    django_redis.get_redis_connection = mock_get_redis_connection

# 论坛配置（新增）
FORUM_CONFIG = {
    'POST_MIN_TITLE_LENGTH': 5,
    'POST_MAX_TITLE_LENGTH': 200,
    'POST_MIN_CONTENT_LENGTH': 10,
    'COMMENT_MIN_CONTENT_LENGTH': 2,
    'HOT_POST_DAYS': 7,  # 热门帖子统计天数
    'HOT_POST_LIMIT': 20,  # 热门帖子数量
    'MAX_FILE_SIZE': 5 * 1024 * 1024,  # 最大文件大小 5MB
    'ALLOWED_FILE_EXTENSIONS': ['.md'],  # 允许的文件扩展名
}

# JWT token settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'UPDATE_LAST_LOGIN': True,
    'AUTH_HEADER_TYPES': ('Token',)
}

# drf-spectacular 的详细配置（可选但推荐）
SPECTACULAR_SETTINGS = {
    'TITLE': 'ICube API',  # API 标题
    'DESCRIPTION': '项目接口文档',  # 描述
    'VERSION': '1.0.0',  # 版本号
    'SERVE_INCLUDE_SCHEMA': False,  # 不在文档中包含 schema 自身
    # 忽略认证警告（如果你不介意的话）
    'AUTHENTICATION_WHITELIST': [],
    'SCHEMA_PATH_PREFIX': '/api/',
    'TAGS': [
        {'name': 'users', 'description': '用户管理'},
        {'name': 'profiles', 'description': '用户资料浏览'},
        {'name': 'forum', 'description': '论坛帖子管理'},
        {'name': 'comments', 'description': '评论系统'},
        {'name': 'tags', 'description': '标签管理'},
        {'name': 'reports', 'description': '举报管理'},
    ],
}

# 1. 彻底禁用 Django 自带的日志配置系统
LOGGING_CONFIG = None

# 2. 显式置空
LOGGING = {}

# 3. 日志配置
from .logger_conf import setup_logging

setup_logging()

# 允许前端地址
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

CORS_ALLOW_ALL_ORIGINS = True

