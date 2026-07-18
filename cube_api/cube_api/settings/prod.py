import os
from .dev import *

DEBUG = False

SECRET_KEY = os.getenv('SECRET_KEY', SECRET_KEY)

ALLOWED_HOSTS = [
    '121.4.62.163',
    'localhost',
    '127.0.0.1',
    'icube_api',
    'api',
]

CORS_ALLOWED_ORIGINS = [
    "http://121.4.62.163",
    "https://121.4.62.163",
    "http://localhost",
    "https://localhost",
]

CORS_ALLOW_CREDENTIALS = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'icube_db'),
        'USER': os.getenv('DB_USER', 'icube_api'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'icube123'),
        'HOST': os.getenv('DB_HOST', 'db'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://redis:6379/1'),
        'OPTIONS': REDIS_BASE_OPTIONS,
        'KEY_PREFIX': 'icube_prod',
        'TIMEOUT': 86400,
    }
}

STATIC_ROOT = os.path.join(BASE_DIR, 'collected_static')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}