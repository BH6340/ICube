# -*- coding: utf-8 -*-
"""
生产环境配置文件

该文件继承自 dev.py，仅覆盖生产环境需要修改的配置项。
通过环境变量配置敏感信息，确保生产环境安全。

配置覆盖项：
    1. DEBUG = False（禁用调试模式）
    2. SECRET_KEY（通过环境变量配置）
    3. ALLOWED_HOSTS（通过环境变量配置）
    4. CORS_ALLOWED_ORIGINS（通过环境变量配置）
    5. DATABASES（生产环境数据库配置）
    6. CACHES（生产环境 Redis 配置）
    7. STATIC_ROOT（静态文件收集目录）
"""
import os
# 继承开发环境配置，然后覆盖生产环境特有的配置
from .dev import *

# ==================== 安全配置 ====================

# 生产环境必须禁用调试模式
# DEBUG=True 会暴露敏感信息，存在安全风险
DEBUG = False

# 密钥：生产环境必须通过环境变量 SECRET_KEY 配置
# 默认为 dev.py 中的密钥（仅作为 fallback，实际生产应设置环境变量）
SECRET_KEY = os.getenv('SECRET_KEY', SECRET_KEY)

# 允许访问的主机列表
# 通过环境变量 ALLOWED_HOSTS 配置，格式为逗号分隔的主机名列表
# 默认包含 Docker 容器内部访问的主机名（icube_api、api）和本地回环地址
ALLOWED_HOSTS = [
    h.strip() for h in os.getenv('ALLOWED_HOSTS', '').split(',') if h.strip()
] + ['localhost', '127.0.0.1', 'icube_api', 'api']

# ==================== CORS 配置 ====================

# 通过环境变量配置允许的前端来源
_allowed_origin = os.getenv('ALLOWED_ORIGIN', '')
CORS_ALLOWED_ORIGINS = [
    f"{scheme}://{_allowed_origin}"
    for scheme in ['http', 'https']
    if _allowed_origin
] + [
    "http://localhost",
    "https://localhost",
]

# 允许携带凭证（Cookie、Authorization 等）
CORS_ALLOW_CREDENTIALS = True

# ==================== 数据库配置 ====================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'icube_db'),       # 数据库名称
        'USER': os.getenv('DB_USER', 'icube_api'),      # 数据库用户名
        'PASSWORD': os.getenv('DB_PASSWORD', 'icube123'), # 数据库密码（必须通过环境变量配置）
        'HOST': os.getenv('DB_HOST', 'db'),             # 数据库主机（Docker 环境中使用服务名 'db'）
        'PORT': os.getenv('DB_PORT', '3306'),           # 数据库端口
        'OPTIONS': {
            'charset': 'utf8mb4',  # 使用 utf8mb4 字符集，支持 emoji 表情
        },
    }
}

# ==================== 缓存配置 ====================

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        # Redis 地址：Docker 环境中使用服务名 'redis'
        'LOCATION': os.getenv('REDIS_URL', 'redis://redis:6379/1'),
        'OPTIONS': REDIS_BASE_OPTIONS,  # 复用 dev.py 中定义的基础配置
        'KEY_PREFIX': 'icube_prod',    # 生产环境使用独立的键前缀
        'TIMEOUT': 86400,              # 默认缓存超时时间：24小时
    }
}

# ==================== 静态文件配置 ====================

# 静态文件收集目录
# 运行 python manage.py collectstatic 时，所有静态文件会被收集到这个目录
# Nginx 需要配置指向这个目录来提供静态文件服务
STATIC_ROOT = os.path.join(BASE_DIR, 'collected_static')