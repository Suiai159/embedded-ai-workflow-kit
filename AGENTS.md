# Agent Handoff Guide

This repository is an agent-neutral embedded workflow kit.

It is not bound to a board, MCU, IDE, toolchain, architecture layout, or Agent vendor.

## First Read Order

Before changing files, read or summarize:

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

Run:

```bash
python tools/context.py validate
python tools/context.py summary
python tools/workflow.py verify-config
python tools/git_guard.py status
python tools/log_guard.py status
```

## Core Contract

- Do not guess architecture directories, board pins, clocks, toolchain paths, or runtime status.
- Use `.context/` for project facts.
- Use `.workflow/project.yaml` for toolchain, build, flash, verify, and layout configuration.
- Use `.agents/rules/` for reusable Agent policy.
- Use `.agents/skills/` for canonical Skills.
- Use `tools/workflow.py` for deterministic build/flash/status/source-registration actions.
- Write generated reports only to `reports/` with fixed overwrite paths.
- Update `PROJECT_LOG.md` and/or `EVOLUTION.md` for meaningful changes.
- Stage coherent task-owned checkpoints, validate, then commit after validation passes.

## Architecture

The workflow kit does not mandate `App/Service/Driver`, `src/include`, or any other layout.

A concrete project must declare its architecture in `.context/engineering.yaml` and `.workflow/project.yaml`.

## Testing

The workflow keeps testing as a first-class interface, but it does not create a default `Test/` directory.

Concrete projects may configure:

- `build.test_command`
- `verify.command`
- `verify.report_path`
- `layout.tests`

## Common Commands

| Intent | Command |
|--------|---------|
| Context summary | `python tools/context.py summary` |
| Validate context | `python tools/context.py validate` |
| Validate workflow config | `python tools/workflow.py verify-config` |
| Generate structure snapshot | `python tools/workflow.py structure` |
| Build configured project | `python tools/workflow.py build` |
| Build test firmware/target | `python tools/workflow.py build --test` |
| Flash configured artifact | `python tools/workflow.py flash` |
| Validate Agent assets | `python tools/agent_assets.py validate` |
| Validate logs | `python tools/log_guard.py validate --mode either` |
| Git status | `python tools/git_guard.py status` |

In unconfigured `workflow_kit` mode, build and flash should stop with clear configuration errors.
