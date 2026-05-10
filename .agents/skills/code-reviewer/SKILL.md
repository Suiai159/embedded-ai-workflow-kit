---
name: code-reviewer
description: Review embedded project changes against requirements, the architecture declared in .context/engineering.yaml, hardware facts, runtime constraints, and report rules. Use for code review without assuming STM32, HAL, Keil, CubeMX, or a specific directory layout.
user-invocable: true
---

# /code-reviewer

Review code for the concrete project that adopted this workflow.

## Steps

1. Run `python tools/context.py validate`.
2. Read `.context/engineering.yaml`, `.context/hardware.yaml`, `.context/version.yaml`, and `.workflow/project.yaml`.
3. Review only the files relevant to the current task.
4. Check requirements consistency, architecture boundaries, resource ownership, blocking behavior, stack/memory risk, and test coverage.
5. Write findings to `reports/code_review_report.md`.
6. Update `PROJECT_LOG.md`.

## Rules

- Do not assume a specific HAL, MCU, IDE, or directory layout.
- Use `tools/code_reviewer_config.json` only as project-specific configuration.
- If architecture or hardware facts are missing, report the missing facts instead of guessing.
- Findings must be actionable and reference exact files/lines when possible.
