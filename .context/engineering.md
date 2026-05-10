# Engineering Context

This repository is an agent-neutral embedded workflow kit, not a configured firmware project.

## What Is Stable

The reusable workflow consists of:

| Path | Role |
|------|------|
| `AGENTS.md` | Generic Agent entry point |
| `.agents/` | Agent rules and canonical Skills |
| `.context/` | AI handoff facts |
| `.workflow/` | Workflow/project configuration |
| `tools/` | Deterministic commands and adapters |
| `docs/` | Workflow documentation |
| `reports/` | Current evidence snapshots |

These paths should be copied into a concrete project as the workflow kit.

## What Is Not Bundled

The kit intentionally does not ship:

- Default application architecture directories such as `App/`, `Service/`, or `Driver/`
- A default `Test/` directory
- CubeMX generated code
- Keil/CMake/GCC project files
- Board, MCU, pin, clock, or peripheral facts
- Tool-specific Agent mirrors such as `.claude/`

The adopting project must declare those facts in `.workflow/project.yaml` and `.context/*`.

## Architecture Rule

The workflow does not mandate a specific architecture. It only requires that a concrete project records:

1. Architecture directories
2. Dependency direction
3. Ownership boundaries
4. Generated/vendor/tool boundaries
5. Test entry points

For this unconfigured kit, architecture is intentionally empty.

## Test Interface

The workflow keeps test and verify interfaces because embedded development should make testing a first-class path. The kit does not create a default `Test/` folder; a project can map tests to any directory or command through `.workflow/project.yaml`.

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

## Git And Logging

Any Agent that changes files must:

1. Run `python tools/git_guard.py status` before editing.
2. Update `PROJECT_LOG.md` and/or `EVOLUTION.md`.
3. Stage only task-owned files as a checkpoint.
4. Validate the checkpoint.
5. Commit after validation passes unless the user explicitly says not to commit.
