#!/bin/bash
# MySQL 连接数 + 慢查询检查
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/config.sh"

DB_PWD="${DB_PASSWORD:-icube123}"

# 连接数
threads_connected=$(docker exec icube_db mysqladmin -uroot -picube_root123 -N processlist 2>/dev/null | wc -l)

# 慢查询数（Slow_queries 累计值，取自 SHOW STATUS）
slow_queries=$(docker exec icube_db mysql -uroot -picube_root123 -N -e "SHOW STATUS LIKE 'Slow_queries'" 2>/dev/null | awk '{print $2}')

ALERTS=""
if [ "${threads_connected:-0}" -ge "$MYSQL_MAX_CONNECTIONS" ]; then
    ALERTS="${ALERTS}<tr><td>活跃连接数</td><td style='color:red;font-weight:bold'>${threads_connected}</td><td>超过阈值 ${MYSQL_MAX_CONNECTIONS}</td></tr>"
fi
if [ "${slow_queries:-0}" -ge "$MYSQL_SLOW_QUERIES" ]; then
    ALERTS="${ALERTS}<tr><td>慢查询数</td><td style='color:red;font-weight:bold'>${slow_queries}</td><td>超过阈值 ${MYSQL_SLOW_QUERIES}</td></tr>"
fi

if [ -n "$ALERTS" ]; then
    python3 "$SCRIPT_DIR/send_alert.py" \
        --subject "MySQL 告警" \
        --body "<h3>MySQL 指标异常</h3><table border='1' cellpadding='6' style='border-collapse:collapse'><tr><th>指标</th><th>当前值</th><th>说明</th></tr>${ALERTS}</table>"
fi
