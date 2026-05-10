---
name: project-port
description: Interactively port or adopt this embedded workflow kit into a real project. Use when the user wants an Agent-guided question-and-answer migration that fills .workflow/project.yaml, .context/*.yaml, project structure, build/flash/verify/test interfaces, hardware facts, version facts, and runtime handoff state without assuming a default architecture, board, IDE, or Test directory.
---

# /project-port

Guide the user through adopting the workflow kit into a concrete embedded project.

## Contract

- Do not assume `App/Service/Driver`, `src/include`, `Test`, CubeMX, Keil, GCC, CMake, OpenOCD, STM32, or any other platform fact.
- Ask concise question batches. Prefer 3 to 6 questions per round.
- Treat missing facts as `unknown` or `unconfigured`; do not invent them.
- Do not create project architecture or test directories unless the user explicitly asks.
- Keep tests as an interface even when the project has no test directory.
- Update machine-readable YAML first, then human-readable Markdown summaries.
- Run validation after each completed adoption pass.

## Preflight

1. Run `python tools/git_guard.py status`.
2. Run `python tools/context.py summary` if context exists.
3. Inspect `.workflow/project.yaml` and `.context/*.yaml`.
4. Explain whether the current repo is still `workflow_kit` mode or already configured.

## Question Rounds

Collect the minimum facts needed to make the workflow usable. Stop and write files only after the user has answered enough to avoid guessing.

### Round 1: Project Shape

Ask for:

- Project name.
- Existing source/layout directories.
- Architecture layers and dependency direction, if any.
- Generated/vendor/tool-owned directories.
- Whether there is an existing test directory or only a test command.

### Round 2: Build And Toolchain

Ask for:

- `toolchain.type`: `gcc`, `cmake`, `keil`, or another adapter plan.
- Build command or CMake settings.
- Test build command, if available.
- Expected artifact paths: ELF, HEX, BIN, or other.
- Build log path, defaulting to `reports/build_log.txt`.

### Round 3: Flash And Verify

Ask for:

- Flash method and command, or whether flashing is currently manual.
- Flash artifact path.
- Flash log path, defaulting to `reports/flash_log.txt`.
- Verify command, serial port, baudrate, and expected evidence format if available.
- Verify report path, defaulting to `reports/verify_report.md`.

### Round 4: Hardware Facts

Ask for:

- Board name.
- MCU family and exact device.
- Clock source and frequency.
- Used peripherals, pins, signal polarity, and ownership.
- Known hardware behaviors already verified.

### Round 5: Version And Runtime

Ask for:

- Compiler, CMake, build system, IDE, debugger, programmer, and firmware library versions.
- Generated code source and regeneration boundary.
- Last known build, flash, verify, and runtime status.
- Evidence paths that should be kept under `reports/`.

## File Updates

Start by clearing the template's own log history, then write project facts:

1. **Reset `EVOLUTION.md`**: Replace with header only — the workflow kit's own evolution history does not belong in the new project.
2. **Reset `PROJECT_LOG.md`**: Replace with header and empty active-task section — the template's task log is not relevant.
3. Update these files when enough facts are known:

   - `.workflow/project.yaml`: project identity, adapter settings, build/flash/verify/test interfaces, reports, layout.
   - `.context/engineering.yaml` and `.context/engineering.md`: architecture, ownership, generated-code boundaries, modification rules.
   - `.context/hardware.yaml` and `.context/hardware.md`: board, MCU, clock, peripherals, pins, ownership, polarity.
   - `.context/version.yaml` and `.context/version.md`: tool versions, generated source, adapter versions.
   - `.context/runtime.yaml` and `.context/runtime.md`: current handoff state only.
   - `.project_structure`: regenerate with `python tools/project_structure.py generate`.
4. **Record the adoption** in both freshly cleared logs:
   - `PROJECT_LOG.md`: log the adoption as the first task entry.
   - `EVOLUTION.md`: log the adoption as the first structural change entry.

## Validation

Run:

```bash
python tools/context.py validate
python tools/workflow.py verify-config
python tools/agent_assets.py validate
python tools/project_structure.py generate
python tools/project_structure.py validate
python tools/log_guard.py validate --mode either
```

If a real adapter is configured, also run the safest applicable command:

```bash
python tools/workflow.py status
python tools/workflow.py build
```

Only run flash or hardware verify after the user confirms hardware is connected and safe.

## Git

Follow `.agents/rules/git.md`:

1. Stage the coherent adoption checkpoint.
2. Review the staged diff.
3. Commit after validation passes unless the user explicitly says not to commit.
