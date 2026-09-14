#!/bin/bash
set -e

echo "=============================="
echo "  DuckDNS HTTPS 一键配置脚本"
echo "=============================="

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
NGINX_CONF_DIR=$PROJECT_DIR/nginx/conf.d
SSL_DIR=$PROJECT_DIR/nginx/ssl

# 1. 拷贝 Let's Encrypt 证书
echo "[1/5] 拷贝 SSL 证书..."
mkdir -p $SSL_DIR
sudo cp /etc/letsencrypt/live/bh6340.duckdns.org/fullchain.pem $SSL_DIR/
sudo cp /etc/letsencrypt/live/bh6340.duckdns.org/privkey.pem $SSL_DIR/
sudo chmod 644 $SSL_DIR/*.pem
echo "  -> 证书已拷贝到 $SSL_DIR/"

# 2. 创建共享路由配置
echo "[2/5] 创建 Nginx 共享路由配置..."
cat > $NGINX_CONF_DIR/icube_routes.inc << 'ROUTESEOF'
    location /api/ {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
    }
    location /admin/ {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
    }
    location /media/ { alias /usr/share/nginx/html/media/; expires 30d; }
    location ~ ^/static/admin/ { alias /usr/share/nginx/html/static/admin/; expires 7d; add_header Cache-Control "public, max-age=604800"; }
    location /static/ { alias /usr/share/nginx/html/static/; expires 30d; }
    location /docs/ {
        alias /usr/share/nginx/html/docs/;
        index index.html;
        try_files $uri $uri/ /docs/index.html;
        default_type text/plain;
        add_header Content-Disposition "inline";
        location ~ \.md$ {
            default_type text/plain;
            add_header Content-Disposition "inline";
            add_header Cache-Control "no-cache, must-revalidate";
            expires off;
        }
    }
    location /code/ {
        alias /usr/share/nginx/html/code/;
        default_type text/plain;
        add_header Content-Disposition "inline";
        add_header Access-Control-Allow-Origin *;
    }
    location /apk/ {
        alias /usr/share/nginx/html/apk/;
        autoindex on;
        types { application/vnd.android.package-archive apk; }
        default_type application/vnd.android.package-archive;
        add_header Content-Disposition "attachment";
    }
    location / {
        proxy_pass http://front:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    access_log /var/log/nginx/icube_access.log;
    error_log /var/log/nginx/icube_error.log;
ROUTESEOF
echo "  -> 路由配置已创建: icube_routes.inc"

# 3. 重写 icube.conf（HTTPS 8443 + HTTP 80 共享路由）
echo "[3/5] 重写 Nginx 站点配置..."
cat > $NGINX_CONF_DIR/icube.conf << 'NGINXEOF'
# HTTPS：DuckDNS + Let's Encrypt 证书，免备案非标准端口
server {
    listen 8443 ssl;
    server_name bh6340.duckdns.org;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    include /etc/nginx/conf.d/icube_routes.inc;
}

# HTTP：IP 直连和本地访问
server {
    listen 80;
    server_name _;

    include /etc/nginx/conf.d/icube_routes.inc;
}
NGINXEOF
echo "  -> 站点配置已重写: icube.conf"

# 4. 给 docker-compose.yml 加 8443 端口
echo "[4/5] 更新 docker-compose.yml..."
if ! grep -q "8443:8443" $PROJECT_DIR/docker-compose.yml; then
    sed -i '/"443:443"/a\      - "8443:8443"' $PROJECT_DIR/docker-compose.yml
    echo "  -> 已添加 8443 端口映射"
else
    echo "  -> 8443 端口已存在，跳过"
fi

# 5. 重建 Nginx 和 API 容器
echo "[5/5] 重建容器..."
cd $PROJECT_DIR
docker compose up -d --force-recreate nginx
echo ""
echo "=============================="
echo "  配置完成！"
echo "=============================="
echo ""
echo "验证步骤："
echo "  1. 确认 Nginx 配置无误："
echo "     docker compose exec nginx nginx -t"
echo ""
echo "  2. 测试 HTTPS 连接："
echo "     curl -k https://bh6340.duckdns.org:8443/"
echo ""
echo "  3. 浏览器访问："
echo "     https://bh6340.duckdns.org:8443/"
echo ""
echo "注意：确保阿里云安全组已开放 8443/TCP 端口"
