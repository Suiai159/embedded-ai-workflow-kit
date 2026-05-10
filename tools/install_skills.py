#!/usr/bin/env python3
"""
Install kit skills into .claude/skills/ via directory junctions/symlinks.

Scans .agents/skills/ in the kit and creates individual links in
.claude/skills/ for each skill that doesn't conflict with existing ones.

Usage:
    python tools/install_skills.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def get_existing_skills(dirs: list[Path]) -> set[str]:
    """Collect skill names that already exist (have SKILL.md)."""
    skills: set[str] = set()
    for d in dirs:
        if d.exists():
            for item in d.iterdir():
                if item.is_dir() and (item / "SKILL.md").exists():
                    skills.add(item.name)
    return skills


def link_skill(target: Path, source: Path) -> bool:
    """Create a junction (Windows) or symlink (other OS)."""
    target.parent.mkdir(parents=True, exist_ok=True)

    if sys.platform == "win32":
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(target), str(source)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"  Error: {result.stderr.strip()}")
            return False
    else:
        target.symlink_to(source, target_is_directory=True)

    return True


def main() -> int:
    # This script is at <kit_root>/tools/install_skills.py
    kit_root = Path(__file__).resolve().parent.parent

    # Project root is cwd (where .claude/ lives)
    project_root = Path.cwd().resolve()

    kit_skills_dir = kit_root / ".agents" / "skills"
    if not kit_skills_dir.exists():
        print(f"Error: kit skills directory not found at {kit_skills_dir}")
        return 1

    claude_skills_dir = project_root / ".claude" / "skills"
    global_skills_dir = Path.home() / ".claude" / "skills"

    existing = get_existing_skills([claude_skills_dir, global_skills_dir])

    kit_skills = sorted(
        item.name for item in kit_skills_dir.iterdir()
        if item.is_dir() and (item / "SKILL.md").exists()
    )

    if not kit_skills:
        print("No kit skills found.")
        return 0

    print(f"Kit skills found: {len(kit_skills)}")
    print()

    installed = 0
    skipped = 0

    for name in kit_skills:
        target = claude_skills_dir / name
        source = kit_skills_dir / name

        if name in existing:
            print(f"  ⏭  {name}: skipped (already exists)")
            skipped += 1
            continue

        if link_skill(target, source):
            print(f"  ✅  {name}: installed")
            installed += 1
        else:
            print(f"  ❌  {name}: link failed")
            skipped += 1

    print()
    print(f"Installed: {installed}, Skipped: {skipped}")

    if skipped and not installed:
        # All were skipped — offer a hint
        print()
        print("All kit skills already exist in your global or project skills.")
        print("They are already available to Claude Code, nothing to install.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
