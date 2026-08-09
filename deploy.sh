#!/usr/bin/env bash

# ICube 服务器一键部署脚本
# 用法：在项目根目录执行 bash deploy.sh，禁止使用 sudo 运行整个脚本。
set -Eeuo pipefail
IFS=$'\n\t'

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
NC='\033[0m'

info() { echo -e "${CYAN}[信息]${NC} $1"; }
pass() { echo -e "${GREEN}[完成]${NC} $1"; }
warn() { echo -e "${YELLOW}[警告]${NC} $1"; }
fail() {
    echo -e "${RED}[错误]${NC} $1" >&2
    return 1
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
OLD_MEDIA_DIR="$PROJECT_DIR/media"
NEW_MEDIA_DIR="$PROJECT_DIR/cube_api/media"
BACKUP_ROOT="${ICUBE_BACKUP_DIR:-$HOME/icube-backups}"
HEALTHCHECK_HOST="${ICUBE_HEALTHCHECK_HOST:-${ALLOWED_HOSTS:-}}"

cd "$PROJECT_DIR"

compose() {
    docker compose "$@"
}

on_error() {
    local exit_code=$?
    local line_no="${1:-unknown}"
    trap - ERR

    echo -e "${RED}[失败]${NC} 部署在第 ${line_no} 行中断，退出码：${exit_code}" >&2
    if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
        compose ps 2>/dev/null || true
        echo ""
        echo "最近 100 行容器日志："
        compose logs --no-color --tail=100 api nginx front db redis 2>/dev/null || true
    fi
    exit "$exit_code"
}

trap 'on_error $LINENO' ERR

require_command() {
    command -v "$1" >/dev/null 2>&1 || fail "缺少命令：$1"
}

resolve_healthcheck_host() {
    local line

    if [ -z "$HEALTHCHECK_HOST" ]; then
        while IFS= read -r line || [ -n "$line" ]; do
            line="${line%$'\r'}"
            case "$line" in
                ALLOWED_HOSTS=*)
                    HEALTHCHECK_HOST="${line#ALLOWED_HOSTS=}"
                    break
                    ;;
            esac
        done < "$PROJECT_DIR/.env"
    fi

    HEALTHCHECK_HOST="${HEALTHCHECK_HOST#\"}"
    HEALTHCHECK_HOST="${HEALTHCHECK_HOST%\"}"
    HEALTHCHECK_HOST="${HEALTHCHECK_HOST#\'}"
    HEALTHCHECK_HOST="${HEALTHCHECK_HOST%\'}"
    HEALTHCHECK_HOST="${HEALTHCHECK_HOST%%,*}"
    HEALTHCHECK_HOST="${HEALTHCHECK_HOST//[[:space:]]/}"
    HEALTHCHECK_HOST="${HEALTHCHECK_HOST#.}"

    if [ "$HEALTHCHECK_HOST" = "*" ]; then
        HEALTHCHECK_HOST="localhost"
    fi

    [ -n "$HEALTHCHECK_HOST" ] || \
        fail "未配置 ALLOWED_HOSTS，无法确定健康检查 Host"
}

check_environment() {
    info "[1/9] 检查部署环境"

    if [ "${EUID:-$(id -u)}" -eq 0 ]; then
        fail "请使用普通部署用户执行，不要运行 sudo bash deploy.sh"
    fi

    require_command git
    require_command docker
    require_command curl

    [ -d "$PROJECT_DIR/.git" ] || fail "当前目录不是 Git 仓库：$PROJECT_DIR"
    [ -f "$PROJECT_DIR/docker-compose.yml" ] || fail "未找到 docker-compose.yml"
    [ -f "$PROJECT_DIR/.env" ] || fail "未找到 .env，请先配置生产环境变量"
    resolve_healthcheck_host

    docker info >/dev/null 2>&1 || fail "当前用户无 Docker 权限或 Docker 未启动"
    compose version >/dev/null 2>&1 || fail "Docker Compose 不可用"

    info "健康检查 Host：$HEALTHCHECK_HOST"
    pass "部署环境检查通过"
}

pull_code() {
    info "[2/9] 拉取远程代码"
    git pull --ff-only
    pass "当前版本：$(git rev-parse --short HEAD)"
}

build_images() {
    info "[3/9] 校验 Compose 配置并构建镜像"
    compose config --quiet
    compose build --pull
    pass "镜像构建完成"
}

stop_api_for_maintenance() {
    info "[4/9] 停止 API，进入维护窗口"
    compose stop api
    pass "API 已停止"
}

migrate_legacy_media() {
    info "[5/9] 检查旧媒体目录"

    if [ ! -d "$OLD_MEDIA_DIR" ]; then
        pass "无需迁移旧媒体目录"
        return
    fi

    local timestamp
    local legacy_backup_dir
    local target_backup_dir
    timestamp="$(date '+%Y%m%d-%H%M%S')"
    legacy_backup_dir="$BACKUP_ROOT/media-before-migration-${timestamp}-$$"
    target_backup_dir="$BACKUP_ROOT/media-target-before-migration-${timestamp}-$$"

    mkdir -p "$NEW_MEDIA_DIR" "$target_backup_dir"
    cp -a "$NEW_MEDIA_DIR/." "$target_backup_dir/"
    cp -a "$OLD_MEDIA_DIR/." "$NEW_MEDIA_DIR/"
    mv "$OLD_MEDIA_DIR" "$legacy_backup_dir"

    pass "媒体文件已迁移至 $NEW_MEDIA_DIR"
    pass "迁移前目标目录已备份至 $target_backup_dir"
    pass "旧目录已备份至 $legacy_backup_dir"
}

wait_for_database() {
    local container_id
    local status="unknown"

    info "[6/9] 启动 MySQL 与 Redis"
    compose up -d db redis
    container_id="$(compose ps -q db)"
    [ -n "$container_id" ] || fail "未找到 MySQL 容器"

    for _ in $(seq 1 60); do
        status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_id")"
        case "$status" in
            healthy)
                pass "MySQL 健康检查通过"
                return
                ;;
            exited|dead)
                fail "MySQL 容器状态异常：$status"
                ;;
        esac
        sleep 2
    done

    fail "等待 MySQL 健康检查超时，当前状态：$status"
}

run_migrations() {
    info "[7/9] 执行 Django 数据库迁移"
    compose run --rm --no-deps api python manage.py migrate --noinput
    pass "数据库迁移完成"
}

start_services() {
    info "[8/9] 启动全部服务"
    compose up -d
    pass "Compose 启动命令执行完成"
}

verify_services() {
    local db_container_id
    local db_status
    local redis_response
    local total_services
    local running_services

    info "[9/9] 验证容器状态和 HTTP"

    for _ in $(seq 1 30); do
        if curl -fsS -H "Host: $HEALTHCHECK_HOST" http://127.0.0.1/ >/dev/null 2>&1 &&
            curl -fsS -H "Host: $HEALTHCHECK_HOST" http://127.0.0.1/api/home/banners/ >/dev/null 2>&1; then
            break
        fi
        sleep 2
    done

    curl -fsS -H "Host: $HEALTHCHECK_HOST" http://127.0.0.1/ >/dev/null
    curl -fsS -H "Host: $HEALTHCHECK_HOST" http://127.0.0.1/api/home/banners/ >/dev/null

    total_services="$(compose config --services | wc -l | tr -d ' ')"
    running_services="$(compose ps --services --status running | wc -l | tr -d ' ')"
    compose ps

    [ "$running_services" -eq "$total_services" ] || \
        fail "仅有 ${running_services}/${total_services} 个服务处于运行状态"

    db_container_id="$(compose ps -q db)"
    [ -n "$db_container_id" ] || fail "未找到 MySQL 容器"
    db_status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$db_container_id")"
    [ "$db_status" = "healthy" ] || fail "MySQL 健康状态异常：$db_status"

    redis_response="$(compose exec -T redis redis-cli ping | tr -d '\r')"
    [ "$redis_response" = "PONG" ] || fail "Redis PING 失败"

    pass "首页、API、MySQL 和 Redis 均正常，全部 ${running_services} 个服务正在运行"
}

main() {
    echo "========================================"
    echo "         ICube 一键部署"
    echo "========================================"

    check_environment
    pull_code
    build_images
    stop_api_for_maintenance
    migrate_legacy_media
    wait_for_database
    run_migrations
    start_services
    verify_services

    trap - ERR
    echo "========================================"
    pass "部署完成"
    echo "========================================"
}

main "$@"
