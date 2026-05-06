---
name: build
description: Build the configured embedded project through tools/workflow.py. Use for compiling firmware regardless of the board name or development tool; adapters include Keil, GCC command, and CMake.
user-invocable: true
---

# /build

Build the project described by `.workflow/project.yaml`.

## Steps

1. Run `python tools/context.py validate`; if it fails, show the missing/stale context and stop.
2. Run `python tools/context.py summary` and use it as the project handoff facts.
3. Run `skill: check-req` before building.
4. If requirement consistency passes, run `python tools/workflow.py build`.
5. If the user requests test firmware, run `python tools/workflow.py build --test`.
6. Read the configured build log from `.workflow/project.yaml` when the build fails.
7. `tools/workflow.py` refreshes `.context/runtime.yaml` after build.

## Rules

- Do not hard-code project names, board names, Keil paths, or hex paths.
- Treat `tools/workflow.py` as the build adapter boundary.
- Supported adapters: `toolchain.type: keil`, `gcc`, and `cmake`.
