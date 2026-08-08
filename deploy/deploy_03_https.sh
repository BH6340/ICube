#!/bin/bash
# ICube 半自动化部署脚本 - 第 3 步：配置 HTTPS（root 执行）
# 功能：Certbot 申请 Let's Encrypt 免费证书 + Nginx HTTPS 配置 + 自动续期钩子

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

TOTAL=8
STEPS=0

# ---------- 权限检查 ----------
if [ "$USER" != "root" ]; then
    fail "此脚本必须以 root 身份运行，请先 su - root"
fi

# ---------- 定位项目目录 ----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR_DEFAULT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [ -f "$PROJECT_DIR_DEFAULT/docker-compose.yml" ]; then
    PROJECT_DIR="$PROJECT_DIR_DEFAULT"
else
    PROJECT_DIR="/home/bh/ICube"
fi
if [ ! -f "$PROJECT_DIR/docker-compose.yml" ]; then
    fail "未找到项目目录（$PROJECT_DIR 下没有 docker-compose.yml）"
fi
info "项目目录: $PROJECT_DIR"

# ---------- 1. 交互式输入域名和邮箱 ----------
((STEPS++)) || true; step "输入域名和邮箱"

read -rp "请输入域名（必须已解析到本服务器公网 IP，例如 icube.example.com）: " DOMAIN_NAME
if [ -z "$DOMAIN_NAME" ]; then
    fail "域名不能为空"
fi

read -rp "请输入你的邮箱（Let's Encrypt 用于续期提醒）: " CONTACT_EMAIL
if [ -z "$CONTACT_EMAIL" ]; then
    fail "邮箱不能为空"
fi

# 验证域名解析
info "正在验证 $DOMAIN_NAME 是否解析到本服务器公网 IP..."
SERVER_PUB_IP=$(curl -s https://ifconfig.me || curl -s https://api.ipify.org || echo "")
if [ -n "$SERVER_PUB_IP" ]; then
    DNS_IP=$(dig +short "$DOMAIN_NAME" 2>/dev/null | tail -1 || echo "")
    if [ -z "$DNS_IP" ]; then
        DNS_IP=$(nslookup "$DOMAIN_NAME" 2>/dev/null | awk '/^Address: / {print $2}' | tail -1 || echo "")
    fi
    if [ -n "$DNS_IP" ] && [ "$DNS_IP" != "$SERVER_PUB_IP" ]; then
        warn "域名 $DOMAIN_NAME 解析到 $DNS_IP，但本服务器公网 IP 是 $SERVER_PUB_IP"
        warn "如果解析未生效，Certbot 会失败！请确认后再继续"
        read -rp "按回车继续（Ctrl+C 终止）" _
    else
        pass "域名解析验证通过（解析到 $DNS_IP）"
    fi
fi

# ---------- 2. 安装 Certbot ----------
((STEPS++)) || true; step "安装 Certbot"
apt update -qq
apt install -y -qq certbot
pass "Certbot 安装完成: $(certbot --version)"

# ---------- 3. 临时停止 Nginx 容器（释放 80 端口，Certbot standalone 要用）----------
((STEPS++)) || true; step "临时停止 Nginx 容器（释放 80 端口）"
cd "$PROJECT_DIR"
# 先记录 nginx 状态，原来就是 stopped 的话就不重启
NGINX_WAS_UP=$(docker compose ps --format '{{.Status}}' nginx 2>/dev/null | grep -c 'Up' || echo 0)
if [ "$NGINX_WAS_UP" -gt 0 ]; then
    docker compose stop nginx
    sleep 2
fi
pass "Nginx 容器已停止"

# ---------- 4. Certbot 申请证书（standalone 模式）----------
((STEPS++)) || true; step "使用 Certbot standalone 模式申请证书"
# --non-interactive 必须配合 --agree-tos --email --no-eff-email
# 如果失败（解析没生效）退出
certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN_NAME" \
    --email "$CONTACT_EMAIL" \
    --preferred-challenges http

if [ -f "/etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem" ]; then
    pass "证书申请成功：/etc/letsencrypt/live/$DOMAIN_NAME/"
else
    fail "证书申请失败，请检查域名解析后重试"
fi

# ---------- 5. 复制证书到容器挂载目录 ----------
((STEPS++)) || true; step "复制证书到项目 nginx/ssl 挂载目录"
mkdir -p "$PROJECT_DIR/nginx/ssl"
cp -f "/etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem" "$PROJECT_DIR/nginx/ssl/"
cp -f "/etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem"   "$PROJECT_DIR/nginx/ssl/"
chown bh:bh "$PROJECT_DIR/nginx/ssl/"*.pem 2>/dev/null || true
pass "证书已复制到 $PROJECT_DIR/nginx/ssl/"
echo "  fullchain.pem  大小: $(wc -c < "$PROJECT_DIR/nginx/ssl/fullchain.pem") bytes"
echo "  privkey.pem    大小: $(wc -c < "$PROJECT_DIR/nginx/ssl/privkey.pem") bytes"

# ---------- 6. 写最终的 HTTPS Nginx 配置 ----------
((STEPS++)) || true; step "写入 HTTPS 版 Nginx 配置"
cp -f "$PROJECT_DIR/nginx/conf.d/icube.conf" "$PROJECT_DIR/nginx/conf.d/icube.conf.bak.$(date +%Y%m%d_%H%M%S)"

cat > "$PROJECT_DIR/nginx/conf.d/icube.conf" << EOF
# ========== HTTP → HTTPS 强制跳转 ==========
server {
    listen 80;
    server_name $DOMAIN_NAME;

    # Let's Encrypt 续期认证路径
    location ~ /.well-known/acme-challenge/ {
        root /usr/share/nginx/html;
        allow all;
    }

    location / {
        return 301 https://\$host\$request_uri;
    }
}

# ========== HTTPS 主配置 ==========
server {
    listen 443 ssl http2;
    server_name $DOMAIN_NAME;

    # SSL 证书（对应 nginx/ssl 挂载目录）
    ssl_certificate     /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    root /usr/share/nginx/html;
    index index.html;

    location /api/ {
        proxy_pass http://icube_api:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /media/ {
        alias /usr/share/nginx/html/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /static/ {
        alias /usr/share/nginx/html/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    access_log /var/log/nginx/icube_access.log;
    error_log  /var/log/nginx/icube_error.log;
}
EOF

pass "Nginx 配置已写入，原配置已备份"

# ---------- 7. 配置自动续期钩子 ----------
((STEPS++)) || true; step "配置 Certbot 自动续期钩子"
mkdir -p /etc/letsencrypt/renewal-hooks/deploy
HOOK_FILE="/etc/letsencrypt/renewal-hooks/deploy/deploy-icube.sh"
cat > "$HOOK_FILE" << EOF
#!/bin/bash
# Let's Encrypt 续期成功后自动执行：
# 复制新证书到 ICube 的 nginx/ssl 目录，并重启 Nginx 容器
DOMAIN="$DOMAIN_NAME"
PROJECT_DIR="$PROJECT_DIR"

cp -f "/etc/letsencrypt/live/\$DOMAIN/fullchain.pem" "\$PROJECT_DIR/nginx/ssl/"
cp -f "/etc/letsencrypt/live/\$DOMAIN/privkey.pem"   "\$PROJECT_DIR/nginx/ssl/"

cd "\$PROJECT_DIR"
docker compose restart nginx >/dev/null 2>&1

logger -t certbot-deploy "ICube Nginx restarted after certificate renewal for \$DOMAIN"
EOF
chmod +x "$HOOK_FILE"
pass "自动续期钩子已写入: $HOOK_FILE"

# 测试续期（dry-run，不真正续期，但验证钩子能加载）
info "执行一次续期演练（dry-run，验证流程）..."
certbot renew --dry-run --quiet 2>&1 | tail -3 || true

# ---------- 8. 重启 Nginx 容器并验证 ----------
((STEPS++)) || true; step "重启 Nginx 容器 & 验证 HTTPS"

cd "$PROJECT_DIR"
docker compose start nginx
sleep 3
# 检查状态
docker compose ps nginx
NGINX_STATUS=$(docker compose ps --format '{{.Status}}' nginx 2>/dev/null | head -1 || echo "")
echo "$NGINX_STATUS" | grep -q 'Up' || fail "Nginx 容器启动失败，请查看 docker compose logs nginx"

# HTTPS 验证
echo ""
info "本地验证 HTTPS（忽略自签警告）..."
HTTPS_CODE=$(curl -sk -o /dev/null -w '%{http_code}' "https://127.0.0.1/" --resolve "$DOMAIN_NAME:443:127.0.0.1" || echo 000)
echo "  https://$DOMAIN_NAME/  返回: $HTTPS_CODE"
([ "$HTTPS_CODE" = "200" ] || [ "$HTTPS_CODE" = "301" ] || [ "$HTTPS_CODE" = "302" ]) \
    && pass "HTTPS 验证通过" \
    || warn "本地验证返回 $HTTPS_CODE（可能是端口映射导致，建议浏览器再确认）"

# ---------- 最终输出 ----------
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   第 3 步 HTTPS 配置完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "浏览器访问地址："
echo -e "  ${CYAN}https://$DOMAIN_NAME/${NC}"
echo ""
echo -e "💡 别忘了更新 .env 中 SERVER_HOST 为 https:// 前缀（如需）"
echo -e "💡 证书 90 天到期，certbot 已配置 systemd timer 自动续期，并重启 Nginx"
echo ""
