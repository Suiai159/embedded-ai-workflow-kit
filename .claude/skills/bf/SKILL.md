---
name: bf
description: Build and Flash Keil project — compile then download to STM32
user-invocable: true
---

# /bf — Build and Flash Keil Project

Compile the project, then flash to STM32 if build succeeds.

## Steps

1. Execute `bash tools/build_keil.sh` to compile
2. If build successful, execute `bash tools/flash_keil.sh`
3. If build failed, stop and report error

## Expected Output

- Build log with error/warning count
- Flash progress and result
- Combined success/failure status
