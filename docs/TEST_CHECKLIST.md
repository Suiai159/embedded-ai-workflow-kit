# Workflow Kit Test Checklist

Use this checklist after changing the workflow kit or after copying it into a concrete project.

## 1. Unconfigured Kit Checks

- [ ] Confirm the repository does not require user architecture directories.
  ```bash
  python tools/context.py validate
  ```
  Expected: passes with `workflow_kit` mode.

- [ ] Confirm workflow config is generic.
  ```bash
  python tools/workflow.py verify-config
  ```
  Expected: `toolchain: none` and a message telling the user to configure the project before build/flash.

- [ ] Confirm structure snapshot can be generated.
  ```bash
  python tools/workflow.py structure
  python tools/workflow.py structure --check
  ```

- [ ] Confirm Agent assets are valid.
  ```bash
  python tools/agent_assets.py validate
  ```

- [ ] Confirm Python tools compile.
  ```bash
  python -m py_compile tools/context.py tools/workflow.py tools/agent_assets.py tools/git_guard.py tools/log_guard.py tools/project_structure.py tools/dev_orchestrator.py
  ```

## 2. No Default Project Binding

- [ ] No required `App/`, `Service/`, `Driver/`, or `Test/` directory.
- [ ] No required `Core/`, `Drivers/`, `MDK-ARM/`, `.ioc`, or `.claude/` directory.
- [ ] `.workflow/project.yaml` does not point to a real board, MCU, Keil path, or project file.
- [ ] `.context/hardware.yaml` has no board-specific resources until configured by a project.
- [ ] `.context/version.yaml` has no generated firmware boundary until configured by a project.

## 3. Test Interface

- [ ] The kit does not create a default `Test/` folder.
- [ ] `.workflow/project.yaml` keeps configurable test hooks:
  - `build.test_command`
  - `verify.command`
  - `verify.report_path`
  - `layout.tests`
- [ ] Verify reports still go to `reports/verify_report.md`.

## 4. Reports

- [ ] `reports/README.md` exists.
- [ ] Reports use fixed overwrite paths:
  - `reports/build_log.txt`
  - `reports/flash_log.txt`
  - `reports/check_req_report.md`
  - `reports/code_review_report.md`
  - `reports/verify_report.md`

## 5. Git And Logging

- [ ] Check current git state.
  ```bash
  python tools/git_guard.py status
  ```

- [ ] Any change updates logs.
  ```bash
  python tools/log_guard.py validate --mode either
  ```

- [ ] Framework changes update both logs.
  ```bash
  python tools/log_guard.py validate --mode both
  ```

- [ ] Stage only task-owned files.
  ```bash
  python tools/git_guard.py stage --paths <task-owned-files>
  ```

- [ ] Commit only after validation passes.

## 6. Concrete Project Adoption Checks

After copying the workflow kit into a real project:

- [ ] Fill `.workflow/project.yaml`.
- [ ] Fill `.context/engineering.yaml` with the project's architecture.
- [ ] Fill `.context/hardware.yaml` with board/MCU/resource facts.
- [ ] Fill `.context/version.yaml` with toolchain/generated-boundary facts.
- [ ] Run:
  ```bash
  python tools/context.py validate
  python tools/workflow.py verify-config
  python tools/workflow.py structure
  ```
- [ ] Run configured build/test/flash commands.
- [ ] Confirm runtime context and reports update.
