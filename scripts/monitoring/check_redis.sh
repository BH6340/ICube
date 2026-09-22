#!/bin/bash
# Redis 内存 + 命中率检查
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/config.sh"

# 内存使用率
mem_used=$(docker exec icube_redis redis-cli INFO memory 2>/dev/null | grep "^used_memory:" | awk -F: '{print $2}' | tr -d '\r')
mem_max=$(docker exec icube_redis redis-cli INFO memory 2>/dev/null | grep "^maxmemory:" | awk -F: '{print $2}' | tr -d '\r')

# 命中率
keyspace_hits=$(docker exec icube_redis redis-cli INFO stats 2>/dev/null | grep "^keyspace_hits:" | awk -F: '{print $2}' | tr -d '\r')
keyspace_misses=$(docker exec icube_redis redis-cli INFO stats 2>/dev/null | grep "^keyspace_misses:" | awk -F: '{print $2}' | tr -d '\r')

ALERTS=""

# 内存使用率（maxmemory=0 表示无限制，跳过）
if [ "${mem_max:-0}" -gt 0 ] 2>/dev/null; then
    mem_pct=$((mem_used * 100 / mem_max))
    if [ "$mem_pct" -ge "$REDIS_MEMORY_THRESHOLD" ]; then
        ALERTS="${ALERTS}<tr><td>内存使用率</td><td style='color:red;font-weight:bold'>${mem_pct}%</td><td>超过阈值 ${REDIS_MEMORY_THRESHOLD}%</td></tr>"
    fi
fi

# 命中率
total=$((keyspace_hits + keyspace_misses))
if [ "$total" -gt 0 ] 2>/dev/null; then
    hit_rate=$((keyspace_hits * 100 / total))
    if [ "$hit_rate" -lt "$REDIS_HIT_RATE_THRESHOLD" ]; then
        ALERTS="${ALERTS}<tr><td>命中率</td><td style='color:orange;font-weight:bold'>${hit_rate}%</td><td>低于阈值 ${REDIS_HIT_RATE_THRESHOLD}%</td></tr>"
    fi
fi

if [ -n "$ALERTS" ]; then
    python3 "$SCRIPT_DIR/send_alert.py" \
        --subject "Redis 告警" \
        --body "<h3>Redis 指标异常</h3><table border='1' cellpadding='6' style='border-collapse:collapse'><tr><th>指标</th><th>当前值</th><th>说明</th></tr>${ALERTS}</table>"
fi
