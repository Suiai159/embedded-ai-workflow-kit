# Agent Assets

This directory is the agent-neutral home for AI workflow assets.

## Layout

| Path | Role |
|------|------|
| `.agents/rules/` | Canonical Agent rules shared by all AI tools |
| `.agents/skills/` | Canonical reusable Skill definitions |
| `.agents/manifest.yaml` | Registry of canonical workflow assets |

## Rules

- Edit `.agents/skills/` first.
- Edit `.agents/rules/` for reusable Agent policy.
- Keep deterministic actions in `tools/`; Skills should describe workflow and call tools.
- Keep project facts in `.context/` and tool/layout config in `.workflow/project.yaml`.
- Do not put build, flash, verify, or review reports here. Reports belong in `reports/`.
- Agents that modify files must update the appropriate log files.
- Agents should stage coherent checkpoints, validate them, then commit when usable unless the user explicitly says not to.

Useful commands:

```bash
python tools/agent_assets.py validate
```

Useful adoption Skill:

- `/project-port`: guide an Agent/user Q&A flow for configuring this workflow kit inside a real embedded project.
