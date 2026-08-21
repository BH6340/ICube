#!/bin/bash
# ICube 半自动化部署脚本 - 第 4 步：日常更新代码（bh 用户执行）
# 功能：git pull + 判断改动 + 选择性 rebuild front / migrate / collectstatic + 重启容器

set -e

# ---------- 颜色 ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
NC='\033[0m'
pass()  { echo -e "${GREEN}✅ $1${NC}"; }
warn()  { echo -e "${YELLOW}⚠️  $1${NC}"; }
fail()  { echo -e "${RED}❌ $1${NC}"; exit 1; }
info()  { echo -e "${CYAN}ℹ️  $1${NC}"; }
ask()   { # $1=提示  $2=默认 y/n
    local default=${2:-n}
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

# ---------- 权限检查 ----------
if [ "$USER" = "root" ]; then
    fail "此脚本请切换到 bh 用户执行： su - bh"
fi

# ---------- 进入项目目录 ----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR_DEFAULT="$(cd "$SCRIPT_DIR/../.." && pwd)"
if [ -f "$PROJECT_DIR_DEFAULT/docker-compose.yml" ]; then
    PROJECT_DIR="$PROJECT_DIR_DEFAULT"
else
    PROJECT_DIR="$HOME/ICube"
fi
cd "$PROJECT_DIR"
[ -f "docker-compose.yml" ] || fail "未找到 docker-compose.yml，目录异常: $PROJECT_DIR"

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   ICube 代码更新${NC}"
echo -e "${CYAN}   项目目录: $PROJECT_DIR${NC}"
echo -e "${CYAN}========================================${NC}"

# ---------- 1. Git pull ----------
echo ""
info "[1/5] 拉取最新代码..."

# 先检查有没有本地未提交改动
if [ -n "$(git status --porcelain)" ]; then
    warn "检测到本地未提交改动："
    git status --short
    if ask "是否丢弃本地改动并强制 pull 到最新？" n; then
        git reset --hard HEAD
        git pull
    else
        fail "有本地未提交改动，请先处理后再更新（或选择强制覆盖）"
    fi
else
    git pull
fi
pass "代码已更新到最新 commit: $(git rev-parse --short HEAD)"

# ---------- 2. 判断哪些文件变了 ----------
echo ""
info "[2/5] 分析改动范围..."

# 用 git diff 和上一次 HEAD（pull 之前的 ORIG_HEAD）对比
if [ -f ".git/ORIG_HEAD" ]; then
    DIFF_TARGET="ORIG_HEAD HEAD"
else
    DIFF_TARGET="HEAD~1 HEAD"
fi
CHANGED_FILES=$(git diff --name-only $DIFF_TARGET 2>/dev/null || git diff --name-only HEAD~1 HEAD)

# 判断改动类型
CHANGE_FRONT=$(echo "$CHANGED_FILES" | grep -c '^cube_front/' || true)
CHANGE_BACK=$(echo "$CHANGED_FILES" | grep -c '^cube_api/' || true)
CHANGE_MIGR=$(echo "$CHANGED_FILES" | grep -cE '^cube_api/.+/migrations/' || true)
CHANGE_STATIC=$(echo "$CHANGED_FILES" | grep -cE '\.(png|jpg|jpeg|gif|svg|css|js|woff|woff2|ttf)$' || true)
CHANGE_COMPOSE=$(echo "$CHANGED_FILES" | grep -c 'docker-compose.yml' || true)
CHANGE_NGINX=$(echo "$CHANGED_FILES" | grep -c '^nginx/' || true)

echo "  前端文件变更:  $CHANGE_FRONT"
echo "  后端文件变更:  $CHANGE_BACK"
echo "  数据库迁移:    $CHANGE_MIGR"
echo "  静态资源变更:  $CHANGE_STATIC"
echo "  compose 配置:  $CHANGE_COMPOSE"
echo "  Nginx 配置:    $CHANGE_NGINX"

# ---------- 3. 前端变更 → rebuild front ----------
echo ""
if [ "$CHANGE_FRONT" -gt 0 ]; then
    warn "检测到前端代码变更，需要重新构建 front 镜像"
    if ask "是否重新构建前端？" y; then
        info "[3/5] 重新构建并启动 front 容器..."
        docker compose up -d --build front
        pass "front 容器已重建"
    else
        warn "跳过前端重建（可能会导致前端页面仍为旧版本）"
    fi
else
    info "[3/5] 无前端代码变更，跳过 front rebuild"
fi

# ---------- 4. compose 配置变更 ----------
if [ "$CHANGE_COMPOSE" -gt 0 ]; then
    echo ""
    warn "检测到 docker-compose.yml 变更，建议重新 up -d 应用配置"
    if ask "是否重新 docker compose up -d（不 rebuild）？" y; then
        docker compose up -d
        pass "compose 配置已重新应用"
    fi
fi

# ---------- 5. Nginx 配置变更 ----------
if [ "$CHANGE_NGINX" -gt 0 ]; then
    echo ""
    warn "检测到 Nginx 配置变更"
    if ask "是否重启 Nginx 容器？" y; then
        docker compose restart nginx
        pass "Nginx 已重启"
    fi
fi

# ---------- 6. 数据库 migrate + collectstatic + 后端重启 ----------
echo ""
info "[4/5] 执行数据库迁移 + 收集静态文件 + 后端热重载"

if [ "$CHANGE_MIGR" -gt 0 ]; then
    info "检测到 migration 文件，执行 migrate..."
    docker compose exec -T api python manage.py migrate --noinput | tail -5
    pass "数据库迁移完成"
fi

# collectstatic 每次都跑（幂等，没变更也很快）
docker compose exec -T api python manage.py collectstatic --noinput 2>&1 | tail -1
pass "静态文件收集完成"

# 后端代码变更 → restart api（Gunicorn 有 --reload，但 volume 挂了目录实际能生效，这里还是 restart 保险）
if [ "$CHANGE_BACK" -gt 0 ] || [ "$CHANGE_MIGR" -gt 0 ] || [ "$CHANGE_COMPOSE" -gt 0 ]; then
    warn "检测到后端/migration/compose 变更，重启 api 容器"
    docker compose restart api
    pass "api 容器已重启"
else
    info "无后端核心变更，跳过 api restart（Gunicorn --reload 已生效）"
fi

# ---------- 7. 验证状态 ----------
echo ""
info "[5/5] 服务状态速览:"
docker compose ps
echo ""

UP_COUNT=$(docker compose ps --format '{{.Status}}' | grep -c 'Up' || true)
TOTAL_SVCS=$(docker compose config --services | wc -l)

echo ""
echo -e "${GREEN}========================================${NC}"
if [ "$UP_COUNT" -eq "$TOTAL_SVCS" ]; then
    echo -e "${GREEN}   更新完成！全部 $UP_COUNT 个服务运行正常${NC}"
else
    echo -e "${YELLOW}   更新完成，但只有 $UP_COUNT / $TOTAL_SVCS 个服务 Up${NC}"
    echo -e "${YELLOW}   请检查 docker compose ps / logs${NC}"
fi
echo -e "${GREEN}========================================${NC}"
echo ""

# 查看最新日志末尾
if ask "是否查看 api 容器最近 30 行日志？" n; then
    docker compose logs --tail=30 api
fi
echo ""
