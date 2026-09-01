# ICube 项目 Skill 使用指南

## 目录

- [概述](#概述)
- [自建 Skill（项目专属）](#自建-skill项目专属)
- [常用 Skill（开发流程）](#常用-skill开发流程)
- [中文规范 Skill](#中文规范-skill)
- [进阶 Skill](#进阶-skill)
- [系统插件 Skill](#系统插件-skill)
- [Skill 调用方式](#skill-调用方式)

---

## 概述

ICube 项目 `.trae/skills/` 目录下共有 24 个 Skill，分为三类：

| 类别 | 数量 | 说明 |
|------|------|------|
| 项目自建 | 2 | 针对ICube业务定制 |
| Superpowers-ZH 框架 | 20 | 通用开发流程规范 |
| 系统插件 | 多个 | TRAE 内置或插件提供（docx/pptx/xlsx 等） |

---

## 自建 Skill（项目专属）

### icube-testing

| 属性 | 值 |
|------|-----|
| 路径 | `.trae/skills/icube-testing/SKILL.md` |
| 触发 | 写测试、审查测试、调试测试失败、添加覆盖率时 |
| 配套 | `test-template.py` — 模型/服务/API 三层测试模板 |

**核心规范**：
- 测试分层：`test_models.py`（模型）→ `test_services.py`（服务层）→ `test_api.py`（API 集成）
- 双 Redis 模拟：`LocMemCache` 替代 Django cache、`fakeredis` 替代原生 redis-py
- 注释要求：每个测试方法带中文注释说明测试意图
- 覆盖清单：字段默认值、`__str__`、property、clean/save、权限、分页、限流
- 反模式红线：禁止 `assertTrue(obj is not None)` 裸用、禁止跳过 tearDown

**常用场景**：
```
"给 forum 模块补测试" → 自动加载 icube-testing，按分层模板生成
"测试失败，排查原因" → 加载 icube-testing + systematic-debugging
```

### cube-article-finder

| 属性 | 值 |
|------|-----|
| 路径 | `.trae/skills/cube-article-finder/SKILL.md` |
| 触发 | 搜索三阶魔方文章/教程，打包为 JSON 供数据库导入 |

**核心流程**：搜索网页 → 提取标题/正文/图片 → 输出标准化 JSON → 配合 `import_articles` 管理命令导入

---

## 常用 Skill（开发流程）

按开发阶段排列，标注使用频率：

### 规划阶段

| Skill | 触发条件 | 使用频率 |
|-------|---------|---------|
| **brainstorming** | 创建功能、构建组件、添加功能或修改行为前 | ⭐⭐⭐ 高 |
| **writing-plans** | 有规格说明或需求用于多步骤任务，动手写代码前 | ⭐⭐ 中 |

### 实现阶段

| Skill | 触发条件 | 使用频率 |
|-------|---------|---------|
| **test-driven-development** | 实现任何功能或修复 bug 时，先写测试 | ⭐⭐⭐ 高 |
| **executing-plans** | 执行书面实现计划，设有审查检查点 | ⭐ 低 |
| **subagent-driven-development** | 当前会话中执行含独立任务的实现计划 | ⭐ 低 |
| **dispatching-parallel-agents** | 2 个以上可独立进行的无依赖任务 | ⭐ 低 |

### 调试验证

| Skill | 触发条件 | 使用频率 |
|-------|---------|---------|
| **systematic-debugging** | 遇到 bug、测试失败或异常行为时 | ⭐⭐⭐ 高 |
| **verification-before-completion** | 宣称完成/修复/测试通过前，提交或创建 PR 前 | ⭐⭐⭐ 高 |

### Git 工作流

| Skill | 触发条件 | 使用频率 |
|-------|---------|---------|
| **using-git-worktrees** | 需要与当前工作区隔离的功能开发 | ⭐ 低 |
| **finishing-a-development-branch** | 实现完成、测试通过、决定如何集成 | ⭐⭐ 中 |

### 代码审查

| Skill | 触发条件 | 使用频率 |
|-------|---------|---------|
| **requesting-code-review** | 完成任务、实现重要功能或合并前 | ⭐⭐ 中 |
| **receiving-code-review** | 收到代码审查反馈后、实施建议前 | ⭐⭐ 中 |

### 文档同步

| Skill | 触发条件 | 使用频率 |
|-------|---------|---------|
| **doc-update-sync** | 代码改动后需要同步 docs/wiki/修改日志/README | ⭐⭐⭐ 高 |

### Skill 管理

| Skill | 触发条件 | 使用频率 |
|-------|---------|---------|
| **writing-skills** | 创建新技能、编辑现有技能或验证技能 | ⭐ 低 |
| **using-superpowers** | 每次对话开始时，确立如何查找和使用技能 | ⭐ 低（自动） |

---

## 中文规范 Skill

这组 Skill 仅在用户显式 `/命令` 时调用，不自动触发：

| Skill | 命令 | 用途 |
|-------|------|------|
| **chinese-code-review** | `/chinese-code-review` | 中文 review 话术模板、分级标注（必须修复/建议修改/仅供参考） |
| **chinese-commit-conventions** | `/chinese-commit-conventions` | Conventional Commits 中文适配、commitlint/commitizen 模板 |
| **chinese-documentation** | `/chinese-documentation` | 中文排版规范（中英文空格、全半角标点、术语保留） |
| **chinese-git-workflow** | `/chinese-git-workflow` | Gitee/Coding.net/极狐GitLab/CNB 的 SSH/HTTPS/CI 配置 |

---

## 进阶 Skill

| Skill | 触发条件 |
|-------|---------|
| **mcp-builder** | 系统化构建生产级 MCP 工具 |
| **workflow-runner** | 用户提供 `.yaml` 工作流文件或要求多角色协作 |

---

## 系统插件 Skill

TRAE 插件提供的 Skill，不属于 `.trae/skills/` 目录但可在项目中使用：

| Skill | 来源插件 | 用途 |
|-------|---------|------|
| **dynamic-ui** | 内置 | 内联 SVG 图表/交互组件 |
| **docx** | 内置 | Word 文档创建/读取/编辑 |
| **pptx** | 内置 | PowerPoint 幻灯片创建/编辑 |
| **xlsx** | 内置 | Excel 表格创建/编辑 |
| **pdf** | 内置 | PDF 读取/合并/拆分/水印 |
| **html-deck** | 内置 | HTML 演示文稿生成 |
| **html-report** | 内置 | HTML 报告/白皮书/PRD 生成 |
| **skill-creator** | 内置 | 创建 SKILL 的引导工具 |
| **research-guide** | 内置 | 研究与分析场景 |
| **doc-writing-guide** | 内置 | 文档写作指导 |
| **frontend-design** | 前端设计插件 | UI/UX 设计实现 |
| **webapp-testing** | Web 开发插件 | Playwright 前端测试 |
| **scrapling-official** | 爬虫插件 | 反机器人绕过的网页抓取 |
| **redis-development** | Redis 插件 | Redis 性能优化与最佳实践 |

---

## Skill 调用方式

### 自动触发

AI 根据任务上下文自动匹配 Skill，无需手动指定：

```
"给 accounts 模块补测试" → 自动加载 icube-testing
"排查这个 bug" → 自动加载 systematic-debugging
```

### 显式调用

用户通过 `/命令` 或 `Use Skill: skill-name` 显式触发：

```
/chinese-code-review     → 调用中文代码审查规范
Use Skill: icube-testing → 强制加载测试规范
```

### 组合使用

实际开发中多个 Skill 会串联使用：

```
需求 → brainstorming（探索意图）
     → writing-plans（写计划）
     → test-driven-development（先写测试）
     → icube-testing（测试规范）
     → systematic-debugging（调试失败）
     → verification-before-completion（验证完成）
     → doc-update-sync（同步文档）
     → finishing-a-development-branch（合并收尾）
```
