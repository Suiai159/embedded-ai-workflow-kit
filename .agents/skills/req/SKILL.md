---
name: req
description: Convert user intent into the project requirement file without assuming board, MCU, architecture, or toolchain facts. Use when requirements need to be created or normalized before design, code, review, build, or verify.
user-invocable: true
---

# /req

Update `需求.md` as the requirement source for the adopting project.

## Rules

- Do not treat conversation history as the durable requirement.
- Do not invent hardware facts. Mark unknowns explicitly.
- If architecture, board, MCU, or toolchain choices are required, list them as open questions.
- Keep verification expectations testable.
- Update `PROJECT_LOG.md` after changing requirements.
