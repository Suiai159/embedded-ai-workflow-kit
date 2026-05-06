#!/bin/bash
# Compatibility wrapper for the reusable workflow CLI.
# Usage: bash tools/flash_keil.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
else
    PYTHON_BIN="python"
fi

"$PYTHON_BIN" tools/workflow.py flash
