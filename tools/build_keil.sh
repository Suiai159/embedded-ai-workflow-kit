#!/bin/bash
# Build Keil Project Script
# Usage: bash tools/build_keil.sh

set -e

# Configuration
PROJECT_NAME="very_test"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 路径配置
PROJECT_FILE="${PROJECT_DIR}/MDK-ARM/${PROJECT_NAME}.uvprojx"
LOG_FILE="${SCRIPT_DIR}/build_log.txt"

# Keil 路径
UV4="D:/Keil5/UV4/UV4.exe"

# 检查 Keil
if [ ! -f "$UV4" ]; then
    echo "Error: Keil not found at $UV4"
    exit 1
fi

# 检查项目
if [ ! -f "$PROJECT_FILE" ]; then
    echo "Error: Project not found at $PROJECT_FILE"
    exit 1
fi

# 转换为 Windows 路径
WIN_PROJECT=$(cygpath -w "$PROJECT_FILE")
WIN_LOG=$(cygpath -w "$LOG_FILE")

echo "Building ${PROJECT_NAME}..."

# 清空旧日志
> "$LOG_FILE"

# 使用 PowerShell 静默编译，完全隐藏 GUI
powershell.exe -ExecutionPolicy Bypass -Command "
    \$psi = New-Object System.Diagnostics.ProcessStartInfo;
    \$psi.FileName = '${UV4}';
    \$psi.Arguments = '-b \"${WIN_PROJECT}\" -j0 -o \"${WIN_LOG}\"';
    \$psi.WindowStyle = 'Hidden';
    \$psi.CreateNoWindow = \$true;
    \$psi.UseShellExecute = \$false;
    \$proc = [System.Diagnostics.Process]::Start(\$psi);
    \$proc.WaitForExit();
    exit \$proc.ExitCode;
"

# 打印日志
echo ""
echo "Build Log:"
echo "================================"
cat "$LOG_FILE"
echo "================================"

# 检查结果
if grep -q "0 Error(s)" "$LOG_FILE" 2>/dev/null; then
    HEX_FILE="${PROJECT_DIR}/MDK-ARM/${PROJECT_NAME}/${PROJECT_NAME}.hex"
    if [ -f "$HEX_FILE" ]; then
        HEX_SIZE=$(stat -c%s "$HEX_FILE" 2>/dev/null || stat -f%z "$HEX_FILE" 2>/dev/null || echo "unknown")
        echo ""
        echo "Build successful!"
        echo "Hex file: ${HEX_FILE##*/}"
        echo "Size: $HEX_SIZE bytes"
        exit 0
    fi
fi

echo ""
echo "Build failed! Check log above for details."
exit 1
