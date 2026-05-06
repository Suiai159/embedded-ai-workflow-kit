#!/usr/bin/env python3
"""
Driver Dev Tool - 外设驱动开发辅助工具
自动管理 Keil 工程文件注册
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

from workflow import cfg_get, find_project_root, load_config

# 修复 Windows 终端编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

PROJECT_ROOT = find_project_root()
CONFIG = load_config(PROJECT_ROOT)
DRIVER_REL_DIR = Path(str(cfg_get(CONFIG, "layout.driver", "Driver")))
TEST_REL_DIR = Path(str(cfg_get(CONFIG, "layout.test", "Test")))
DRIVER_DIR = PROJECT_ROOT / DRIVER_REL_DIR
TEST_DIR = PROJECT_ROOT / TEST_REL_DIR

def ensure_directories():
    """确保目录存在"""
    DRIVER_DIR.mkdir(parents=True, exist_ok=True)
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✅ 目录检查: {DRIVER_REL_DIR}, {TEST_REL_DIR}")

def add_to_keil(driver_name):
    """将驱动和测试代码添加到配置声明的工程文件"""
    workflow = PROJECT_ROOT / "tools" / "workflow.py"
    result = subprocess.run(
        [sys.executable, str(workflow), "register-driver", "--name", driver_name],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode == 0

def generate_skeleton(driver_name, interface):
    """生成驱动和测试代码的骨架文件（如果还不存在）"""
    driver_h = DRIVER_DIR / f"{driver_name}_driver.h"
    driver_c = DRIVER_DIR / f"{driver_name}_driver.c"
    test_c = TEST_DIR / f"{driver_name}_driver_test.c"

    if not driver_h.exists():
        header = f"""#ifndef __{driver_name.upper()}_DRIVER_H
#define __{driver_name.upper()}_DRIVER_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {{
#endif

/* {driver_name} Driver - Interface: {interface} */

int {driver_name}_Driver_Init(void);
int {driver_name}_Driver_DeInit(void);

/* TODO: Add read/write/control APIs */

#ifdef __cplusplus
}}
#endif

#endif /* __{driver_name.upper()}_DRIVER_H */
"""
        driver_h.write_text(header, encoding='utf-8')
        print(f"📝 生成骨架: {driver_h}")

    if not driver_c.exists():
        source = f"""#include "{driver_name}_driver.h"

/* {driver_name} Driver Implementation */
/* Interface: {interface} */

int {driver_name}_Driver_Init(void)
{{
    /* TODO: Initialize {interface} peripheral and device */
    return 0;
}}

int {driver_name}_Driver_DeInit(void)
{{
    /* TODO: De-initialize */
    return 0;
}}
"""
        driver_c.write_text(source, encoding='utf-8')
        print(f"📝 生成骨架: {driver_c}")

    if not test_c.exists():
        test = f"""#include "{driver_name}_driver.h"
#include <stdio.h>

/* {driver_name} Driver Test */

void {driver_name}_Driver_Test(void)
{{
    printf("[{driver_name}] Starting driver test...\\r\\n");

    if ({driver_name}_Driver_Init() != 0) {{
        printf("[{driver_name}] Init failed!\\r\\n");
        return;
    }}

    /* TODO: Add test cases */

    printf("[{driver_name}] Test completed.\\r\\n");
}}
"""
        test_c.write_text(test, encoding='utf-8')
        print(f"📝 生成骨架: {test_c}")

def main():
    parser = argparse.ArgumentParser(description="Driver Dev Tool")
    parser.add_argument("--name", "-n", required=True, help="驱动名称，如 st7789")
    parser.add_argument("--interface", "-i", default="", help="通信接口，如 SPI/I2C/UART")
    parser.add_argument("--add-to-keil", action="store_true", help="注册到当前配置声明的工程（兼容旧参数名）")
    parser.add_argument("--skeleton", action="store_true", help="生成骨架文件")

    args = parser.parse_args()

    driver_name = args.name.lower().replace(" ", "_")

    ensure_directories()

    if args.skeleton:
        generate_skeleton(driver_name, args.interface)

    if args.add_to_keil:
        if not add_to_keil(driver_name):
            return 1

    # 打印总结
    print(f"\n📋 驱动开发准备完成:")
    print(f"   驱动头文件: {DRIVER_REL_DIR}/{driver_name}_driver.h")
    print(f"   驱动源文件: {DRIVER_REL_DIR}/{driver_name}_driver.c")
    print(f"   测试代码  : {TEST_REL_DIR}/{driver_name}_driver_test.c")
    if args.add_to_keil:
        print(f"   工程注册  : 已处理")

    return 0

if __name__ == '__main__':
    sys.exit(main())
