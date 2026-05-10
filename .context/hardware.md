# Hardware Context

No board or MCU is bundled with this workflow kit.

When the workflow is copied into a concrete embedded project, fill `.context/hardware.yaml` with:

- MCU family, exact device, core, clock tree
- Board name and hardware revision
- GPIO, timer, UART/SPI/I2C/ADC/DMA resources
- Resource ownership
- Signal polarity
- Verified hardware behavior
- Evidence paths for schematics, datasheets, or measurements

Do not infer these facts from conversation history.
