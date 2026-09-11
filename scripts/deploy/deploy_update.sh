#!/bin/bash
# ICube 部署更新脚本
# 功能：代码同步 + 智能变更检测 + 选择性构建 + 迁移备份回滚 + 健康检查回滚
# 适用场景：CI/CD 自动部署、手动日常更新
#
# 常用调用：
#   手动更新：           bash scripts/deploy/deploy_update.sh
#   CI/CD 全量部署：     bash scripts/deploy/deploy_update.sh --non-interactive --force-sync --backup-db --post-backup
#   仅构建重启（回滚用）：bash scripts/deploy/deploy_update.sh --non-interactive --skip-migrate --skip-healthcheck

set -e

# ============================== 错误处理 ==============================
# 部署失败时自动打印容器状态和最近日志，便于排查
on_error() {
    local exit_code=$?
    local line_no="${1:-unknown}"
    trap - ERR  # 避免错误处理本身再触发 trap

    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}❌ 部署在第 ${line_no} 行中断，退出码：${exit_code}${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""

    if command -v docker >/dev/null 2>&1 && \
        docker info --format '{{.ServerVersion}}' >/dev/null 2>&1; then
        echo "容器状态："
        docker compose ps 2>/dev/null || true
        echo ""
        echo "最近 100 行容器日志（api/nginx/front/db/redis）："
        echo "----------------------------------------"
        docker compose logs --no-color --tail=100 api nginx front db redis 2>/dev/null || true
        echo "----------------------------------------"
    fi

    exit "$exit_code"
}

trap 'on_error $LINENO' ERR

# ============================== 参数解析 ==============================
NON_INTERACTIVE=false
SKIP_HEALTHCHECK=false
SKIP_MIGRATE=false
FORCE_SYNC=false          # 强制同步远程代码（git reset --hard origin/main）
BACKUP_DB_BEFORE_MIGR=false  # 迁移前备份数据库，失败自动回滚
POST_BACKUP=false         # 部署成功后异步执行全量备份
ROLLBACK_MODE=false
ROLLBACK_TARGET=""

for arg in "$@"; do
    case "$arg" in
        --non-interactive)    NON_INTERACTIVE=true ;;
        --skip-healthcheck)   SKIP_HEALTHCHECK=true ;;
        --skip-migrate)       SKIP_MIGRATE=true ;;
        --force-sync)         FORCE_SYNC=true ;;
        --backup-db)          BACKUP_DB_BEFORE_MIGR=true ;;
        --post-backup)        POST_BACKUP=true ;;
        --rollback-to=*)      ROLLBACK_MODE=true; ROLLBACK_TARGET="${arg#*=}" ;;
    esac
done

# ============================== 颜色与工具函数 ==============================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
NC='\033[0m'
pass()  { echo -e "${GREEN}✅ $1${NC}"; }
warn()  { echo -e "${YELLOW}⚠️  $1${NC}"; }
fail()  { echo -e "${RED}❌ $1${NC}"; exit 1; }
info()  { echo -e "${CYAN}ℹ️  $1${NC}"; }

ask() {
    local default=${2:-n}
    if [ "$NON_INTERACTIVE" = true ]; then
        if [ "$default" = "y" ]; then
            return 0
        else
            return 1
        fi
    fi
    local prompt
    if [ "$default" = "y" ]; then
        prompt=" [Y/n] "
    else
        prompt=" [y/N] "
    fi
    read -rp "$1$prompt" ans
    ans=$(echo "$ans" | tr '[:upper:]' '[:lower:]')
    [ -z "$ans" ] && ans="$default"
    [ "$ans" = "y" ] || [ "$ans" = "yes" ]
}

# ============================== 健康检查 ==============================
# 从 .env 读取 ALLOWED_HOSTS 作为 Host 头，兼容多站点 nginx 配置
resolve_healthcheck_host() {
    local line
    HEALTHCHECK_HOST="${ICUBE_HEALTHCHECK_HOST:-}"

    if [ -z "$HEALTHCHECK_HOST" ] && [ -f .env ]; then
        while IFS= read -r line || [ -n "$line" ]; do
            line="${line%$'\r'}"
            case "$line" in
                ALLOWED_HOSTS=*)
                    HEALTHCHECK_HOST="${line#ALLOWED_HOSTS=}"
                    break
                    ;;
            esac
        done < .env
    fi

    # 去除引号、空格、取第一个域名
    HEALTHCHECK_HOST="${HEALTHCHECK_HOST#\"}"
    HEALTHCHECK_HOST="${HEALTHCHECK_HOST%\"}"
    HEALTHCHECK_HOST="${HEALTHCHECK_HOST#\'}"
    HEALTHCHECK_HOST="${HEALTHCHECK_HOST%\'}"
    HEALTHCHECK_HOST="${HEALTHCHECK_HOST%%,*}"
    HEALTHCHECK_HOST="${HEALTHCHECK_HOST//[[:space:]]/}"
    HEALTHCHECK_HOST="${HEALTHCHECK_HOST#.}"

    # ALLOWED_HOSTS=* 时用 localhost
    if [ "$HEALTHCHECK_HOST" = "*" ]; then
        HEALTHCHECK_HOST="localhost"
    fi

    # 实在没有就用 localhost
    if [ -z "$HEALTHCHECK_HOST" ]; then
        HEALTHCHECK_HOST="localhost"
    fi
}

healthcheck() {
    local max_retries=${1:-5}
    local wait_time=${2:-3}
    local attempt=1

    while [ $attempt -le $max_retries ]; do
        info "健康检查 第 $attempt/$max_retries 次（Host: $HEALTHCHECK_HOST）..."

        HTTP_CODE=$(curl -fsS -o /dev/null -w "%{http_code}" -H "Host: $HEALTHCHECK_HOST" http://127.0.0.1/ 2>/dev/null || echo "000")
        API_CODE=$(curl -fsS -o /dev/null -w "%{http_code}" -H "Host: $HEALTHCHECK_HOST" http://127.0.0.1/api/home/banners/ 2>/dev/null || echo "000")

        if [ "$HTTP_CODE" = "200" ] && [ "$API_CODE" = "200" ]; then
            pass "健康检查通过 (前端: $HTTP_CODE, API: $API_CODE)"
            return 0
        fi

        warn "前端: $HTTP_CODE, API: $API_CODE，${wait_time}s 后重试..."
        sleep $wait_time
        attempt=$((attempt + 1))
    done

    fail "健康检查失败 (前端: $HTTP_CODE, API: $API_CODE)"
}

# ============================== 数据库配置 ==============================
# 从 .env 读取数据库连接信息
load_db_config() {
    if [ ! -f .env ]; then
        return 1
    fi
    DB_PASSWORD=$(grep -E '^MYSQL_ROOT_PASSWORD=' .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    DB_NAME=$(grep -E '^MYSQL_DATABASE=' .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    [ -n "$DB_PASSWORD" ] && [ -n "$DB_NAME" ]
}

# ============================== 数据库备份与回滚 ==============================
backup_database() {
    local backup_file="$1"
    info "备份数据库到 $backup_file ..."
    docker compose exec -T db mysqldump -u root -p"$DB_PASSWORD" "$DB_NAME" > "$backup_file"
    local size
    size=$(wc -c < "$backup_file" | tr -d ' ')
    pass "数据库备份完成 (${size} bytes)"
}

rollback_database() {
    local backup_file="$1"
    if [ ! -f "$backup_file" ]; then
        warn "数据库备份文件不存在，跳过数据库回滚: $backup_file"
        return 1
    fi
    warn "从备份恢复数据库..."
    docker compose exec -T db mysql -u root -p"$DB_PASSWORD" "$DB_NAME" < "$backup_file"
    pass "数据库已恢复"
}

# ============================== 代码回滚 ==============================
# 将代码重置到目标 commit，并重新构建启动服务
# 注意：不递归调用脚本本身，避免 git pull 把代码拉回坏版本
rollback_code() {
    local target_commit="$1"
    echo ""
    warn "========================================"
    warn "  代码回滚到: $(echo "$target_commit" | cut -c1-7)"
    warn "========================================"

    git reset --hard "$target_commit"
    info "代码已回退，commit: $(git rev-parse --short HEAD)"

    # 直接重建并启动所有服务（全量重建，确保回滚彻底）
    info "重建前端镜像..."
    docker compose up -d --build front 2>&1 | tail -3

    info "启动全部服务..."
    docker compose up -d 2>&1 | tail -3

    info "收集静态文件..."
    docker compose exec -T api python manage.py collectstatic --noinput 2>&1 | tail -1

    info "重启 API 容器..."
    docker compose restart api 2>&1 | tail -2

    pass "回滚后服务已重建"
}

# ============================== 权限与目录检查 ==============================
if [ "$USER" = "root" ]; then
    fail "此脚本请切换到普通用户执行，不要用 root"
fi

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR_DEFAULT="$(cd "$SCRIPT_DIR/../.." && pwd)"
if [ -f "$PROJECT_DIR_DEFAULT/docker-compose.yml" ]; then
    PROJECT_DIR="$PROJECT_DIR_DEFAULT"
else
    PROJECT_DIR="$HOME/ICube"
fi
cd "$PROJECT_DIR"
[ -f "docker-compose.yml" ] || fail "未找到 docker-compose.yml，目录异常: $PROJECT_DIR"

# 解析健康检查 Host（从 .env 读 ALLOWED_HOSTS）
resolve_healthcheck_host

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   ICube 部署更新${NC}"
echo -e "${CYAN}   项目目录: $PROJECT_DIR${NC}"
echo -e "${CYAN}   健康检查 Host: $HEALTHCHECK_HOST${NC}"
echo -e "${CYAN}========================================${NC}"

# ============================== [1/6] 代码同步 ==============================
echo ""
info "[1/6] 同步代码..."

# 记录部署前的 commit（用于回滚）
PREV_COMMIT=$(git rev-parse HEAD)
info "部署前 commit: $(echo $PREV_COMMIT | cut -c1-7)"

# 回滚模式：直接重置到目标 commit
if [ "$ROLLBACK_MODE" = true ] && [ -n "$ROLLBACK_TARGET" ]; then
    info "回滚模式：直接重置到目标 commit"
    git reset --hard "$ROLLBACK_TARGET"
    PREV_COMMIT=""  # 回滚模式不做智能变更检测，全量重建
elif [ "$FORCE_SYNC" = true ]; then
    # 强制同步模式：fetch + reset --hard origin/main
    # 自动备份本地改动为 patch（CI/CD 场景用）
    info "强制同步模式：fetch + reset --hard origin/main"

    git fetch origin main

    # 检测本地改动并备份为 patch
    LOCAL_CHANGES=$(git status --porcelain)
    if [ -n "$LOCAL_CHANGES" ]; then
        PATCH_FILE="/tmp/local_changes_$(date +%Y%m%d_%H%M%S).patch"
        warn "检测到本地改动，备份到 $PATCH_FILE"
        echo "$LOCAL_CHANGES"
        git diff > "$PATCH_FILE"
        echo "" >> "$PATCH_FILE"
        echo "# Untracked files:" >> "$PATCH_FILE"
        git ls-files --others --exclude-standard >> "$PATCH_FILE"
        pass "本地改动已备份"
    fi

    git reset --hard origin/main
    pass "代码已同步到: $(git rev-parse --short HEAD)"
else
    # 默认模式：git pull，有本地改动提示用户
    if [ -n "$(git status --porcelain)" ]; then
        warn "检测到本地未提交改动："
        git status --short
        if [ "$NON_INTERACTIVE" = true ]; then
            info "[非交互] 自动丢弃本地改动并强制 pull"
            git reset --hard HEAD
            git pull --ff-only
        elif ask "是否丢弃本地改动并强制 pull 到最新？" n; then
            git reset --hard HEAD
            git pull
        else
            fail "有本地未提交改动，请先处理后再更新（或选择强制覆盖）"
        fi
    else
        if [ "$NON_INTERACTIVE" = true ]; then
            git pull --ff-only
        else
            git pull
        fi
    fi
    pass "代码已更新到: $(git rev-parse --short HEAD)"
fi

# ============================== [2/6] 分析改动范围 ==============================
echo ""
info "[2/6] 分析改动范围..."

# 用 git diff 对比部署前后的变更
if [ -n "$PREV_COMMIT" ] && [ "$PREV_COMMIT" != "$(git rev-parse HEAD)" ]; then
    CHANGED_FILES=$(git diff --name-only "$PREV_COMMIT" HEAD 2>/dev/null || true)
elif [ -f ".git/ORIG_HEAD" ]; then
    CHANGED_FILES=$(git diff --name-only ORIG_HEAD HEAD 2>/dev/null || true)
else
    CHANGED_FILES=$(git diff --name-only HEAD~1 HEAD 2>/dev/null || true)
fi

CHANGE_FRONT=$(echo "$CHANGED_FILES" | grep -c '^cube_front/' || true)
CHANGE_BACK=$(echo "$CHANGED_FILES" | grep -c '^cube_api/' || true)
CHANGE_MIGR=$(echo "$CHANGED_FILES" | grep -cE '^cube_api/.+/migrations/' || true)
CHANGE_COMPOSE=$(echo "$CHANGED_FILES" | grep -c 'docker-compose.yml' || true)
CHANGE_NGINX=$(echo "$CHANGED_FILES" | grep -c '^nginx/' || true)

echo "  前端文件变更:  $CHANGE_FRONT"
echo "  后端文件变更:  $CHANGE_BACK"
echo "  数据库迁移:    $CHANGE_MIGR"
echo "  compose 配置:  $CHANGE_COMPOSE"
echo "  Nginx 配置:    $CHANGE_NGINX"

# ============================== [3/6] 前端变更 → rebuild front ==============================
echo ""
if [ "$CHANGE_FRONT" -gt 0 ]; then
    warn "检测到前端代码变更，重新构建 front 镜像"
    info "[3/6] 构建并启动 front 容器..."
    docker compose up -d --build front
    pass "front 容器已重建"
else
    info "[3/6] 无前端代码变更，跳过 front rebuild"
fi

# ============================== [4/6] compose / nginx 配置变更 ==============================
if [ "$CHANGE_COMPOSE" -gt 0 ]; then
    echo ""
    warn "检测到 docker-compose.yml 变更，重新应用配置"
    docker compose up -d
    pass "compose 配置已重新应用"
fi

if [ "$CHANGE_NGINX" -gt 0 ]; then
    echo ""
    warn "检测到 Nginx 配置变更，重启 Nginx"
    docker compose restart nginx
    pass "Nginx 已重启"
fi

# ============================== [5/6] 数据库迁移 + collectstatic + 后端重启 ==============================
echo ""
info "[5/6] 数据库迁移 + 静态文件收集 + 后端重载"

DB_BACKUP_FILE=""

# --- 数据库迁移（带备份回滚）---
if [ "$CHANGE_MIGR" -gt 0 ] && [ "$SKIP_MIGRATE" = false ]; then
    info "检测到 migration 文件"

    # 如果开启了数据库备份回滚（CI/CD 场景）
    if [ "$BACKUP_DB_BEFORE_MIGR" = true ]; then
        if load_db_config; then
            DB_BACKUP_FILE="/tmp/icube_db_backup_$(date +%Y%m%d_%H%M%S).sql"
            backup_database "$DB_BACKUP_FILE"

            # 执行迁移，失败则回滚数据库 + 回滚代码
            set +e
            docker compose exec -T api python manage.py migrate --noinput 2>&1
            MIGR_RESULT=$?
            set -e

            if [ $MIGR_RESULT -ne 0 ]; then
                fail_migrate() {
                    echo ""
                    echo "❌ 数据库迁移失败"

                    # 数据库回滚
                    rollback_database "$DB_BACKUP_FILE" || true
                    rm -f "$DB_BACKUP_FILE"

                    # 代码回滚（如果有可回滚的 commit）
                    if [ -n "$PREV_COMMIT" ] && [ "$PREV_COMMIT" != "$(git rev-parse HEAD)" ]; then
                        rollback_code "$PREV_COMMIT"

                        # 回滚后健康检查确认服务恢复
                        sleep 3
                        set +e
                        healthcheck 3 3
                        HC_AFTER_RB=$?
                        set -e

                        if [ $HC_AFTER_RB -eq 0 ]; then
                            warn "迁移失败，已回滚数据库和代码，服务已恢复"
                        else
                            echo "❌ 回滚后健康检查仍然失败！请紧急手动处理"
                            docker compose ps
                        fi
                    else
                        warn "无可回滚的 commit，仅回滚了数据库"
                        docker compose ps
                    fi

                    exit 1
                }
                fail_migrate
            fi

            pass "数据库迁移成功"
            rm -f "$DB_BACKUP_FILE"
        else
            warn "无法读取数据库配置，跳过数据库备份，直接执行迁移"
            docker compose exec -T api python manage.py migrate --noinput 2>&1 | tail -5
            pass "数据库迁移完成"
        fi
    else
        # 手动模式：直接迁移，不备份（手动场景用户自己判断）
        docker compose exec -T api python manage.py migrate --noinput 2>&1 | tail -5
        pass "数据库迁移完成"
    fi
elif [ "$CHANGE_MIGR" -gt 0 ] && [ "$SKIP_MIGRATE" = true ]; then
    info "检测到 migration 文件，但已指定 --skip-migrate，跳过"
else
    info "无待应用的迁移，跳过"
fi

# --- collectstatic（幂等，每次都跑）---
docker compose exec -T api python manage.py collectstatic --noinput 2>&1 | tail -1
pass "静态文件收集完成"

# --- 后端重启 ---
if [ "$CHANGE_BACK" -gt 0 ] || [ "$CHANGE_MIGR" -gt 0 ] || [ "$CHANGE_COMPOSE" -gt 0 ]; then
    warn "检测到后端/migration/compose 变更，重启 api 容器"
    docker compose restart api
    pass "api 容器已重启"
else
    info "无后端核心变更，跳过 api restart"
fi

# ============================== [6/6] 健康检查 + 自动回滚 ==============================
echo ""
if [ "$SKIP_HEALTHCHECK" = true ]; then
    info "[6/6] 已跳过健康检查"
elif [ "$ROLLBACK_MODE" = true ]; then
    info "[6/6] 回滚模式下跳过健康检查（由调用方处理）"
else
    info "[6/6] 健康检查 + 自动回滚..."

    set +e
    healthcheck 5 3
    HC_RESULT=$?
    set -e

    if [ $HC_RESULT -ne 0 ]; then
        warn "健康检查失败"

        if [ -z "$PREV_COMMIT" ] || [ "$PREV_COMMIT" = "$(git rev-parse HEAD)" ]; then
            fail "无法回滚：部署前后 commit 相同或未记录部署前 commit"
        fi

        # 代码回滚（内部会重建服务）
        rollback_code "$PREV_COMMIT"

        # 回滚后再次健康检查
        sleep 3
        set +e
        healthcheck 3 3
        HC_AFTER_RB=$?
        set -e

        echo ""
        if [ $HC_AFTER_RB -eq 0 ]; then
            warn "========================================"
            warn "  ⚠️  部署失败，已自动回滚到上一版本"
            warn "  服务已恢复，请排查本次部署的问题"
            warn "========================================"
        else
            echo "❌ 回滚后健康检查仍然失败！请紧急手动处理"
            docker compose ps
        fi
        echo ""
        exit 1
    fi
fi

# ============================== 部署后异步备份 ==============================
if [ "$POST_BACKUP" = true ] && [ -f "./scripts/backup.sh" ]; then
    echo ""
    info "启动异步全量备份..."
    nohup ./scripts/backup.sh > /tmp/backup_deploy.log 2>&1 &
    pass "备份已在后台启动"
fi

# ============================== 完成 ==============================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   部署完成${NC}"
echo -e "${GREEN}   当前 commit: $(git rev-parse --short HEAD)${NC}"
echo -e "${GREEN}   时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 服务状态速览
docker compose ps
echo ""

# 手动模式下询问是否查看日志
if [ "$NON_INTERACTIVE" = false ]; then
    if ask "是否查看 api 容器最近 30 行日志？" n; then
        docker compose logs --tail=30 api
    fi
    echo ""
fi
