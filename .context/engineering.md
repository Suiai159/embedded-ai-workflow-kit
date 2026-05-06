# Engineering Context

This file is the human-readable handoff note for the project architecture. The machine-readable companion is `.context/engineering.yaml`.

## What This Project Is

This repository is an embedded STM32 template with reusable AI-assisted workflow tooling. The source tree intentionally separates generated platform code from hand-maintained application logic.

The workflow and layout facts live in `.workflow/project.yaml`. Do not duplicate tool paths or project output paths in Skills.

## Architecture Rules

- Dependency direction is `App -> Service -> Driver -> HAL`.
- `App/` must not include STM32 HAL headers or call Driver APIs directly.
- `Service/` owns feature-level behavior and may call Driver APIs.
- `Driver/` may wrap HAL/register access but must not include Service or App headers.
- `Core/` and `Drivers/` are treated as CubeMX/vendor generated areas.

## Current Initialization Reality

The ideal rule says `System_Init()` should initialize drivers first, then services, then apps. Current code partially violates that ideal because `LOG_Service_Init()`, `LED_Service_Init()`, and `PWM_Service_Init()` call lower-layer init functions internally.

AI should not silently "fix" this while doing unrelated work. Treat it as a known architecture debt unless the task is explicitly about initialization cleanup.

## AI Handoff Rule

Before changing code, read:

1. `.context/engineering.yaml`
2. `.context/hardware.yaml`
3. `.context/version.yaml`
4. `.context/runtime.yaml`
5. `.workflow/project.yaml`
6. `需求.md`

Conversation history is not a substitute for these files.
