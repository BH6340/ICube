被搁置的蓝绿部署计划（个人开发，没必要整太复杂）：


针对你的要求（不使用 `green` 后缀，统一使用 **`dev` 后缀**，即在单台服务器上同时运行 `main` 分支的**生产（Prod）环境**和 `dev` 分支的**测试/开发（Dev）环境**），为你量身定制的轻量级蓝绿/多环境并行部署计划如下：

---

### 一、 核心环境命名与端口隔离规划

为了让生产和测试在同一台服务器上井水不犯河水，我们采用“目录隔离 + 容器命名隔离 + 端口错位”的方案：

| 维度                   | 生产环境 (Prod)      | 测试环境 (Dev)                           |
| ---------------------- | -------------------- | ---------------------------------------- |
| **Git 分支**           | `main`               | `dev`                                    |
| **服务器目录**         | `/home/bh/ICube`     | `/home/bh/icube_dev`                     |
| **Docker 配置文件**    | `docker-compose.yml` | `docker-compose.dev.yml`                 |
| **后端 API 容器名**    | `cube_api_prod`      | `cube_api_dev`                           |
| **后端宿主机映射端口** | `8000`               | `8001`                                   |
| **MySQL 数据库名**     | `icube` (主库)       | `icube_dev` (测试库)                     |
| **Redis 数据库索引**   | `DB 0`               | `DB 1`                                   |
| **外部访问入口**       | 域名 / 80 端口       | `dev.你的域名` 或 `IP:8080` (Nginx 分发) |

---

### 二、 实施计划步骤

#### 第一阶段：目录与配置文件准备

1. **代码多路复用**：
在服务器上创建两个独立的目录：
* 生产目录：`/opt/icube_prod`（拉取 `main` 分支）
* 测试目录：`/opt/icube_dev`（拉取 `dev` 分支）


2. **复制并修改测试环境的 Compose 配置**：
在 `/opt/icube_dev` 下，将原有的 `docker-compose.yml` 复制一份并重命名为 `docker-compose.dev.yml`。
* 修改内部所有容器的名字，加上 `_dev` 后缀（如 `cube_api` 改为 `cube_api_dev`）。
* 修改端口映射，将后端映射到宿主机的 `8001` 端口。
* 修改环境变量（`.env` 文件），将数据库名指向 `icube_dev`，Redis DB 指向 `1`。



#### 第二阶段：编写自动化发布与切换脚本 (`deploy-dev.sh`)

在 `/opt/icube_dev` 目录下编写一个专属的测试环境一键更新脚本，实现“每次提交代码自动/手动一键刷新 Dev 环境”：

```bash
#!/bin/bash
set -e

echo "=== 1. 开始更新测试环境 (Dev) ==="
cd /opt/icube_dev

echo "=== 2. 拉取 dev 分支最新代码 ==="
git pull origin dev

echo "=== 3. 重新构建并启动 Dev 容器 ==="
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml build --pull
docker compose -f docker-compose.dev.yml up -d

echo "=== 4. 执行测试数据库迁移 ==="
docker compose -f docker-compose.dev.yml exec -T api-dev python manage.py migrate --noinput

echo "=== 5. Dev 环境部署完成！访问端口: 8001 ==="

```

#### 第三阶段：配置 Nginx 统一网关分流

通过服务器上的 Nginx，将不同域名的流量安全地引导到对应的容器实例上，实现前端无感切换：

1. **生产环境配置 (`/etc/nginx/conf.d/icube.conf`)**：
```nginx
server {
    listen 80;
    server_name yourdomain.com; # 你的生产域名

    location /api/ {
        proxy_pass http://127.0.0.1:8000; # 指向生产后端
        include proxy_params;
    }
    # 其他静态资源或前端路由...
}

```


2. **测试环境配置 (`/etc/nginx/conf.d/icube-dev.conf`)**：
```nginx
server {
    listen 80;
    server_name dev.yourdomain.com; # 你的测试子域名（或通过端口 8080 访问）

    location /api/ {
        proxy_pass http://127.0.0.1:8001; # 指向测试后端 (dev)
        include proxy_params;
    }
    # 其他静态资源或前端路由...
}

```


修改完后执行 `nginx -s reload` 使配置生效。

#### 第四阶段：日常开发与演练闭环

* **日常开发流**：
1. 在本地电脑写完新功能，推送到远程仓库的 `dev` 分支。
2. 登录服务器，进入 `/opt/icube_dev` 执行 `bash deploy-dev.sh`。
3. 访问 `dev.yourdomain.com`，立刻就能在线上真实环境中体验和测试刚写好的新功能。


* **线上发布流**：
1. 测试没问题后，将 `dev` 分支合并到 `main` 分支。
2. 进入 `/opt/icube_prod` 目录，执行你原有的生产部署脚本 `bash deploy.sh full`。


3. 生产环境平滑升级，测试环境继续保留供下一次迭代使用。