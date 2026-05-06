# Agent Assets

This directory is the agent-neutral home for AI workflow assets.

## Layout

| Path | Role |
|------|------|
| `.agents/rules/` | Canonical Agent rules shared by all AI tools |
| `.agents/skills/` | Canonical reusable Skill definitions |
| `.agents/manifest.yaml` | Registry of canonical assets and compatibility mirrors |
| `.claude/skills/` | Compatibility mirror for Claude/Codex-style Skill discovery |

## Rules

- Edit `.agents/skills/` first.
- Edit `.agents/rules/` for reusable Agent policy.
- Treat `.claude/skills/` as a generated or synchronized compatibility mirror.
- Keep deterministic actions in `tools/`; Skills should describe workflow and call tools.
- Keep project facts in `.context/` and tool/layout config in `.workflow/project.yaml`.
- Do not put build, flash, verify, or review reports here. Reports belong in `reports/`.
- Agents that modify files must update the appropriate log files.
- Agents should stage coherent checkpoints, validate them, then commit when usable unless the user explicitly says not to.

Useful commands:

```bash
python tools/agent_assets.py validate
python tools/agent_assets.py sync-skills --target claude
```
