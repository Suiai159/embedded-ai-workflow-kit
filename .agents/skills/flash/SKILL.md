---
name: flash
description: Flash the configured embedded firmware through tools/workflow.py. Use for downloading compiled firmware without hard-coding board, hex, or tool paths; supports Keil and generic command flashing.
user-invocable: true
---

# /flash

Flash the firmware artifact described by `.workflow/project.yaml`.

## Steps

1. Confirm the configured hex exists, or ask the user to run `/build`.
2. Run `python tools/workflow.py flash`.
3. Read the configured flash log when flashing fails.

## Rules

- Do not hard-code the hex path, project name, board name, or debugger.
- Treat `tools/workflow.py` as the flashing adapter boundary.
