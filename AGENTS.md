# Agent 交接指南

本仓库是一个 Agent 中立的嵌入式工作流工具包。

它不绑定任何板卡、MCU、IDE、工具链、架构布局或 Agent 厂商。

## 首次阅读顺序

在修改文件之前，请阅读或摘要以下内容：

1. `.context/engineering.yaml`
2. `.context/hardware.yaml`
3. `.context/version.yaml`
4. `.context/runtime.yaml`
5. `.agents/rules/entrypoints.md`
6. `.agents/rules/git.md`
7. `.agents/rules/logging.md`
8. `.workflow/project.yaml`
9. `需求.md`
10. 相关源文件

运行：

```bash
python tools/context.py validate
python tools/context.py summary
python tools/workflow.py verify-config
python tools/git_guard.py status
python tools/log_guard.py status
```

## 核心约定

- 不要猜测架构目录、板卡引脚、时钟、工具链路径或运行状态。
- 使用 `.context/` 存放项目事实。
- 使用 `.workflow/project.yaml` 存放工具链、编译、烧录、验证和布局配置。
- 使用 `.agents/rules/` 存放可复用的 Agent 策略。
- 使用 `.agents/skills/` 存放规范 Skill。
- 使用 `tools/workflow.py` 执行确定性的编译/烧录/状态/源注册操作。
- 生成的报告只写入 `reports/`，使用固定的覆盖写入路径。
- 有意义的变更需更新 `PROJECT_LOG.md` 和/或 `EVOLUTION.md`。
- 暂存连贯的任务所属检查点，验证通过后提交。

## 架构

工作流工具包不强制使用 `App/Service/Driver`、`src/include` 或其他任何一种布局。

具体项目必须在 `.context/engineering.yaml` 和 `.workflow/project.yaml` 中声明其架构。

## 测试

工作流将测试作为一等接口保留，但不创建默认的 `Test/` 目录。

具体项目可以配置：

- `build.test_command`
- `verify.command`
- `verify.report_path`
- `layout.tests`

## 常用命令

| 用途 | 命令 |
| ------ | ------ |
| 上下文摘要 | `python tools/context.py summary` |
| 验证上下文 | `python tools/context.py validate` |
| 验证工作流配置 | `python tools/workflow.py verify-config` |
| 生成结构快照 | `python tools/workflow.py structure` |
| 编译已配置项目 | `python tools/workflow.py build` |
| 编译测试固件/目标 | `python tools/workflow.py build --test` |
| 烧录已配置产物 | `python tools/workflow.py flash` |
| 验证 Agent 资产 | `python tools/agent_assets.py validate` |
| 验证日志 | `python tools/log_guard.py validate --mode either` |
| Git 状态 | `python tools/git_guard.py status` |

在未配置的 `workflow_kit` 模式下，编译和烧录应停止并显示清晰的配置错误提示。
