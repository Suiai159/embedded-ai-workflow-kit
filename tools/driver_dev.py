#!/usr/bin/env python3
"""Driver/module development helper for the configured project layout."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from workflow import cfg_get, find_project_root, load_config


PROJECT_ROOT = find_project_root()
CONFIG = load_config(PROJECT_ROOT)


def configured_path(*keys: str) -> Path | None:
    for key in keys:
        value = cfg_get(CONFIG, key)
        if value:
            return Path(str(value))
    return None


def resolve_layout(source_dir: str | None, test_dir: str | None) -> tuple[Path, Path | None]:
    source_rel = Path(source_dir) if source_dir else configured_path("layout.driver", "layout.source", "layout.sources")
    test_rel = Path(test_dir) if test_dir else configured_path("layout.test", "layout.tests")

    if source_rel is None:
        raise RuntimeError(
            "No driver/source directory configured. Pass --source-dir or declare "
            "layout.driver/layout.source in .workflow/project.yaml."
        )

    source_abs = PROJECT_ROOT / source_rel
    test_abs = PROJECT_ROOT / test_rel if test_rel is not None else None
    return source_abs, test_abs


def register_with_workflow(module_name: str) -> bool:
    workflow = PROJECT_ROOT / "tools" / "workflow.py"
    result = subprocess.run(
        [sys.executable, str(workflow), "register-driver", "--name", module_name],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode == 0


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def generate_skeleton(module_name: str, interface: str, source_dir: Path, test_dir: Path | None) -> None:
    guard = f"__{module_name.upper()}_DRIVER_H"
    header_path = source_dir / f"{module_name}_driver.h"
    source_path = source_dir / f"{module_name}_driver.c"

    header = f"""#ifndef {guard}
#define {guard}

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {{
#endif

int {module_name}_Driver_Init(void);
int {module_name}_Driver_DeInit(void);

#ifdef __cplusplus
}}
#endif

#endif /* {guard} */
"""
    source = f"""#include "{module_name}_driver.h"

/* Interface: {interface or "unconfigured"} */

int {module_name}_Driver_Init(void)
{{
    return 0;
}}

int {module_name}_Driver_DeInit(void)
{{
    return 0;
}}
"""

    for path, content in ((header_path, header), (source_path, source)):
        if write_if_missing(path, content):
            print(f"created {path.relative_to(PROJECT_ROOT).as_posix()}")
        else:
            print(f"kept existing {path.relative_to(PROJECT_ROOT).as_posix()}")

    if test_dir is None:
        print("test skeleton skipped: no test directory configured")
        return

    test_path = test_dir / f"{module_name}_driver_test.c"
    test = f"""#include "{module_name}_driver.h"

int {module_name}_Driver_Test(void)
{{
    return {module_name}_Driver_Init();
}}
"""
    if write_if_missing(test_path, test):
        print(f"created {test_path.relative_to(PROJECT_ROOT).as_posix()}")
    else:
        print(f"kept existing {test_path.relative_to(PROJECT_ROOT).as_posix()}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create and optionally register a configured project driver/module.")
    parser.add_argument("--name", "-n", required=True, help="Driver/module name, for example st7789.")
    parser.add_argument("--interface", "-i", default="", help="Interface note, for example SPI/I2C/UART.")
    parser.add_argument("--source-dir", help="Project source/driver directory. Overrides workflow layout.")
    parser.add_argument("--test-dir", help="Project test directory. Overrides workflow layout.")
    parser.add_argument("--skeleton", action="store_true", help="Generate missing skeleton files.")
    parser.add_argument("--register", action="store_true", help="Register generated files through tools/workflow.py.")
    parser.add_argument("--add-to-keil", action="store_true", help="Deprecated alias for --register.")
    args = parser.parse_args()

    module_name = args.name.lower().replace(" ", "_")
    source_dir, test_dir = resolve_layout(args.source_dir, args.test_dir)

    if args.skeleton:
        generate_skeleton(module_name, args.interface, source_dir, test_dir)

    if args.register or args.add_to_keil:
        if not register_with_workflow(module_name):
            return 1

    print("driver/module helper complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
