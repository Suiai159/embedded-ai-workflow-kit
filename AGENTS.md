# Agent Handoff Guide

This project is designed for any capable AI coding agent, not for a single vendor or tool.

`AGENTS.md` is the generic root entry point. Canonical reusable rules live under `.agents/rules/`, and canonical Skills live under `.agents/skills/`. `CLAUDE.md` and `.claude/skills/` are kept as compatibility entries for Claude Code style agents. Other agents should follow the same project facts and call the same deterministic tools.

## First Read Order

Before changing code, read or summarize these sources in order:

1. `.context/engineering.yaml`
2. `.context/hardware.yaml`
3. `.context/version.yaml`
4. `.context/runtime.yaml`
5. `.agents/rules/entrypoints.md`
6. `.agents/rules/git.md`
7. `.agents/rules/logging.md`
8. `.workflow/project.yaml`
9. `需求.md`
10. Relevant source files

Run this first when possible:

```bash
python tools/context.py validate
python tools/context.py summary
python tools/workflow.py verify-config
python tools/git_guard.py status
python tools/log_guard.py status
```

## Agent-Neutral Contract

- Do not infer board pins, signal polarity, clock rates, toolchain paths, or current runtime status from conversation history.
- Use `.context/` for project facts, `.workflow/project.yaml` for toolchain/layout configuration, `.agents/rules/` for canonical Agent rules, and `.agents/skills/` for canonical Skills.
- Use `tools/workflow.py` for build, flash, status, and source registration.
- Use `tools/context.py touch-runtime` after build, flash, or verify evidence changes.
- Write all reports and logs to fixed paths under `reports/`; overwrite current reports by default instead of creating timestamped files.
- Keep generated/vendor areas (`Core/`, `Drivers/`, `.ioc`, tool project files) separate from hand-maintained code unless the task explicitly targets generated code.
- Any Agent that changes files must update `PROJECT_LOG.md` and/or `EVOLUTION.md`. See `.agents/rules/logging.md`.
- Any Agent that changes files must stage coherent task-owned checkpoints, validate them, then commit the usable checkpoint unless the user explicitly says not to commit. See `.agents/rules/git.md`.

## Current Workflow Adapter

The repository keeps canonical Skill definitions under `.agents/skills/`. `.claude/skills/` is a compatibility mirror for agents that discover Skills from Claude-style paths.

Equivalent actions for any agent:

| Intent | Generic command or source |
|--------|---------------------------|
| Context handoff | `python tools/context.py summary` |
| Validate context | `python tools/context.py validate` |
| Build | `python tools/workflow.py build` |
| Test build | `python tools/workflow.py build --test` |
| Flash | `python tools/workflow.py flash` |
| Register driver files | `python tools/workflow.py register-driver --name <name>` |
| Query next step | `python tools/dev_orchestrator.py --query-next-step` |

## Development Rules

- Requirement-driven work starts from `需求.md`.
- `App/`, `Service/`, and `Driver/` are stable project framework layers. Do not change their responsibilities because the host OS, IDE, compiler, or AI Agent changes.
- Architecture follows `App -> Service -> Driver -> HAL/platform`.
- Toolchain and host-platform variation belongs in `.workflow/project.yaml`, `tools/workflow.py`, and platform adapters.
- MCU/board migration may change Driver internals and HAL bindings, but must preserve the App/Service/Driver public contract unless the architecture is explicitly redesigned.
- Hardware resource ownership is defined in `.context/hardware.yaml`.
- Current runtime state is defined in `.context/runtime.yaml`.
- Structural workflow changes should be recorded in `EVOLUTION.md`.

## Directory Boundary

Project-invariant directories:

| Directory | Meaning |
|-----------|---------|
| `App/` | Application behavior and business logic |
| `Service/` | Hardware feature abstraction |
| `Driver/` | Project-owned driver APIs and low-level wrappers |
| `Test/` | Firmware test code |
| `docs/` | Project knowledge base |
| `.context/` | AI handoff facts |
| `.workflow/` | Project workflow configuration |
| `.agents/` | Agent-neutral rules, workflow assets, and canonical Skills |
| `tools/` | Deterministic automation and adapters |
| `reports/` | Current evidence snapshots, overwritten by default |

Platform, tool, IDE, or local adapter areas:

| Directory or file | Meaning |
|-------------------|---------|
| `Core/` | CubeMX/generated platform code |
| `Drivers/` | Vendor HAL/CMSIS code |
| `MDK-ARM/` | Keil project adapter |
| `.vscode/` | Local editor settings |
| `.claude/` | Optional Claude/Codex Skill adapter |
| `very_test.ioc` | CubeMX hardware/platform source |

When switching Windows/Linux, Keil/GCC/CMake, OpenOCD/GDB, or AI agents, preserve the project-invariant directories and change only workflow configuration, adapters, or platform-generated areas as needed.
