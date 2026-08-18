#!/usr/bin/env bash
# --------------------------------------------------------------
# ICube 服务端数据库转储脚本（crontab 入口）
# 通过 Docker mysqldump 导出数据库到 init_data.sql 并推送到 Git
# 手动一键执行
# python server_db_dump.py

# 或通过 shell 包装
# bash scripts/server_backup.sh

# 预览不执行
# python server_db_dump.py --dry-run

# 只导出不推送
# python server_db_dump.py --no-push

# 用法：每天 22:00 执行
#   0 22 * * * /opt/icube/scripts/server_backup.sh >> /opt/icube/logs/server-backup-cron.log 2>&1
# --------------------------------------------------------------
set -u

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
    echo "[$(date '+%F %T')] 找不到 python 解释器" >> "$PROJECT_DIR/logs/server-backup-cron.log"
    exit 1
fi

# 优先从 .env.backup 加载
if [ -f "$PROJECT_DIR/.env.backup" ]; then
    set -a
    . "$PROJECT_DIR/.env.backup"
    set +a
fi

export REPO_PATH="$PROJECT_DIR"

echo ""
echo "============================================================"
echo "[$(date '+%F %T')] 开始服务端数据库转储 @ $(hostname)"
echo "  PROJECT_DIR = $PROJECT_DIR"
echo "  PYTHON_BIN  = $PYTHON_BIN"
echo "============================================================"

"$PYTHON_BIN" "$PROJECT_DIR/scripts/server_db_dump.py"
RC=$?

if [ "$RC" -eq 0 ]; then
    echo "[$(date '+%F %T')] 转储成功 (exit=0)"
else
    echo "[$(date '+%F %T')] 转储失败 (exit=$RC)"
fi

exit $RC
