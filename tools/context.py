#!/usr/bin/env python3
"""
AI handoff context CLI.

This tool validates and summarizes the four context groups under `.context/`:
engineering, hardware, version, and runtime.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


ROOT_MARKERS = (".context", ".workflow/project.yaml", "CLAUDE.md", ".git")
KINDS = ("engineering", "hardware", "version", "runtime")


class ContextError(RuntimeError):
    pass


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    while True:
        if any((current / marker).exists() for marker in ROOT_MARKERS):
            return current
        if current == current.parent:
            return (start or Path.cwd()).resolve()
        current = current.parent


def load_yaml(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception as exc:
        raise ContextError("PyYAML is required for context files with lists and nested data") from exc

    if not path.exists():
        raise ContextError(f"Missing context file: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ContextError(f"Context file must be a YAML mapping: {path}")
    return data


def write_yaml(path: Path, data: Dict[str, Any]) -> None:
    import yaml  # type: ignore

    with path.open("w", encoding="utf-8", newline="\n") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def cfg_get(data: Dict[str, Any], dotted_key: str, default: Any = None) -> Any:
    current: Any = data
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def require_keys(data: Dict[str, Any], keys: Iterable[str], label: str) -> List[str]:
    errors = []
    for key in keys:
        if cfg_get(data, key) in (None, "", []):
            errors.append(f"{label}: missing required key `{key}`")
    return errors


def path_exists_or_external(root: Path, item: Any) -> bool:
    if isinstance(item, dict):
        if item.get("external") is True or item.get("status") == "external":
            return True
        value = item.get("path")
    else:
        value = item
    if not value:
        return False
    return (root / str(value)).exists()


def relpath(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def load_all(root: Path) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, str]]:
    context_dir = root / ".context"
    data = {}
    markdown = {}
    for kind in KINDS:
        yaml_path = context_dir / f"{kind}.yaml"
        md_path = context_dir / f"{kind}.md"
        data[kind] = load_yaml(yaml_path)
        if not md_path.exists():
            raise ContextError(f"Missing context file: {md_path}")
        markdown[kind] = md_path.read_text(encoding="utf-8")
    return data, markdown


def validate(root: Path) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    try:
        data, _ = load_all(root)
    except ContextError as exc:
        return [str(exc)], warnings

    workflow = load_yaml(root / ".workflow" / "project.yaml")

    errors += require_keys(
        data["engineering"],
        [
            "source_of_truth.workflow_config",
            "layout.app",
            "layout.service",
            "layout.driver",
            "layout.test",
            "layout.reports",
            "architecture.layers",
            "ai_rules.must_read_before_code_change",
        ],
        "engineering",
    )
    errors += require_keys(
        data["hardware"],
        ["mcu.family", "mcu.device", "resources"],
        "hardware",
    )
    errors += require_keys(
        data["version"],
        ["project.name", "toolchain.active_adapter", "generated_code_boundaries.cube_generated"],
        "version",
    )
    errors += require_keys(
        data["runtime"],
        ["status.handoff_state", "status.last_known_build", "status.last_known_flash", "status.last_known_verify"],
        "runtime",
    )

    for key in ("app", "service", "driver", "test", "reports"):
        context_value = cfg_get(data["engineering"], f"layout.{key}")
        workflow_value = cfg_get(workflow, f"layout.{key}")
        if context_value != workflow_value:
            errors.append(
                f"layout mismatch `{key}`: engineering={context_value!r}, workflow={workflow_value!r}"
            )

    resources = cfg_get(data["hardware"], "resources", [])
    seen: Dict[str, str] = {}
    for resource in resources:
        if not isinstance(resource, dict):
            errors.append("hardware: each resource must be a mapping")
            continue
        identifier = resource.get("id")
        physical = f"{resource.get('type')}:{resource.get('peripheral')}:{resource.get('pin', '')}"
        if not identifier:
            errors.append("hardware: resource missing `id`")
        if not resource.get("owner"):
            errors.append(f"hardware: resource `{identifier}` missing `owner`")
        if physical in seen:
            errors.append(f"hardware: duplicate physical resource `{physical}` used by {seen[physical]} and {identifier}")
        seen[physical] = str(identifier)
        reference = resource.get("reference")
        if reference and not (root / str(reference)).exists():
            errors.append(f"hardware: reference path missing for `{identifier}`: {reference}")

    for key in ("project.ioc_file", "project.workflow_config"):
        value = cfg_get(data["version"], key)
        if value and not path_exists_or_external(root, value):
            errors.append(f"version: path missing `{key}` -> {value}")

    for path_value in cfg_get(data["version"], "generated_code_boundaries.cube_generated", []):
        if not path_exists_or_external(root, path_value):
            warnings.append(f"version: generated boundary path not found: {path_value}")

    for evidence_key in ("last_build.evidence", "last_flash.evidence", "last_verify.evidence"):
        value = cfg_get(data["runtime"], evidence_key)
        if value and not path_exists_or_external(root, value):
            warnings.append(f"runtime: evidence path not found `{evidence_key}` -> {value}")

    return errors, warnings


def print_summary(root: Path) -> int:
    data, _ = load_all(root)
    workflow = load_yaml(root / ".workflow" / "project.yaml")

    print("# AI Handoff Context Summary")
    print("")
    print("## Engineering")
    print(f"- Project: {cfg_get(workflow, 'project.name', cfg_get(data['version'], 'project.name', 'unknown'))}")
    print(f"- Toolchain adapter: {cfg_get(workflow, 'toolchain.type', cfg_get(data['version'], 'toolchain.active_adapter', 'unknown'))}")
    print(f"- Layout: App={cfg_get(data['engineering'], 'layout.app')}, Service={cfg_get(data['engineering'], 'layout.service')}, Driver={cfg_get(data['engineering'], 'layout.driver')}, Test={cfg_get(data['engineering'], 'layout.test')}")
    print("- Dependency rule: App -> Service -> Driver -> HAL")
    print("")
    print("## Hardware")
    print(f"- MCU: {cfg_get(data['hardware'], 'mcu.family')} / {cfg_get(data['hardware'], 'mcu.device')}")
    print(f"- Clock: {cfg_get(data['hardware'], 'clocks.system_hz', 'unknown')} Hz")
    for resource in cfg_get(data["hardware"], "resources", []):
        print(f"- Resource: {resource.get('id')} owned by {resource.get('owner')} ({resource.get('type')} {resource.get('peripheral')})")
    print("")
    print("## Version")
    print(f"- Active adapter: {cfg_get(data['version'], 'toolchain.active_adapter')}")
    print(f"- Observed compiler: {cfg_get(data['version'], 'toolchain.keil.compiler_version_observed', 'unknown')}")
    print("- Generated boundary: " + ", ".join(str(p) for p in cfg_get(data["version"], "generated_code_boundaries.cube_generated", [])))
    print("")
    print("## Runtime")
    print(f"- Handoff state: {cfg_get(data['runtime'], 'status.handoff_state')}")
    print(f"- Build: {cfg_get(data['runtime'], 'status.last_known_build')} ({cfg_get(data['runtime'], 'last_build.evidence', '')})")
    print(f"- Flash: {cfg_get(data['runtime'], 'status.last_known_flash')} ({cfg_get(data['runtime'], 'last_flash.evidence', '')})")
    print(f"- Verify: {cfg_get(data['runtime'], 'status.last_known_verify')} ({cfg_get(data['runtime'], 'last_verify.evidence', '')})")
    known_issues = cfg_get(data["runtime"], "known_issues", [])
    if known_issues:
        print("- Known issues:")
        for issue in known_issues:
            print(f"  - {issue.get('id')}: {issue.get('summary')}")
    return 0


def infer_build(root: Path, workflow: Dict[str, Any]) -> Dict[str, str]:
    build_log = root / str(cfg_get(workflow, "build.log_path", "tools/build_log.txt"))
    if not build_log.exists():
        return {"result": "unknown", "evidence": relpath(root, build_log), "summary": "No build log found."}
    text = build_log.read_text(encoding="utf-8", errors="ignore")
    exit_codes = re.findall(r"\[workflow\] exit_code=(\d+)", text)
    if exit_codes:
        result = "pass" if exit_codes[-1] == "0" else "fail"
        return {"result": result, "evidence": relpath(root, build_log), "summary": f"workflow exit_code={exit_codes[-1]}"}
    if "0 Error(s)" in text:
        return {"result": "pass", "evidence": relpath(root, build_log), "summary": "Build log reports 0 Error(s)."}
    if "Error(s)" in text or "error:" in text.lower():
        return {"result": "fail", "evidence": relpath(root, build_log), "summary": "Build log contains errors."}
    return {"result": "unknown", "evidence": relpath(root, build_log), "summary": "Build log exists but result could not be inferred."}


def infer_flash(root: Path, workflow: Dict[str, Any]) -> Dict[str, str]:
    flash_log = root / str(cfg_get(workflow, "flash.log_path", "tools/flash_log.txt"))
    if not flash_log.exists():
        return {"result": "unknown", "evidence": relpath(root, flash_log), "summary": "No flash log found."}
    text = flash_log.read_text(encoding="utf-8", errors="ignore")
    exit_codes = re.findall(r"\[workflow\] exit_code=(\d+)", text)
    if exit_codes:
        result = "pass" if exit_codes[-1] == "0" else "fail"
        return {"result": result, "evidence": relpath(root, flash_log), "summary": f"workflow exit_code={exit_codes[-1]}"}
    if "Flash successful" in text or "Verify OK" in text:
        return {"result": "pass", "evidence": relpath(root, flash_log), "summary": "Flash log indicates success."}
    if "Flash failed" in text or "Error" in text:
        return {"result": "fail", "evidence": relpath(root, flash_log), "summary": "Flash log indicates failure."}
    return {"result": "unknown", "evidence": relpath(root, flash_log), "summary": "Flash log exists but result could not be inferred."}


def infer_verify(root: Path, workflow: Dict[str, Any]) -> Dict[str, str]:
    report_dir = str(cfg_get(workflow, "layout.reports", "reports"))
    verify_report = root / report_dir / "verify_report.md"
    if not verify_report.exists():
        return {"result": "unknown", "evidence": relpath(root, verify_report), "summary": "No verify report found."}
    text = verify_report.read_text(encoding="utf-8", errors="ignore")
    if "最终结果**: ✓" in text or "最终结果**: PASS" in text:
        return {"result": "pass", "evidence": relpath(root, verify_report), "summary": "Verify report indicates pass."}
    if "最终结果**: ✗" in text or "失败" in text:
        first_error = re.search(r"## 错误信息\s+```([\s\S]*?)```", text)
        summary = first_error.group(1).strip().splitlines()[0] if first_error else "Verify report indicates failure."
        return {"result": "fail", "evidence": relpath(root, verify_report), "summary": summary}
    return {"result": "unknown", "evidence": relpath(root, verify_report), "summary": "Verify report exists but result could not be inferred."}


def touch_runtime(root: Path) -> int:
    runtime_path = root / ".context" / "runtime.yaml"
    runtime = load_yaml(runtime_path)
    workflow = load_yaml(root / ".workflow" / "project.yaml")

    build = infer_build(root, workflow)
    flash = infer_flash(root, workflow)
    verify = infer_verify(root, workflow)

    runtime["status"] = {
        "handoff_state": "dirty_worktree",
        "last_known_build": build["result"],
        "last_known_flash": flash["result"],
        "last_known_verify": verify["result"],
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    runtime["last_build"] = build
    runtime["last_flash"] = flash
    runtime["last_verify"] = verify
    runtime["serial"] = {
        "port": cfg_get(workflow, "serial.port", "auto"),
        "baudrate": cfg_get(workflow, "serial.baudrate", 115200),
    }

    known_issues = []
    if verify["result"] == "fail":
        known_issues.append({
            "id": "VERIFY_FAILED",
            "status": "open",
            "evidence": verify["evidence"],
            "summary": verify["summary"],
        })
    runtime["known_issues"] = known_issues

    write_yaml(runtime_path, runtime)
    write_runtime_markdown(root / ".context" / "runtime.md", runtime)
    print(f"Updated {runtime_path}")
    return 0


def write_runtime_markdown(path: Path, runtime: Dict[str, Any]) -> None:
    known_issues = runtime.get("known_issues", [])
    lines = [
        "# Runtime Context",
        "",
        "This file is the current handoff snapshot. Historical work remains in `PROJECT_LOG.md` and `EVOLUTION.md`.",
        "",
        "## Current State",
        "",
        f"- Worktree: {cfg_get(runtime, 'status.handoff_state', 'unknown')}",
        f"- Last known build: {cfg_get(runtime, 'status.last_known_build', 'unknown')}",
        f"- Last known flash: {cfg_get(runtime, 'status.last_known_flash', 'unknown')}",
        f"- Last known verify: {cfg_get(runtime, 'status.last_known_verify', 'unknown')}",
        f"- Updated at: {cfg_get(runtime, 'status.updated_at', 'unknown')}",
        "",
        "## Evidence",
        "",
        f"- Build evidence: `{cfg_get(runtime, 'last_build.evidence', '')}`",
        f"- Flash evidence: `{cfg_get(runtime, 'last_flash.evidence', '')}`",
        f"- Verify evidence: `{cfg_get(runtime, 'last_verify.evidence', '')}`",
        "",
        "## Current Summaries",
        "",
        f"- Build: {cfg_get(runtime, 'last_build.summary', '')}",
        f"- Flash: {cfg_get(runtime, 'last_flash.summary', '')}",
        f"- Verify: {cfg_get(runtime, 'last_verify.summary', '')}",
        "",
        "## Known Runtime Issues",
        "",
    ]
    if known_issues:
        for issue in known_issues:
            lines.append(f"- `{issue.get('id')}` ({issue.get('status')}): {issue.get('summary')} [{issue.get('evidence')}]")
    else:
        lines.append("*No open runtime issues recorded.*")
    lines.extend([
        "",
        "## Handoff Rule",
        "",
        "When build, flash, or verify status changes, update this runtime snapshot with `python tools/context.py touch-runtime`.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="AI handoff context tools")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="Validate context files and cross-file consistency")
    sub.add_parser("summary", help="Print AI handoff summary")
    sub.add_parser("touch-runtime", help="Refresh runtime context from build/flash/verify evidence")
    args = parser.parse_args()

    root = find_project_root()
    try:
        if args.command == "validate":
            errors, warnings = validate(root)
            for warning in warnings:
                print(f"Warning: {warning}")
            if errors:
                for error in errors:
                    print(f"Error: {error}", file=sys.stderr)
                return 1
            print("Context validation passed.")
            return 0
        if args.command == "summary":
            return print_summary(root)
        if args.command == "touch-runtime":
            return touch_runtime(root)
    except ContextError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
