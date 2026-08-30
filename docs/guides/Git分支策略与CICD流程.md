# Git 分支策略与 CI/CD 流程

## 分支模型

```
feature/xxx（可选）     dev               main
    │                   │                  │
    └── 合并到 dev ────→│                  │
                        │                  │
                        └── PR 到 main ───→│ → 自动部署
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

### 3. 合并后同步 dev

```bash
git checkout dev
git pull origin dev
```

Squash merge 会在 dev 上生成一个 merge commit，pull 一下保持同步。

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

# 4. 部署完成后，把修复同步回 dev
git checkout dev
git merge origin/main
git push origin dev

# 5. 删除 hotfix 分支
git branch -d hotfix/fix-xxx
git push origin --delete hotfix/fix-xxx
```

## GitHub 仓库配置

### 分支保护规则（需手动设置）

进入 `Settings` → `Branches` → `Add branch protection rule`：

| 配置项 | 值 | 说明 |
|--------|-----|------|
| Branch name pattern | `main` | 保护 main 分支 |
| Require a pull request before merging | ✅ | 禁止直接 push |
| Require approvals | ❌ | 一个人开发不需要审批 |
| Require status checks to pass before merging | ✅ | CI 必须通过才能合并 |
| Require branches to be up to date before merging | ❌ | 一个人开发不需要 |
| Do not allow bypassing the above settings | ✅ | 防止管理员绕过 |

> **注意**：分支保护是 GitHub Free 公开仓库的功能。如果仓库是私有的，Free 计划不支持分支保护，需升级到 Pro 或保持仓库公开。

### 合并策略

进入 `Settings` → `General` → `Pull Requests`：

- 勾选 **Allow squash merging**（推荐）
- 取消 **Allow merge commits**
- 取消 **Allow rebase merging**

Squash merge 会把 PR 的所有 commit 压成一个，main 历史干净整洁。

## CI 触发规则

| 事件 | 后端检查 | 前端构建 | Docker 构建 | 部署 |
|------|:-------:|:-------:|:----------:|:----:|
| push 到 `dev` | ✅ | ✅ | ✅ | - |
| PR: `dev` → `main` | ✅ | ✅ | ✅ | - |
| push 到 `main`（合并） | ✅ | ✅ | ✅ | ✅ |
| PR: `hotfix/*` → `main` | ✅ | ✅ | ✅ | - |
| push 到 `main`（hotfix 合并） | ✅ | ✅ | ✅ | ✅ |
| 纯文档变更 | - | - | - | - |

## Path Filter 智能跳过

每个 Job 内部还会根据文件变更路径决定是否实际执行：

| 文件变更 | 后端检查 | 前端构建 | Docker 构建 |
|---------|:-------:|:-------:|:----------:|
| `cube_api/**` | ✅ 执行 | ⏭ 跳过 | ⏭ 跳过 |
| `cube_front/**` | ⏭ 跳过 | ✅ 执行 | ⏭ 跳过 |
| `Dockerfile` / `docker-compose.yml` | ⏭ 跳过 | ⏭ 跳过 | ✅ 执行 |
| `docs/**` / `*.md` | 不触发 CI | 不触发 CI | 不触发 CI |

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

## 注意事项

1. **部署脚本不变**：`deploy_update.sh` 拉的是当前分支（main 服务器上 checkout 的是 main），无需修改
2. **Secrets 不变**：现有 4 个 GitHub Secret 保持不变
3. **dev 上 CI 失败不阻塞**：只是通知你测试挂了，不影响任何环境
4. **PR 可以自己合并**：一个人开发时，自己发 PR 自己合并，GitHub 允许这样做
5. **Squash merge 后 dev 的处理**：合并后 GitHub 会提示 "Delete branch"，**不要删 dev**，只删 feature/hotfix 分支
6. **服务器上的 main 分支**：服务器上 `git pull` 拉的是 main，PR 合并后 main 更新，部署脚本自动拉到最新代码
