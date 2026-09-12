# Git 分支策略与 CI/CD 流程

> 本文面向小白，用通俗的话讲清楚 CI/CD 是什么、为什么要用、它在背后是怎么干活的。看完你就能理解 GitHub Actions 里那些绿色对勾和红色叉叉到底在干嘛。

## 目录

- [CI/CD 是什么（小白必读）](#cicd-是什么小白必读)
- [GitHub Actions 工作原理](#github-actions-工作原理)
- [Docker 构建缓存原理](#docker-构建缓存原理)
- [分支模型](#分支模型)
- [日常开发流程](#日常开发流程)
- [紧急修复流程](#紧急修复流程)
- [GitHub 仓库配置](#github-仓库配置)
- [CI/CD 总览](#cicd-总览)
- [CI 触发规则与路径过滤](#ci-触发规则与路径过滤)
- [CI Jobs 详解](#ci-jobs-详解)
- [CD 自动部署详解](#cd-自动部署详解)
- [部署日志持久化](#部署日志持久化)
- [自动 CHANGELOG](#自动-changelog)
- [部署通知](#部署通知)
- [本地测试环境](#本地测试环境)
- [首次配置步骤](#首次配置步骤)
- [注意事项](#注意事项)

---

## CI/CD 是什么（小白必读）

### 用生活中的例子理解

想象你在一家奶茶店打工：

- **没有 CI/CD 时**：你做好一杯奶茶，自己尝一口（手动测试），觉得没问题就端给客人（手动部署）。但你有时候会忘放糖、或者用错茶底，客人喝了一口就吐了。

- **有了 CI/CD 后**：你每做一杯奶茶，旁边有一台自动检测机：
  - **CI（持续集成）**：自动检测糖度、茶底温度、配料对不对，全部合格才允许出餐
  - **CD（持续部署）**：检测合格后，自动通过传送带送到客人桌上，不用你端

### 用程序员的话讲

| 概念 | 全称 | 通俗解释 | 在本项目中做什么 |
|------|------|---------|----------------|
| **CI** | Continuous Integration 持续集成 | "代码提交后自动检查有没有问题" | 跑测试、构建前端、验证 Docker 镜像 |
| **CD** | Continuous Deployment 持续部署 | "检查通过后自动上线" | SSH 到服务器执行部署脚本 |

### 为什么要用 CI/CD

1. **防止"我本地明明能跑啊"** — 你电脑上能跑不代表服务器上能跑，CI 在一个干净的环境里重新构建一遍
2. **不用手动 SSH 上去敲命令部署** — 点一下合并，自动上线
3. **部署失败能自动回滚** — 不用半夜爬起来手动救场
4. **每次提交都有记录** — 哪次提交引入了 bug，一目了然

---

## GitHub Actions 工作原理

### 它到底是什么

GitHub Actions 就是 GitHub 提供的"免费机器人"。你告诉它"什么时候做什么事"，它就乖乖照做。

### 核心概念（从大到小）

```
Workflow（工作流）          ← 一个 .yml 文件，描述整套流程
  └── Job（任务）            ← 一个独立的"小项目"，比如"后端测试"
       └── Step（步骤）      ← 一条条具体命令，比如"安装依赖"、"跑测试"
```

| 概念 | 类比奶茶店 | 说明 |
|------|-----------|------|
| **Workflow** | 整套出餐流程 | 存在 `.github/workflows/` 目录下的 `.yml` 文件 |
| **Job** | 一个操作台 | 比如"泡茶台"、"配料台"，可以同时干（并行） |
| **Step** | 一个动作 | 比如"放茶叶"、"加热水"、"过滤茶渣" |
| **Runner** | 操作员 | GitHub 提供的虚拟机，Ubuntu 系统，2 核 7GB 内存 |
| **Action** | 专用工具 | 别人写好的步骤包，比如"上传文件"、"设置 Node 环境" |

### 一次 CI 运行的完整过程

```
1. 你 push 代码到 GitHub
   │
2. GitHub 检测到："哦，这个仓库有 workflow 文件，触发条件匹配"
   │
3. GitHub 分配一台虚拟机（Runner）
   │  ↳ 全新的 Ubuntu 系统，什么都没有
   │  ↳ 免费版有使用时间限制（公开仓库无限制，私有仓库每月 2000 分钟）
   │
4. 虚拟机启动，拉取你的代码（git checkout）
   │
5. 按顺序执行每个 Job 的每个 Step
   │  ↳ 安装依赖、跑测试、构建镜像...
   │  ↳ 每一步都有日志输出
   │
6. 全部成功 → 打个绿色对勾 ✅
   有一个失败 → 打个红色叉叉 ❌
   │
7. 虚拟机销毁（什么都不留下，下次又是全新的）
```

> **为什么每次都要从头开始？** 因为干净环境才能保证"你本地能跑、CI 也能跑"。如果虚拟机上残留了上次的东西，可能会掩盖问题。但这也是为什么 CI 有时候慢——每次都要重新装依赖。

### 并行 Job 是什么

多个 Job 之间是**同时运行**的，就像奶茶店里"泡茶的"和"备料的"可以同时开工。

```
push 代码
  │
  ├─ backend-check（后端测试） ← 同时跑
  ├─ frontend-check（前端构建） ← 同时跑
  └─ docker-build-api（后端 Docker）← 同时跑
  └─ docker-build-front（前端 Docker）← 同时跑
```

但如果一个 Job 需要另一个 Job 的结果（比如"部署"必须等"测试"通过），就用 `needs` 关键字指定依赖关系：

```yaml
deploy:
  needs: [backend-check, frontend-check, docker-build-api, docker-build-front]
```

### Artifact 是什么

前面说了，虚拟机跑完就销毁了。那如果你想保留测试报告、部署日志这些文件怎么办？

用 **Artifact**（产物）—— 把文件上传到 GitHub 的服务器上存着，之后可以下载查看。

类比：奶茶做完后拍个照存档，客人说"这奶茶不对"时可以翻照片查当时的状态。

```
虚拟机里生成文件
  ↓
actions/upload-artifact 上传
  ↓
GitHub 服务器保存（有过期时间，默认 90 天）
  ↓
Actions 页面可以下载查看
```

---

## Docker 构建缓存原理

### 为什么 Docker 构建有时候快有时候慢

Docker 镜像是**一层一层**叠起来的，每一层对应 Dockerfile 里的一条指令：

```
第 1 层：基础系统（python:3.13-slim）   ← 几百 MB，最慢
第 2 层：安装系统依赖（gcc 等）
第 3 层：复制 requirements.txt
第 4 层：pip 安装 Python 依赖        ← 也很慢，要下载编译
第 5 层：复制项目代码                 ← 很快，只是复制文件
第 6 层：创建日志目录
```

**缓存的魔法**：如果某一层的输入（文件内容、命令内容）没变，Docker 就直接用上次的结果，跳过执行。

```
第一次构建（全量）：
  ✅ 拉取基础镜像（2 分钟）
  ✅ 安装系统依赖（1 分钟）
  ✅ pip 安装依赖（2 分钟）
  ✅ 复制代码（几秒）
  总计：~5 分钟

第二次构建（只改了代码，依赖没变）：
  🟡 基础镜像（缓存命中，跳过）
  🟡 系统依赖（缓存命中，跳过）
  🟡 pip 依赖（缓存命中，跳过）
  ✅ 复制代码（几秒）← 只有这层重新执行
  总计：~30 秒
```

### 为什么之前 CI 构建慢

GitHub Actions 每次用全新的虚拟机，**默认没有 Docker 缓存**。所以每次构建都要从头来，5 分钟起步。

### 现在怎么解决的

用了 `docker/build-push-action` 的 `cache-from` / `cache-to` 功能，把 Docker 每一层的缓存保存到 GitHub Actions Cache 里：

```yaml
cache-from: type=gha,scope=api     # 从 GitHub Cache 读缓存
cache-to: type=gha,scope=api,mode=max  # 把新的缓存写回 GitHub Cache
```

- `scope=api` / `scope=front`：后端和前端各有各的缓存，互不干扰
- `mode=max`：缓存所有中间层（不只是最终镜像），加速效果最好

### Dockerfile 怎么写才能最大化缓存效果

关键原则：**把不容易变的放前面，容易变的放后面**。

```dockerfile
# ✅ 好的写法：依赖在前，代码在后
FROM python:3.13-slim          # 很少变 → 最前面
RUN apt-get install gcc ...    # 很少变
COPY requirements.txt .        # 偶尔变（加新依赖时才变）
RUN pip install -r requirements.txt  # 跟着 requirements.txt 变
COPY . .                       # 每次改代码都变 → 最后面
```

如果反过来写：

```dockerfile
# ❌ 坏的写法：代码在前，依赖在后
FROM python:3.13-slim
COPY . .                       # 每次改代码都变 → 后面全部失效
COPY requirements.txt .
RUN pip install -r requirements.txt  # 每次都要重新装，白瞎了缓存
```

本项目的 Dockerfile 已经是正确的顺序了，所以缓存效果会很好。

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

> Secrets 是什么？就是存密码的地方。你不想把服务器密码写进代码里吧？那就存在 GitHub 的 Secrets 里，CI 运行时才能读取到，代码里看不到明文。

---

## CI/CD 总览

```
push 到 dev / PR 到 main
  │
  ├─ backend-check（pytest + 覆盖率）     ← 并行
  ├─ frontend-check（npm build）          ← 并行
  ├─ docker-build-api（后端 Docker 构建） ← 并行
  └─ docker-build-front（前端 Docker 构建 + compose 校验）← 并行
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
| `coverage-report` artifact | 30 天 | XML 覆盖率报告 |
| `deploy-log-{run_id}` artifact | 90 天 | 部署完整 stdout，排查部署失败 |

---

## CI 触发规则与路径过滤

### 顶层路径过滤

CI 仅在以下路径有变更时触发：

```
cube_api/**    后端代码
cube_front/**  前端代码
docker-compose.yml
**/Dockerfile
scripts/**     部署脚本
.github/workflows/cicd.yml
docs/**        文档（触发部署，CI Job 自动跳过）
README.md
```

> **为什么文档变更也触发？** 因为文档变更需要部署到服务器上让用户能看到，但不需要跑测试和构建。所以 workflow 会触发，但每个 CI Job 内部会判断：如果只是文档变了，我就跳过。

### 触发矩阵

| 事件 | 后端检查 | 前端构建 | Docker 构建 | 部署 |
|------|:-------:|:-------:|:----------:|:----:|
| push 到 `dev` | ✅ | ✅ | ✅ | - |
| PR: `dev` → `main` | ✅ | ✅ | ✅ | - |
| push 到 `main`（合并） | ✅ | ✅ | ✅ | ✅ |
| PR: `hotfix/*` → `main` | ✅ | ✅ | ✅ | - |
| push 到 `main`（hotfix 合并） | ✅ | ✅ | ✅ | ✅ |
| 纯文档变更 | ⏭ | ⏭ | ⏭ | ✅ |

### Job 内部路径过滤

每个 Job 内部用 `git diff` + `grep` 二次判断，仅相关文件变更时才实际执行：

| 文件变更 | 后端检查 | 前端构建 | 后端 Docker | 前端 Docker |
|---------|:-------:|:-------:|:----------:|:----------:|
| `cube_api/**` | ✅ 执行 | ⏭ 跳过 | ⏭ 跳过 | ⏭ 跳过 |
| `cube_front/**` | ⏭ 跳过 | ✅ 执行 | ⏭ 跳过 | ⏭ 跳过 |
| `cube_api/Dockerfile` / `docker-compose.yml` | ⏭ 跳过 | ⏭ 跳过 | ✅ 执行 | ✅ 执行 |
| `cube_front/Dockerfile` | ⏭ 跳过 | ⏭ 跳过 | ⏭ 跳过 | ✅ 执行 |
| `docs/**` / `*.md` | ⏭ 跳过 | ⏭ 跳过 | ⏭ 跳过 | ⏭ 跳过 |

> **工作原理**：用 `git diff --name-only HEAD~1 HEAD` 列出变更文件，再用 `grep -c '^cube_api/'` 数匹配的行数。如果行数大于 0，说明有相关变更，就执行后面的步骤。否则就跳过。

---

## CI Jobs 详解

### 1. backend-check（后端 Lint + Test）

| 步骤 | 命令 | 说明 |
|------|------|------|
| 拉取代码 | `actions/checkout@v5` | `fetch-depth: 2` 以便和上一个 commit 比较 |
| 路径检测 | `git diff` + `grep` | 仅 `cube_api/**` 变更时执行后续步骤 |
| 系统依赖 | `apt-get install default-libmysqlclient-dev` | mysqlclient 编译需要 |
| Python 环境 | `actions/setup-python@v5` | 设置 Python 版本，缓存 pip 下载 |
| Python 依赖 | `pip install -r requirements.txt` + `ruff` | 含 pytest/pytest-django/pytest-cov |
| Ruff 检查 | `ruff check cube_api/cube_api/` | `continue-on-error: true`，不阻塞 |
| 全量测试 | `pytest --cov=cube_api/apps --cov=cube_api/utils --cov-report=xml` | pytest 替代 manage.py test |
| 覆盖率上传 | `actions/upload-artifact@v5` | `coverage-report`，保留 30 天 |

### 2. frontend-check（前端 Build 验证）

| 步骤 | 命令 | 说明 |
|------|------|------|
| 拉取代码 | `actions/checkout@v5` | |
| 路径检测 | `git diff` + `grep` | 仅 `cube_front/**` 变更时执行 |
| Node 环境 | `actions/setup-node@v5` | 设置 Node 版本，缓存 npm |
| 前端依赖 | `npm ci` | 基于 package-lock.json，严格一致 |
| 构建验证 | `npm run build` | Vite 生产构建 |

### 3. docker-build-api（后端 Docker 镜像构建验证）

| 步骤 | 说明 |
|------|------|
| 拉取代码 | `actions/checkout@v5` |
| 路径检测 | 仅 `cube_api/Dockerfile` 或 `docker-compose.yml` 变更时执行 |
| 设置 Buildx | `docker/setup-buildx-action@v3` | 启用 BuildKit 高级功能 |
| 构建镜像 | `docker/build-push-action@v6` | 带层缓存（`type=gha,scope=api`），依赖不变时 ~30s |

### 4. docker-build-front（前端 Docker 镜像构建验证 + compose 校验）

| 步骤 | 说明 |
|------|------|
| 拉取代码 | `actions/checkout@v5` |
| 路径检测 | 仅 `cube_front/Dockerfile` 或 `docker-compose.yml` 变更时执行 |
| 设置 Buildx | `docker/setup-buildx-action@v3` | 启用 BuildKit |
| 构建镜像 | `docker/build-push-action@v6` | 带层缓存（`type=gha,scope=front`） |
| compose 校验 | `docker compose config -q` | 验证 compose 配置语法正确 |

> **为什么拆成两个 Job？** 因为可以并行构建，总时间取两者最大值，而不是相加。后端构建慢（要编译 Python 原生扩展），前端快，并行的话总耗时基本等于后端构建时间。

---

## CD 自动部署详解

### 触发条件

```
github.event_name == 'push' && github.ref == 'refs/heads/main'
&& 所有 CI Job 全部通过（或被跳过）
```

### 部署流程（5 步）

```
[0/5] 强制同步远程代码
  ├── git fetch origin main
  ├── 记录 PREV_COMMIT（用于回滚）
  ├── 检测本地改动 → 备份为 /tmp/local_changes_*.patch
  └── git reset --hard origin/main

[1/5] 变更分析与增量构建
  ├── git diff 判断哪些文件变了
  ├── 前端变了 → 重新构建 front 镜像
  ├── 后端变了 → 重新构建 api 镜像
  ├── compose 变了 → docker compose up -d 重新应用
  └── nginx 变了 → 重启 nginx 容器

[2/5] 数据库迁移
  ├── 检测是否有待应用迁移
  ├── 有迁移 → mysqldump 备份数据库 → migrate --noinput
  │   ├── 迁移成功 → 清理备份文件
  │   └── 迁移失败 → 恢复数据库 + 代码回滚 → exit 1
  └── 无迁移 → 跳过

[3/5] 健康检查（5 次重试，每次间隔 3s）
  ├── curl http://localhost/          → 前端 200
  ├── curl http://localhost/api/home/banners/ → API 200
  ├── 通过 → 继续
  └── 失败 → 代码回滚到 PREV_COMMIT → 回滚后健康检查 → exit 1

[4/5] 部署成功
  ├── collectstatic 收集静态文件
  ├── 后端变了则重启 api 容器
  └── 输出当前 commit 和时间

[5/5] 异步全量备份（部署成功后）
  └── nohup ./scripts/backup.sh > /tmp/backup_deploy.log 2>&1 &
```

### 自动回滚机制

**代码回滚**（`rollback_code`）：
1. `git reset --hard $PREV_COMMIT` 回退到部署前 commit
2. 重新构建镜像并启动服务
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
  uses: actions/upload-artifact@v5
  with:
    name: deploy-log-${{ github.run_id }}
    path: deploy.log
    retention-days: 90
  continue-on-error: true
```

**使用方式**：
- 部署失败时在 Actions run 页面直接下载 `deploy-log-{run_id}` artifact
- 日志保留 90 天，无需登录服务器查看

> **`always()` 是什么？** 就是"不管前面成功还是失败，都要执行我"。部署失败了更需要日志来排查原因，所以日志保存必须在任何情况下都执行。
>
> **`continue-on-error: true` 呢？** 就是"就算我失败了也别影响整体流程"。保存日志是次要任务，不能因为日志没存上反而把部署标红。

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
| 内容 | commit message 汇总 | 修改原因、影响范围 |
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

1. **部署脚本**：`deploy_update.sh` 支持 `--non-interactive`、`--backup-db`、`--post-backup`、`--rollback-to=<commit>` 等参数
2. **Secrets**：共 5 个 GitHub Secret（`SERVER_HOST`、`SERVER_USER`、`SSH_PRIVATE_KEY`、`DEPLOY_PATH`、`SERVERCHAN_KEY`）
3. **dev 上 CI 失败不阻塞**：只是通知测试挂了，不影响任何环境
4. **PR 可以自己合并**：个人开发时，自己发 PR 自己合并，GitHub 允许这样做
5. **Squash merge 后 dev 的处理**：合并后 GitHub 会提示 "Delete branch"，**不要删 dev**，只删 feature/hotfix 分支
6. **服务器上的 main 分支**：服务器上 checkout 的是 main，部署脚本 `git reset --hard origin/main` 同步到最新
7. **sync-dev 用 force push**：合并到 main 后 dev 会被强制同步到 main，本地 dev 需 `git pull --force` 或 `git reset --hard origin/dev`
8. **CHANGELOG 推到 dev 而非 main**：main 受保护无法直接 push，CHANGELOG 提交到 dev 随下次 PR 进入 main
9. **部署日志 artifact 在 `always()` 条件下执行**：即使部署失败也会保存日志，且 `continue-on-error: true` 避免日志保存失败影响整体流程
10. **覆盖率报告不阻塞 CI**：Ruff 检查设为 `continue-on-error: true`，不阻塞测试和部署
11. **Docker 缓存用 GitHub Cache 存储**：有 10GB 空间限制和 7 天过期，不用担心占满，缓存失效了大不了下次重新构建
12. **路径过滤用 git diff 实现**：不依赖第三方 action，避免 Node.js 版本弃用警告
