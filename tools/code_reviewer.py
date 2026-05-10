#!/usr/bin/env python3
"""Generic embedded code reviewer.

The reviewer is intentionally conservative in workflow-kit mode. It only runs
checks that are valid for most embedded C projects unless the adopting project
enables project-specific rules in tools/code_reviewer_config.json.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "tools" / "code_reviewer_config.json"
REPORT_PATH = ROOT / "reports" / "code_review_report.md"

DEFAULT_CONFIG: dict[str, Any] = {
    "source_dirs": [],
    "exclude_dirs": [],
    "isr_functions": [],
    "forbidden_in_isr": ["printf", "sprintf", "fprintf", "malloc", "free"],
    "max_stack_buffer": 256,
    "check_rules": {
        "isr_blocking": True,
        "infinite_loop": True,
        "stack_usage": True,
        "magic_number": True,
        "clock_enable": False,
    },
}


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG.copy()
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        cfg = json.load(f)
    merged = DEFAULT_CONFIG.copy()
    merged.update(cfg)
    merged["check_rules"] = {
        **DEFAULT_CONFIG["check_rules"],
        **cfg.get("check_rules", {}),
    }
    return merged


def iter_source_files(targets: list[str], cfg: dict[str, Any]) -> list[Path]:
    if not targets:
        targets = [str(p) for p in cfg.get("source_dirs", [])]
    if not targets:
        raise SystemExit(
            "No review target configured. Pass paths explicitly or set "
            "source_dirs in tools/code_reviewer_config.json."
        )

    exclude = {str(x).replace("\\", "/").rstrip("/") for x in cfg.get("exclude_dirs", [])}
    files: list[Path] = []
    for target in targets:
        path = (ROOT / target).resolve() if not Path(target).is_absolute() else Path(target)
        if path.is_file() and path.suffix.lower() in {".c", ".h", ".cpp", ".hpp"}:
            files.append(path)
            continue
        if path.is_dir():
            for suffix in ("*.c", "*.h", "*.cpp", "*.hpp"):
                files.extend(path.rglob(suffix))

    filtered: list[Path] = []
    for file_path in sorted(set(files)):
        rel = file_path.relative_to(ROOT).as_posix() if file_path.is_relative_to(ROOT) else file_path.as_posix()
        if any(rel == item or rel.startswith(item + "/") for item in exclude):
            continue
        filtered.append(file_path)
    return filtered


def line_of(content: str, offset: int) -> int:
    return content[:offset].count("\n") + 1


def issue(severity: str, category: str, title: str, file_path: Path, line: int, detail: str) -> dict[str, Any]:
    rel = file_path.relative_to(ROOT).as_posix() if file_path.is_relative_to(ROOT) else file_path.as_posix()
    return {
        "severity": severity,
        "category": category,
        "title": title,
        "file": rel,
        "line": line,
        "detail": detail,
    }


def function_body(content: str, function_name: str) -> tuple[int, str] | None:
    match = re.search(rf"\b(?:void|int|uint\w+_t|bool)\s+{re.escape(function_name)}\s*\([^)]*\)\s*{{", content)
    if not match:
        return None
    start = match.end()
    depth = 1
    pos = start
    while pos < len(content) and depth:
        if content[pos] == "{":
            depth += 1
        elif content[pos] == "}":
            depth -= 1
        pos += 1
    return match.start(), content[start : pos - 1]


def check_isr_safety(file_path: Path, content: str, cfg: dict[str, Any]) -> list[dict[str, Any]]:
    if not cfg.get("check_rules", {}).get("isr_blocking", True):
        return []
    issues: list[dict[str, Any]] = []
    for isr_name in cfg.get("isr_functions", []):
        body_info = function_body(content, isr_name)
        if body_info is None:
            continue
        body_offset, body = body_info
        for forbidden in cfg.get("forbidden_in_isr", []):
            for match in re.finditer(rf"\b{re.escape(forbidden)}\s*\(", body):
                issues.append(
                    issue(
                        "critical",
                        "ISR safety",
                        f"Forbidden call in ISR: {forbidden}()",
                        file_path,
                        line_of(content, body_offset + match.start()),
                        f"{isr_name} calls {forbidden}(), which is unsafe in most interrupt contexts.",
                    )
                )
    return issues


def check_busy_waits(file_path: Path, content: str, cfg: dict[str, Any]) -> list[dict[str, Any]]:
    if not cfg.get("check_rules", {}).get("infinite_loop", True):
        return []
    issues: list[dict[str, Any]] = []
    patterns = [
        r"while\s*\(\s*!\s*\w+\s*\)\s*;",
        r"while\s*\(\s*\w+\s*\)\s*;",
        r"while\s*\(\s*\w+\s*==\s*0\s*\)\s*;",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, content):
            context = content[max(0, match.start() - 200) : min(len(content), match.end() + 200)]
            if not re.search(r"timeout|deadline|tick|counter|elapsed", context, re.IGNORECASE):
                issues.append(
                    issue(
                        "warning",
                        "blocking wait",
                        "Busy wait has no visible timeout",
                        file_path,
                        line_of(content, match.start()),
                        "A blocking wait without a timeout can lock firmware if hardware state never changes.",
                    )
                )
    return issues


def check_stack_buffers(file_path: Path, content: str, cfg: dict[str, Any]) -> list[dict[str, Any]]:
    if not cfg.get("check_rules", {}).get("stack_usage", True):
        return []
    max_bytes = int(cfg.get("max_stack_buffer", 256))
    type_sizes = {
        "char": 1,
        "uint8_t": 1,
        "int8_t": 1,
        "uint16_t": 2,
        "int16_t": 2,
        "uint32_t": 4,
        "int32_t": 4,
        "int": 4,
        "float": 4,
        "double": 8,
    }
    issues: list[dict[str, Any]] = []
    pattern = r"\b(char|u?int(?:8|16|32)_t|int|float|double)\s+\w+\s*\[(\d+)\]\s*;"
    for match in re.finditer(pattern, content):
        byte_count = type_sizes.get(match.group(1), 4) * int(match.group(2))
        if byte_count > max_bytes:
            issues.append(
                issue(
                    "warning",
                    "stack usage",
                    f"Large local buffer: {byte_count} bytes",
                    file_path,
                    line_of(content, match.start()),
                    f"Local arrays larger than {max_bytes} bytes may overflow small embedded stacks.",
                )
            )
    return issues


def check_magic_delays(file_path: Path, content: str, cfg: dict[str, Any]) -> list[dict[str, Any]]:
    if not cfg.get("check_rules", {}).get("magic_number", True):
        return []
    delay_functions = cfg.get("delay_functions", ["delay_ms", "sleep_ms"])
    issues: list[dict[str, Any]] = []
    for func in delay_functions:
        for match in re.finditer(rf"\b{re.escape(func)}\s*\(\s*(\d+)\s*\)", content):
            value = int(match.group(1))
            if value not in {0, 1, 2, 5, 10, 100, 1000}:
                issues.append(
                    issue(
                        "suggestion",
                        "maintainability",
                        f"Delay literal used in {func}()",
                        file_path,
                        line_of(content, match.start()),
                        "Prefer a named constant for timing values that carry behavior meaning.",
                    )
                )
    return issues[:5]


def check_clock_enable(file_path: Path, content: str, cfg: dict[str, Any]) -> list[dict[str, Any]]:
    if not cfg.get("check_rules", {}).get("clock_enable", False):
        return []
    pairs = cfg.get("clock_enable_pairs", [])
    issues: list[dict[str, Any]] = []
    for pair in pairs:
        init_call = pair.get("init_call")
        enable_regex = pair.get("enable_regex")
        label = pair.get("label", init_call)
        if init_call and enable_regex and re.search(rf"\b{re.escape(init_call)}\s*\(", content):
            if not re.search(enable_regex, content):
                match = re.search(rf"\b{re.escape(init_call)}\s*\(", content)
                issues.append(
                    issue(
                        "warning",
                        "platform init",
                        f"{label} init has no configured enable evidence",
                        file_path,
                        line_of(content, match.start() if match else 0),
                        "The project-specific clock/resource enable rule is active and did not find expected evidence.",
                    )
                )
    return issues


def review_file(file_path: Path, cfg: dict[str, Any]) -> list[dict[str, Any]]:
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    checks = [
        check_isr_safety,
        check_busy_waits,
        check_stack_buffers,
        check_magic_delays,
        check_clock_enable,
    ]
    issues: list[dict[str, Any]] = []
    for check in checks:
        issues.extend(check(file_path, content, cfg))
    return issues


def render_report(files: list[Path], issues: list[dict[str, Any]]) -> str:
    lines = [
        "# Code Review Report",
        "",
        f"- Files reviewed: {len(files)}",
        f"- Findings: {len(issues)}",
        "",
    ]
    if not issues:
        lines.append("No issues found by the configured generic checks.")
        lines.append("")
        return "\n".join(lines)

    order = {"critical": 0, "warning": 1, "suggestion": 2}
    for item in sorted(issues, key=lambda x: (order.get(x["severity"], 9), x["file"], x["line"])):
        lines.append(f"## {item['severity'].upper()}: {item['title']}")
        lines.append(f"- File: `{item['file']}:{item['line']}`")
        lines.append(f"- Category: {item['category']}")
        lines.append(f"- Detail: {item['detail']}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run generic embedded code review checks.")
    parser.add_argument("targets", nargs="*", help="Files or directories to review.")
    args = parser.parse_args()

    cfg = load_config()
    files = iter_source_files(args.targets, cfg)
    issues: list[dict[str, Any]] = []
    for file_path in files:
        issues.extend(review_file(file_path, cfg))

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = render_report(files, issues)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report)
    print(f"Report written to {REPORT_PATH.relative_to(ROOT).as_posix()}")
    return 1 if any(item["severity"] == "critical" for item in issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
