#!/bin/bash
# 安装 crontab 定时任务
# 用法: sudo bash scripts/monitoring/setup_cron.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON3=$(command -v python3 || echo "python3")

CRON_ENTRIES="
# ICube 监控系统定时任务
# 每5分钟：磁盘、MySQL、Redis 检查
*/5 * * * * $SCRIPT_DIR/check_disk.sh >> /var/log/icube/monitor.log 2>&1
*/5 * * * * $SCRIPT_DIR/check_mysql.sh >> /var/log/icube/monitor.log 2>&1
*/5 * * * * $SCRIPT_DIR/check_redis.sh >> /var/log/icube/monitor.log 2>&1
# 每10分钟：API 错误率检查
*/10 * * * * $PYTHON3 $SCRIPT_DIR/check_api_errors.py >> /var/log/icube/monitor.log 2>&1
# 每日 08:00：每日汇总报告
0 8 * * * $PYTHON3 $SCRIPT_DIR/daily_report.py >> /var/log/icube/monitor.log 2>&1
# 每日凌晨 02:00：清理30天前的监控日志
0 2 * * * find /var/log/icube/ -name "cube-*.log.*" -mtime +30 -delete
"

# 确保 cron 已安装
if ! command -v crontab &> /dev/null; then
    echo "crontab 未安装，正在安装..."
    apt-get update -qq && apt-get install -y -qq cron
    systemctl enable cron
    systemctl start cron
fi

# 移除旧的 ICube 监控任务（以 # ICube 监控系统定时任务 为标记）
EXISTING=$(crontab -l 2>/dev/null | sed '/^# ICube 监控系统定时任务$/,/^# 每日凌晨/d' || true)

# 追加新任务
echo "$EXISTING" | { cat; echo "$CRON_ENTRIES"; } | crontab -

echo "crontab 安装完成"
crontab -l | grep -A20 "ICube 监控"
