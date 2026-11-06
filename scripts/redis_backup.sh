#!/usr/bin/env bash
# --------------------------------------------------------------
# ICube Redis 备份脚本（crontab 入口）
# 用法：每天凌晨 3 点执行
#   0 3 * * * /opt/icube/scripts/redis_backup.sh >> /opt/icube/logs/redis-backup-cron.log 2>&1
# --------------------------------------------------------------
set -eu

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR" || exit 1

mkdir -p "$PROJECT_DIR/logs"

# 找 Python 解释器
PYTHON_BIN=""
if [ -x "$PROJECT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
else
    echo "[$(date '+%F %T')] 找不到 python 解释器" >> "$PROJECT_DIR/logs/redis-backup-cron.log"
    exit 1
fi

# 加载 .env（如存在）
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    . "$PROJECT_DIR/.env"
    set +a
fi

echo ""
echo "============================================================"
echo "[$(date '+%F %T')] Redis 备份开始 @ $(hostname)"
echo "  PROJECT_DIR = $PROJECT_DIR"
echo "  PYTHON_BIN  = $PYTHON_BIN"
echo "============================================================"

RC=0
"$PYTHON_BIN" "$PROJECT_DIR/scripts/redis_backup.py" || RC=$?

if [ "$RC" -eq 0 ]; then
    echo "[$(date '+%F %T')] Redis 备份成功 (exit=0)"
else
    echo "[$(date '+%F %T')] Redis 备份失败 (exit=$RC)"
fi

exit $RC
