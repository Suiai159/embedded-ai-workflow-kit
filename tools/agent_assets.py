#!/usr/bin/env python3
"""
Manage agent-neutral AI assets.

`.agents/skills` is the canonical Skill source. Tool-specific directories such
as `.claude/skills` are compatibility mirrors.
"""

from __future__ import annotations

import argparse
import shutil
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
    claude_mirror = root / ".claude" / "skills"

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
        if ".claude/skills" in text.replace("\\", "/"):
            errors.append(
                f"canonical skill references `.claude/skills`: {skill_file.relative_to(root)}"
            )

    if not claude_mirror.exists():
        warnings.append("compatibility mirror `.claude/skills` does not exist")
    else:
        for skill_dir in skill_dirs:
            mirrored = claude_mirror / skill_dir.name / "SKILL.md"
            if not mirrored.exists():
                warnings.append(f"Claude mirror missing skill: {skill_dir.name}")

    return errors, warnings


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)
    for path in src.rglob("*"):
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(src)
        target = dst / rel
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def sync_skills(root: Path, target: str) -> int:
    src = root / ".agents" / "skills"
    if target != "claude":
        print(f"Error: unsupported target `{target}`", file=sys.stderr)
        return 1
    if not src.exists():
        print("Error: missing canonical skills directory `.agents/skills`", file=sys.stderr)
        return 1

    dst = root / ".claude" / "skills"
    copy_tree(src, dst)
    print(f"Synced {src.relative_to(root)} -> {dst.relative_to(root)}")
    return 0


def main() -> int:
    ensure_utf8_stdio()
    root = find_project_root()

    parser = argparse.ArgumentParser(description="Manage agent-neutral AI assets")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="Validate canonical agent assets")
    sync_parser = sub.add_parser("sync-skills", help="Sync canonical Skills to a compatibility target")
    sync_parser.add_argument("--target", choices=["claude"], required=True)

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

    if args.command == "sync-skills":
        return sync_skills(root, args.target)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
