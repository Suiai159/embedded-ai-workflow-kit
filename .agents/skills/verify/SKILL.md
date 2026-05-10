---
name: verify
description: Run the configured project verification flow through .workflow/project.yaml and tools/workflow.py. Use when an Agent needs to build test firmware/targets, run a project-defined verify command, capture reports under reports/, and update runtime context without assuming a board, MCU, IDE, serial protocol, or test directory.
user-invocable: true
---

# /verify

Verify the concrete project described by `.workflow/project.yaml`.

## Steps

1. Run `python tools/context.py validate`.
2. Run `python tools/context.py summary`.
3. Read `.workflow/project.yaml`.
4. If `verify.command` is configured, run it exactly as the project adapter command.
5. Otherwise, run `python tools/workflow.py build --test` if `build.test_command` or a toolchain test target is configured.
6. Ensure verification evidence is written to `reports/verify_report.md` or the configured `verify.report_path`.
7. Run `python tools/context.py touch-runtime`.
8. Update `PROJECT_LOG.md` with the result.

## Rules

- Do not assume a `Test/` directory exists.
- Do not assume STM32, CubeMX, Keil, OpenOCD, serial JSON, or a specific board.
- Do not invent hardware facts. Use `.context/hardware.yaml`.
- Do not scatter reports outside `reports/`.
- If the project has no verify command or test build configured, stop with a clear configuration message.
