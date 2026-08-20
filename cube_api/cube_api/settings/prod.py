# -*- coding: utf-8 -*-
"""
生产环境配置文件

该文件继承自 dev.py，仅覆盖生产环境需要修改的配置项。
通过环境变量配置敏感信息，确保生产环境安全。

配置覆盖项：
    1. DEBUG = False（禁用调试模式）
    2. SECRET_KEY（通过环境变量配置）
    3. ALLOWED_HOSTS（通过环境变量配置）
    4. CORS_ALLOWED_ORIGINS（根据环境变量生成来源列表）
    5. DATABASES（生产环境数据库配置）
    6. CACHES（生产环境 Redis 配置）
    7. STATIC_ROOT（静态文件收集目录）
"""
import os

# 继承开发环境配置，再覆盖生产环境差异项
from .dev import *

# ==================== 安全配置 ====================

# 生产环境必须禁用调试模式
# DEBUG = True 会暴露详细错误信息，不可用于生产环境
DEBUG = False

# Django 加密签名密钥，生产环境必须通过 SECRET_KEY 覆盖
# 默认值仅作为启动兜底，不应在真实生产环境使用
SECRET_KEY = os.getenv('SECRET_KEY', SECRET_KEY)

# ALLOWED_HOSTS 使用逗号分隔的主机名，不包含协议和端口
# 额外保留 Docker 服务名、容器名和本地回环地址
ALLOWED_HOSTS = [
    h.strip() for h in os.getenv('ALLOWED_HOSTS', '').split(',') if h.strip()
] + ['localhost', '127.0.0.1', 'icube_api', 'api']

# ==================== CORS 配置 ====================

# ALLOWED_ORIGIN 应为不含协议的主机名，代码会生成 HTTP 与 HTTPS 来源
# 注意：本文件继承 dev.py 的 CORS_ALLOW_ALL_ORIGINS = True；
# 若未显式覆盖为 False，下方白名单不会形成限制
_allowed_origin = os.getenv('ALLOWED_ORIGIN', '')
CORS_ALLOWED_ORIGINS = [
    f"{scheme}://{_allowed_origin}"
    for scheme in ['http', 'https']
    if _allowed_origin
] + [
    "http://localhost",
    "https://localhost",
]

# 允许跨源请求携带 Cookie、Authorization 等凭证
CORS_ALLOW_CREDENTIALS = True

# ==================== 数据库配置 ====================

# 生产数据库参数优先从环境变量读取
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
        # Docker 网络内通过 redis 服务名连接
        'LOCATION': os.getenv('REDIS_URL', 'redis://redis:6379/1'),
        # 复用 dev.py 的阻塞连接池与 JSON 序列化配置
        'OPTIONS': REDIS_BASE_OPTIONS,
        'KEY_PREFIX': 'icube_prod',    # 生产环境使用独立的键前缀
        'TIMEOUT': 86400,              # 默认缓存有效期：24 小时
    }
}

# ==================== django-unfold 配置 ====================

# 允许同源页面嵌入管理后台，满足 Unfold 组件需求
X_FRAME_OPTIONS = 'SAMEORIGIN'

# ==================== 静态文件配置 ====================

# collectstatic 输出目录，由 Nginx 通过共享卷提供静态资源
STATIC_ROOT = os.path.join(BASE_DIR, 'collected_static')

# ==================== 邮件 SMTP 配置 ====================

# 生产环境通过环境变量覆盖邮件配置
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.qq.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 465))
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_DISPLAY_NAME = os.getenv('EMAIL_DISPLAY_NAME', 'ICube魔方平台')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', f'"{EMAIL_DISPLAY_NAME}" <{EMAIL_HOST_USER}>' if EMAIL_HOST_USER else EMAIL_HOST_USER)
# 生产环境不禁用任何邮箱后缀
EMAIL_TEST_SUFFIXES = []
