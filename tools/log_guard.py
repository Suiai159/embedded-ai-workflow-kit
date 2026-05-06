#!/usr/bin/env python3
"""
Guard mandatory project logging for AI agents.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Set


ROOT_MARKERS = (".git", "AGENTS.md", ".workflow/project.yaml")
PROJECT_LOG = "PROJECT_LOG.md"
EVOLUTION_LOG = "EVOLUTION.md"


def ensure_utf8_stdio() -> None:
    if sys.platform != "win32":
        return
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    while True:
        if any((current / marker).exists() for marker in ROOT_MARKERS):
            return current
        if current == current.parent:
            return (start or Path.cwd()).resolve()
        current = current.parent


def run_git(root: Path, args: List[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if check and completed.returncode != 0:
        if completed.stdout:
            print(completed.stdout, end="")
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
        raise SystemExit(completed.returncode)
    return completed


def changed_since_head(root: Path) -> Set[str]:
    names: Set[str] = set()
    commands = [
        ["diff", "--name-only", "HEAD"],
        ["diff", "--cached", "--name-only"],
        ["ls-files", "--others", "--exclude-standard"],
    ]
    for command in commands:
        completed = run_git(root, command, check=True)
        for line in completed.stdout.splitlines():
            normalized = line.strip().replace("\\", "/")
            if normalized:
                names.add(normalized)
    return names


def command_status(root: Path) -> int:
    changed = sorted(changed_since_head(root))
    if not changed:
        print("No changes since HEAD.")
        return 0
    print("Changed paths since HEAD:")
    for path in changed:
        print(path)
    return 0


def command_validate(root: Path, mode: str) -> int:
    changed = changed_since_head(root)
    has_project = PROJECT_LOG in changed
    has_evolution = EVOLUTION_LOG in changed

    if mode == "project":
        ok = has_project
        expected = PROJECT_LOG
    elif mode == "evolution":
        ok = has_evolution
        expected = EVOLUTION_LOG
    elif mode == "both":
        ok = has_project and has_evolution
        expected = f"{PROJECT_LOG} and {EVOLUTION_LOG}"
    else:
        ok = has_project or has_evolution
        expected = f"{PROJECT_LOG} or {EVOLUTION_LOG}"

    if ok:
        print(f"Log guard passed: updated {expected}.")
        return 0

    print(f"Log guard failed: expected update to {expected}.", file=sys.stderr)
    print("Update the durable log before staging/committing this task.", file=sys.stderr)
    return 1


def main() -> int:
    ensure_utf8_stdio()
    root = find_project_root()

    parser = argparse.ArgumentParser(description="Guard mandatory project logging")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="Show changed paths considered by the log guard")
    validate_parser = sub.add_parser("validate", help="Require PROJECT_LOG.md and/or EVOLUTION.md updates")
    validate_parser.add_argument(
        "--mode",
        choices=["either", "project", "evolution", "both"],
        default="either",
        help="Which durable log update is required",
    )

    args = parser.parse_args()
    if args.command == "status":
        return command_status(root)
    if args.command == "validate":
        return command_validate(root, args.mode)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
