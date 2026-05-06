#!/usr/bin/env python3
"""
Dev Orchestrator - 项目自动化总控
负责状态管理、任务调度、项目日志维护
"""

import sys
import os
import re
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

from workflow import cfg_get, find_project_root, load_config

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

PROJECT_ROOT = find_project_root()
CONFIG = load_config(PROJECT_ROOT)
REPORT_DIR = Path(str(cfg_get(CONFIG, "layout.reports", "reports")))
DRIVER_DIR = Path(str(cfg_get(CONFIG, "layout.driver", "Driver")))
TEST_DIR = Path(str(cfg_get(CONFIG, "layout.test", "Test")))

PROJECT_LOG = Path("PROJECT_LOG.md")
BUILD_LOG = Path(str(cfg_get(CONFIG, "build.log_path", "reports/build_log.txt")))
REPORT_FILES = {
    "code_review": REPORT_DIR / "code_review_report.md",
    "verify": REPORT_DIR / "verify_report.md",
    "check_req": REPORT_DIR / "check_req_report.md",
}

# ============================================================
# Git 相关
# ============================================================

def get_git_status():
    try:
        status = subprocess.check_output(["git", "status", "--short"], text=True, stderr=subprocess.DEVNULL)
        branch = subprocess.check_output(["git", "branch", "--show-current"], text=True, stderr=subprocess.DEVNULL).strip()
        changes = [line.strip() for line in status.strip().split("\n") if line.strip()]
        return {"branch": branch, "dirty": bool(changes), "changes": changes}
    except Exception as e:
        return {"branch": "unknown", "dirty": False, "changes": [], "error": str(e)}

def get_last_commit_message():
    try:
        return subprocess.check_output(["git", "log", "-1", "--pretty=%B"], text=True, stderr=subprocess.DEVNULL).strip()
    except:
        return ""

# ============================================================
# PROJECT_LOG 解析
# ============================================================

def parse_project_log():
    if not PROJECT_LOG.exists():
        return {"active_tasks": [], "blockers": [], "today_done": []}

    content = PROJECT_LOG.read_text(encoding='utf-8')
    result = {"active_tasks": [], "blockers": [], "today_done": []}

    # 解析活跃任务
    active_match = re.search(r'## 活跃任务\s*\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
    if active_match:
        active_text = active_match.group(1).strip()
        if active_text and not active_text.startswith('*'):
            for line in active_text.split('\n'):
                task = parse_task_line(line)
                if task:
                    result["active_tasks"].append(task)

    # 解析阻塞项
    blocker_match = re.search(r'## 阻塞项\s*\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
    if blocker_match:
        blocker_text = blocker_match.group(1).strip()
        for line in blocker_text.split('\n'):
            line = line.strip()
            if line and line.startswith('- '):
                result["blockers"].append(line[2:].strip())

    # 解析今日已完成（找第一个日期块）
    today_match = re.search(r'## (\d{4}-\d{2}-\d{2})\s*\n.*?### 已完成\s*\n(.*?)(?=###|\n## |\Z)', content, re.DOTALL)
    if today_match:
        done_text = today_match.group(2).strip()
        for line in done_text.split('\n'):
            line = line.strip()
            if line.startswith('- [x]'):
                result["today_done"].append(line[5:].strip())

    return result

def parse_task_line(line):
    """解析活跃任务行，如: - [ ] [driver-dev] ST7789 驱动开发 (since 2026-04-16)"""
    m = re.match(r'- \[([ x])\] \[(\w+)\] (.+?)(?: \(since (\d{4}-\d{2}-\d{2})\))?$', line.strip())
    if not m:
        return None
    done = m.group(1) == 'x'
    task_type = m.group(2)
    title = m.group(3).strip()
    since = m.group(4)

    # 尝试从后续行解析 meta（简单实现：在 log 文本里找这个任务的详细块）
    meta = {"title": title}
    if PROJECT_LOG.exists():
        content = PROJECT_LOG.read_text(encoding='utf-8')
        # 找到这一行后面紧跟的缩进内容
        pattern = re.escape(line.strip()) + r'\n((?:  .*(?:\n|$))*)'
        mm = re.search(pattern, content)
        if mm:
            for meta_line in mm.group(1).strip().split('\n'):
                meta_line = meta_line.strip()
                if meta_line.startswith('- '):
                    kv = meta_line[2:].split(':', 1)
                    if len(kv) == 2:
                        meta[kv[0].strip()] = kv[1].strip()

    return {"done": done, "type": task_type, "title": title, "since": since, "meta": meta}

# ============================================================
# 状态探测
# ============================================================

def check_build_status():
    """简单探测最近一次编译是否成功"""
    if not BUILD_LOG.exists():
        return "unknown", "无编译记录"
    log = BUILD_LOG.read_text(encoding='utf-8', errors='ignore')
    generic_exit = re.findall(r'\[workflow\] exit_code=(\d+)', log)
    if generic_exit:
        return ("success", "编译成功") if int(generic_exit[-1]) == 0 else ("failed", f"编译失败: exit_code={generic_exit[-1]}")
    # Keil 编译成功通常包含 0 Error(s)
    errors = re.findall(r'(\d+) Error\(s\)', log)
    warnings = re.findall(r'(\d+) Warning\(s\)', log)
    if errors:
        last_err = int(errors[-1])
        last_warn = int(warnings[-1]) if warnings else 0
        if last_err > 0:
            return "failed", f"编译失败: {last_err} Error(s), {last_warn} Warning(s)"
        return "success", f"编译成功: {last_err} Error(s), {last_warn} Warning(s)"
    return "unknown", "无法解析编译日志"

def check_code_review():
    if not REPORT_FILES["code_review"].exists():
        return "none", ""
    report = REPORT_FILES["code_review"].read_text(encoding='utf-8')
    if "🔴 [严重]" in report:
        return "critical", report
    if "🟡 [警告]" in report:
        return "warning", report
    return "pass", report

def check_driver_state(name):
    """检查 driver-dev 任务的当前状态"""
    driver_c = DRIVER_DIR / f"{name}_driver.c"
    driver_h = DRIVER_DIR / f"{name}_driver.h"
    test_c = TEST_DIR / f"{name}_driver_test.c"

    if not driver_c.exists():
        return "missing", "驱动源文件不存在"

    size = driver_c.stat().st_size
    content = driver_c.read_text(encoding='utf-8', errors='ignore')

    # 骨架特征：大量 TODO 或文件很小
    todo_count = content.count("TODO")
    if size < 800 or todo_count >= 3:
        return "skeleton", "驱动文件为骨架状态，需要填充实现"

    # 有实质内容了
    return "implemented", "驱动文件已有实质内容"

# ============================================================
# 决策引擎
# ============================================================

def determine_next_step():
    log = parse_project_log()
    git = get_git_status()
    build_status, build_msg = check_build_status()
    review_status, review_report = check_code_review()

    # 1. 阻塞项检查
    if log["blockers"]:
        return {
            "action": "pause",
            "reason": "存在阻塞项，需要解决后才能继续",
            "blockers": log["blockers"],
            "suggestion": "请处理阻塞项后重新运行 /dev --go"
        }

    # 2. 活跃任务驱动
    for task in log["active_tasks"]:
        if task["type"] == "driver-dev":
            name = task["meta"].get("name", "")
            if not name:
                # 尝试从标题里提取
                m = re.search(r'(\w+)', task["title"])
                name = m.group(1).lower() if m else ""

            driver_state, driver_msg = check_driver_state(name)

            if driver_state in ("missing", "skeleton"):
                return {
                    "action": "driver-dev",
                    "args": {
                        "source": task["meta"].get("资料", ""),
                        "name": name,
                        "interface": task["meta"].get("接口", "")
                    },
                    "reason": driver_msg,
                    "task": task
                }

            # 已生成，先 review
            if review_status == "none":
                return {
                    "action": "code-reviewer",
                    "args": f"{DRIVER_DIR}/{name}_driver.c {TEST_DIR}/{name}_driver_test.c",
                    "reason": "驱动已生成，需要代码审查",
                    "task": task
                }

            if review_status == "critical":
                return {
                    "action": "pause",
                    "reason": "code-review 发现严重问题，必须修复后才能继续",
                    "task": task,
                    "report_summary": review_report[:800] if isinstance(review_report, str) else ""
                }

            # review 通过或只有警告，继续 build
            if build_status == "failed":
                return {
                    "action": "build",
                    "reason": f"代码审查通过，但编译失败: {build_msg}",
                    "task": task
                }

            if build_status in ("unknown", "success"):
                return {
                    "action": "build",
                    "reason": "驱动已生成且审查通过，需要编译验证",
                    "task": task
                }

        # 其他任务类型的扩展点...
        if task["type"] == "verify":
            return {
                "action": "verify",
                "reason": "需要执行完整验证流程",
                "task": task
            }

    # 3. 没有活跃任务时，检查是否有未提交的改动
    if git["dirty"]:
        return {
            "action": "pause",
            "reason": "工作区有未提交修改",
            "changes": git["changes"],
            "suggestion": "建议运行 /dev --wrap 结束今日工作并生成 commit"
        }

    # 4. 空闲
    return {
        "action": "idle",
        "reason": "当前没有活跃任务，也没有待处理的改动",
        "suggestion": "可以新建一个需求 (/req) 或开始驱动开发 (/driver-dev)"
    }

# ============================================================
# 日志操作
# ============================================================

def ensure_log_structure():
    if PROJECT_LOG.exists():
        return
    PROJECT_LOG.write_text(
        "# 项目开发日志\n\n"
        "## 活跃任务\n*暂无活跃任务*\n\n"
        "## 阻塞项\n*暂无阻塞项*\n\n",
        encoding='utf-8'
    )

def set_active_task(task_type, title, meta_dict):
    ensure_log_structure()
    content = PROJECT_LOG.read_text(encoding='utf-8')
    today = datetime.now().strftime("%Y-%m-%d")

    meta_lines = ""
    for k, v in meta_dict.items():
        meta_lines += f"  - {k}: {v}\n"

    new_task = f"- [ ] [{task_type}] {title} (since {today})\n{meta_lines}"

    # 替换活跃任务块
    if "*暂无活跃任务*" in content:
        content = content.replace("*暂无活跃任务*\n", new_task)
    else:
        # 在活跃任务块末尾追加
        active_match = re.search(r'(## 活跃任务\s*\n)(.*?)(?=\n## |\Z)', content, re.DOTALL)
        if active_match:
            insert_pos = active_match.end()
            content = content[:insert_pos] + new_task + content[insert_pos:]
        else:
            # 没有活跃任务块，插入
            content = content.replace("# 项目开发日志\n", f"# 项目开发日志\n\n## 活跃任务\n{new_task}\n")

    PROJECT_LOG.write_text(content, encoding='utf-8')
    print(f"✅ 已设置活跃任务: [{task_type}] {title}")

def clear_active_tasks():
    if not PROJECT_LOG.exists():
        return
    content = PROJECT_LOG.read_text(encoding='utf-8')
    content = re.sub(r'## 活跃任务\s*\n.*?\n(?=## |\Z)', '## 活跃任务\n*暂无活跃任务*\n\n', content, flags=re.DOTALL)
    PROJECT_LOG.write_text(content, encoding='utf-8')
    print("✅ 已清空活跃任务")

def append_log_entry(text, section="进行中"):
    ensure_log_structure()
    content = PROJECT_LOG.read_text(encoding='utf-8')
    today = datetime.now().strftime("%Y-%m-%d")

    # 检查今日块是否存在
    date_header = f"## {today}"
    if date_header not in content:
        # 在历史前面插入今日块
        entry = f"{date_header}\n### {section}\n- {text}\n\n"
        # 插入到第一个 ## 20xx-xx-xx 之前，或阻塞项之后
        first_date = re.search(r'\n## \d{4}-\d{2}-\d{2}', content)
        if first_date:
            pos = first_date.start() + 1
            content = content[:pos] + entry + content[pos:]
        else:
            content += "\n" + entry
    else:
        # 在今日块的对应 section 追加
        # 简单处理：在日期块内找 section
        pattern = rf"({re.escape(date_header)}.*?### {re.escape(section)}\n)(.*?)(?=###|\n## |\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            insert_pos = match.start(2) + len(match.group(2))
            content = content[:insert_pos] + f"- {text}\n" + content[insert_pos:]
        else:
            # section 不存在，在日期块末尾加
            pattern2 = rf"({re.escape(date_header)}.*?)(?=\n## |\Z)"
            match2 = re.search(pattern2, content, re.DOTALL)
            if match2:
                insert_pos = match2.end()
                content = content[:insert_pos] + f"### {section}\n- {text}\n" + content[insert_pos:]

    PROJECT_LOG.write_text(content, encoding='utf-8')
    print(f"✅ 已追加日志: {text}")

def wrap_day():
    """结束今日工作，生成总结"""
    ensure_log_structure()
    git = get_git_status()
    build_status, build_msg = check_build_status()
    review_status, _ = check_code_review()
    log = parse_project_log()

    today = datetime.now().strftime("%Y-%m-%d")
    summary = []
    summary.append(f"## {today} 日终总结")
    summary.append(f"- 分支: {git['branch']}")
    summary.append(f"- 工作区状态: {'有未提交修改' if git['dirty'] else '干净'}")
    if log["today_done"]:
        summary.append(f"- 今日完成任务: {len(log['today_done'])} 项")
    if log["active_tasks"]:
        summary.append(f"- 活跃任务: {len(log['active_tasks'])} 项")
    if log["blockers"]:
        summary.append(f"- 阻塞项: {len(log['blockers'])} 项 ⚠️")
    summary.append(f"- 编译状态: {build_msg}")
    summary.append(f"- 代码审查: {review_status}")

    # 推荐 commit message
    if git["dirty"]:
        files = [c.split()[-1] for c in git["changes"]]
        if log["today_done"]:
            msg = f"Update: {log['today_done'][0]}"
        else:
            msg = f"Update: {', '.join(files[:3])}"
        summary.append(f"\n### 推荐 Commit")
        summary.append(f"```bash")
        summary.append(f"git add ...")
        summary.append(f'git commit -m "{msg}"')
        summary.append(f"```")

    result = "\n".join(summary)
    print(result)
    return result

# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Dev Orchestrator")
    parser.add_argument("--query-next-step", action="store_true", help="查询下一步行动")
    parser.add_argument("--wrap", action="store_true", help="结束今日工作")
    parser.add_argument("--log-entry", help="追加日志条目")
    parser.add_argument("--log-section", default="进行中", help="日志条目所属 section")
    parser.add_argument("--set-active", help="设置活跃任务 JSON")
    parser.add_argument("--clear-active", action="store_true", help="清空活跃任务")
    parser.add_argument("--mark-done", help="将指定标题的活跃任务标记为完成")

    args = parser.parse_args()

    if args.query_next_step:
        step = determine_next_step()
        print(json.dumps(step, ensure_ascii=False, indent=2))
    elif args.wrap:
        wrap_day()
    elif args.log_entry:
        append_log_entry(args.log_entry, args.log_section)
    elif args.set_active:
        data = json.loads(args.set_active)
        set_active_task(data["type"], data["title"], data.get("meta", {}))
    elif args.clear_active:
        clear_active_tasks()
    elif args.mark_done:
        # 简单实现：找到标题匹配的任务，把 [ ] 改成 [x]
        if PROJECT_LOG.exists():
            content = PROJECT_LOG.read_text(encoding='utf-8')
            content = content.replace(f"] {args.mark_done}", f"] {args.mark_done}")
            # 更精确：替换活跃任务里的 [ ]
            pattern = rf'(- )\[ \](.*?{re.escape(args.mark_done)}.*?\n)'
            content = re.sub(pattern, r'\1[x]\2', content)
            PROJECT_LOG.write_text(content, encoding='utf-8')
            print(f"✅ 已标记完成: {args.mark_done}")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
