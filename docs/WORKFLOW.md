# Workflow Rules

This workflow kit is project-neutral. It orchestrates work, but the adopting project provides architecture, hardware, toolchain, and test facts.

## Standard Flow

```text
context validate
→ requirement update
→ architecture/design update
→ code change
→ review/check
→ build
→ test/verify
→ reports/runtime update
→ log update
→ staged checkpoint
→ commit after validation
```

## Required Checks

```bash
python tools/context.py validate
python tools/workflow.py verify-config
python tools/agent_assets.py validate
python tools/log_guard.py validate --mode either
```

## Build And Flash

Use `tools/workflow.py`; do not hard-code tool commands in Agent prompts.

```bash
python tools/workflow.py build
python tools/workflow.py build --test
python tools/workflow.py flash
```

If `toolchain.type: none`, build/flash should stop with a clear configuration message.

## Testing

The workflow keeps test interfaces but does not create a default test directory.

Concrete projects can configure:

- `build.test_command`
- `verify.command`
- `layout.tests`
- `verify.report_path`

## Reports

All generated evidence goes under `reports/` with stable overwrite paths.

## Git And Logs

Agents must update durable logs, stage task-owned files, validate, then commit the usable checkpoint.
