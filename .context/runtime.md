# Runtime Context

The workflow kit is not connected to a concrete firmware project yet.

Current status:

- Build: not configured
- Flash: not configured
- Verify: not configured
- Serial: unconfigured

After adopting this workflow into a project, update `.workflow/project.yaml`, run the configured build/flash/verify flow, then refresh runtime context with:

```bash
python tools/context.py touch-runtime
```

Historical notes belong in `PROJECT_LOG.md` and `EVOLUTION.md`; this file is only the current handoff snapshot.
