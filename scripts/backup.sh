#!/usr/bin/env bash
# --------------------------------------------------------------
# ICube 数据库+媒体文件 自动备份脚本（crontab 入口）
# 用法：每天 22:00 执行
#   0 22 * * * /opt/icube/scripts/backup.sh >> /opt/icube/logs/backup-cron.log 2>&1
# --------------------------------------------------------------
set -u

# 项目根目录（部署到服务器后如果不是 /opt/icube 请改这里）
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR" || exit 1

# 日志目录
mkdir -p "$PROJECT_DIR/logs"

# 找到 python 解释器（优先 venv，其次系统 python3）
PYTHON_BIN=""
if [ -x "$PROJECT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
else
    echo "[$(date '+%F %T')] ❌ 找不到 python 解释器" >> "$PROJECT_DIR/logs/backup-cron.log"
    exit 1
fi

# 优先从项目根下的 .env.backup 加载（不修改原 .env）
if [ -f "$PROJECT_DIR/.env.backup" ]; then
    # shellcheck disable=SC1091
    set -a
    . "$PROJECT_DIR/.env.backup"
    set +a
fi

echo ""
echo "============================================================"
echo "[$(date '+%F %T')] 开始备份 run @ $(hostname)"
echo "  PROJECT_DIR = $PROJECT_DIR"
echo "  PYTHON_BIN  = $PYTHON_BIN"
echo "============================================================"

# 确保 REPO_PATH 指向项目根（覆盖脚本默认值）
export REPO_PATH="$PROJECT_DIR"

"$PYTHON_BIN" "$PROJECT_DIR/scripts/update_db_dump.py"
RC=$?

if [ "$RC" -eq 0 ]; then
    echo "[$(date '+%F %T')] ✅ 备份脚本执行成功 (exit=0)"
else
    echo "[$(date '+%F %T')] ❌ 备份脚本执行失败 (exit=$RC)"
fi

exit $RC
