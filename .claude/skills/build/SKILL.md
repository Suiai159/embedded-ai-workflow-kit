---
name: build
description: Compile the Keil project (MDK-ARM/very_test.uvprojx) using tools/build_keil.sh
user-invocable: true
---

# /build — Compile Keil Project

Compile the Keil project by executing `tools/build_keil.sh`.

## Project Structure

- **Project file:** `MDK-ARM/very_test.uvprojx`
- **Build script:** `tools/build_keil.sh`
- **Build log:** `tools/build_log.txt`
- **Output:** `MDK-ARM/very_test/very_test.hex`

## Steps

### 1. Execute Build

Run: `bash tools/build_keil.sh`

### 2. Analyze Result

**If build SUCCESS:**
- Show hex file size
- Stop here

**If build FAILED:**
- Read `tools/build_log.txt`
- Analyze errors and attempt fixes

### 3. Auto-Fix Patterns

- Syntax errors (missing semicolons, brackets)
- Undefined variables/functions
- Missing includes
- Type mismatches

### 4. Retry

After fixes, re-run build script.

## Expected Output

- Build log
- Success/failure status
- Fix summary (if any changes made)
