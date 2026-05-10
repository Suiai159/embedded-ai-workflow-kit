#!/usr/bin/env python3
"""Agent-neutral development orchestrator.

This helper reports the next likely workflow action from project logs, reports,
and workflow configuration. It does not assume any source, driver, or test
directory until the adopting project declares one.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from workflow import cfg_get, find_project_root, load_config


ROOT = find_project_root()
CONFIG = load_config(ROOT)
REPORT_DIR = ROOT / str(cfg_get(CONFIG, "layout.reports", "reports"))
PROJECT_LOG = ROOT / "PROJECT_LOG.md"
BUILD_LOG = ROOT / str(cfg_get(CONFIG, "build.log_path", "reports/build_log.txt"))

REPORT_FILES = {
    "code_review": REPORT_DIR / "code_review_report.md",
    "verify": REPORT_DIR / str(cfg_get(CONFIG, "verify.report_path", "reports/verify_report.md")).split("/")[-1],
    "check_req": REPORT_DIR / "check_req_report.md",
}


def layout_path(*keys: str) -> Path | None:
    for key in keys:
        value = cfg_get(CONFIG, key)
        if value:
            return ROOT / str(value)
    return None


def git_status() -> dict[str, Any]:
    try:
        status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
        branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        changes = [line.strip() for line in status.splitlines() if line.strip()]
        return {"branch": branch, "dirty": bool(changes), "changes": changes}
    except Exception as exc:
        return {"branch": "unknown", "dirty": False, "changes": [], "error": str(exc)}


def read_log() -> str:
    return PROJECT_LOG.read_text(encoding="utf-8", errors="ignore") if PROJECT_LOG.exists() else ""


def parse_active_tasks() -> list[dict[str, Any]]:
    content = read_log()
    match = re.search(r"## Active Tasks\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if not match:
        match = re.search(r"## 活跃任务\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if not match:
        return []

    tasks: list[dict[str, Any]] = []
    for line in match.group(1).splitlines():
        task = re.match(r"- \[([ x])\] \[([^\]]+)\] (.+?)(?: \(since ([^)]+)\))?$", line.strip())
        if task:
            tasks.append(
                {
                    "done": task.group(1) == "x",
                    "type": task.group(2),
                    "title": task.group(3),
                    "since": task.group(4),
                    "meta": {},
                }
            )
    return [task for task in tasks if not task["done"]]


def parse_blockers() -> list[str]:
    content = read_log()
    match = re.search(r"## Blockers\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if not match:
        match = re.search(r"## 阻塞项\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if not match:
        return []
    return [line[2:].strip() for line in match.group(1).splitlines() if line.strip().startswith("- ")]


def build_status() -> tuple[str, str]:
    if not BUILD_LOG.exists():
        return "unknown", "no build log"
    log = BUILD_LOG.read_text(encoding="utf-8", errors="ignore")
    workflow_exit = re.findall(r"\[workflow\] exit_code=(\d+)", log)
    if workflow_exit:
        code = int(workflow_exit[-1])
        return ("success", "build succeeded") if code == 0 else ("failed", f"build failed: exit_code={code}")

    errors = re.findall(r"(\d+) Error\(s\)", log)
    warnings = re.findall(r"(\d+) Warning\(s\)", log)
    if errors:
        err = int(errors[-1])
        warn = int(warnings[-1]) if warnings else 0
        if err:
            return "failed", f"build failed: {err} Error(s), {warn} Warning(s)"
        return "success", f"build succeeded: {warn} Warning(s)"
    return "unknown", "build log format is not recognized"


def code_review_status() -> str:
    report = REPORT_FILES["code_review"]
    if not report.exists():
        return "none"
    text = report.read_text(encoding="utf-8", errors="ignore")
    if "CRITICAL:" in text:
        return "critical"
    if "WARNING:" in text:
        return "warning"
    return "pass"


def driver_state(name: str) -> tuple[str, str]:
    source_dir = layout_path("layout.driver", "layout.source")
    test_dir = layout_path("layout.test")
    if source_dir is None:
        return "unconfigured", "driver/source layout is not configured"

    driver_c = source_dir / f"{name}_driver.c"
    if not driver_c.exists():
        return "missing", f"{driver_c.relative_to(ROOT).as_posix()} does not exist"

    content = driver_c.read_text(encoding="utf-8", errors="ignore")
    if "TODO" in content or driver_c.stat().st_size < 300:
        return "skeleton", "driver file still looks like a skeleton"

    if test_dir is None:
        return "implemented", "driver exists; test layout is not configured"
    return "implemented", "driver and project layout are configured"


def determine_next_step() -> dict[str, Any]:
    blockers = parse_blockers()
    if blockers:
        return {"action": "pause", "reason": "blockers are recorded", "blockers": blockers}

    review = code_review_status()
    b_status, b_message = build_status()
    tasks = parse_active_tasks()

    for task in tasks:
        if task["type"] == "driver-dev":
            name_match = re.search(r"([A-Za-z0-9_]+)", task["title"])
            name = name_match.group(1).lower() if name_match else ""
            state, message = driver_state(name)
            if state in {"unconfigured", "missing", "skeleton"}:
                return {"action": "driver-dev", "reason": message, "task": task}
            if review == "none":
                return {"action": "code-reviewer", "reason": "driver exists and needs review", "task": task}
            if review == "critical":
                return {"action": "pause", "reason": "code review has critical findings", "task": task}
            if b_status != "success":
                return {"action": "build", "reason": b_message, "task": task}

        if task["type"] == "verify":
            return {"action": "verify", "reason": "active verification task", "task": task}

    git = git_status()
    if git["dirty"]:
        return {
            "action": "pause",
            "reason": "worktree has uncommitted changes",
            "changes": git["changes"][:50],
        }
    return {"action": "idle", "reason": "no active task or dirty worktree"}


def ensure_project_log() -> None:
    if PROJECT_LOG.exists():
        return
    PROJECT_LOG.write_text("# Project Log\n\n## Active Tasks\n*None*\n\n## Blockers\n*None*\n", encoding="utf-8")


def append_log_entry(text: str, section: str) -> None:
    ensure_project_log()
    today = datetime.now().strftime("%Y-%m-%d")
    content = read_log()
    entry = f"\n## {today}\n### {section}\n- {text}\n"
    if f"## {today}" not in content:
        content = content.rstrip() + "\n" + entry
    else:
        pattern = rf"(## {today}.*?### {re.escape(section)}\n)(.*?)(?=###|\n## |\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            insert = match.end(2)
            content = content[:insert] + f"- {text}\n" + content[insert:]
        else:
            block = re.search(rf"(## {today}.*?)(?=\n## |\Z)", content, re.DOTALL)
            insert = block.end(1) if block else len(content)
            content = content[:insert] + f"\n### {section}\n- {text}\n" + content[insert:]
    PROJECT_LOG.write_text(content, encoding="utf-8")
    print(f"logged: {text}")


def set_active_task(task_type: str, title: str) -> None:
    ensure_project_log()
    today = datetime.now().strftime("%Y-%m-%d")
    content = read_log()
    new_task = f"- [ ] [{task_type}] {title} (since {today})"
    if "## Active Tasks" in content:
        content = re.sub(r"(## Active Tasks\s*\n)(\*None\*\n)?", rf"\1{new_task}\n", content, count=1)
    else:
        content = content.rstrip() + f"\n\n## Active Tasks\n{new_task}\n"
    PROJECT_LOG.write_text(content, encoding="utf-8")
    print(f"active task set: [{task_type}] {title}")


def clear_active_tasks() -> None:
    ensure_project_log()
    content = read_log()
    content = re.sub(r"## Active Tasks\s*\n.*?(?=\n## |\Z)", "## Active Tasks\n*None*\n", content, flags=re.DOTALL)
    content = re.sub(r"## 活跃任务\s*\n.*?(?=\n## |\Z)", "## 活跃任务\n*暂无活跃任务*\n", content, flags=re.DOTALL)
    PROJECT_LOG.write_text(content, encoding="utf-8")
    print("active tasks cleared")


def mark_done(title: str) -> None:
    ensure_project_log()
    content = read_log()
    content = re.sub(rf"(- )\[ \](\[.*?\] .*?{re.escape(title)}.*)", r"\1[x]\2", content)
    PROJECT_LOG.write_text(content, encoding="utf-8")
    print(f"marked done: {title}")


def wrap_day() -> str:
    git = git_status()
    b_status, b_message = build_status()
    review = code_review_status()
    summary = [
        f"## {datetime.now().strftime('%Y-%m-%d')} Day Wrap",
        f"- Branch: {git['branch']}",
        f"- Worktree: {'dirty' if git['dirty'] else 'clean'}",
        f"- Build: {b_status} ({b_message})",
        f"- Code review: {review}",
        f"- Active tasks: {len(parse_active_tasks())}",
        f"- Blockers: {len(parse_blockers())}",
    ]
    text = "\n".join(summary)
    print(text)
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description="Query and update workflow development state.")
    parser.add_argument("--query-next-step", action="store_true")
    parser.add_argument("--wrap", action="store_true")
    parser.add_argument("--log-entry")
    parser.add_argument("--log-section", default="Progress")
    parser.add_argument("--set-active", help='JSON object with "type" and "title".')
    parser.add_argument("--clear-active", action="store_true")
    parser.add_argument("--mark-done")
    args = parser.parse_args()

    if args.query_next_step:
        print(json.dumps(determine_next_step(), ensure_ascii=False, indent=2))
    elif args.wrap:
        wrap_day()
    elif args.log_entry:
        append_log_entry(args.log_entry, args.log_section)
    elif args.set_active:
        data = json.loads(args.set_active)
        set_active_task(data["type"], data["title"])
    elif args.clear_active:
        clear_active_tasks()
    elif args.mark_done:
        mark_done(args.mark_done)
    else:
        parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
