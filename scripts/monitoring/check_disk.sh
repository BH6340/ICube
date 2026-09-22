#!/bin/bash
# 磁盘使用率检查
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/config.sh"

ALERTS=""
for partition in $(df -h --output=target | tail -n +2); do
    usage_pct=$(df -h "$partition" | tail -1 | awk '{print $5}' | tr -d '%')
    if [ "$usage_pct" -ge "$DISK_THRESHOLD" ]; then
        ALERTS="${ALERTS}<tr><td>${partition}</td><td style='color:red;font-weight:bold'>${usage_pct}%</td><td>超过阈值 ${DISK_THRESHOLD}%</td></tr>"
    fi
done

if [ -n "$ALERTS" ]; then
    python3 "$SCRIPT_DIR/send_alert.py" \
        --subject "磁盘使用率告警" \
        --body "<h3>磁盘使用率告警</h3><table border='1' cellpadding='6' style='border-collapse:collapse'><tr><th>挂载点</th><th>使用率</th><th>说明</th></tr>${ALERTS}</table>"
fi
