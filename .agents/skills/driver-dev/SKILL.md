---
name: driver-dev
description: Develop a project-specific driver or low-level module using the architecture and source/test directories declared in .context/engineering.yaml and .workflow/project.yaml. Use when generating driver/module code, tests, and optional project-file registration without assuming App/Service/Driver, Test, HAL, Keil, or a specific MCU.
user-invocable: true
---

# /driver-dev

Create driver or low-level module code for the adopting project.

## Steps

1. Run `python tools/context.py validate`.
2. Read `.context/engineering.yaml`, `.context/hardware.yaml`, and `.workflow/project.yaml`.
3. Confirm the project has declared architecture/source directories.
4. Confirm the project has declared test directories or test generation is intentionally disabled.
5. Generate code inside the declared project-owned directories.
6. If project-file registration is needed, call:
   ```bash
   python tools/workflow.py register-driver --name <name>
   ```
7. Write any generated report to `reports/`.
8. Update `PROJECT_LOG.md`.

## Rules

- Do not create a default `Driver/` directory in workflow-kit mode.
- Do not create a default `Test/` directory in workflow-kit mode.
- Do not assume HAL, Keil, STM32, CubeMX, or a specific file naming convention.
- Use resource ownership from `.context/hardware.yaml`.
- If required layout facts are missing, stop and ask the project to configure `.workflow/project.yaml` and `.context/engineering.yaml`.
