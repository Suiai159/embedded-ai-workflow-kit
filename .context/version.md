# Version Context

This repository is currently an unconfigured workflow kit.

## Active Toolchain

No build adapter is active by default.

Available adapter implementations live in `tools/workflow.py`:

- `gcc`
- `cmake`
- `keil`

A concrete project must choose and configure one in `.workflow/project.yaml`.

## Generated Code Boundary

No generated firmware code is bundled with the kit.

Treat these as human-maintained workflow assets:

- `AGENTS.md`
- `.agents/`
- `.context/`
- `.workflow/`
- `docs/`
- `reports/README.md`
- `tools/`

Generated code, IDE files, vendor libraries, CubeMX output, and tool-specific Agent mirrors should be added by the adopting project only when they are actually used.
