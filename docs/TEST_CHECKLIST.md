# 工程工作流测试清单

这份清单用于验证当前模板改造是否真的可接手、可迁移、可构建、可记录。建议按顺序执行：先做无硬件检查，再做本机工具链检查，最后做真板构建/烧录/验证。

## 0. 准备

- [ ] 确认当前分支正确。
  ```bash
  git status --short
  ```
- [ ] 记录开始测试前已有的本地脏文件，避免误判为本次测试产生。
- [ ] 确认只把测试产生的报告写到 `reports/`，不要在 `tools/`、根目录或临时目录散落报告。

## 1. 上下文接手检查

- [ ] 校验四类上下文文件完整。
  ```bash
  python tools/context.py validate
  ```
  期望：输出 `Context validation passed.`

- [ ] 查看 AI 接手摘要。
  ```bash
  python tools/context.py summary
  ```
  期望：能说清工程分层、硬件资源、工具链、运行状态。

- [ ] 检查 `.context/engineering.yaml` 中的目录策略。
  期望：
  - `directory_policy.workflow_invariant` 包含 `docs`, `.context`, `.workflow`, `.agents`, `tools`, `reports`
  - `directory_policy.project_architecture` 声明当前项目架构目录，例如本模板的 `App`, `Service`, `Driver`, `Test`

## 2. Workflow 配置检查

- [ ] 校验 workflow 配置。
  ```bash
  python tools/workflow.py verify-config
  ```
  期望：能解析当前 project、board、mcu、toolchain、hex path、build log。

- [ ] 确认 build/flash log 指向 `reports/`。
  期望：
  - `build_log` 指向 `reports/build_log.txt`
  - `flash_log` 指向 `reports/flash_log.txt`

- [ ] 查看当前 workflow 状态。
  ```bash
  python tools/workflow.py status
  ```
  期望：能输出 hex/project_file 是否存在。

## 3. `.project_structure` 生成检查

- [ ] 重新生成结构快照。
  ```bash
  python tools/workflow.py structure
  ```
  期望：输出 `Generated .project_structure`

- [ ] 校验结构快照是最新的。
  ```bash
  python tools/workflow.py structure --check
  ```
  期望：输出 `Project structure validation passed.`

- [ ] 打开 `.project_structure`，确认它声明自己是 generated file，且事实源是 `.context/engineering.yaml` + `.workflow/project.yaml`。

## 4. Agent 资产检查

- [ ] 校验 Agent 资产。
  ```bash
  python tools/agent_assets.py validate
  ```
  期望：输出 `Agent assets validation passed.`

- [ ] 确认 canonical Skills 位于 `.agents/skills/`。
- [ ] 确认 `.claude/skills/` 只是兼容镜像，不是唯一事实源。
- [ ] 如修改了 `.agents/skills/`，同步兼容镜像。
  ```bash
  python tools/agent_assets.py sync-skills --target claude
  ```

## 5. Git 与日志强制规则检查

- [ ] 查看 git 状态。
  ```bash
  python tools/git_guard.py status
  ```
  期望：能看到当前脏文件；不要把 `.claude/settings.local.json`、`MDK-ARM/very_test/main.d` 等无关本地文件混入任务。

- [ ] 修改文件后，先暂存本次任务拥有的文件。
  ```bash
  python tools/git_guard.py stage --paths <task-owned-files>
  ```
  期望：输出 staged checkpoint 文件列表。

- [ ] 修改文件后，必须更新日志。
  ```bash
  python tools/log_guard.py validate --mode either
  ```
  期望：普通任务至少更新 `PROJECT_LOG.md` 或 `EVOLUTION.md`。

- [ ] 框架、规则、Skill、tools、目录边界改动时，同时更新两个日志。
  ```bash
  python tools/log_guard.py validate --mode both
  ```

- [ ] 验证通过后再提交，不要每个小步骤都 commit。
  ```bash
  git diff --cached --name-only
  git commit -m "type: concise summary"
  ```

## 6. Reports 目录检查

- [ ] 确认 `reports/README.md` 存在。
- [ ] 确认生成报告使用固定文件名覆盖，而不是新增时间戳文件。
- [ ] 当前固定报告路径：
  - `reports/build_log.txt`
  - `reports/flash_log.txt`
  - `reports/check_req_report.md`
  - `reports/code_review_report.md`
  - `reports/verify_report.md`
- [ ] 确认 `tools/build_log.txt` 和 `tools/flash_log.txt` 不再作为日志事实源。

## 7. 无硬件 Python 工具检查

- [ ] 编译关键 Python 工具。
  ```bash
  python -m py_compile tools/context.py tools/workflow.py tools/agent_assets.py tools/git_guard.py tools/log_guard.py tools/project_structure.py tools/dev_orchestrator.py
  ```
  期望：无输出且返回 0。

- [ ] 查询开发总控下一步。
  ```bash
  python tools/dev_orchestrator.py --query-next-step
  ```
  期望：能读取 reports、PROJECT_LOG、需求状态并给出下一步。

## 8. Keil 构建兼容检查

- [ ] 执行普通构建。
  ```bash
  python tools/workflow.py build
  ```
  期望：
  - 调用 `.workflow/project.yaml` 中配置的 Keil adapter
  - 日志写入 `reports/build_log.txt`
  - `.context/runtime.yaml` 更新 build 状态

- [ ] 执行测试构建。
  ```bash
  python tools/workflow.py build --test
  ```
  期望：
  - 临时注入 `TEST_MODE`
  - 构建结束后恢复工程文件
  - 不产生重复工程配置项

## 9. 烧录检查（需要硬件）

- [ ] 确认 hex 文件存在。
  ```bash
  python tools/workflow.py status
  ```

- [ ] 执行烧录。
  ```bash
  python tools/workflow.py flash
  ```
  期望：
  - 使用 `.workflow/project.yaml` 中配置的 flash adapter
  - 日志写入 `reports/flash_log.txt`
  - `.context/runtime.yaml` 更新 flash 状态

- [ ] hex 不存在时，提示先 build，而不是静默失败。

## 10. Verify 闭环检查（需要硬件和串口）

- [ ] 执行 verify。
  ```bash
  python .agents/skills/verify/verify.py --single-run --max-retries 0 --req 需求.md
  ```
  期望：
  - 构建 TEST_MODE 固件
  - 烧录
  - 串口读取 JSON 测试结果
  - 输出 `reports/verify_report.md`
  - 更新 `.context/runtime.yaml`

- [ ] verify 失败时，失败现象写入 `reports/verify_report.md` 和 `.context/runtime.yaml`，不要只留在对话里。

## 11. GCC/CMake Adapter 预留检查

- [ ] 将 `.workflow/project.yaml` 临时复制到测试配置文件，不直接破坏当前 Keil 配置。
- [ ] 在测试配置中设置 `toolchain.type: gcc` 并配置 `build.command`。
- [ ] 执行：
  ```bash
  python tools/workflow.py --config <test-config.yaml> verify-config
  ```
  期望：能解析 GCC command adapter。

- [ ] 在测试配置中设置 `toolchain.type: cmake` 并配置 `source_dir/build_dir`。
- [ ] 执行：
  ```bash
  python tools/workflow.py --config <test-config.yaml> verify-config
  ```
  期望：能解析 CMake adapter。

## 12. 通过标准

- [ ] 无硬件检查全部通过。
- [ ] 有硬件时 build、flash、verify 的报告都固定写入 `reports/`。
- [ ] `.context/runtime.*` 能反映最近一次 build/flash/verify 状态。
- [ ] `.project_structure` 可重新生成且校验通过。
- [ ] `.agents/skills/` 是 Skill 源，`.claude/skills/` 是兼容镜像。
- [ ] 每次改动都有日志记录。
- [ ] 每次改动先暂存，验证可用后再提交。
