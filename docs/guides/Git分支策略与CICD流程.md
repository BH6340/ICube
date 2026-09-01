# Git 分支策略与 CI/CD 流程

## 目录

- [分支模型](#分支模型)
- [日常开发流程](#日常开发流程)
- [紧急修复流程](#紧急修复流程)
- [GitHub 仓库配置](#github-仓库配置)
- [CI/CD 总览](#cicd-总览)
- [CI 触发规则与 Path Filter](#ci-触发规则与-path-filter)
- [CI Jobs 详解](#ci-jobs-详解)
- [CD 自动部署详解](#cd-自动部署详解)
- [部署日志持久化](#部署日志持久化)
- [自动 CHANGELOG](#自动-changelog)
- [部署通知](#部署通知)
- [本地测试环境](#本地测试环境)
- [首次配置步骤](#首次配置步骤)
- [注意事项](#注意事项)

---

## 分支模型

```
feature/xxx（可选）     dev               main
    │                   │                  │
    └── 合并到 dev ────→│                  │
                        │                  │
                        └── PR 到 main ───→│ → 自动部署 → sync-dev → changelog
                                           │
                        hotfix/xxx ───────→│ → 自动部署
                              │             │
                              └── 反合并 → dev
```

| 分支 | 用途 | 保护 | CI | 部署 |
|------|------|------|-----|------|
| `main` | 生产环境代码 | 禁止直接 push，只接受 PR | ✅ | ✅ |
| `dev` | 日常开发 | 不保护 | ✅ | - |
| `feature/*` | 临时功能分支（可选） | 不保护 | - | - |
| `hotfix/*` | 紧急修复（可选） | 不保护 | - | - |

---

## 日常开发流程

### 1. 切换到 dev 分支开发

```bash
git checkout dev
git pull origin dev

# 写代码...
git add .
git commit -m "feat: xxx"
git push origin dev
```

push 到 dev 后，CI 自动触发检查（后端测试 + 前端构建 + Docker 构建），**不会部署**。

### 2. 发起 PR 合并到 main

1. 打开 `https://github.com/BH6340/ICube`
2. 点击 **"Compare & pull request"**（GitHub 会自动提示 dev 有新提交）
3. 确认 PR 方向：`base: main` ← `compare: dev`
4. 点击 **"Create pull request"**
5. CI 自动跑检查
6. CI 全绿后，点击 **"Merge pull request"** → **"Confirm merge"**
7. main 收到合并 → 自动触发部署

### 3. 合并后自动同步

合并到 main 后，CI 自动执行两个后续 Job：

1. **sync-dev**：将 dev 分支强制同步到 main 的最新 commit（`git reset --hard origin/main` + `git push --force`），确保下次 dev 上的 PR 只包含新提交
2. **changelog**：从 git log 自动生成 `CHANGELOG.md`，提交到 dev 分支（随下次 PR 进入 main）

本地只需：

```bash
git checkout dev
git pull origin dev
```

---

## 紧急修复流程

生产环境出 bug 需要紧急修复时，从 main 拉临时分支：

```bash
# 1. 从 main 创建 hotfix 分支
git checkout main
git pull origin main
git checkout -b hotfix/fix-xxx

# 2. 修复 bug
git add .
git commit -m "fix: 紧急修复 xxx"
git push origin hotfix/fix-xxx

# 3. 发 PR: hotfix/fix-xxx → main，CI 通过后合并 → 自动部署

# 4. 部署完成后，把修复同步回 dev（sync-dev 会自动处理，手动也可）
git checkout dev
git merge origin/main
git push origin dev

# 5. 删除 hotfix 分支
git branch -d hotfix/fix-xxx
git push origin --delete hotfix/fix-xxx
```

---

## GitHub 仓库配置

### 分支保护规则

进入 `Settings` → `Branches` → `Add branch protection rule`：

| 配置项 | 值 | 说明 |
|--------|-----|------|
| Branch name pattern | `main` | 保护 main 分支 |
| Require a pull request before merging | ✅ | 禁止直接 push |
| Require approvals | ❌ | 个人开发不需要审批 |
| Dismiss stale pull request approvals when new commits are pushed | ❌ | 无审批需求 |
| Require review from Code Owners | ❌ | 无 Code Owner |
| Require approval of the most recent reviewable push | ❌ | 个人开发 |
| Require status checks to pass before merging | ✅ | CI 必须通过才能合并 |
| Require branches to be up to date before merging | ❌ | 个人开发不需要 |
| Do not allow bypassing the above settings | ✅ | 防止管理员绕过 |

> **注意**：分支保护是 GitHub Free 公开仓库的功能。私有仓库需升级到 Pro。

### 合并策略

进入 `Settings` → `General` → `Pull Requests`：

- ✅ **Allow squash merging**（推荐）
- ❌ Allow merge commits
- ❌ Allow rebase merging

Squash merge 把 PR 的所有 commit 压成一个，main 历史干净整洁。

### GitHub Secrets

在 `Settings` → `Secrets and variables` → `Actions` 中配置：

| Secret | 用途 |
|--------|------|
| `SERVER_HOST` | 服务器 IP 地址 |
| `SERVER_USER` | SSH 登录用户名 |
| `SSH_PRIVATE_KEY` | SSH 私钥 |
| `DEPLOY_PATH` | 服务器项目路径 |
| `SERVERCHAN_KEY` | Server酱微信通知密钥 |

---

## CI/CD 总览

```
push 到 dev / PR 到 main
  │
  ├─ backend-check（pytest + 覆盖率）
  ├─ frontend-check（npm build）
  └─ docker-build（Dockerfile 构建）
         │
         │  仅 push 到 main 时继续
         ▼
       deploy
         │
         ├─ SSH 部署脚本
         ├─ 数据库迁移检查 + 备份
         ├─ 健康检查 + 自动回滚
         ├─ 部署日志 artifact
         ├─ 微信通知（成功/失败）
         │
         ▼
       sync-dev（dev 同步到 main）
         │
         ▼
       changelog（生成 CHANGELOG.md → 推到 dev）
```

### CI/CD 产物

| 产物 | 保留时长 | 用途 |
|------|---------|------|
| `coverage-report` artifact | 30 天 | XML 覆盖率报告，可上传 Codecov |
| `deploy-log-{run_id}` artifact | 90 天 | 部署完整 stdout，排查部署失败 |

---

## CI 触发规则与 Path Filter

### 顶层路径过滤

CI 仅在以下路径有变更时触发：

```
cube_api/**    后端代码
cube_front/**  前端代码
docker-compose.yml
**/Dockerfile
scripts/**     部署脚本
.github/workflows/cicd.yml
```

纯文档变更（`docs/**`、`*.md`）不触发任何 CI Job。

### 触发矩阵

| 事件 | 后端检查 | 前端构建 | Docker 构建 | 部署 |
|------|:-------:|:-------:|:----------:|:----:|
| push 到 `dev` | ✅ | ✅ | ✅ | - |
| PR: `dev` → `main` | ✅ | ✅ | ✅ | - |
| push 到 `main`（合并） | ✅ | ✅ | ✅ | ✅ |
| PR: `hotfix/*` → `main` | ✅ | ✅ | ✅ | - |
| push 到 `main`（hotfix 合并） | ✅ | ✅ | ✅ | ✅ |
| 纯文档变更 | - | - | - | - |

### Job 内部 Path Filter

每个 Job 内部用 `dorny/paths-filter@v3` 二次判断，仅相关文件变更时才实际执行：

| 文件变更 | 后端检查 | 前端构建 | Docker 构建 |
|---------|:-------:|:-------:|:----------:|
| `cube_api/**` | ✅ 执行 | ⏭ 跳过 | ⏭ 跳过 |
| `cube_front/**` | ⏭ 跳过 | ✅ 执行 | ⏭ 跳过 |
| `Dockerfile` / `docker-compose.yml` | ⏭ 跳过 | ⏭ 跳过 | ✅ 执行 |
| `docs/**` / `*.md` | 不触发 CI | 不触发 CI | 不触发 CI |

---

## CI Jobs 详解

### 1. backend-check（后端 Lint + Test）

| 步骤 | 命令 | 说明 |
|------|------|------|
| 路径检测 | `dorny/paths-filter@v3` | 仅 `cube_api/**` 变更时执行 |
| 系统依赖 | `apt-get install default-libmysqlclient-dev` | mysqlclient 编译需要 |
| Python 依赖 | `pip install -r requirements.txt` + `ruff` | 含 pytest/pytest-django/pytest-cov |
| Ruff 检查 | `ruff check cube_api/cube_api/` | `continue-on-error: true`，不阻塞 |
| 全量测试 | `pytest --cov=cube_api/apps --cov=cube_api/utils --cov-report=xml --cov-report=term-missing` | pytest 替代 manage.py test |
| 覆盖率上传 | `actions/upload-artifact@v4` | `coverage-report`，保留 30 天 |

### 2. frontend-check（前端 Build 验证）

| 步骤 | 命令 | 说明 |
|------|------|------|
| 路径检测 | `dorny/paths-filter@v3` | 仅 `cube_front/**` 变更时执行 |
| Node 依赖 | `npm ci` | 基于 package-lock.json |
| 构建验证 | `npm run build` | Vite 生产构建 |

### 3. docker-build（Docker 镜像构建验证）

| 步骤 | 命令 | 说明 |
|------|------|------|
| 路径检测 | `dorny/paths-filter@v3` | 仅 Dockerfile/compose 变更时执行 |
| 后端镜像 | `docker build -t icube-api-ci ./cube_api` | 验证 Dockerfile 可构建 |
| 前端镜像 | `docker build -t icube-front-ci ./cube_front` | 验证 Dockerfile 可构建 |
| compose 校验 | `docker compose config -q` | 验证 compose 配置语法 |

---

## CD 自动部署详解

### 触发条件

```
github.event_name == 'push' && github.ref == 'refs/heads/main'
&& CI Jobs 全部通过（或被跳过）
```

### 部署流程（5 步）

```
[0/5] 强制同步远程代码
  ├── git fetch origin main
  ├── 记录 PREV_COMMIT（用于回滚）
  ├── 检测本地改动 → 备份为 /tmp/local_changes_*.patch
  └── git reset --hard origin/main

[1/5] 执行部署脚本
  └── deploy_update.sh --non-interactive --skip-migrate --skip-healthcheck

[2/5] 数据库迁移前置检查
  ├── migrate --check 检测是否有待应用迁移
  ├── 有迁移 → mysqldump 备份数据库 → migrate --noinput
  │   ├── 迁移成功 → 清理备份文件
  │   └── 迁移失败 → 恢复数据库 + 代码回滚 → exit 1
  └── 无迁移 → 跳过

[3/5] 健康检查（5 次重试，每次间隔 3s）
  ├── curl http://localhost/          → 前端 200
  ├── curl http://localhost/api/home/banners/ → API 200
  ├── 通过 → 继续
  └── 失败 → 代码回滚到 PREV_COMMIT → 回滚后健康检查 → exit 1

[4/5] 每日全量备份（异步）
  └── nohup backup.sh > /tmp/backup_deploy.log 2>&1 &

[5/5] 部署成功
  └── 输出当前 commit 和时间
```

### 自动回滚机制

**代码回滚**（`rollback_code`）：
1. `git reset --hard $PREV_COMMIT` 回退到部署前 commit
2. `deploy_update.sh --non-interactive --skip-migrate --skip-healthcheck` 重新构建
3. 等待 3s 后进入健康检查

**数据库回滚**（`rollback_db`）：
1. `mysql < $DB_BACKUP_FILE` 从备份恢复数据库
2. 配合代码回滚一起执行

**回滚触发条件**：
- 健康检查 5 次全部失败 → 代码回滚
- 数据库迁移失败 → 数据库回滚 + 代码回滚

**本地改动保护**：
- `git reset --hard` 前检测 `git status --porcelain`
- 有本地改动时生成 `/tmp/local_changes_$(date +%Y%m%d_%H%M%S).patch` 备份
- 避免强制覆盖服务器上的手动修改

---

## 部署日志持久化

部署过程的 SSH stdout 保存为 GitHub Actions artifact，便于排查部署失败：

```yaml
- name: 保存部署日志
  if: always()
  env:
    DEPLOY_STDOUT: ${{ steps.deploy.outputs.stdout }}
  run: printf '%s\n' "$DEPLOY_STDOUT" > deploy.log
  continue-on-error: true

- name: 上传部署日志
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: deploy-log-${{ github.run_id }}
    path: deploy.log
    retention-days: 90
  continue-on-error: true
```

**使用方式**：
- 部署失败时在 Actions run 页面直接下载 `deploy-log-{run_id}` artifact
- 或用 `gh run download <run-id> -n deploy-log-<run-id>` 命令下载
- 日志保留 90 天，无需登录服务器查看

---

## 自动 CHANGELOG

部署成功且 sync-dev 完成后，自动从 git log 生成 `CHANGELOG.md`：

```bash
# 按 conventional commit 类型分组
for entry in "feat:新功能" "fix:修复" "docs:文档" "refactor:重构" ...
  COMMITS=$(git log --pretty=format:"- %s (%h)" --no-merges --grep="^${type}")
  # 有提交才输出对应分组
```

**提交目标**：推送到 dev 分支（main 受保护无法直接 push），随下次 PR 合并进入 main。

**与 `docs/修改日志.md` 的区别**：

| 维度 | `CHANGELOG.md`（自动） | `docs/修改日志.md`（手动） |
|------|----------------------|------------------------|
| 生成方式 | CI 从 git log 自动生成 | 人工编写 |
| 内容 | commit message 汇总 | 修改原因、影响范围、验证结果 |
| 更新频率 | 每次 main 合并 | 每次重要改动 |
| 用途 | 技术改动归档 | 业务决策记录 |

---

## 部署通知

通过 Server酱（微信推送）通知部署结果：

**部署成功**：
```
title: ICube 部署成功
des:   Commit: <commit message>
       时间: 2026-08-31 18:00:00
       状态: ✅ 部署成功
       [查看详情](Actions 链接)
```

**部署失败**：
```
title: ICube 部署失败
des:   Commit: <commit message>
       时间: 2026-08-31 18:00:00
       状态: ❌ 部署失败（可能已自动回滚）
       [查看详情](Actions 链接)
```

---

## 本地测试环境

### 测试命令

```bash
# 使用 pytest（推荐）
cd cube_api
pytest                                          # 全量测试
pytest cube_api/apps/accounts/tests/            # 指定模块
pytest cube_api/apps/timer/tests/test_models.py # 指定文件
pytest -v --tb=short                            # 详细输出

# 覆盖率报告
pytest --cov=cube_api/apps --cov=cube_api/utils --cov-report=term-missing
pytest --cov=cube_api/apps --cov-report=html    # HTML 报告 → htmlcov/index.html

# 兼容 manage.py test（仍可用）
python manage.py test
python manage.py test apps.forum.tests.test_models
```

### 测试环境配置

`settings/dev.py` 通过 `_IS_TEST = 'test' in sys.argv or 'pytest' in sys.modules` 自动检测，兼容两种运行方式：

| 组件 | 生产环境 | 测试环境 | 用途 |
|------|---------|---------|------|
| 数据库 | MySQL 8.0 | SQLite 内存库 | 隔离测试数据 |
| Django cache | Redis（RedisCache） | LocMemCache | 帖子缓存、API 缓存 |
| Redis 直连 | 真实 Redis | fakeredis.FakeRedis() | JWT 黑名单、关注集合、限流计数 |
| 邮件 | SMTP | locmem backend | 不实际发送邮件 |
| 限流 | 正常限流值 | 1000/minute | 测试不触发限流 |
| 密码哈希 | PBKDF2 | MD5 | 加速测试 |

> 双 Redis 模拟机制详见 [测试文档](测试文档.md#5-测试环境配置)。

---

## 首次配置步骤

```bash
# 1. 从 main 创建 dev 分支
git checkout main
git pull origin main
git checkout -b dev
git push origin dev

# 2. 设置本地默认跟踪 dev
git branch --set-upstream-to=origin/dev dev

# 3. 后续开发在 dev 上进行
git checkout dev
```

---

## 注意事项

1. **部署脚本**：`deploy_update.sh` 支持 `--non-interactive`、`--skip-migrate`、`--skip-healthcheck`、`--rollback-to=<commit>` 参数，CI 非交互模式下用前三个
2. **Secrets**：共 5 个 GitHub Secret（`SERVER_HOST`、`SERVER_USER`、`SSH_PRIVATE_KEY`、`DEPLOY_PATH`、`SERVERCHAN_KEY`）
3. **dev 上 CI 失败不阻塞**：只是通知测试挂了，不影响任何环境
4. **PR 可以自己合并**：个人开发时，自己发 PR 自己合并，GitHub 允许这样做
5. **Squash merge 后 dev 的处理**：合并后 GitHub 会提示 "Delete branch"，**不要删 dev**，只删 feature/hotfix 分支
6. **服务器上的 main 分支**：服务器上 checkout 的是 main，部署脚本 `git reset --hard origin/main` 同步到最新
7. **sync-dev 用 force push**：合并到 main 后 dev 会被强制同步到 main，本地 dev 需 `git pull --force` 或 `git reset --hard origin/dev`
8. **CHANGELOG 推到 dev 而非 main**：main 受保护无法直接 push，CHANGELOG 提交到 dev 随下次 PR 进入 main
9. **部署日志 artifact 在 `always()` 条件下执行**：即使部署失败也会保存日志，且 `continue-on-error: true` 避免日志保存失败影响整体流程
10. **覆盖率报告不阻塞 CI**：Ruff 检查设为 `continue-on-error: true`，不阻塞测试和部署
