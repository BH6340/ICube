# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# ICube — 魔方学习平台

基于 Django + Vue 3 的魔方学习交流平台，提供公式库、3D 可视化、论坛、商城等功能。使用 Docker Compose 进行容器化部署。

> 子目录 `cube_api/` 和 `cube_front/` 各有独立的 CLAUDE.md，包含各自领域的详细约定。

## 技术栈
- 后端：Django 6.0 + DRF + MySQL 8.0 + Redis 7
- 前端：Vue 3.5 + Vite 8.0 + Element Plus 2.14 + Three.js 0.184
- 部署：Docker Compose + Nginx
- Python 解释器（本地开发）：固定使用 `E:\software\python\python313\env\cube_api\Scripts\python.exe`，禁止使用其他解释器

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

# 运行全部测试（自动切换到 SQLite 内存库 + Mock Redis + 禁用限流 + MD5 哈希）
sudo docker compose exec api python manage.py test

# 运行单个测试模块
sudo docker compose exec api python manage.py test apps.forum.tests.test_models

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
│   ├── CLAUDE.md                # 后端专属约定
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
│       └── utils/               # 统一响应 (APIResponse)、异常处理、分页
├── cube_front/                  # Vue 3 前端
│   ├── CLAUDE.md                # 前端专属约定
│   ├── vite.config.js           # Vite 配置 + /api 代理
│   └── src/
│       ├── api/                 # 按模块封装的接口（user.js, posts.js, shop.js 等）
│       ├── http/request.js      # Axios 实例 + 统一拦截器
│       ├── stores/              # Pinia 状态管理
│       └── components/formula/CubeDemo.vue  # Three.js 3D 魔方组件
├── nginx/conf.d/icube.conf      # Nginx 路由配置
├── init_data.sql                # 数据库初始化种子数据（MySQL 容器启动时自动执行）
└── docker-compose.yml
```

## 请求流转路径

理解请求在各服务间的走向，是排查问题的关键：

```
浏览器
  │
  ├─ /api/*   → Nginx → proxy_pass → icube_api:8000（Django/DRF）
  ├─ /media/* → Nginx → alias → media_volume（Docker 共享卷）
  ├─ /static/*→ Nginx → alias → collected_static（Docker 共享卷）
  └─ /*       → Nginx → try_files → front_dist（Vue 构建产物，SPA 回退到 index.html）
```

本地开发时，Vite dev server 接管前端，`/api` 请求通过 `vite.config.js` 中的 proxy 转发到 `127.0.0.1:8000`。

## 关键架构约定

### 后端
- **sys.path 注入**：`dev.py` 将 `apps/` 和父目录插入 `sys.path`，应用导入为 `apps.accounts` 而非 `cube_api.apps.accounts`
- **API 响应格式**：所有视图必须使用 `utils/common_response.py` 中的 `APIResponse`，成功时 `code=100`。前端拦截器将 `code !== 100` 视为错误
- **日志**：严格禁止 `logging` 模块，只能使用 `from loguru import logger`。`logger_conf.py` 通过 `InterceptHandler` 拦截所有第三方库日志，`dev.py` 中 `LOGGING_CONFIG = None` 彻底禁用 Django 默认日志系统
- **设置继承**：`prod.py` 从 `dev.py` 导入全部内容（`from .dev import *`），然后覆盖 DB/Redis/CORS/DEBUG 等生产配置
- **认证**：`CachedJWTAuthentication` 通过 Redis 缓存用户实例（key: `user_instance_cache_{user_id}`，TTL 1h），支持 JWT 黑名单（注销时 jti 入黑名单）。Token 前缀为 `Token`，非标准 `Bearer`
- **测试模式**：通过 `if 'test' in sys.argv` 检测，自动切换到 SQLite 内存库、Mock Redis、禁用限流、MD5 哈希

### 前端
- **自动导入**：`unplugin-auto-import` 自动导入 Vue/Vue Router/Pinia API，`unplugin-vue-components` 自动导入 Element Plus 组件，无需手动 import
- **路由结构**：`HomeView` 是父布局路由，其余页面均为其子路由
- **Three.js 清理**：`CubeDemo.vue` 必须在 `onBeforeUnmount` 中执行 `geometry.dispose()`、`material.dispose()`、`renderer.dispose()` 并取消 `requestAnimationFrame`，否则内存泄漏

### Nginx 路由规则（icube.conf）
| 路径 | 处理方式 |
|------|---------|
| `/api/*` | `proxy_pass` 到 `icube_api:8000`，保留 `/api/` 前缀 |
| `/media/*` | `alias` 到共享卷，30天缓存 |
| `/static/*` | `alias` 到共享卷，30天缓存 |
| `/*` | SPA 回退：`try_files $uri $uri/ /index.html` |

### 服务依赖关系
- nginx 依赖 api 和 front
- api 依赖 db（需健康检查通过，`start_period: 45s`）和 redis
- front 独立构建，产物通过 `front_dist` 卷共享给 nginx

## 业务领域约定
- 公式列表排序字段：`view_count`（不是 `views`）
- 公式缩略图路径匹配：`/media/formulas/`（不是 `/media/formula_thumbnails/`）
- 公式图片两字段区分：`thumbnail_file`（用户上传）与 `thumbnail_path`（公式库图片引用）
- 新增/修改公式：按 `category_id` 自动绑定 `target_state_id`，改分类时同步更新
- 公式卡片显示：头部=公式名+难度标签，底部=分类名  by  用户名（中间两个空格）
- 帖子图片关联：全量同步模式——从 Markdown 解析所有 `![alt](url)`，删除多余、补齐缺失
- 帖子列表布局：flex 左右结构，左侧内容自适应，右侧图片固定 140px，垂直居中；图片 1:1、`object-fit: contain`，不裁剪
- 轮播图推荐规格：16:9，1280×720~1920×1080，100-300KB，PNG
- 教程导航：`/tutorials` → `/tutorial/beginner`、`/tutorial/cfop` 及子页面
- 媒体文件夹 `/media` 必须纳入 Git 版本控制并上传服务器

## 易踩坑位（历史教训）
- 未处理的 `AuthenticationFailed` 会让无 Token 的只读请求返回 401
- 直接对 `ImageFieldFile` 调字符串方法 → `AttributeError`
- DB 图片路径前缀不一致（有无 `/media/`）→ 部分图片无法访问
- 未导入 `F` 表达式直接使用 → `NameError: name 'models' is not defined`
- 浏览器 Private Network Access 会阻止公网域名直接访问 localhost 图片资源
- `build_image_url` 中 `hasattr(relative_path, 'path')` 会在头像路径以 `/` 开头时触发 `SuspiciousFileOperation`
- Django `ImageField` 无法直接用字符串路径赋值更新，需走 `.name` 或 `.save()`
- JWT Token 有效但用户不存在时，`authenticate` 返回 `(None, validated_token)` 会导致 DRF 状态不一致，应返回 `None`

## 注意事项
- 前端代码中禁止硬编码 `localhost:8000`，API 请求通过 `/api` 代理，媒体文件通过 `/media/` 访问
- 修改 `cube_api/mysql.conf` 可能影响数据库初始化，需谨慎
- `docker-compose.yml` 中的 `version` 字段已过时，可移除避免告警
- 生产环境需通过环境变量配置：`ALLOWED_HOSTS`（服务器公网 IP/域名）、`ALLOWED_ORIGIN`（前端 CORS 来源）、`SERVER_HOST`（支付宝回调地址），均在 `docker-compose.yml` 中通过 `${VAR:-}` 语法支持 `.env` 文件或系统环境变量传入
- `init_data.sql` 在 MySQL 容器首次启动时自动执行，修改会影响初始数据

<!-- superpowers-zh:begin (do not edit between these markers) -->
# Superpowers-ZH 中文增强版

本项目已安装 superpowers-zh 技能框架（20 个 skills）。

## 核心规则

1. **收到任务时，先检查是否有匹配的 skill** — 哪怕只有 1% 的可能性也要检查
2. **设计先于编码** — 收到功能需求时，先用 brainstorming skill 做需求分析
3. **测试先于实现** — 写代码前先写测试（TDD）
4. **验证先于完成** — 声称完成前必须运行验证命令

## 可用 Skills

Skills 位于 `.claude/skills/` 目录，每个 skill 有独立的 `SKILL.md` 文件。

- **brainstorming**: 在任何创造性工作之前必须使用此技能——创建功能、构建组件、添加功能或修改行为。在实现之前先探索用户意图、需求和设计。
- **chinese-code-review**: 中文 review 沟通参考——话术模板、分级标注（必须修复/建议修改/仅供参考）、国内团队常见反模式应对。仅在用户显式 /chinese-code-review 时调用，不要根据上下文自动触发。
- **chinese-commit-conventions**: 中文 commit 与 changelog 配置参考——Conventional Commits 中文适配、commitlint/husky/commitizen 中文模板、conventional-changelog 中文配置。仅在用户显式 /chinese-commit-conventions 时调用，不要根据上下文自动触发。
- **chinese-documentation**: 中文文档排版参考——中英文空格、全半角标点、术语保留、链接格式、中文文案排版指北约定。仅在用户显式 /chinese-documentation 时调用，不要根据上下文自动触发。
- **chinese-git-workflow**: 国内 Git 平台配置参考——Gitee、Coding.net、极狐 GitLab、CNB 的 SSH/HTTPS/凭据/CI 接入差异与镜像同步配置。仅在用户显式 /chinese-git-workflow 时调用，不要根据上下文自动触发。
- **dispatching-parallel-agents**: 当面对 2 个以上可以独立进行、无共享状态或顺序依赖的任务时使用
- **executing-plans**: 当你有一份书面实现计划需要在单独的会话中执行，并设有审查检查点时使用
- **finishing-a-development-branch**: 当实现完成、所有测试通过、需要决定如何集成工作时使用——通过提供合并、PR 或清理等结构化选项来引导开发工作的收尾
- **mcp-builder**: MCP 服务器构建方法论 — 系统化构建生产级 MCP 工具，让 AI 助手连接外部能力
- **receiving-code-review**: 收到代码审查反馈后、实施建议之前使用，尤其当反馈不明确或技术上有疑问时——需要技术严谨性和验证，而非敷衍附和或盲目执行
- **requesting-code-review**: 完成任务、实现重要功能或合并前使用，用于验证工作成果是否符合要求
- **subagent-driven-development**: 当在当前会话中执行包含独立任务的实现计划时使用
- **systematic-debugging**: 遇到任何 bug、测试失败或异常行为时使用，在提出修复方案之前执行
- **test-driven-development**: 在实现任何功能或修复 bug 时使用，在编写实现代码之前
- **using-git-worktrees**: 当需要开始与当前工作区隔离的功能开发，或在执行实现计划之前使用——通过原生工具或 git worktree 回退机制确保隔离工作区存在
- **using-superpowers**: 在开始任何对话时使用——确立如何查找和使用技能，要求在任何响应（包括澄清性问题）之前调用 Skill 工具
- **verification-before-completion**: 在宣称工作完成、已修复或测试通过之前使用，在提交或创建 PR 之前——必须运行验证命令并确认输出后才能声称成功；始终用证据支撑断言
- **workflow-runner**: 在 Claude Code / OpenClaw / Cursor 中直接运行 agency-orchestrator YAML 工作流——无需 API key，使用当前会话的 LLM 作为执行引擎。当用户提供 .yaml 工作流文件或要求多角色协作完成任务时触发。
- **writing-plans**: 当你有规格说明或需求用于多步骤任务时使用，在动手写代码之前
- **writing-skills**: 当创建新技能、编辑现有技能或在部署前验证技能是否有效时使用

## 如何使用

当任务匹配某个 skill 时，使用 `Skill` 工具加载对应 skill 并严格遵循其流程。绝不要用 Read 工具读取 SKILL.md 文件。

如果你认为哪怕只有 1% 的可能性某个 skill 适用于你正在做的事情，你必须调用该 skill 检查。
<!-- superpowers-zh:end -->
