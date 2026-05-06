---
name: bf
description: Build and flash the configured embedded project through the reusable workflow CLI.
user-invocable: true
---

# /bf

Build the configured project, then flash it if the build succeeds.

## Steps

1. Run `python tools/workflow.py build`.
2. If the build succeeds, run `python tools/workflow.py flash`.
3. If either step fails, read the configured log path from `.workflow/project.yaml` and report the useful error lines.
