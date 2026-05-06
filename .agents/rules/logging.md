# Mandatory Logging Policy

Project memory is part of the deliverable. Agents must record meaningful work without waiting for the user to ask.

## Required Sequence

Any Agent that changes files must:

1. Decide whether the change is daily project work, structural workflow evolution, or both.
2. Update `PROJECT_LOG.md` for task progress, verification results, blockers, and next steps.
3. Update `EVOLUTION.md` for reusable framework changes, rule changes, Skill changes, tool changes, layout changes, or architecture policy changes.
4. Keep reports in `reports/` and summarize durable conclusions in logs.
5. Stage log updates with the code/rule/tool changes they explain.

## What Goes Where

| File | Use for |
|------|---------|
| `PROJECT_LOG.md` | Current task progress, validation results, blockers, runtime observations, next actions |
| `EVOLUTION.md` | Reusable template/framework evolution, Agent rules, Skills, tools, directory policy, architecture policy |
| `reports/` | Current evidence snapshots from tools, overwritten by default |
| `.context/runtime.*` | Current handoff state only, not history |

## Guard Commands

Use the helper when possible:

```bash
python tools/log_guard.py status
python tools/log_guard.py validate --mode either
python tools/log_guard.py validate --mode both
```

Use `--mode both` for framework/tool/rule changes. Use `--mode project` for normal feature work. Use `--mode evolution` for pure template changes.
