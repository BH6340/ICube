# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# ICube — 魔方学习平台

基于 Django + Vue 3 的魔方学习交流平台，提供公式库、3D可视化、论坛、商城等功能。使用 Docker Compose 进行容器化部署。

## 技术栈
- 后端：Django 6.0 + DRF + MySQL 8.0 + Redis 6.x
- 前端：Vue 3.5 + Vite 8.0 + Element Plus 2.14 + Three.js 0.184
- 部署：Docker Compose + Nginx

## 常用命令
```bash
# 构建并启动所有服务
sudo docker compose up -d --build

# 仅重启后端（代码修改后，因为有 volume 挂载）
sudo docker compose restart api

# 查看日志
sudo docker compose logs -f api

# 停止所有服务
sudo docker compose down

# 数据库迁移
sudo docker compose exec api python manage.py migrate

# 创建超级用户
sudo docker compose exec api python manage.py createsuperuser

# 运行测试（测试模式自动使用 SQLite + 模拟 Redis）
sudo docker compose exec api python manage.py test

# 本地开发：后端
cd cube_api && python manage.py runserver 8000 --settings=cube_api.settings.dev
# 本地开发：前端（自动代理 /api → 127.0.0.1:8000）
cd cube_front && npm run dev
```

## 项目结构
```
ICube/
├── cube_api/                    # Django 后端（Docker 构建上下文）
│   ├── Dockerfile
│   ├── manage.py
│   ├── requirements.txt
│   └── cube_api/                # Django 项目根目录
│       ├── settings/
│       │   ├── dev.py           # 开发配置（prod.py 通过 from .dev import * 继承）
│       │   ├── prod.py          # 生产配置（覆盖 DB/Redis/CORS/DEBUG）
│       │   └── logger_conf.py   # Loguru 日志配置
│       ├── apps/                # Django 应用（通过 sys.path 注入，导入为 apps.xxx）
│       │   ├── accounts/        # 用户认证、JWT 黑名单、关注系统
│       │   ├── forum/           # 帖子、评论、点赞、收藏、举报
│       │   ├── formula/         # 公式分类、公式管理、3D 状态数据
│       │   ├── shop/            # 商品、购物车、订单、支付宝支付
│       │   └── home/            # 首页菜单、轮播图
│       └── utils/               # 统一响应、异常处理、分页
├── cube_front/                  # Vue 3 前端
├── nginx/conf.d/                # Nginx 站点配置
└── docker-compose.yml
```

## 关键架构约定

### 后端
- **sys.path 注入**：`dev.py` 将 `apps/` 和父目录插入 `sys.path`，所以应用导入为 `apps.accounts` 而不是 `cube_api.apps.accounts`
- **API 响应**：所有视图必须使用 `utils/common_response.py` 中的 `APIResponse`，成功时 `code=100`。前端拦截器期望 `code !== 100` 表示错误
- **日志**：严格禁止使用 `logging` 模块。只能使用 `from loguru import logger`。`logger_conf.py` 通过 `InterceptHandler` 拦截所有第三方库日志
- **设置继承**：`prod.py` 从 `dev.py` 导入所有内容（`from .dev import *`），然后覆盖数据库/Redis/缓存/CORS 设置
- **认证**：`CachedJWTAuthentication` 通过 Redis 缓存用户实例，并支持 JWT 黑名单（注销时使用）
- **测试模式**：通过 `if 'test' in sys.argv` 检测。切换到 SQLite 内存数据库、模拟 Redis、禁用限流、使用 MD5 密码哈希
- **支付宝沙箱**：密钥存储在 `apps/shop/keys/`（不能提交）。`alipay_config.py` 配置沙箱网关

### 前端
- **自动导入**：`unplugin-auto-import` 自动导入 Vue、Vue Router、Pinia。`unplugin-vue-components` 自动导入 Element Plus 组件。无需手动导入
- **Vite 代理**：开发模式下 `/api` 请求代理到 `http://127.0.0.1:8000`
- **Three.js 清理**：`CubeDemo.vue` 必须在 `onBeforeUnmount` 中执行 `geometry.dispose()`、`material.dispose()`、`renderer.dispose()` 并取消 `requestAnimationFrame`

### 服务依赖关系
- nginx 依赖 api 和 front
- api 依赖 db（需健康检查通过）和 redis
- front 独立构建，产物由 nginx 提供静态服务

## 注意事项
- 前端代码中禁止硬编码 localhost:8000，API 请求通过 /api 代理，媒体文件通过 /media/ 访问
- 修改 cube_api/mysql.conf 可能影响数据库初始化，需谨慎
- docker-compose.yml 中的 version 字段已过时，可移除避免告警