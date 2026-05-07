#!/usr/bin/env python3
"""
Generate and validate `.project_structure` from workflow and context facts.

The file is a generated human-readable snapshot. The facts live in
`.context/engineering.yaml` and `.workflow/project.yaml`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

from context import cfg_get, load_yaml
from workflow import find_project_root, load_config


OUTPUT_PATH = ".project_structure"


def ensure_utf8_stdio() -> None:
    if sys.platform != "win32":
        return
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def rel(root: Path, value: Any) -> str:
    if value is None:
        return ""
    path = Path(str(value))
    if path.is_absolute():
        try:
            return str(path.relative_to(root)).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")
    return str(path).replace("\\", "/")


def rows(items: Iterable[Dict[str, Any]], root: Path) -> List[str]:
    lines: List[str] = []
    for item in items:
        path = rel(root, item.get("path", ""))
        role = str(item.get("role", "")).replace("\n", " ")
        changes_when = str(item.get("changes_when", "")).replace("\n", " ")
        exists = "yes" if path and (root / path).exists() else "no"
        lines.append(f"| `{path}` | {role} | {changes_when} | {exists} |")
    return lines


def active_adapter_rows(root: Path, workflow: Dict[str, Any]) -> List[str]:
    toolchain = str(cfg_get(workflow, "toolchain.type", "unknown"))
    lines = [
        "| Fact | Value |",
        "|------|-------|",
        f"| Active toolchain | `{toolchain}` |",
    ]

    project_file = cfg_get(workflow, "toolchain.project_file")
    if project_file:
        lines.append(f"| Tool project file | `{rel(root, project_file)}` |")
    tool_exe = cfg_get(workflow, "toolchain.exe")
    if tool_exe:
        lines.append(f"| Tool executable | `{tool_exe}` |")
    source_dir = cfg_get(workflow, "toolchain.source_dir")
    if source_dir:
        lines.append(f"| CMake source dir | `{rel(root, source_dir)}` |")
    build_dir = cfg_get(workflow, "toolchain.build_dir")
    if build_dir:
        lines.append(f"| CMake build dir | `{rel(root, build_dir)}` |")
    build_command = cfg_get(workflow, "build.command")
    if build_command:
        lines.append(f"| Build command | `{build_command}` |")
    hex_path = cfg_get(workflow, "build.hex_path")
    if hex_path:
        lines.append(f"| Hex artifact | `{rel(root, hex_path)}` |")
    elf_path = cfg_get(workflow, "build.elf_path")
    if elf_path:
        lines.append(f"| ELF artifact | `{rel(root, elf_path)}` |")
    build_log = cfg_get(workflow, "build.log_path")
    if build_log:
        lines.append(f"| Build log | `{rel(root, build_log)}` |")
    flash_log = cfg_get(workflow, "flash.log_path")
    if flash_log:
        lines.append(f"| Flash log | `{rel(root, flash_log)}` |")

    return lines


def generate(root: Path) -> str:
    workflow = load_config(root)
    engineering = load_yaml(root / ".context" / "engineering.yaml")
    project = cfg_get(workflow, "project.name", root.name)
    board = cfg_get(workflow, "board.name", "")
    mcu = cfg_get(workflow, "mcu.device", cfg_get(workflow, "mcu.family", ""))

    workflow_invariant = cfg_get(engineering, "directory_policy.workflow_invariant", [])
    project_architecture = cfg_get(engineering, "directory_policy.project_architecture", [])
    variable = cfg_get(engineering, "directory_policy.platform_or_tool_variable", [])

    lines: List[str] = [
        "# Project Structure",
        "",
        "> Generated file. Do not edit by hand.",
        "> Source of truth: `.context/engineering.yaml` + `.workflow/project.yaml`.",
        "> Regenerate with: `python tools/project_structure.py generate` or `python tools/workflow.py structure`.",
        "",
        "## Project",
        "",
        f"- Project: `{project}`",
        f"- Board: `{board}`",
        f"- MCU: `{mcu}`",
        f"- Reports directory: `{cfg_get(workflow, 'layout.reports', 'reports')}`",
        "",
        "## Workflow-Invariant Directories",
        "",
        "These directories belong to the reusable AI workflow framework. They are not architecture-layer directories and should stay stable when the host OS, IDE, compiler, debugger, or AI Agent changes.",
        "",
        "| Path | Role | Changes when | Exists |",
        "|------|------|--------------|--------|",
    ]
    lines.extend(rows(workflow_invariant, root))
    lines.extend(
        [
            "",
            "## Current Project Architecture Directories",
            "",
            "These directories are this project's declared architecture. They are configurable project facts, not mandatory directories for every project that reuses the AI workflow.",
            "",
            "| Path | Role | Changes when | Exists |",
            "|------|------|--------------|--------|",
        ]
    )
    lines.extend(rows(project_architecture, root))
    lines.extend(
        [
            "",
            "## Platform / Tool Adapter Boundaries",
            "",
            "These paths may vary when the MCU, board, IDE, toolchain, generated code, or optional Agent adapter changes.",
            "",
            "| Path | Role | Changes when | Exists |",
            "|------|------|--------------|--------|",
        ]
    )
    lines.extend(rows(variable, root))
    lines.extend(
        [
            "",
            "## Active Tool Adapter",
            "",
        ]
    )
    lines.extend(active_adapter_rows(root, workflow))
    lines.extend(
        [
            "",
            "## Hard Rules",
            "",
            "- New layered code goes only into this project's declared architecture directories.",
            "- Do not move declared architecture directories into generated/vendor/platform adapter directories.",
            "- A different project may declare different architecture directories in `.context/engineering.yaml` and `.workflow/project.yaml`.",
            "- Host OS, compiler, IDE, debugger, and flash-tool changes belong in `.workflow/project.yaml`, `tools/`, or adapter directories.",
            "- Build, flash, check, review, and verify reports belong under `reports/` with fixed overwrite paths.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    ensure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Generate or validate .project_structure")
    sub = parser.add_subparsers(dest="command", required=True)
    generate_parser = sub.add_parser("generate", help="Generate .project_structure")
    generate_parser.add_argument("--print", action="store_true", help="Print generated content without writing")
    sub.add_parser("validate", help="Check whether .project_structure is up to date")

    args = parser.parse_args()
    root = find_project_root()
    output = root / OUTPUT_PATH
    content = generate(root)

    if args.command == "generate":
        if args.print:
            print(content)
            return 0
        output.write_text(content, encoding="utf-8", newline="\n")
        print(f"Generated {OUTPUT_PATH}")
        return 0

    if args.command == "validate":
        if not output.exists():
            print(f"Error: missing {OUTPUT_PATH}", file=sys.stderr)
            return 1
        existing = output.read_text(encoding="utf-8", errors="ignore")
        if existing.replace("\r\n", "\n").strip() != content.strip():
            print(f"Error: {OUTPUT_PATH} is stale. Run `python tools/project_structure.py generate`.", file=sys.stderr)
            return 1
        print("Project structure validation passed.")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
