#!/usr/bin/env python3
"""
Driver Dev Tool - 外设驱动开发辅助工具
自动管理 Keil 工程文件注册
"""

import sys
import os
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

# 修复 Windows 终端编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

PROJECT_FILE = Path("MDK-ARM/very_test.uvprojx")
DRIVER_DIR = Path("Driver")
TEST_DIR = Path("Test")

def ensure_directories():
    """确保目录存在"""
    DRIVER_DIR.mkdir(parents=True, exist_ok=True)
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✅ 目录检查: {DRIVER_DIR}, {TEST_DIR}")

def find_group(groups, name):
    """在 Groups 中查找指定 GroupName"""
    for group in groups:
        group_name = group.find("GroupName")
        if group_name is not None and group_name.text == name:
            return group
    return None

def create_file_node(filename, filepath):
    """创建 Keil 工程中的 File 节点"""
    file_node = ET.Element("File")

    fn = ET.SubElement(file_node, "FileName")
    fn.text = filename

    ft = ET.SubElement(file_node, "FileType")
    # 1=C文件, 2=汇编, 5=h文件(通常不用加入编译组)
    ft.text = "1" if filename.endswith(".c") else "5"

    fp = ET.SubElement(file_node, "FilePath")
    fp.text = filepath

    return file_node

def add_file_to_group(groups, group_name, filename, filepath):
    """添加文件到指定 Group，如果已存在则跳过"""
    group = find_group(groups, group_name)

    if group is None:
        # 创建新 Group
        group = ET.SubElement(groups, "Group")
        gn = ET.SubElement(group, "GroupName")
        gn.text = group_name
        files_node = ET.SubElement(group, "Files")
        print(f"🆕 新建 Group: {group_name}")
    else:
        files_node = group.find("Files")
        if files_node is None:
            files_node = ET.SubElement(group, "Files")

        # 检查是否已存在
        for f in files_node.findall("File"):
            fp = f.find("FilePath")
            if fp is not None and fp.text == filepath:
                print(f"⏭️ 文件已存在: {filepath} in {group_name}")
                return False

    file_node = create_file_node(filename, filepath)
    files_node.append(file_node)
    print(f"➕ 添加文件: {filepath} -> {group_name}")
    return True

def add_to_keil(driver_name):
    """将驱动和测试代码添加到 Keil 工程"""
    if not PROJECT_FILE.exists():
        print(f"❌ Keil 工程文件不存在: {PROJECT_FILE}")
        return False

    tree = ET.parse(PROJECT_FILE)
    root = tree.getroot()

    groups = root.find(".//Groups")
    if groups is None:
        print("❌ Keil 工程文件中未找到 Groups 节点")
        return False

    # 驱动文件 -> Driver Group
    driver_c = f"{driver_name}_driver.c"
    driver_h = f"{driver_name}_driver.h"
    driver_c_path = f"../Driver/{driver_c}"

    # 测试文件 -> Test Group (或新建)
    test_c = f"{driver_name}_driver_test.c"
    test_c_path = f"../Test/{test_c}"

    modified = False

    if add_file_to_group(groups, "Driver", driver_c, driver_c_path):
        modified = True

    if add_file_to_group(groups, "Test", test_c, test_c_path):
        modified = True

    if modified:
        # 保存时保留 XML 声明
        tree.write(PROJECT_FILE, encoding="UTF-8", xml_declaration=True)
        print(f"💾 Keil 工程已更新: {PROJECT_FILE}")
    else:
        print("ℹ️ 无需修改 Keil 工程")

    return True

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
    parser.add_argument("--add-to-keil", action="store_true", help="添加到 Keil 工程")
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
    print(f"   驱动头文件: {DRIVER_DIR}/{driver_name}_driver.h")
    print(f"   驱动源文件: {DRIVER_DIR}/{driver_name}_driver.c")
    print(f"   测试代码  : {TEST_DIR}/{driver_name}_driver_test.c")
    if args.add_to_keil:
        print(f"   Keil 工程 : 已注册")

    return 0

if __name__ == '__main__':
    sys.exit(main())
