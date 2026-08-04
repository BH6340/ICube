# CLAUDE.md - 后端  — Django + DRF

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

基于 Django REST Framework 的 API 服务，使用 JWT 认证和 Redis 缓存。

## 常用命令
```bash
# 在 Docker 中执行（推荐）
sudo docker compose exec api python manage.py migrate
sudo docker compose exec api python manage.py createsuperuser
sudo docker compose exec api python manage.py shell
sudo docker compose exec api python manage.py collectstatic

# 运行测试（自动切换到 SQLite 内存数据库 + 模拟 Redis + 禁用限流）
sudo docker compose exec api python manage.py test
sudo docker compose exec api python manage.py test apps.forum.tests.test_models  # 单个测试模块

# 本地开发
python manage.py runserver 8000 --settings=cube_api.settings.dev
```

## 项目结构（实际路径）
注意：由于 `sys.path` 注入，实际路径为 `cube_api/cube_api/apps/`，而非 `cube_api/apps/`。

- cube_api/cube_api/apps/accounts/ — 用户认证、关注、JWT 黑名单、CachedJWTAuthentication
- cube_api/cube_api/apps/forum/ — 帖子、评论、点赞、收藏、举报
- cube_api/cube_api/apps/formula/ — 公式分类、公式管理、收藏、3D 状态数据
- cube_api/cube_api/apps/shop/ — 商品、购物车、订单、支付宝支付
- cube_api/cube_api/apps/home/ — 首页菜单、轮播图
- cube_api/cube_api/utils/ — 统一响应格式 (common_response.py)、异常处理 (common_exception.py)、分页 (common_pagination.py)
- cube_api/cube_api/settings/ — dev.py（开发，被 prod.py 继承）、prod.py（生产覆盖）、logger_conf.py（Loguru 配置）

## 编码规范
- 视图：优先使用 DRF ModelViewSet，复杂逻辑拆分到 services.py
- 序列化器：定义在 serializers.py，使用 extend_schema_field 标注自定义字段类型
- 权限：自定义权限类放在 permissions.py（如 IsOwnerOrReadOnly）
- 缓存：Redis 操作统一封装在 services.py 中（如 ProfileCacheService、PostCacheService）
- API 响应：必须使用 utils/common_response.py 中的 APIResponse 统一格式
- 数据库查询：禁止在视图中直接编写复杂查询，应通过 Service 层封装
- 图片路径：存储相对路径，禁止硬编码 `http://localhost:8000`；URL 生成统一走 `utils/image_url.py` 的 `build_image_url` 添加 `/media/` 前缀
- ImageFieldFile 处理：先判断并转字符串再调用字符串方法；用 `isinstance` 检查 `FieldFile`，禁止用 `hasattr(.., 'path')`（会触发 `SuspiciousFileOperation`）

## 关键架构约定

### sys.path 注入
`dev.py` 将 `apps/` 目录和父目录插入 `sys.path`，使得应用可以导入为 `apps.accounts` 而非 `cube_api.apps.accounts`。这是 `INSTALLED_APPS` 中写 `'apps.accounts'` 能正常工作的原因。

### 设置模块继承
`prod.py` 通过 `from .dev import *` 继承所有开发设置，然后覆盖：
- `DEBUG = False`
- `DATABASES`（host 指向 `db` 即 Docker 服务名）
- `CACHES`（Redis 指向 `redis` 即 Docker 服务名）
- `ALLOWED_HOSTS` / `CORS_ALLOWED_ORIGINS`
- `STATIC_ROOT`

### 测试模式
通过 `if 'test' in sys.argv` 检测，自动切换：
- 数据库：SQLite 内存数据库（`:memory:`）
- Redis：使用 django_redis 模拟（`get_redis_connection` 被 mock 掉）
- 限流：完全禁用
- 密码哈希：使用 MD5（加速测试）

### Loguru 日志（严格强制）
- **禁止使用** Python 内置 `logging` 模块
- 只能使用 `from loguru import logger`
- `logger_conf.py` 通过 `InterceptHandler` 将 Django/gunicorn 等第三方库的 `logging` 调用全部转发到 Loguru
- 日志文件：`log/cube-{level}.log`（DEBUG/INFO/WARNING/ERROR/CRITICAL 分级）
- 设置中 `LOGGING_CONFIG = None` 禁用 Django 默认日志系统

### 支付宝沙箱集成
- 配置文件：`apps/shop/alipay_config.py`
- 密钥：`apps/shop/keys/`（禁止提交到版本控制）
- 沙箱网关：`openapi-sandbox.dl.alipaydev.com`
- 异步通知：`notify_url` 必须可被支付宝公网访问（本地开发需内网穿透）
- 金额精度：使用 `Decimal` 类型，传给支付宝的 `total_amount` 为精确到两位的字符串

### JWT 认证
- 使用 `CachedJWTAuthentication`（继承自 `simplejwt.JWTAuthentication`）
- 用户实例缓存在 Redis 中（key: `user_instance_cache_{user_id}`，TTL: 1 小时）
- JWT 黑名单：注销时将 `jti` 加入 Redis 黑名单（通过 `JWTCacheService.is_blacklisted()` 检查）
- Token 前缀：`Token`（而非默认的 `Bearer`），通过 `AUTH_HEADER_TYPES: ('Token',)` 配置
- `authenticate` 方法：Token 无效或用户不存在时返回 `None`，不抛 `AuthenticationFailed`，以兼容 `IsAuthenticatedOrReadOnly`

## 易踩坑位（历史教训）
- 未处理的 `AuthenticationFailed` 会让无 Token 的只读请求返回 401
- 直接对 `ImageFieldFile` 调字符串方法 → `AttributeError`
- DB 图片路径前缀不一致（有无 `/media/`）→ 部分图片无法访问
- 未导入 `F` 表达式直接使用 → `NameError: name 'models' is not defined`
- `build_image_url` 中 `hasattr(relative_path, 'path')` 会在头像路径以 `/` 开头时触发 `SuspiciousFileOperation`
- Django `ImageField` 无法直接用字符串路径赋值更新，需走 `.name` 或 `.save()`
- JWT Token 有效但用户不存在时，`authenticate` 返回 `(None, validated_token)` 会导致 DRF 状态不一致，应返回 `None`

## 注意事项
- 生产环境使用 settings.prod，确保 DEBUG=False
- 媒体文件路径存储必须使用相对路径（如 /media/avatars/xxx.png），禁止硬编码 http://localhost:8000
- 修改用户状态后需清理对应的 JWT 缓存
- 公式库的 3D 状态数据为 JSON 格式，修改 pre_state_definition 或 target_state_id 时需确保与前端 Three.js 渲染逻辑兼容
- 支付宝密钥文件（keys/）禁止提交到版本控制