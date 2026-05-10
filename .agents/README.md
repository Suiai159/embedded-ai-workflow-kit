# Agent 资产目录

本目录是 AI 工作流资产的 Agent 中立主目录。

## 目录布局

| 路径 | 作用 |
|------|------|
| `.agents/rules/` | 所有 AI 工具可共享的规范 Agent 规则 |
| `.agents/skills/` | 可复用的规范 Skill 定义 |
| `.agents/manifest.yaml` | 工作流规范资产注册表 |

## 规则

- 优先编辑 `.agents/skills/`。
- 可复用的 Agent 策略编辑 `.agents/rules/`。
- 确定性操作放在 `tools/` 中；Skill 应描述工作流并调用工具。
- 项目事实放在 `.context/`，工具和布局配置放在 `.workflow/project.yaml`。
- 编译、烧录、审查、验证报告不要放在这里，报告属于 `reports/`。
- 修改文件的 Agent 必须更新相应的日志文件。
- Agent 应将连贯的检查点暂存、验证，验证通过后提交，除非用户明确表示不提交。

常用命令：

```bash
python tools/agent_assets.py validate
```

项目接入 Skill：

- `/project-port`：通过 Agent/用户问答的方式，将本工作流工具包接入真实嵌入式工程。
