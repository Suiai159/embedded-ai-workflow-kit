# Mandatory Git Policy

Git is part of the engineering workflow, not an optional cleanup step.

## Required Sequence

Any Agent that changes files must:

1. Run `git status --short` before editing and identify pre-existing dirty files.
2. Avoid reverting or staging unrelated user changes.
3. After edits, run the relevant validation commands.
4. Run `git diff` or an equivalent scoped diff review.
5. Stage only files changed for the current task.
6. Create a git commit before final handoff, unless the user explicitly says not to commit.
7. Mention the commit hash and remaining unstaged files in the final response.

## Guard Commands

Use the helper when possible:

```bash
python tools/git_guard.py status
python tools/git_guard.py pre-final
python tools/git_guard.py commit --message "type: concise summary" --paths <file-or-dir>...
```

`pre-final` fails while tracked or untracked changes remain outside a commit. If the user explicitly asks to pause before commit, say that clearly and leave the worktree status in the handoff.

## Commit Rules

- Commit messages should be concise and describe the engineering change.
- Do not commit generated build artifacts unless they are intentionally tracked project files.
- Do not stage local settings such as `.claude/settings.local.json`.
- Do not stage unrelated generated files such as dependency `.d` files unless the task explicitly owns them.
- If a command cannot commit because of permissions, request approval for the git command rather than leaving changes uncommitted.
