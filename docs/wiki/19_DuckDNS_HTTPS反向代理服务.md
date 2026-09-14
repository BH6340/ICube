# DuckDNS HTTPS 反向代理服务配置指南

> 本文档记录 ICube 项目从 Cloudflare Tunnel 迁移到 DuckDNS + Let's Encrypt 方案的完整过程，
> 涵盖原理、实施步骤、踩坑记录与运维维护。
>
> 适用场景：阿里云国内服务器、试用期未备案、需要 HTTPS 访问。

---

## 一、背景与方案选型

### 1.1 问题背景：为什么需要 HTTPS

ICube 项目部署在阿里云国内 ECS（8.136.100.251），初期使用 Cloudflare Tunnel 实现 HTTPS。

原方案 `https://bh6340.me` 通过 Cloudflare Tunnel → 服务器 Nginx 的链路提供 HTTPS 访问。
但 cloudflared 需要通过 QUIC 协议（UDP 7844 端口）连接 Cloudflare 边缘节点，
国内服务器跨境网络不稳定，导致隧道频繁断连、HTTPS 间歇性 502。

此外，Django Admin 后台登录需要 HTTPS（CSRF 验证依赖安全来源），HTTP 方式会导致 403。

### 1.2 国内服务器免备案 HTTPS 方案对比

| 方案 | 原理 | 速度 | 成本 | 稳定性 | 复杂度 | 备案 |
|------|------|------|------|--------|--------|------|
| **Cloudflare Tunnel** | 服务器主动连 Cloudflare 边缘（7844 端口） | 慢 | 免费 | 差（跨境网络） | 低 | 不需要 |
| **cpolar 等穿透** | 第三方内网穿透服务 | 中等 | 免费/付费 | 中等 | 低 | 不需要 |
| **DuckDNS + Let's Encrypt** | DDNS 解析 + 直连服务器 + 自管证书 | 快 | 免费 | 高 | 中 | 不需要（非标准端口） |
| **frp 自建中继** | 海外 VPS 做中转 | 取决于中继 | ~$3-5/月 | 高 | 中 | 不需要 |
| **域名直接解析 + 443** | 域名 A 记录指向服务器 IP | 快 | 免费 | 高 | 低 | **国内必须备案** |

**DuckDNS 方案核心优势**：直连服务器不经过任何中转，速度快；Let's Encrypt 证书免费；非标准端口（8443）绕过阿里云备案检测。

### 1.3 方案架构图

```
用户浏览器
  │
  ├─ https://bh6340.duckdns.org:8443/
  │     │
  │     ├─ DNS 解析：bh6340.duckdns.org → 8.136.100.251
  │     │   (DuckDNS 提供 DDNS，每5分钟/每天保活)
  │     │
  │     └─ 直连服务器 8.136.100.251:8443
  │           │
  │           └─ Nginx (icube_nginx 容器)
  │                 ├─ SSL 证书：Let's Encrypt (DNS-01 验证获取)
  │                 ├─ 8443 ssl → 反向代理 → front:80 (前端)
  │                 ├─ /api/    → 反向代理 → api:8000 (Django)
  │                 ├─ /admin/ → 反向代理 → api:8000 (Django Admin)
  │                 ├─ /media/  → 静态文件
  │                 └─ /static/ → 静态文件
  │
  └─ http://8.136.100.251/ (IP 直连，不走域名)
        └─ Nginx 80 端口 (不触发备案检测)
```

---

## 二、核心知识点与原理

### 2.1 反向代理

#### 正向代理 vs 反向代理

| 类型 | 方向 | 用户感知 | 典型场景 |
|------|------|---------|---------|
| **正向代理** | 用户 → 代理 → 服务器 | 用户知道代理存在 | VPN、科学上网、爬虫 IP 池 |
| **反向代理** | 用户 → 代理 → 内部服务器 | 用户不知道内部服务器 | Nginx、负载均衡、CDN |

反向代理的核心：用户只看到代理服务器（Nginx），看不到后面的应用服务器（Django、前端容器）。

#### Nginx 反向代理工作原理

Nginx 接收 HTTP 请求后，根据 `location` 匹配规则决定转发目标：

```nginx
location /api/ {
    proxy_pass http://api:8000;  # 转发给 Docker 网络中的 api 容器
}
```

#### proxy_pass 与 Host/X-Forwarded-* 头

反向代理转发请求时，默认不修改请求头。但后端需要知道原始请求信息：

| 请求头 | 作用 | 示例值 |
|--------|------|--------|
| `Host` | 原始请求的域名 | `bh6340.duckdns.org` |
| `X-Real-IP` | 用户真实 IP | `1.2.3.4` |
| `X-Forwarded-For` | 代理链路 IP | `1.2.3.4, 172.18.0.6` |
| `X-Forwarded-Proto` | 原始协议 | `https` |

如果不设置 `X-Forwarded-Proto: https`，Django 会认为请求是 HTTP，
导致 CSRF cookie 不设 Secure 标志、重定向到 HTTP 等问题。

Nginx 配置标准写法：

```nginx
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```

### 2.2 DNS 与 DDNS

#### DNS 解析流程

```
浏览器输入 bh6340.duckdns.org
  │
  ├─ 1. 查本地缓存 → 没命中
  ├─ 2. 查系统 hosts → 没命中
  ├─ 3. 查本地 DNS 服务器 → 没命中
  ├─ 4. 递归查询：从根域名服务器开始
  │     ├─ 根 (.) → 指向 .org 的 NS
  │     ├─ .org NS → 指向 duckdns.org 的 NS
  │     └─ duckdns.org NS → 返回 bh6340.duckdns.org 的 A 记录
  │        返回 IP: 8.136.100.251
  └─ 5. 浏览器连接 8.136.100.251:8443
```

#### 动态 DNS（DDNS）原理

传统 DNS 的 A 记录是静态的，IP 变了要手动改。
DDNS 通过 API 自动更新 A 记录：客户端定时调用 DDNS 服务的 API，上报当前 IP。

#### DuckDNS 的工作方式

DuckDNS 是免费 DDNS 服务，提供 `xxx.duckdns.org` 子域名。

更新 API：

```
https://www.duckdns.org/update?domains=bh6340&token=你的token&ip=
```

#### 为什么 `ip=` 留空能自动检测

`ip=` 参数留空时，DuckDNS 服务器会从 HTTP 请求的来源 IP（`REMOTE_ADDR`）自动获取客户端的公网 IP。
这比客户端自己检测更准确——因为客户端可能在内网（NAT 后面），无法获知自己的公网 IP。

> **注意**：阿里云服务器 IP 是静态的，不会变。但 DuckDNS 规定 **30 天不更新的域名会被删除**，
> 所以仍需定时调用 API 保活。

### 2.3 HTTPS 与 SSL/TLS

#### HTTPS 握手过程

```
客户端                                     服务器
  │                                           │
  │─── 1. ClientHello ──────────────────────→ │  (支持的 TLS 版本、加密套件、随机数)
  │                                           │
  │←── 2. ServerHello + 证书 + 公钥 ────────── │  (选择加密套件、服务器证书、服务器随机数)
  │                                           │
  │─── 3. 验证证书 → 生成 Pre-Master Secret ──→│  (用服务器公钥加密 Pre-Master)
  │     用公钥加密发送                          │
  │                                           │
  │←═══ 4. 双方用三个随机数生成对称密钥 ═══════│  (对称加密开始)
  │                                           │
  │═══ 5. 加密通信 ═══════════════════════════│
```

#### 证书链：root CA → intermediate → leaf

```
ISRG Root X1 (根 CA，自签名，预装在操作系统/浏览器中)
  └─ Let's Encrypt R3 (中间 CA)
       └─ bh6340.duckdns.org (叶子证书，你的证书)
```

浏览器验证链路：
1. 收到叶子证书 + 中间证书（`fullchain.pem` 包含两者）
2. 用中间证书的公钥验证叶子证书的签名
3. 用根证书的公钥验证中间证书的签名
4. 根证书在系统信任库中 → 验证通过

#### 非对称加密 vs 对称加密在 HTTPS 中的分工

| 阶段 | 加密方式 | 用途 |
|------|---------|------|
| 握手阶段 | 非对称加密（RSA/ECDHE） | 安全交换对称密钥 |
| 通信阶段 | 对称加密（AES） | 高效传输数据 |

非对称加密慢但安全（用于握手），对称加密快（用于数据传输）。

### 2.4 Let's Encrypt 与 ACME 协议

#### Let's Encrypt 免费证书机制

Let's Encrypt 是免费、自动化的 CA（证书颁发机构），由 ISRG（互联网安全研究组）运营。
证书有效期 90 天，通过 ACME 协议自动颁发和续期。

#### ACME 协议三种验证方式

| 方式 | 原理 | 需要的端口 | 适用场景 |
|------|------|-----------|---------|
| **HTTP-01** | CA 访问 `http://域名/.well-known/acme-challenge/xxx` | 80 | 有公网 80 端口 |
| **DNS-01** | CA 查询 `_acme-challenge.域名` 的 TXT 记录 | 无 | 任何场景 |
| **TLS-ALPN-01** | CA 用 TLS 连接验证 | 443 | 特殊场景 |

#### 为什么国内服务器只能用 DNS-01

阿里云国内服务器有**域名备案检测机制**：
当用域名（非 IP）通过 80 端口访问时，如果域名未备案，阿里云网络层会返回 `Connection reset by peer`。

Let's Encrypt 的 HTTP-01 验证需要 CA 用域名访问 80 端口取验证文件，
但域名访问 80 端口被阿里云拦截，导致验证失败。

IP 直连 80 端口不触发检测（如 `http://8.136.100.251`），但 CA 只认域名不认 IP。

**DNS-01 不依赖任何端口**，只需在 DNS 添加 TXT 记录，完全绕过备案检测。

### 2.5 非标准端口（8443）

#### 为什么不用标准 443

阿里云的备案检测不仅检查 80 端口，**域名访问 443 端口同样会检测备案**。
试用服务器未备案，域名访问 443 会被拦截。

非标准端口（8443）不在阿里云检测范围内，可以正常使用。

#### 阿里云域名备案检测机制

| 访问方式 | 端口 | 是否检测备案 | 结果 |
|---------|------|-------------|------|
| IP 直连 | 80 | 否 | 正常 |
| 域名访问 | 80 | **是** | Connection reset |
| 域名访问 | 443 | **是** | Connection reset |
| 域名访问 | 8443 | 否 | 正常 |

#### IP 直连 vs 域名访问的行为差异

- `http://8.136.100.251` → 阿里云视为 IP 访问，不检查备案 → 正常
- `http://bh6340.duckdns.org` → 阿里云视为域名访问，检查备案 → 被 reset
- `https://bh6340.duckdns.org:8443` → 非标准端口，不检查备案 → 正常

### 2.6 Django CSRF 与 ALLOWED_HOSTS

#### CSRF_TRUSTED_ORIGINS 的作用

Django 4.0+ 对 HTTPS 请求强制要求 `CSRF_TRUSTED_ORIGINS` 配置。
当用户通过 HTTPS 提交 POST 表单时，Django 检查请求的 `Origin` 头是否在信任列表中。

**格式要求**：必须包含协议 + 域名 + 端口（非标准端口时）：

```python
CSRF_TRUSTED_ORIGINS = [
    "https://bh6340.duckdns.org:8443",  # 非标准端口必须带端口
    "http://localhost",                  # 标准端口可省略
]
```

**为什么需要带端口**：浏览器的 `Origin` 头包含端口（如 `https://bh6340.duckdns.org:8443`），
Django 做精确匹配，不带端口会匹配失败。

#### ALLOWED_HOSTS 的作用

`ALLOWED_HOSTS` 检查请求的 `Host` 头是否允许。与 CSRF 不同：

| 配置 | 检查的请求头 | 是否包含端口 | 对应 Django 中间件 |
|------|-------------|-------------|-------------------|
| `ALLOWED_HOSTS` | `Host` | **不包含端口** | `HostMiddleware` |
| `CSRF_TRUSTED_ORIGINS` | `Origin` | **包含端口**（非标准端口时） | `CsrfViewMiddleware` |

```python
ALLOWED_HOSTS = ["bh6340.duckdns.org", ...]  # 不带端口
CSRF_TRUSTED_ORIGINS = ["https://bh6340.duckdns.org:8443", ...]  # 带端口
```

#### 为什么两者都需要配置

- 缺 `ALLOWED_HOSTS` → Django 返回 `DisallowedHost: Invalid HTTP_HOST header`（400）
- 缺 `CSRF_TRUSTED_ORIGINS` → Django 返回 `CSRF verification failed`（403）

Admin 后台登录是 POST + Session 认证，两个检查都会触发，缺一不可。

### 2.7 Docker 网络与端口映射

#### ports vs expose

| 指令 | 作用 | 对外可见 |
|------|------|---------|
| `ports: "8443:8443"` | 映射到宿主机 | 外部可访问 |
| `expose: 8443` | 仅在 Docker 网络内开放 | 外部不可访问 |

本方案需要在 `docker-compose.yml` 的 nginx 服务中添加 `ports: "8443:8443"`。

#### volumes 挂载证书目录

Let's Encrypt 证书在宿主机 `/etc/letsencrypt/live/bh6340.duckdns.org/`，
Nginx 容器需要读取这些文件：

```yaml
volumes:
  - ./nginx/ssl:/etc/nginx/ssl  # 证书拷贝到项目目录后挂载
```

> **注意**：直接挂载 `/etc/letsencrypt/` 也可行，但 Let's Encrypt 的实际文件是符号链接，
> Docker 挂载符号链接可能有问题。更稳妥的做法是拷贝证书文件到 `nginx/ssl/` 目录。

#### Nginx include 机制与 .conf/.inc 后缀区别

Nginx 的 `include /etc/nginx/conf.d/*.conf` 会自动加载该目录下所有 `.conf` 文件到 `http` 顶层上下文。

**问题**：如果把 `location` 指令放在 `.conf` 文件里，Nginx 会在 `http` 上下文中解析它，
而 `location` 只能出现在 `server` 块内，导致 `"location" directive is not allowed here` 错误。

**解决**：将共享路由配置文件后缀改为 `.inc`，Nginx 不会自动加载它，
只能通过 `include /etc/nginx/conf.d/icube_routes.inc` 在 `server` 块内显式引用：

```
nginx/conf.d/
  ├── icube.conf         # Nginx 自动加载（包含 server 块）
  └── icube_routes.inc   # 不被自动加载（通过 include 引用）
```

---

## 三、实施步骤

### 3.1 前置条件

**服务器环境要求**：
- 阿里云 ECS（Linux）
- Docker + Docker Compose 已安装
- Nginx 容器已运行（ICube 项目已部署）
- 阿里云安全组已开放 80、443、8443/TCP 端口

**安全组端口开放清单**：

| 端口 | 协议 | 用途 | 来源 |
|------|------|------|------|
| 80 | TCP | HTTP（IP 直连 + Let's Encrypt HTTP-01 验证，本方案未使用） | 0.0.0.0/0 |
| 443 | TCP | 标准 HTTPS（本方案未使用，保留兼容） | 0.0.0.0/0 |
| 8443 | TCP | 非标准端口 HTTPS（本方案核心） | 0.0.0.0/0 |
| 22 | TCP | SSH 管理 | 建议限制来源 IP |

### 3.2 注册 DuckDNS 并配置域名

#### 创建子域名

1. 访问 [duckdns.org](https://www.duckdns.org/)
2. 使用 GitHub/Google 账号登录
3. 在 "domains" 页面创建子域名（如 `bh6340`）
4. 自动检测当前 IP，或手动填写服务器 IP
5. 记录 **token**（后续 API 调用需要）

#### 配置 authtoken 与保活脚本

```bash
# 创建保活脚本
mkdir -p ~/duckdns
echo 'curl -s "https://www.duckdns.org/update?domains=bh6340&token=你的token&ip=" >/dev/null' > ~/duckdns/duck.sh
chmod +x ~/duckdns/duck.sh

# 添加 crontab 定时任务（每天凌晨3点保活）
(crontab -l 2>/dev/null; echo "0 3 * * * ~/duckdns/duck.sh") | crontab -
```

> **为什么是每天一次而不是每 5 分钟**：
> 阿里云服务器 IP 是静态的，不会变。DuckDNS 的 30 天未更新删除策略，
> 每天更新一次即可保活，不需要频繁更新。

#### 验证 DNS 解析

```bash
# 验证域名解析到服务器 IP
dig bh6340.duckdns.org +short
# 期望输出：8.136.100.251

# 验证 API 调用
curl "https://www.duckdns.org/update?domains=bh6340&token=你的token&ip="
# 期望输出：OK
```

### 3.3 获取 Let's Encrypt 证书（DNS-01 验证）

#### 安装 certbot

```bash
sudo apt update
sudo apt install certbot
```

#### 手动 DNS-01 验证流程

```bash
sudo certbot certonly \
  --manual \
  --preferred-challenges dns \
  -d bh6340.duckdns.org \
  --email your-email@qq.com \
  --agree-tos \
  --no-eff-email
```

执行后 certbot 会输出：

```
Please deploy a DNS TXT record under the name:
_acme-challenge.bh6340.duckdns.org.
with the following value:
7LzGQ_7iFgQy3YC3VaQBc95hkyePY8JvETYgHELQKfY
```

#### DuckDNS API 添加 TXT 记录

在服务器上**另开终端**执行：

```bash
curl "https://www.duckdns.org/update?domains=bh6340&token=你的token&txt=7LzGQ_7iFgQy3YC3VaQBc95hkyePY8JvETYgHELQKfY"
```

返回 `OK` 说明 TXT 记录已添加。等待 DNS 生效后验证：

```bash
dig TXT _acme-challenge.bh6340.duckdns.org +short
# 期望输出：7LzGQ_7iFgQy3YC3VaQBc95hkyePY8JvETYgHELQKfY
```

回到 certbot 终端按 **Enter** 继续验证。

#### 证书文件说明

验证成功后，证书保存在：

```
/etc/letsencrypt/live/bh6340.duckdns.org/
  ├── fullchain.pem    # 完整证书链（叶子证书 + 中间证书），Nginx 的 ssl_certificate 用
  ├── privkey.pem      # 私钥，Nginx 的 ssl_certificate_key 用
  ├── cert.pem         # 仅叶子证书（本方案不需要）
  └── chain.pem        # 仅中间证书（本方案不需要）
```

#### 证书续期

手动验证方式获取的证书不会自动续期。续期时重复执行上述命令即可。

也可编写 `--manual-auth-hook` 脚本实现自动续期：

```bash
#!/bin/bash
# /home/bh/duckdns/auth-hook.sh
curl "https://www.duckdns.org/update?domains=bh6340&token=你的token&txt=$CERTBOT_VALIDATION"
sleep 10  # 等待 DNS 生效
```

```bash
sudo certbot renew --manual-auth-hook /home/bh/duckdns/auth-hook.sh
```

证书有效期 90 天，建议在到期前 30 天续期。

### 3.4 Nginx 配置 HTTPS 反向代理

#### 目录结构说明

```
nginx/
  ├── conf.d/
  │   ├── icube.conf          # 站点配置（Nginx 自动加载）
  │   └── icube_routes.inc    # 共享路由配置（通过 include 引用）
  └── ssl/
      ├── fullchain.pem       # SSL 证书（.gitignore 排除）
      └── privkey.pem         # SSL 私钥（.gitignore 排除）
```

#### icube.conf：8443 HTTPS + 80 HTTP 双 server

```nginx
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
```

#### icube_routes.inc：共享路由配置

两个 server 块共享同一套路由，避免重复：

```nginx
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
location /static/ { alias /usr/share/nginx/html/static/; expires 30d; }
# ... 其余路由省略，详见文件
location / {
    proxy_pass http://front:80;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

#### 证书挂载到 Docker 容器

`docker-compose.yml` 的 nginx 服务配置：

```yaml
nginx:
  image: nginx:1.28-alpine
  ports:
    - "80:80"
    - "443:443"
    - "8443:8443"          # 新增非标准端口
  volumes:
    - ./nginx/conf.d:/etc/nginx/conf.d
    - ./nginx/ssl:/etc/nginx/ssl   # 证书目录
    # ... 其余挂载省略
```

#### 拷贝证书到项目目录

```bash
mkdir -p ~/ICube/nginx/ssl
sudo cp /etc/letsencrypt/live/bh6340.duckdns.org/fullchain.pem ~/ICube/nginx/ssl/
sudo cp /etc/letsencrypt/live/bh6340.duckdns.org/privkey.pem ~/ICube/nginx/ssl/
sudo chmod 644 ~/ICube/nginx/ssl/*.pem
```

> **为什么不直接挂载 /etc/letsencrypt**：
> Let's Encrypt 的 `live/` 目录下文件是符号链接（指向 `archive/`），
> Docker 挂载符号链接可能无法正确解析。拷贝到项目目录更稳妥。

### 3.5 Django 后端配置

#### ALLOWED_HOSTS 加域名

```python
# prod.py
ALLOWED_HOSTS = [
    "8.136.100.251",
    "bh6340.me",
    "bh6340.duckdns.org",  # 新增 DuckDNS 域名（不带端口）
    "localhost",
    "127.0.0.1",
    "icube_api",
    "api",
]
```

#### CSRF_TRUSTED_ORIGINS 加带端口的来源

```python
# prod.py
CSRF_TRUSTED_ORIGINS = [
    f"{scheme}://{host}"
    for host in _allowed_origins
    for scheme in ["https", "http"]
] + [
    "http://localhost",
    "https://localhost",
    "https://bh6340.duckdns.org:8443",  # 新增（带端口）
    "http://bh6340.duckdns.org:8443",
]
```

#### 重建 API 容器（build + up）

```bash
cd ~/ICube
docker compose build api      # 重新编译镜像（COPY 最新代码）
docker compose up -d --force-recreate api  # 用新镜像启动容器
```

> **为什么必须先 build 再 up**：
> - `build`：根据 Dockerfile 重新编译镜像，将最新代码 COPY 进镜像
> - `up`：用新镜像创建并启动新容器
> - 只 build 不 up → 新镜像在硬盘上，容器还是旧的
> - 只 up 不 build → 容器重建了，但镜像是旧的，代码没更新

#### 验证配置生效

```bash
docker compose exec api python -c "
from django.conf import settings
print('CSRF:', settings.CSRF_TRUSTED_ORIGINS)
print('ALLOWED:', settings.ALLOWED_HOSTS)
"
```

### 3.6 一键配置脚本

项目提供了 `scripts/setup_duckdns_https.sh` 一键脚本，自动完成证书拷贝、Nginx 配置、Docker 端口映射和容器重建。

#### 脚本说明

脚本按 5 个步骤执行：

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 拷贝 SSL 证书 | 从 `/etc/letsencrypt/` 拷贝到 `nginx/ssl/` |
| 2 | 创建共享路由配置 | 生成 `icube_routes.inc` |
| 3 | 重写 Nginx 站点配置 | 生成 `icube.conf`（8443 + 80 双 server） |
| 4 | 更新 docker-compose.yml | 添加 8443 端口映射 |
| 5 | 重建 Nginx 容器 | `docker compose up -d --force-recreate nginx` |

#### 使用方法

```bash
cd ~/ICube
bash scripts/setup_duckdns_https.sh
```

#### 路径推导逻辑

脚本使用相对路径推导项目根目录，不依赖 `~` 展开：

```bash
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
```

| 调用方式 | `$0` | `dirname $0` | `../..` | `pwd` |
|---------|------|-------------|---------|-------|
| `bash scripts/setup_duckdns_https.sh` | `scripts/...` | `scripts` | `.` | `/home/bh/ICube` |
| `bash ~/ICube/scripts/...` | `~/ICube/scripts/...` | `~/ICube/scripts` | `~/ICube` | `/home/bh/ICube` |

---

## 四、常见问题与排查

### 4.1 Connection reset by peer（HTTP-01 验证失败）

**现象**：

```
Certbot failed to authenticate some domains
Detail: Fetching `http://bh6340.duckdns.org/.well-known/acme-challenge/xxx`: Connection reset by peer
```

**根因**：阿里云国内服务器的域名备案检测机制。用域名访问 80 端口时，
如果域名未备案，阿里云网络层会 reset 连接。Let's Encrypt CA 用域名访问 80 端口获取验证文件，被拦截。

**验证方法**：

```bash
# IP 直连 80 端口 → 正常
curl http://8.136.100.251/

# 域名访问 80 端口 → 被 reset
curl http://bh6340.duckdns.org/
# curl: (56) Recv failure: Connection reset by peer
```

**解决方案**：改用 DNS-01 验证（不依赖任何端口）：

```bash
sudo certbot certonly --manual --preferred-challenges dns -d bh6340.duckdns.org ...
```

### 4.2 Nginx "location directive is not allowed here"

**现象**：

```
nginx: [emerg] "location" directive is not allowed here in /etc/nginx/conf.d/icube_routes.conf:1
```

Nginx 容器进入 restart loop，反复重启。

**根因**：Nginx 默认加载 `conf.d/*.conf` 文件到 `http` 顶层上下文。
`location` 指令只能出现在 `server` 块内，不能在 `http` 上下文中使用。

**解决方案**：将共享路由文件后缀从 `.conf` 改为 `.inc`，Nginx 不会自动加载它，
只能通过 `include` 在 `server` 块内引用：

```bash
cd ~/ICube/nginx/conf.d
mv icube_routes.conf icube_routes.inc
sed -i 's/icube_routes.conf/icube_routes.inc/g' icube.conf
docker compose up -d --force-recreate nginx
```

### 4.3 DisallowedHost / Invalid HTTP_HOST header

**现象**：

```
django.core.exceptions.DisallowedHost: Invalid HTTP_HOST header: 'bh6340.duckdns.org'.
You may need to add 'bh6340.duckdns.org' to ALLOWED_HOSTS.
```

**根因**：Django 的 `ALLOWED_HOSTS` 没有包含 DuckDNS 域名。
`ALLOWED_HOSTS` 检查请求的 `Host` 头，域名不在列表中就返回 400。

**解决方案**：

```python
# prod.py
ALLOWED_HOSTS = [..., "bh6340.duckdns.org"]  # 不带端口
```

### 4.4 图片加载失败（Mixed Content + 缺少端口）

**现象**：HTTPS 页面上的图片加载失败，DevTools 显示：

```
Failed to load resource: net::ERR_CONNECTION_REFUSED
图片 URL: https://bh6340.duckdns.org/media/banners/banner1.png  ← 少了 :8443
```

**根因**：两个问题叠加：
1. API 返回的图片 URL 是绝对路径 `http://bh6340.duckdns.org/media/...`（HTTP 协议），
   浏览器在 HTTPS 页面中请求 HTTP 资源 → Mixed Content 拦截
2. 即使改成 `https://`，URL 没带 `:8443` 端口 → 连接 443 端口被拒

**解决方案**：将数据库中的绝对路径改为相对路径 `/media/...`，
浏览器会自动拼接当前页面的域名 + 端口：

```bash
docker compose exec api python3 << 'PYEOF'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cube_api.settings.prod')
import django
django.setup()
from apps.home.models import Banner
for banner in Banner.objects.all():
    old = banner.image_url
    new = old.replace('http://bh6340.duckdns.org', '').replace('https://bh6340.duckdns.org', '')
    banner.image_url = new
    banner.save()
    print(f'{banner.id}: {old} -> {new or "(relative)"}')
PYEOF
```

### 4.5 Cloudflare Tunnel QUIC 超时（备选方案失败记录）

**现象**：cloudflared 容器日志持续报错：

```
ERR Failed to dial a quic connection error="failed to dial to edge with quic: timeout"
ERR Unable to establish connection with Cloudflare edge
SUMMARY: Environment has critical failures
```

**根因**：cloudflared 默认使用 QUIC 协议（UDP 7844 端口）连接 Cloudflare 边缘节点。
国内服务器到 Cloudflare 边缘节点的 UDP 7844 跨境网络不稳定，导致连接超时。

**尝试过的解决方案**：
1. `--protocol http2`（改用 TCP）→ 部分区域 TCP 7844 也不通
2. `TUNNEL_EDGE_IP_VERSION=4`（强制 IPv4）→ 无改善
3. `TUNNEL_HA_CONNECTIONS=8`（增加连接数）→ 偶尔有 1-2 条连上，但不稳定

**最终结论**：Cloudflare Tunnel 在阿里云国内服务器上不可靠，放弃此方案，改用 DuckDNS + Let's Encrypt。

### 4.6 证书过期续期

**现象**：证书有效期 90 天，到期后浏览器显示"不安全"警告。

**检查证书到期时间**：

```bash
sudo certbot certificates
# 或
openssl x509 -enddate -noout -in /etc/letsencrypt/live/bh6340.duckdns.org/fullchain.pem
```

**手动续期**：

```bash
# 重新获取证书（DNS-01 验证）
sudo certbot certonly --manual --preferred-challenges dns -d bh6340.duckdns.org ...

# 拷贝新证书到 Nginx 目录
sudo cp /etc/letsencrypt/live/bh6340.duckdns.org/fullchain.pem ~/ICube/nginx/ssl/
sudo cp /etc/letsencrypt/live/bh6340.duckdns.org/privkey.pem ~/ICube/nginx/ssl/

# 重启 Nginx
cd ~/ICube
docker compose restart nginx
```

### 4.7 DuckDNS 域名被删除（30 天未更新保活）

**现象**：DuckDNS 网页上域名消失，`dig bh6340.duckdns.org` 返回 NXDOMAIN。

**根因**：DuckDNS 规定 30 天不更新的域名会被自动删除。

**解决方案**：配置 crontab 保活（每天更新一次）：

```bash
(crontab -l 2>/dev/null; echo "0 3 * * * ~/duckdns/duck.sh") | crontab -
```

---

## 五、运维与维护

### 5.1 日常检查清单

| 检查项 | 命令 | 预期结果 |
|--------|------|---------|
| HTTPS 访问 | `curl -k https://bh6340.duckdns.org:8443/` | 返回 HTML |
| Nginx 配置 | `docker compose exec nginx nginx -t` | `syntax is ok` |
| 证书有效期 | `sudo certbot certificates` | 剩余 > 30 天 |
| DuckDNS 解析 | `dig bh6340.duckdns.org +short` | 8.136.100.251 |
| DuckDNS 保活 | `crontab -l \| grep duckdns` | 存在定时任务 |
| 容器状态 | `docker compose ps` | 全部 Up |

### 5.2 证书续期流程

```
到期前 30 天
  │
  ├─ 1. 执行 certbot 重新获取证书（DNS-01 验证）
  ├─ 2. 拷贝证书到 nginx/ssl/
  ├─ 3. 重启 Nginx 容器
  └─ 4. 验证 HTTPS 访问正常
```

或配置 `--manual-auth-hook` 实现自动续期。

### 5.3 配置文件索引

| 文件 | 路径 | 用途 | Git 追踪 |
|------|------|------|---------|
| Nginx 站点配置 | `nginx/conf.d/icube.conf` | 8443 HTTPS + 80 HTTP 双 server | 是 |
| Nginx 共享路由 | `nginx/conf.d/icube_routes.inc` | 两个 server 共享的 location 配置 | 是 |
| SSL 证书 | `nginx/ssl/fullchain.pem` | 证书链 | 否（.gitignore） |
| SSL 私钥 | `nginx/ssl/privkey.pem` | 私钥 | 否（.gitignore） |
| DuckDNS 保活脚本 | `~/duckdns/duck.sh` | DDNS 保活 | 否（服务器本地） |
| 一键配置脚本 | `scripts/setup_duckdns_https.sh` | 证书拷贝 + Nginx 配置 + 重建 | 是 |
| Django 生产配置 | `cube_api/cube_api/settings/prod.py` | ALLOWED_HOSTS + CSRF_TRUSTED_ORIGINS | 是 |
| Docker Compose | `docker-compose.yml` | nginx 端口映射 + 证书目录挂载 | 是 |
