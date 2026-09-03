#!/bin/bash
# ICube 半自动化部署脚本 - 第 2 步：部署应用（bh 用户执行）
# 功能：SSH key -> git clone -> 交互式填写配置 -> 自动生成 SECRET_KEY -> 启容器 -> 验 HTTP

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
step()  { echo -e "\n${YELLOW}[$STEPS/$TOTAL] $1${NC}"; }

TOTAL=10
STEPS=0

# ---------- 权限检查 ----------
if [ "$USER" = "root" ]; then
    fail "此脚本不能以 root 运行，请先 su - bh"
fi

# ---------- 进入项目目录（兼容脚本在 scripts/deploy/ 下直接跑或从别处跑）----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 脚本在 ICube/scripts/deploy/ 时，ICube 目录是 SCRIPT_DIR 向上两级
PROJECT_DIR_DEFAULT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# 如果 PROJECT_DIR_DEFAULT 下没有 docker-compose.yml，那说明脚本是被单独复制来跑的，走 ~/ICube
if [ -f "$PROJECT_DIR_DEFAULT/docker-compose.yml" ]; then
    PROJECT_DIR="$PROJECT_DIR_DEFAULT"
else
    PROJECT_DIR="$HOME/ICube"
fi
cd "$PROJECT_DIR" 2>/dev/null || true
if [ ! -f "docker-compose.yml" ]; then
    # 还没 clone，第 2 步会处理
    PROJECT_DIR="$HOME/ICube"
fi

# ---------- 1. 检查 Docker ----------
((STEPS++)) || true; step "检查 Docker 权限"
if ! docker ps &>/dev/null; then
    fail "docker 命令无权限。请重新登录 SSH（或执行 newgrp docker）让 docker 组生效"
fi
pass "Docker 权限正常：$(docker --version)"

# ---------- 2. SSH key 配置 + git clone ----------
((STEPS++)) || true; step "配置 SSH Key & 拉取代码"

# 2.1 生成 SSH key（不存在才生成）
SSH_KEY="$HOME/.ssh/id_ed25519"
if [ ! -f "$SSH_KEY.pub" ]; then
    info "未检测到 SSH key，正在生成..."
    ssh-keygen -t ed25519 -N "" -f "$SSH_KEY" -C "deploy@icube-server" -q
    pass "SSH key 已生成到 $SSH_KEY.pub"
fi

# 2.2 检查 GitHub 认证是否已通
AUTH_MSG=$(ssh -o StrictHostKeyChecking=accept-new -T git@github.com 2>&1 || true)
if ! echo "$AUTH_MSG" | grep -q "successfully authenticated"; then
    echo ""
    warn "GitHub SSH 认证尚未通过，请复制下面这段公钥，去 GitHub 添加："
    echo ""
    echo -e "${CYAN}---------- 复制开始 ----------${NC}"
    cat "$SSH_KEY.pub"
    echo -e "${CYAN}---------- 复制结束 ----------${NC}"
    echo ""
    echo "添加步骤： GitHub 右上角头像 → Settings → SSH and GPG keys → New SSH key"
    echo "          Title 随便填（如 云服务器），Key 粘贴上面内容 → Add SSH key"
    echo ""
    read -rp "添加完成后，按回车继续...（输入 s 跳过验证） " ANS
    if [ "$ANS" != "s" ]; then
        # 循环验证，直到成功
        for i in 1 2 3 4 5; do
            AUTH_MSG=$(ssh -o StrictHostKeyChecking=accept-new -T git@github.com 2>&1 || true)
            if echo "$AUTH_MSG" | grep -q "successfully authenticated"; then
                break
            fi
            warn "第 $i 次验证未通过，请确认已添加公钥...（5 秒后重试）"
            sleep 5
        done
        if ! echo "$AUTH_MSG" | grep -q "successfully authenticated"; then
            fail "SSH 认证仍未通过，请检查 GitHub 配置后再运行本脚本"
        fi
    fi
fi
pass "GitHub SSH 认证已通过"

# 2.3 git clone 或 pull
mkdir -p "$HOME"
if [ -d "$PROJECT_DIR/.git" ]; then
    cd "$PROJECT_DIR"
    info "项目目录已存在 ($PROJECT_DIR)，执行 git pull 更新..."
    git pull
    pass "代码已更新到最新"
else
    info "克隆代码到 $PROJECT_DIR ..."
    git clone git@github.com:BH6340/ICube.git "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    pass "代码克隆完成"
fi

# 再次确认进入项目目录
cd "$PROJECT_DIR"
if [ ! -f "docker-compose.yml" ]; then
    fail "目录内未找到 docker-compose.yml，请确认项目结构正常"
fi

# ---------- 3. 交互式填写配置 ----------
((STEPS++)) || true; step "填写服务器配置"

# 3.1 服务器公网 IP
read -rp "请输入服务器公网 IP（例如 103.100.211.146）: " SERVER_IP
if [ -z "$SERVER_IP" ]; then
    fail "IP 不能为空"
fi

# 3.2 域名（可空，后续 HTTPS 再填）
read -rp "请输入域名（没有就直接回车，后续 HTTPS 时再填）: " DOMAIN_NAME
if [ -z "$DOMAIN_NAME" ]; then
    DOMAIN_NAME="$SERVER_IP"
fi

# 3.3 SERVER_HOST（支付宝回调地址）
SERVER_HOST="http://$DOMAIN_NAME"

ALLOWED_HOSTS="$SERVER_IP,$DOMAIN_NAME,localhost,127.0.0.1"
ALLOWED_ORIGIN="$DOMAIN_NAME"

echo ""
info "配置预览："
echo "  ALLOWED_HOSTS   = $ALLOWED_HOSTS"
echo "  ALLOWED_ORIGIN  = $ALLOWED_ORIGIN"
echo "  SERVER_HOST     = $SERVER_HOST"

# ---------- 4. 自动生成 SECRET_KEY ----------
((STEPS++)) || true; step "自动生成 Django SECRET_KEY"
if command -v python3 &>/dev/null; then
    # 整个 -c 参数用单引号，避免 bash !@# 历史扩展问题
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')
elif command -v openssl &>/dev/null; then
    SECRET_KEY=$(openssl rand -base64 64 | tr -d '\n')
else
    # 最后兜底，读 urandom
    SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9!@#$%^&*(-_=+)' | head -c 80)
fi
if [ -z "$SECRET_KEY" ]; then
    fail "SECRET_KEY 生成失败，请手动填写"
fi
pass "SECRET_KEY 已自动生成（长度 ${#SECRET_KEY}）"

# ---------- 5. 写 .env 文件 ----------
((STEPS++)) || true; step "写入 .env 配置文件"
cat > "$PROJECT_DIR/.env" << EOF
# ========== 自动生成的部署配置 ==========
# 允许访问的主机
ALLOWED_HOSTS=$ALLOWED_HOSTS

# 允许的前端跨域来源
ALLOWED_ORIGIN=$ALLOWED_ORIGIN

# 支付宝回调地址
SERVER_HOST=$SERVER_HOST

# Django 生产密钥（自动生成，不要泄漏）
SECRET_KEY=$SECRET_KEY

# 数据库密码（与 docker-compose.yml 保持一致）
DB_PASSWORD=icube123

# 支付宝配置（上线支付前需修改）
ALIPAY_APP_ID=9021000162660623
ALIPAY_DEBUG=True
EOF

pass ".env 已写入到 $PROJECT_DIR/.env"

# ---------- 6. 建 SSL 目录 ----------
((STEPS++)) || true; step "创建 Nginx SSL 挂载目录"
mkdir -p "$PROJECT_DIR/nginx/ssl"
pass "nginx/ssl 目录已创建"

# ---------- 7. 构建 & 启动服务 ----------
((STEPS++)) || true; step "docker compose up -d --build（首次 5-15 分钟，耐心等待）"
docker compose up -d --build
pass "docker compose 启动完成"

# ---------- 8. 检查容器状态 ----------
((STEPS++)) || true; step "检查容器状态"
sleep 5
docker compose ps
echo ""
UP_COUNT=$(docker compose ps --format '{{.Status}}' | grep -c 'Up' || true)
TOTAL_SVCS=$(docker compose config --services | wc -l)
if [ "$UP_COUNT" -lt "$TOTAL_SVCS" ]; then
    warn "有容器未 Up，请用 docker compose ps / logs 排查，然后继续执行验证步骤"
else
    pass "$UP_COUNT / $TOTAL_SVCS 个容器已 Up"
fi

# ---------- 9. 等 MySQL healthy + migrate / collectstatic ----------
((STEPS++)) || true; step "等待 MySQL healthy"
echo -n "等待中"
for i in $(seq 1 30); do
    STATUS=$(docker inspect -f '{{.State.Health.Status}}' icube_db 2>/dev/null || echo "starting")
    if [ "$STATUS" = "healthy" ]; then
        echo " done"
        break
    fi
    sleep 2
    echo -n "."
done
echo ""
STATUS=$(docker inspect -f '{{.State.Health.Status}}' icube_db 2>/dev/null || echo "unknown")
if [ "$STATUS" != "healthy" ]; then
    warn "MySQL 仍未 healthy，可能是初始化较慢；继续尝试（如报错请用 docker compose logs db 排查）"
else
    pass "MySQL healthy，迁移和静态文件已在容器启动时自动执行"
    # 可选：手动再补一次 migrate + collectstatic，保证万无一失
    info "手动再执行一次 migrate + collectstatic（幂等，重复执行无影响）"
    docker compose exec -T api python manage.py migrate --noinput 2>&1 | tail -3
    docker compose exec -T api python manage.py collectstatic --noinput 2>&1 | tail -1
fi

# ---------- 10. 验证 HTTP ----------
((STEPS++)) || true; step "验证 HTTP 访问（服务器本地）"

sleep 3
# 前端
echo "  → GET /  "
FRONT_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1/ || echo 000)
[ "$FRONT_CODE" = "200" ] && pass "前端首页 返回 $FRONT_CODE" || warn "前端首页 返回 $FRONT_CODE（Nginx 可能还在启动）"

# API 登录端点
echo "  → GET /api/users/login/  "
API_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1/api/users/login/ || echo 000)
([ "$API_CODE" = "200" ] || [ "$API_CODE" = "405" ]) && pass "登录接口 返回 $API_CODE（405 表示 GET 方法拒绝，属正常）" || warn "登录接口 返回 $API_CODE"

# 静态文件目录
echo "  → GET /static/  "
STATIC_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1/static/ || echo 000)
([ "$STATIC_CODE" = "200" ] || [ "$STATIC_CODE" = "403" ]) && pass "静态目录 返回 $STATIC_CODE（403 为禁止列目录，属正常）" || warn "静态目录 返回 $STATIC_CODE（可能 collectstatic 未完成）"

# ---------- 最终输出 ----------
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   第 2 步应用部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "浏览器访问地址："
echo -e "  前台首页：  ${CYAN}http://$SERVER_IP/${NC}"
echo -e "  后台管理：  ${CYAN}http://$SERVER_IP/admin/${NC}"
echo -e "  登录接口：  ${CYAN}http://$SERVER_IP/api/users/login/${NC}"
echo ""
echo -e "如果尚未创建超级管理员，可执行："
echo -e "  ${YELLOW}cd ~/ICube && docker compose exec api python manage.py createsuperuser${NC}"
echo ""
echo -e "后续步骤："
echo -e "  1. （可选，有域名时）执行 ${YELLOW}sudo bash scripts/deploy/deploy_03_https.sh${NC} 配置 HTTPS"
echo -e "  2. 更新代码执行 ${YELLOW}bash scripts/deploy/deploy_update.sh${NC}"
echo ""
