# Reports Directory

`reports/` is the current evidence snapshot directory.

Rules:

- All Agent, Skill, and script reports must be written under `reports/`.
- Each report type uses a stable file name and overwrites the previous run.
- Do not create timestamped report files by default.
- Historical summaries belong in `PROJECT_LOG.md`.
- Structural workflow changes belong in `EVOLUTION.md`.
- Only create `reports/archive/` when a user explicitly asks to preserve a past report.

Allowed current-snapshot files:

| File | Owner |
|------|-------|
| `build_log.txt` | `tools/workflow.py build` |
| `flash_log.txt` | `tools/workflow.py flash` |
| `check_req_report.md` | `/check-req` |
| `code_review_report.md` | `/code-reviewer` |
| `verify_report.md` | `/verify` |
| `register_driver_log.txt` | `tools/workflow.py register-driver` when command adapter is used |
