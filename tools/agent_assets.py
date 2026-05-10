#!/usr/bin/env python3
"""
Manage agent-neutral AI assets.

`.agents/skills` is the canonical Skill source.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List, Tuple


ROOT_MARKERS = (".agents/manifest.yaml", ".workflow/project.yaml", "AGENTS.md", ".git")


def ensure_utf8_stdio() -> None:
    if sys.platform != "win32":
        return
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    while True:
        if any((current / marker).exists() for marker in ROOT_MARKERS):
            return current
        if current == current.parent:
            return (start or Path.cwd()).resolve()
        current = current.parent


def iter_skill_dirs(skills_root: Path) -> Iterable[Path]:
    if not skills_root.exists():
        return []
    return sorted(path for path in skills_root.iterdir() if path.is_dir())


def validate(root: Path) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    manifest = root / ".agents" / "manifest.yaml"
    rules = root / ".agents" / "rules"
    canonical = root / ".agents" / "skills"

    if not manifest.exists():
        errors.append("missing `.agents/manifest.yaml`")
    if not rules.exists():
        errors.append("missing canonical rules directory `.agents/rules`")
    else:
        for required in ("entrypoints.md", "git.md", "logging.md"):
            if not (rules / required).exists():
                errors.append(f"missing agent rule `.agents/rules/{required}`")
    if not canonical.exists():
        errors.append("missing canonical skills directory `.agents/skills`")
        return errors, warnings

    skill_dirs = list(iter_skill_dirs(canonical))
    if not skill_dirs:
        errors.append("canonical skills directory `.agents/skills` is empty")

    for skill_dir in skill_dirs:
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            errors.append(f"skill missing SKILL.md: {skill_dir.relative_to(root)}")
            continue
        text = skill_file.read_text(encoding="utf-8", errors="ignore")
        if not text.startswith("---"):
            errors.append(f"skill missing YAML frontmatter: {skill_file.relative_to(root)}")
    return errors, warnings


def main() -> int:
    ensure_utf8_stdio()
    root = find_project_root()

    parser = argparse.ArgumentParser(description="Manage agent-neutral AI assets")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="Validate canonical agent assets")

    args = parser.parse_args()

    if args.command == "validate":
        errors, warnings = validate(root)
        for warning in warnings:
            print(f"Warning: {warning}")
        if errors:
            for error in errors:
                print(f"Error: {error}", file=sys.stderr)
            return 1
        print("Agent assets validation passed.")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
