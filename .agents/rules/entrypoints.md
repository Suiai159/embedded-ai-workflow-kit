# Agent 规则入口文件

根目录的 Agent 文件是发现入口。保持简短，便于工具快速查找和读取。

## 规范位置

规范的 Agent 规则文件存放在 `.agents/rules/` 下。

| 路径 | 作用 |
|------|------|
| `AGENTS.md` | 通用 AI Agent 根入口 |
| `.agents/rules/entrypoints.md` | 规则文件布局和发现策略 |
| `.agents/rules/git.md` | 强制 Git 保存和提交策略 |
| `.agents/skills/` | 可复用的规范 Skill |

## 规则

- 根入口文件保持精简，只放高价值摘要信息。
- 可复用的 Agent 策略放在 `.agents/rules/`。
- 可复用的工作流 Skill 放在 `.agents/skills/`。
- 确定性命令放在 `tools/`。
- 项目事实放在 `.context/`。
- 工具链和布局配置放在 `.workflow/project.yaml`。
- 不得将任何工具特定的 Agent 目录作为项目规则或 Skill 的规范主目录。
