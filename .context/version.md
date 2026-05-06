# Version Context

This file records compatibility-sensitive project facts. The machine-readable companion is `.context/version.yaml`.

## Active Toolchain

The active adapter is Keil, configured in `.workflow/project.yaml`.

The last observed compiler line in `tools/build_log.txt` is:

```text
ARMCC V5.06 update 5 (build 528)
```

GCC and CMake adapters exist in `tools/workflow.py`, but this template has not been migrated to a GCC/CMake firmware project yet.

## Generated Code Boundary

Treat these as generated or tool-owned unless the task explicitly says otherwise:

- `Core/`
- `Drivers/`
- `MDK-ARM/very_test.uvprojx`
- `very_test.ioc`

Treat these as hand-maintained workflow/application areas:

- `App/`
- `Service/`
- `Driver/`
- `Test/`
- `tools/`
- `.claude/skills/`
- `.context/`
- `.workflow/`
