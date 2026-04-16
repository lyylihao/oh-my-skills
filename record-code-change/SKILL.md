---
name: record-code-change
description: 在当前任务产生代码新增、修改、删除、重构、配置变更、脚本变更或测试变更后，自动生成或更新 Obsidian 版本变更记录。配置从 setting.json 读取。记录文件按项目聚合为单文件，每个分支作为项目文件中的一级标题。仅在确实发生代码差异时触发；纯讨论、纯说明、无代码变更时不要触发。
---

你是“代码变更记录助手”。

只要当前任务对代码库产生实际变更，在结束任务前必须补写一份变更记录，并写入 Obsidian。

# 配置来源

所有配置优先从 `setting.json` 读取，不要在 skill 内写死 Obsidian 路径、项目名或默认分支。

配置文件位置规则：

- Claude Code：`.claude/skills/record-code-change/setting.json`
- Codex：`.agents/skills/record-code-change/setting.json`

配置项至少包括：

- `vault_root`：Obsidian Vault 根目录
- `root_folder_name`：记录根目录名，默认建议为 `record-code-change`
- `obsidian_cli_bin`：Obsidian CLI 命令名，可为空
- `branch_strategy`：分支策略，固定为 `current_git_branch`
- `stop_when_branch_missing`：找不到当前 Git 分支时是否中断，固定为 `true`

# 目标

- 优先使用 Obsidian CLI 创建或更新变更文件。
- 文件路径固定为：`<vault_root>/<root_folder_name>/<project_name>.md`
- 一个项目只维护一个 Markdown 文件。
- 每个分支在项目文件中使用一级标题：`# <branch_name>`
- 同一分支的多次变更，统一写入该分支标题下。
- 若分支已存在，则将**新记录插入到该分支标题下方最前面**，保证最新记录优先展示。
- 若分支不存在，则在文件末尾新增该分支一级标题后再写入本次内容。
- 每次具体变更记录都使用二级标题：`## 【YYYY-MM-DD HH:mm 简述】`
- 简述限制在 10 个汉字以内。
- 使用标准 Markdown。
- 标题层级清晰。
- 内容完整但不冗长。
- 不粘贴大段 diff。

# 项目名规则

项目名不从 `setting.json` 读取，必须在运行时自动获取。

获取顺序如下：

1. 当前项目名称：当前工作目录名
2. 仓库名称：
   - 优先取 Git 仓库根目录名
   - 若仍取不到，则尝试从 `origin` 远程地址解析仓库名
3. 如果仍无法确定，则停止并提示用户

最终项目文件路径为：

`<vault_root>/<root_folder_name>/<project_name>.md`

# 分支规则

- 分支版本必须与当前 Git 分支名保持一致。
- 优先使用 `git symbolic-ref --quiet --short HEAD` 获取当前分支。
- 若失败，再尝试 `git rev-parse --abbrev-ref HEAD`。
- 若仍失败，再尝试解析 `.git/HEAD`。
- 不要猜测分支名。
- 不要写死 `master`、`main`、`lihao-v1.0` 或其他默认值。
- 如果无法获取当前分支，必须停止写入，并明确告诉用户：
  - 当前无法识别 Git 分支
  - 需要用户回复当前分支名后再继续

# 特殊场景：未提交的初始分支

仓库处于“未提交的初始分支”（unborn branch）时：

- 仍然要尽量识别出当前分支名
- 分支识别优先读取 HEAD 的符号引用，而不是依赖已有提交
- 不要因为尚未产生首个 commit 就默认判定“没有分支”

# 必须采集的信息

## 1. 项目名
优先级如下：
1. 当前工作目录名
2. Git 仓库根目录名
3. `origin` 远程地址解析出的仓库名
4. 若仍取不到，则停止并提示用户

## 2. 分支版本
优先级如下：
1. `git symbolic-ref --quiet --short HEAD`
2. `git rev-parse --abbrev-ref HEAD`
3. 解析 `.git/HEAD`
4. 如果取不到，停止并提示用户提供分支名，不继续写入

## 3. 变更简述
优先级如下：
1. skill 参数 `$ARGUMENTS`
2. 根据改动自动生成
3. 必须控制在 10 个汉字以内，避免“修改一下”“优化代码”这类空泛描述

## 4. 改动范围
使用以下信息源收集变更：

- `git status --short`
- `git diff --name-only`
- `git diff --stat`
- 必要时读取具体 diff

若仓库处于未提交的初始分支状态，优先使用：

- `git status --short`
- `git diff --cached --name-only`
- `git diff --cached --stat`
- `git diff --cached`

重点归纳以下内容：

- 功能变化
- 修复点
- 接口/数据结构变化
- 配置变化
- 脚本与流水线变化
- 测试与验证情况
- 风险、兼容性、发布注意事项

# 文件组织规则

- 目标文件：`<vault_root>/<root_folder_name>/<project_name>.md`
- 分支作为一级标题，例如：
  - `# master`
  - `# lihao-v1.0`
- 每次变更记录写入对应分支标题下
- 若分支标题已存在，则将新记录插入该分支标题下方最前面
- 若分支标题不存在，则在文件末尾新增该分支标题及本次变更内容
- 不为每个分支单独创建 md 文件

# 归类规则

将代码变更目录按模块归入以下分类（模块无变更时隐藏分类）：

- 【前端】
- 【后端】
- 【数据库】
- 【配置】
- 【测试】
- 【脚本与CI】
- 【文档】
- 【其他】

归类要求：

- 优先按目录职责归类，不要只按文件后缀机械分类
- 目录去重
- 尽量上卷到“模块/子模块”层级，不要把每个文件都列成一行
- 代码变更目录只输出本次实际有变更的模块
- 未涉及的模块不要输出
- 不要出现“无”
- 若某个分类没有实际变更，该分类标题和内容整段都不要生成
- 若生成结果中出现“#### 【任意模块】”后仅跟“无”或空内容，视为归类失败，必须重新整理后再继续

示例：

- `web/src/pages/login/index.tsx` -> 【前端】`web/src/pages/login/`
- `service/user/controller/UserController.java` -> 【后端】`service/user/controller/`
- `db/migrations/V20260413__add_index.sql` -> 【数据库】`db/migrations/`
- `.github/workflows/release.yml` -> 【脚本与CI】`.github/workflows/`

# 写入流程

## 1. 先判断是否真的发生代码变更
- 若没有代码差异，不创建记录，也不要空写

## 2. 读取 setting.json
- 读取 `vault_root`
- 读取 `root_folder_name`
- 读取 `obsidian_cli_bin`
- 校验配置是否齐全

## 3. 识别项目名
- 先取当前工作目录名
- 若失败，取 Git 仓库根目录名
- 若仍失败，尝试从 `origin` 远程地址解析仓库名
- 若仍失败，则停止并提示用户

## 4. 获取当前 Git 分支
- 先执行 `git symbolic-ref --quiet --short HEAD`
- 若失败，再执行 `git rev-parse --abbrev-ref HEAD`
- 若仍失败，再解析 `.git/HEAD`
- 若仍失败，则立即停止，并向用户说明“当前无法识别 Git 分支，请回复分支名后再继续”

## 5. 生成目标文件路径
- 目标路径：`<vault_root>/<root_folder_name>/<project_name>.md`

## 6. 目标文件不存在时
创建项目文件，并按以下结构初始化：

---
project_name: <项目名>
last_updated: <当前时间>
record_mode: per_project_single_file
---

# <当前分支>

## 【<YYYY-MM-DD HH:mm> <10字内简述>】
<本次变更内容>

## 7. 目标文件已存在时
- 保留原内容
- 更新 frontmatter 中的 `last_updated`
- 若当前分支标题已存在，则将新的本次变更块插入到该分支标题下方最前面
- 若当前分支标题不存在，则在文件末尾新增该分支标题，再追加本次变更块

## 8. 每次追加内容必须使用以下模板

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
仅输出本次实际涉及的模块；未涉及的模块不要写，也不要写“无”。

硬性约束：

- 不得输出空模块标题
- 不得为了凑模板而保留无变更分类
- 若最终只有 1 个分类有变更，则只输出这 1 个分类
- 若最终没有可归类目录，说明归类过程有误，禁止直接写入，必须重新检查变更范围

错误示例（禁止）：

#### 【前端】
- 无

#### 【后端】
- 无

#### 【其他】
- hello_world.py

上面的写法是错误的，因为未修改模块被输出，而且出现了“无”。

示例：

#### 【后端】
- service/user/controller/
- service/user/service/

#### 【配置】
- config/
- .claude/skills/record-code-change/

# 写作要求

- 只总结有价值的信息，不要把 diff 翻译一遍
- 优先写“行为变化”“接口变化”“风险”“验证”
- 没有的项写“无”，但“代码变更目录”除外
- 代码变更目录只输出本次实际有变更的模块，未涉及的模块不要输出
- “代码变更目录”中，禁止输出“无”，禁止输出空模块标题，某个模块没有变更时，整段模块标题和内容都不要生成
- 避免模糊表述，例如：
  - 优化了一下
  - 调整了部分代码
  - 做了少量修改
- 标题和小节名保持固定，保证后续可检索、可解析
- 输出中文

## 写入前自检

在调用写入脚本前，必须逐项检查准备写入的 markdown：

- “### 4. 代码变更目录”下不得出现“无”
- 不得出现没有内容的模块标题
- 模块数量必须等于本次实际发生变更的分类数量
- 若只涉及一个分类，则只能保留这一个分类
- 任一检查不通过，禁止写入 Obsidian，必须先修正内容再执行写入

# 执行方式

优先使用 helper script 写入。

当你已生成好“本次变更块”的 markdown 内容后，将其保存到一个临时文件，再执行下面命令之一。

## Claude Code
`python .claude/skills/record-code-change/scripts/obsidian_change_log.py --content-file "$TMP_CHANGELOG_MD" --title "$CHANGE_TITLE"`

## Codex
`python .agents/skills/record-code-change/scripts/obsidian_change_log.py --content-file "$TMP_CHANGELOG_MD" --title "$CHANGE_TITLE"`

说明：

- `TMP_CHANGELOG_MD` 是你先生成好的“本次变更块” markdown 临时文件
- `CHANGE_TITLE` 必须是 10 字以内简述
- 所有配置从 `setting.json` 读取
- 项目名自动获取，不从配置读取
- 分支版本必须从当前 Git 分支读取
- 如果当前 Git 分支取不到，停止执行并提示用户回复分支名
- 若用户已经回复了分支名，可将该分支名作为脚本参数再次执行

# 失败处理

- 若 `setting.json` 不存在，明确告知缺少配置文件
- 若 `vault_root` 为空或路径不存在，明确告知 Vault 路径无效
- 若项目名无法获取，停止并提示用户
- 若 Git 分支拿不到，停止并提示用户提供当前分支名
- 若写入失败，保留已生成的 markdown 内容，并在回复中贴出，避免记录丢失

# 触发时机

- 你自己完成代码修改后，在最终回复前执行
- 用户要求“顺手记一下变更”“更新版本记录”“写入 Obsidian 变更日志”时立即执行
- 纯咨询、纯设计讨论、没有落地产生代码差异时不要触发
