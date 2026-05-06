# Engineering Context

This file is the human-readable handoff note for the project architecture. The machine-readable companion is `.context/engineering.yaml`.

## What This Project Is

This repository is an embedded STM32 template with reusable AI-assisted workflow tooling. The source tree intentionally separates generated platform code from hand-maintained application logic.

The workflow and layout facts live in `.workflow/project.yaml`. Do not duplicate tool paths or project output paths in Agent prompts, Skills, or tool-specific adapters.

## Architecture Rules

- `App/`, `Service/`, and `Driver/` are project framework layers. They are not owned by Windows/Linux, Keil/GCC/CMake, or a specific AI Agent.
- Toolchain and host-platform changes must be handled through `.workflow/project.yaml`, `tools/workflow.py`, and platform adapter code.
- MCU or board migration may change `Driver/` internals and HAL bindings, but it must not change the App/Service/Driver dependency contract.
- Dependency direction is `App -> Service -> Driver -> HAL`.
- `App/` must not include STM32 HAL headers or call Driver APIs directly.
- `Service/` owns feature-level behavior and may call Driver APIs.
- `Driver/` may wrap HAL/register access but must not include Service or App headers.
- `Core/` and `Drivers/` are treated as CubeMX/vendor generated areas.

## Directory Boundary

These directories are part of the project framework and should move together when this template is reused:

| Directory | Stable meaning |
|-----------|----------------|
| `App/` | Application behavior and business logic |
| `Service/` | Hardware feature abstraction and orchestration |
| `Driver/` | Project-owned driver APIs and low-level wrappers |
| `Test/` | Firmware test code |
| `docs/` | Project knowledge base and reference notes |
| `.context/` | AI handoff facts |
| `.workflow/` | Tool/layout configuration source |
| `.agents/` | Agent-neutral workflow assets and canonical Skills |
| `tools/` | Deterministic workflow commands and adapters |
| `reports/` | Current report and evidence snapshots |

These areas are platform, vendor, IDE, or local adapter boundaries:

| Directory or file | Variable meaning |
|-------------------|------------------|
| `Core/` | CubeMX/generated startup and HAL glue |
| `Drivers/` | Vendor HAL/CMSIS packages |
| `MDK-ARM/` | Keil project adapter artifacts |
| `.vscode/` | Local editor settings |
| `.claude/` | Optional Claude/Codex workflow adapter |
| `very_test.ioc` | CubeMX hardware/platform source |

Changing host OS, compiler, debugger, IDE, or AI Agent should not move the project framework directories. Put that variation into `.workflow/project.yaml`, `tools/workflow.py`, or a platform adapter.

## Current Initialization Reality

The ideal rule says `System_Init()` should initialize drivers first, then services, then apps. Current code partially violates that ideal because `LOG_Service_Init()`, `LED_Service_Init()`, and `PWM_Service_Init()` call lower-layer init functions internally.

AI should not silently "fix" this while doing unrelated work. Treat it as a known architecture debt unless the task is explicitly about initialization cleanup.

## AI Handoff Rule

Before changing code, read:

1. `AGENTS.md`
2. `.context/engineering.yaml`
3. `.context/hardware.yaml`
4. `.context/version.yaml`
5. `.context/runtime.yaml`
6. `.agents/rules/entrypoints.md`
7. `.agents/rules/git.md`
8. `.agents/rules/logging.md`
9. `.workflow/project.yaml`
10. `需求.md`

Conversation history is not a substitute for these files.

## Git Handoff Rule

Any Agent that changes files must use git as part of the work:

1. Run `python tools/git_guard.py status` before editing.
2. Review diffs after editing.
3. Stage only task-owned files as a checkpoint.
4. Commit after validation passes unless the user explicitly says not to commit.

The detailed rule is `.agents/rules/git.md`.

## Logging Rule

Any Agent that changes files must update durable logs:

- `PROJECT_LOG.md` for daily project work, validation, blockers, and next actions.
- `EVOLUTION.md` for framework, rule, Skill, tool, layout, or architecture-policy changes.

The detailed rule is `.agents/rules/logging.md`.
