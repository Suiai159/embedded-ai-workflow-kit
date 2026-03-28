---
name: flash
description: Flash the compiled Keil project to STM32 using tools/flash_keil.sh
user-invocable: true
---

# /flash — Flash Keil Project to STM32

Flash the compiled program to STM32 MCU.

## Project Structure

- **Build script:** `tools/build_keil.sh`
- **Flash script:** `tools/flash_keil.sh`
- **Hex file:** `MDK-ARM/very_test/very_test.hex`

## Steps

1. Check if hex file exists
2. Run: `bash tools/flash_keil.sh`

## Prerequisites

- Project must be compiled first
- DAP/ST-Link debugger connected

## Expected Output

- Flash progress log
- Erase/Programming/Verify status
- Success/failure result
