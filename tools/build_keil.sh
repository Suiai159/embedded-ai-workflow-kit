#!/bin/bash
# Compatibility wrapper for the reusable workflow CLI.
# Usage: bash tools/build_keil.sh [--test]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
else
    PYTHON_BIN="python"
fi

if [ "$1" = "--test" ]; then
    "$PYTHON_BIN" tools/workflow.py build --test
else
    "$PYTHON_BIN" tools/workflow.py build
fi
