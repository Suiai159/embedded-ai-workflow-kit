#!/usr/bin/env python3
"""
Guard git handoff discipline for AI agents.

The guard does not decide what belongs in a commit. It makes the required git
state visible and provides a scoped commit helper so agents can stage only the
paths they own for the current task.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List


ROOT_MARKERS = (".git", "AGENTS.md", ".workflow/project.yaml")


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


def porcelain(root: Path) -> str:
    completed = run_git(root, ["status", "--short"], check=True)
    return completed.stdout


def command_status(root: Path) -> int:
    text = porcelain(root)
    if text:
        print(text, end="")
    else:
        print("Git worktree is clean.")
    return 0


def command_pre_final(root: Path) -> int:
    text = porcelain(root)
    if not text:
        print("Git guard passed: worktree is clean.")
        return 0

    print("Git guard failed: uncommitted changes remain.", file=sys.stderr)
    print(text, end="", file=sys.stderr)
    print(
        "Commit task-owned changes before final handoff, or state that the user explicitly asked not to commit.",
        file=sys.stderr,
    )
    return 1


def command_stage(root: Path, paths: List[str]) -> int:
    if not paths:
        print("Error: pass explicit --paths so unrelated user changes are not staged.", file=sys.stderr)
        return 1

    missing = []
    for path in paths:
        if (root / path).exists():
            continue
        tracked = run_git(root, ["ls-files", "--error-unmatch", path])
        if tracked.returncode != 0:
            missing.append(path)
    if missing:
        print("Error: stage path does not exist: " + ", ".join(missing), file=sys.stderr)
        return 1

    run_git(root, ["add", "--", *paths], check=True)
    staged = run_git(root, ["diff", "--cached", "--name-only"], check=True).stdout.strip()
    if staged:
        print("Staged checkpoint:")
        print(staged)
    else:
        print("No staged changes.")
    return 0


def command_commit(root: Path, message: str, paths: List[str]) -> int:
    if not paths:
        print("Error: pass explicit --paths so unrelated user changes are not staged.", file=sys.stderr)
        return 1

    missing = []
    for path in paths:
        if (root / path).exists():
            continue
        tracked = run_git(root, ["ls-files", "--error-unmatch", path])
        if tracked.returncode != 0:
            missing.append(path)
    if missing:
        print("Error: commit path does not exist: " + ", ".join(missing), file=sys.stderr)
        return 1

    run_git(root, ["add", "--", *paths], check=True)
    staged = run_git(root, ["diff", "--cached", "--name-only"], check=True).stdout.strip()
    if not staged:
        print("No staged changes to commit.")
        return 0

    completed = run_git(root, ["commit", "-m", message])
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    if completed.returncode != 0:
        return completed.returncode

    commit_hash = run_git(root, ["rev-parse", "--short", "HEAD"], check=True).stdout.strip()
    print(f"Committed {commit_hash}")
    return 0


def main() -> int:
    ensure_utf8_stdio()
    root = find_project_root()

    parser = argparse.ArgumentParser(description="Guard git save/commit discipline")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="Show short git status")
    sub.add_parser("pre-final", help="Fail if uncommitted changes remain")
    stage_parser = sub.add_parser("stage", help="Stage explicit task-owned paths as a checkpoint")
    stage_parser.add_argument("--paths", nargs="+", required=True, help="Task-owned paths to stage")
    commit_parser = sub.add_parser("commit", help="Stage explicit paths and commit")
    commit_parser.add_argument("--message", required=True, help="Commit message")
    commit_parser.add_argument("--paths", nargs="+", required=True, help="Task-owned paths to stage")

    args = parser.parse_args()

    if args.command == "status":
        return command_status(root)
    if args.command == "pre-final":
        return command_pre_final(root)
    if args.command == "stage":
        return command_stage(root, args.paths)
    if args.command == "commit":
        return command_commit(root, args.message, args.paths)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
