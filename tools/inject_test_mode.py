#!/usr/bin/env python3
"""
Temporarily inject TEST_MODE macro into Keil uvprojx Define field.
Usage: python tools/inject_test_mode.py <uvprojx_path>
"""

import sys
import xml.etree.ElementTree as ET


def inject(uvprojx_path):
    tree = ET.parse(uvprojx_path)
    root = tree.getroot()

    found = False
    for target in root.iter('Target'):
        for define in target.iter('Define'):
            text = define.text or ""
            if 'TEST_MODE' not in text:
                define.text = text + ',TEST_MODE' if text else 'TEST_MODE'
                found = True
                break
        if found:
            break

    if not found:
        print("Warning: Could not find Define node in uvprojx", file=sys.stderr)
        return 1

    # Preserve XML declaration and encoding
    tree.write(uvprojx_path, xml_declaration=True, encoding='UTF-8')
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python inject_test_mode.py <uvprojx_path>")
        sys.exit(1)
    sys.exit(inject(sys.argv[1]))
