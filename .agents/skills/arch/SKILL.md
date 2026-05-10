---
name: arch
description: Plan or update the adopting project's architecture using requirements and .context facts. Use when defining modules, directories, dependency rules, ownership, initialization order, or test strategy without assuming a default App/Service/Driver layout.
user-invocable: true
---

# /arch

Plan architecture for the concrete project using this workflow.

## Inputs

- `需求.md`
- `.context/engineering.yaml`
- `.context/hardware.yaml`
- `.workflow/project.yaml`

## Steps

1. Validate context with `python tools/context.py validate`.
2. Read the current requirement file.
3. Identify missing architecture, hardware, toolchain, or test facts.
4. Propose architecture directories and dependency rules for this project.
5. Update `.context/engineering.yaml` when the user accepts the architecture.
6. Regenerate `.project_structure`:
   ```bash
   python tools/workflow.py structure
   ```
7. Update `PROJECT_LOG.md` and `EVOLUTION.md` when workflow structure changes.

## Rules

- Do not assume App/Service/Driver.
- Do not create architecture directories until the project declares them.
- Keep workflow directories separate from project architecture directories.
- Keep testing as an explicit part of the architecture, even if the project has no `Test/` directory.
