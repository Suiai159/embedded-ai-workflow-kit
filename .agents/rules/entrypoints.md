# Agent Rule Entrypoints

Root-level Agent files are discovery shims. Keep them short enough for tools to find and read quickly.

## Canonical Location

Canonical Agent rules live under `.agents/rules/`.

| Path | Role |
|------|------|
| `AGENTS.md` | Generic root entrypoint for any AI Agent |
| `.agents/rules/entrypoints.md` | Rule-file placement and discovery policy |
| `.agents/rules/git.md` | Mandatory git save and commit policy |
| `.agents/skills/` | Canonical reusable Skills |

## Rules

- Keep root entrypoints as high-signal summaries.
- Put reusable Agent policy in `.agents/rules/`.
- Put reusable workflow Skills in `.agents/skills/`.
- Put deterministic commands in `tools/`.
- Put project facts in `.context/`.
- Put toolchain and layout configuration in `.workflow/project.yaml`.
- Do not make any tool-specific Agent directory the canonical home for project rules or Skills.
