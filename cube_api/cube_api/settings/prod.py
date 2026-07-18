import os
from .dev import *

DEBUG = False

SECRET_KEY = os.getenv('SECRET_KEY', SECRET_KEY)

ALLOWED_HOSTS = [
    h.strip() for h in os.getenv('ALLOWED_HOSTS', '').split(',') if h.strip()
] + ['localhost', '127.0.0.1', 'icube_api', 'api']

_allowed_origin = os.getenv('ALLOWED_ORIGIN', '')
CORS_ALLOWED_ORIGINS = [
    f"{scheme}://{_allowed_origin}"
    for scheme in ['http', 'https']
    if _allowed_origin
] + [
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