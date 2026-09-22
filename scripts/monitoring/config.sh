#!/bin/bash
# 监控阈值配置

# 告警收件人
ALERT_RECIPIENT="1154406467@qq.com"

# QQ 邮箱 SMTP 配置（授权码非 QQ 密码）
SMTP_HOST="smtp.qq.com"
SMTP_PORT="465"
SMTP_USER="1154406467@qq.com"
SMTP_AUTH_CODE="${MONITOR_MAIL_AUTH_CODE:-}"

# 项目根目录（服务器上）
PROJECT_DIR="${PROJECT_DIR:-/opt/ICube}"

# Django 日志目录
LOG_DIR="${LOG_DIR:-/var/log/icube}"

# 阈值
DISK_THRESHOLD=85              # 磁盘使用率 %
MYSQL_MAX_CONNECTIONS=80       # MySQL 活跃连接数
MYSQL_SLOW_QUERIES=10          # 慢查询数（10分钟内）
REDIS_MEMORY_THRESHOLD=80      # Redis 内存使用率 %
REDIS_HIT_RATE_THRESHOLD=90    # Redis 命中率 %
API_ERROR_RATE_THRESHOLD=5     # API 5xx 错误率 %
API_SLOW_THRESHOLD=2.0         # API 平均响应时间（秒）

# 防刷：同一告警冷却时间（分钟）
ALERT_COOLDOWN=30

# 告警缓存目录
ALERT_CACHE_DIR="/tmp/icube_monitor_cache"

# Docker 容器名
CONTAINERS=("icube_db" "icube_redis" "icube_api" "icube_front" "icube_nginx" "icube_cloudflared")
