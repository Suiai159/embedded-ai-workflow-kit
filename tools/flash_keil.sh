#!/bin/bash
# Flash Keil Project Script
# Usage: bash tools/flash_keil.sh

set -e

# Configuration
PROJECT_NAME="very_test"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 路径配置
PROJECT_FILE="${PROJECT_DIR}/MDK-ARM/${PROJECT_NAME}.uvprojx"
LOG_FILE="${SCRIPT_DIR}/flash_log.txt"
HEX_FILE="${PROJECT_DIR}/MDK-ARM/${PROJECT_NAME}/${PROJECT_NAME}.hex"

# Keil 路径
UV4="D:/Keil5/UV4/UV4.exe"

# 检查 Keil
if [ ! -f "$UV4" ]; then
    echo "Error: Keil not found at $UV4"
    exit 1
fi

# 检查 hex 文件
if [ ! -f "$HEX_FILE" ]; then
    echo "Error: Hex file not found. Please build first."
    echo "Expected: $HEX_FILE"
    exit 1
fi

# 转换为 Windows 路径
WIN_PROJECT=$(cygpath -w "$PROJECT_FILE")
WIN_LOG=$(cygpath -w "$LOG_FILE")

echo "Flashing ${PROJECT_NAME} to STM32..."

# 清空旧日志
> "$LOG_FILE"

# 使用 PowerShell 静默烧录，完全隐藏 GUI
powershell.exe -ExecutionPolicy Bypass -Command "
    \$psi = New-Object System.Diagnostics.ProcessStartInfo;
    \$psi.FileName = '${UV4}';
    \$psi.Arguments = '-f \"${WIN_PROJECT}\" -j0 -o \"${WIN_LOG}\"';
    \$psi.WindowStyle = 'Hidden';
    \$psi.CreateNoWindow = \$true;
    \$psi.UseShellExecute = \$false;
    \$proc = [System.Diagnostics.Process]::Start(\$psi);
    \$proc.WaitForExit();
    exit \$proc.ExitCode;
"

FLASH_RESULT=$?

# 打印日志
echo ""
echo "Flash Log:"
echo "================================"
cat "$LOG_FILE"
echo "================================"

if [ $FLASH_RESULT -eq 0 ]; then
    echo ""
    echo "Flash successful!"
    exit 0
else
    echo ""
    echo "Flash failed! Check log above for details."
    exit 1
fi
