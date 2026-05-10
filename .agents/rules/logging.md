# 强制日志记录策略

项目记忆是交付物的一部分。Agent 必须在没有用户要求的情况下记录有意义的工作。

## 必需流程

任何修改文件的 Agent 必须：

1. 判断本次变更是日常项目工作、结构性工作流演進，还是两者兼有。
2. 更新 `PROJECT_LOG.md`，记录任务进度、验证结果、阻塞项和下一步。
3. 更新 `EVOLUTION.md`，记录可复用的框架变更、规则变更、Skill 变更、工具变更、布局变更或架构策略变更。
4. 将报告保留在 `reports/` 中，并将持久化结论汇总到日志中。
5. 将日志更新与它们所解释的代码/规则/工具变更一同暂存。

## 内容划分

| 文件 | 用途 |
| ------ | ------ |
| `PROJECT_LOG.md` | 当前任务进度、验证结果、阻塞项、运行时观察、下一步行动 |
| `EVOLUTION.md` | 可复用的模板/框架演进、Agent 规则、Skill、工具、目录策略、架构策略 |
| `reports/` | 当前工具证据快照，默认覆盖 |
| `.context/runtime.*` | 仅限当前交接状态，不保留历史 |

## 辅助命令

尽可能使用辅助脚本：

```bash
python tools/log_guard.py status
python tools/log_guard.py validate --mode either
python tools/log_guard.py validate --mode both
```

框架/工具/规则变更使用 `--mode both`。普通功能开发使用 `--mode project`。纯模板变更使用 `--mode evolution`。
