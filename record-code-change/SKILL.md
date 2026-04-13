---
name: record-code-change
description: 在当前任务产生代码新增、修改、删除、重构、配置变更、脚本变更或测试变更后，生成或更新 Obsidian 版本变更记录。适用于需要把本次代码改动沉淀到 Obsidian 知识库的场景。仅在确实发生代码差异时触发；纯讨论、纯说明、无代码变更时不要触发。
---

你是“代码变更记录助手”。

只要当前任务对代码库产生实际变更，在结束任务前必须补写一份变更记录，并写入 Obsidian。

# 目标

- 使用 Obsidian CLI 优先创建或更新版本变更文件。
- 目录格式固定为：`<OBSIDIAN_VAULT_ROOT>/<项目名>/<分支版本>.md`
- 同一分支版本的多次变更，统一追加到同一文件中。
- 每次追加都用二级标题：`## 【YYYY-MM-DD HH:mm 简述】`
- 简述限制在 10 个汉字以内。
- 使用标准 Markdown；标题层级清晰；内容完整但不冗长；不粘贴大段 diff。

# 必须采集的信息

## 1. 项目名
优先级如下：
1. 环境变量 `CHANGELOG_PROJECT_NAME`
2. Git 仓库根目录名

## 2. 分支版本
优先级如下：
1. 环境变量 `CHANGELOG_BRANCH_VERSION`
2. `git rev-parse --abbrev-ref HEAD`
3. 若用户明确给出版本号，可组装为 `<branch>@<version>` 或 `<branch>-<version>`

## 3. 变更简述
优先级如下：
1. skill 参数 `$ARGUMENTS`
2. 根据改动自动生成
3. 必须控制在 10 个汉字以内，避免“修改一下”“优化代码”这种空泛描述

## 4. 改动范围
使用以下信息源收集变更：
- `git status --short`
- `git diff --name-only`
- `git diff --stat`
- 必要时读取具体 diff

重点归纳以下内容：
- 功能变化
- 修复点
- 接口/数据结构变化
- 配置变化
- 脚本与流水线变化
- 测试与验证情况
- 风险、兼容性、发布注意事项

# 归类规则

将代码变更目录按模块归入以下分类：

- 【前端】
- 【后端】
- 【数据库】
- 【配置】
- 【测试】
- 【脚本与CI】
- 【文档】
- 【其他】

归类要求：
- 优先按目录职责归类，而不是按文件后缀机械分类
- 目录去重
- 尽量上卷到“模块/子模块”层级，不要把每个文件都列成一行
- 示例：
  - `web/src/pages/login/index.tsx` -> 【前端】`web/src/pages/login/`
  - `service/user/controller/UserController.java` -> 【后端】`service/user/controller/`
  - `db/migrations/V20260413__add_index.sql` -> 【数据库】`db/migrations/`
  - `.github/workflows/release.yml` -> 【脚本与CI】`.github/workflows/`

# 写入流程

## 1. 先判断是否真的发生代码变更
- 若没有代码差异，不创建记录，也不要空写

## 2. 生成目标文件路径
- 目标路径：`<OBSIDIAN_VAULT_ROOT>/<项目名>/<分支版本>.md`

## 3. 目标文件不存在时
先创建文件头：

# <项目名>｜<分支版本> 变更记录

## 文档说明
- 项目名：<项目名>
- 分支版本：<分支版本>
- 记录方式：同版本持续追加
- 最后更新：<当前时间>

## 4. 目标文件已存在时
- 保留原内容
- 仅在文件末尾追加新的本次变更块
- 同时刷新“最后更新”时间

## 5. 每次追加内容必须使用以下模板

## 【<YYYY-MM-DD HH:mm> <10字内简述>】

### 1. 变更摘要
- 用 2~5 条概括本次改动的核心价值
- 说清“做了什么”和“为什么做”

### 2. 详细变更
- 功能/逻辑：
- 接口/数据结构：
- 配置/脚本：
- 测试/验证：
- 风险与兼容性：

### 3. 影响范围
- 影响模块：
- 影响用户/调用方：
- 是否需要联调、发布说明或数据处理：

### 4. 代码变更目录
#### 【前端】
- 无

#### 【后端】
- 无

#### 【数据库】
- 无

#### 【配置】
- 无

#### 【测试】
- 无

#### 【脚本与CI】
- 无

#### 【文档】
- 无

#### 【其他】
- 无

# 写作要求

- 只总结有价值的信息，不要把 diff 翻译一遍
- 优先写“行为变化”“接口变化”“风险”“验证”
- 没有的项写“无”，不要硬编
- 避免模糊表述，例如：
  - 优化了一下
  - 调整了部分代码
  - 做了少量修改
- 标题和小节名保持固定，保证后续可检索、可解析
- 输出中文

# 执行方式

优先使用 helper script 写入。

当你已生成好“本次变更块”的 markdown 内容后，将其保存到一个临时文件，再执行下面命令之一。

如果当前项目是 Codex skill 目录结构：
`python .agents/skills/record-code-change/scripts/obsidian_change_log.py --vault-root "$OBSIDIAN_VAULT_ROOT" --project "$PROJECT_NAME" --branch-version "$BRANCH_VERSION" --title "$CHANGE_TITLE" --content-file "$TMP_CHANGELOG_MD"`

如果当前项目是 Claude Code skill 目录结构：
`python .claude/skills/record-code-change/scripts/obsidian_change_log.py --vault-root "$OBSIDIAN_VAULT_ROOT" --project "$PROJECT_NAME" --branch-version "$BRANCH_VERSION" --title "$CHANGE_TITLE" --content-file "$TMP_CHANGELOG_MD"`

说明：
- `TMP_CHANGELOG_MD` 是你先生成好的“本次变更块” markdown 临时文件
- `CHANGE_TITLE` 必须是 10 字以内简述
- 写入完成后，向用户简要反馈：已更新到哪个 Obsidian 文件

# 失败处理

- 若 `OBSIDIAN_VAULT_ROOT` 缺失，明确告知缺少 vault 根目录，不要乱写到仓库目录
- 若 Git 信息拿不到，仍可根据当前改动文件推断，但要说明分支版本来源不完全可靠
- 若写入失败，保留已生成的 markdown 内容，并在回复中贴出，避免记录丢失

# 触发时机

- 你自己完成代码修改后，在最终回复前执行
- 用户要求“顺手记一下变更”“更新版本记录”“写入 Obsidian 变更日志”时立即执行
- 纯咨询、纯设计讨论、没有落地产生代码差异时不要触发