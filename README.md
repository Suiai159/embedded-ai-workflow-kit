# Embedded AI Workflow Kit

这是一个可复制到任意嵌入式工程里的 AI 工作流工具包。它不绑定板子、MCU、IDE、工具链、目录架构或特定 Agent。

目标是让用户把这些 workflow 文件放进自己的工程后，通过配置文件声明项目事实，而不是先删除一堆与自己无关的 STM32、CubeMX、Keil 或 Claude Code 残留。

## 核心目录

```text
.agents/      # Agent-neutral 规则和 canonical Skills
.context/     # AI 接手事实源
.workflow/    # 项目/工具链/布局配置
docs/         # 工作流说明和测试清单
reports/      # 当前证据快照，默认覆盖
tools/        # 确定性工具和 adapter
AGENTS.md     # 通用 Agent 入口
PROJECT_LOG.md
EVOLUTION.md
```

默认不包含：

- 用户工程架构目录，例如 `App/`, `Service/`, `Driver/`
- 用户测试目录，例如 `Test/`
- CubeMX 生成代码
- Keil/CMake/GCC 工程文件
- 板卡、MCU、引脚、时钟、外设事实
- `.claude/` 等工具私有 Agent 目录

## 接入一个真实工程

1. 复制 workflow 目录和入口文件到你的工程。
2. 修改 `.workflow/project.yaml`：
   - `project.name`
   - `toolchain.type`
   - `build.*`
   - `flash.*`
   - `verify.*`
   - `layout.architecture`
   - `layout.tests`
3. 修改 `.context/*.yaml`，记录架构、硬件、版本、运行状态。
4. 运行校验：

```bash
python tools/context.py validate
python tools/workflow.py verify-config
python tools/agent_assets.py validate
python tools/project_structure.py generate
python tools/project_structure.py validate
```

## 架构原则

workflow 不强制任何架构命名。用户项目可以是：

- `App/Service/Driver`
- `Application/Domain/Platform`
- `src/include/tests`
- RTOS task/module/component 风格

唯一要求是：在 `.context/engineering.yaml` 中说清楚架构目录、依赖方向、所有权和生成代码边界。

## 测试接口

默认不创建 `Test/` 目录，因为用户可能已有自己的测试布局。但 workflow 保留测试接口：

- `.workflow/project.yaml` 的 `build.test_command`
- `.workflow/project.yaml` 的 `verify.command`
- `.workflow/project.yaml` 的 `layout.tests`
- `reports/verify_report.md`
- `.context/runtime.yaml` 的 verify 快照

## 常用命令

```bash
python tools/context.py summary
python tools/context.py validate
python tools/workflow.py verify-config
python tools/workflow.py build
python tools/workflow.py build --test
python tools/workflow.py flash
python tools/workflow.py status
python tools/agent_assets.py validate
python tools/project_structure.py generate
python tools/log_guard.py validate --mode either
python tools/git_guard.py status
```

在未配置真实工程时，`build` 和 `flash` 会提示你先配置 adapter。

## Reports 规则

所有工具报告都写入 `reports/`，并使用固定文件名覆盖旧结果。历史结论写入 `PROJECT_LOG.md` 或 `EVOLUTION.md`。

常用固定文件：

- `reports/build_log.txt`
- `reports/flash_log.txt`
- `reports/check_req_report.md`
- `reports/code_review_report.md`
- `reports/verify_report.md`

## Git 与日志规则

Agent 修改文件后必须：

1. 运行 `python tools/git_guard.py status`
2. 更新 `PROJECT_LOG.md` 和/或 `EVOLUTION.md`
3. 只暂存本次任务拥有的文件
4. 验证通过后提交

不要每个小步骤都 commit；用 staged checkpoint 表示当前候选状态。

## 测试清单

见 [docs/TEST_CHECKLIST.md](docs/TEST_CHECKLIST.md)。
