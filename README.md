# oh-my-skills
保存个人常用skills

## 1 record-code-change
- 功能：使用obsidian cli在开发后自动保存代码变更内容
- 提示：建议补一段 CLAUDE.md 或 AGENTS.md：
    发生代码变更并准备结束任务时，必须调用 `record-code-change`。
    配置从 setting.json 读取。
    分支版本必须与当前 Git 分支名一致。
    如果无法识别当前 Git 分支，则停止并提示用户回复分支名后再继续。