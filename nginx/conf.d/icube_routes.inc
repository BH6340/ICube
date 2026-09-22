    # 保留 /api/ 前缀并转发给 Compose 中的 api 服务
    location /api/ {
        proxy_pass http://api:8000;

        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $http_host;
        proxy_set_header X-Forwarded-Port $server_port;

        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Django Admin 后台
    location /admin/ {
        proxy_pass http://api:8000;

        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $http_host;
        proxy_set_header X-Forwarded-Port $server_port;

        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 用户上传文件由宿主机 ./media 绑定目录提供
    location /media/ {
        alias /usr/share/nginx/html/media/;
        expires 30d;
    }

    # Django Admin 静态资源（7天缓存，更新不频繁）
    location ~ ^/static/admin/ {
        alias /usr/share/nginx/html/static/admin/;
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
    }

    # Django collectstatic 产物通过 collected_static 命名卷共享
    location /static/ {
        alias /usr/share/nginx/html/static/;
        expires 30d;
    }

    # Docsify 文档站点
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

    # 后端源码只读访问
    location /code/ {
        alias /usr/share/nginx/html/code/;
        default_type text/plain;
        add_header Content-Disposition "inline";
        add_header Access-Control-Allow-Origin *;
    }

    # Uptime Kuma 监控面板（WebSocket + 子路径重写）
    location /monitor/ {
        proxy_pass http://uptime-kuma:3001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 重写 Location 头：/dashboard → /monitor/dashboard
        proxy_redirect / /monitor/;

        # 重写页面内路径
        sub_filter 'href="/' 'href="/monitor/';
        sub_filter 'src="/' 'src="/monitor/';
        sub_filter 'action="/' 'action="/monitor/';
        sub_filter '"/socket' '"/monitor/socket';
        sub_filter '"/assets/' '"/monitor/assets/';
        sub_filter '"/icon.svg' '"/monitor/icon.svg';
        sub_filter_once off;
        sub_filter_types application/javascript text/css;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_connect_timeout 10s;
        proxy_read_timeout 120s;
    }

    # Kuma Socket.io WebSocket 连接（子路径模式）
    location /monitor/socket.io/ {
        proxy_pass http://uptime-kuma:3001/socket.io/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_connect_timeout 10s;
        proxy_read_timeout 120s;
    }

    # APK 下载目录
    location /apk/ {
        alias /usr/share/nginx/html/apk/;
        autoindex on;
        types { application/vnd.android.package-archive apk; }
        default_type application/vnd.android.package-archive;
        add_header Content-Disposition "attachment";
    }

    # 其余请求交给前端容器；SPA 路由回退由前端 Nginx 处理
    location / {
        proxy_pass http://front:80;

        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $http_host;
        proxy_set_header X-Forwarded-Port $server_port;
    }

    access_log /var/log/nginx/icube_access.log;
    error_log /var/log/nginx/icube_error.log;
