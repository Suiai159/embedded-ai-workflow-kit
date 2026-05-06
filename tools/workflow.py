#!/usr/bin/env python3
"""
Reusable project workflow CLI.

The workflow layer keeps Skills and scripts independent from a specific board,
project name, or development tool. The current implementation provides Keil,
GCC command, and CMake adapters.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ROOT_MARKERS = (".workflow/project.yaml", "CLAUDE.md", ".git")


class WorkflowError(RuntimeError):
    pass


def ensure_utf8_stdio() -> None:
    if sys.platform != "win32":
        return
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def find_project_root(start: Optional[Path] = None) -> Path:
    current = (start or Path.cwd()).resolve()
    while True:
        if any((current / marker).exists() for marker in ROOT_MARKERS):
            return current
        if current == current.parent:
            return (start or Path.cwd()).resolve()
        current = current.parent


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    try:
        return int(value)
    except ValueError:
        return value


def parse_simple_yaml(text: str) -> Dict[str, Any]:
    """Parse the small nested key/value YAML shape used by project.yaml."""
    root: Dict[str, Any] = {}
    stack: List[tuple[int, Dict[str, Any]]] = [(-1, root)]

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        item = line.strip()
        if ":" not in item:
            raise WorkflowError(f"Unsupported YAML line: {raw_line}")

        key, value = item.split(":", 1)
        key = key.strip()
        value = value.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if value == "":
            child: Dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = parse_scalar(value)

    return root


def load_config(root: Path) -> Dict[str, Any]:
    config_path = root / ".workflow" / "project.yaml"
    if not config_path.exists():
        raise WorkflowError(f"Missing workflow config: {config_path}")

    text = config_path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text) or {}
    except Exception:
        data = parse_simple_yaml(text)

    if not isinstance(data, dict):
        raise WorkflowError("Workflow config must be a YAML mapping")
    return data


def cfg_get(config: Dict[str, Any], dotted_key: str, default: Any = None) -> Any:
    current: Any = config
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def require_config(config: Dict[str, Any], keys: Iterable[str]) -> None:
    missing = [key for key in keys if cfg_get(config, key) in (None, "")]
    if missing:
        raise WorkflowError("Missing required config key(s): " + ", ".join(missing))


def resolve_project_path(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (root / path).resolve()


def toolchain_type(config: Dict[str, Any]) -> str:
    return str(cfg_get(config, "toolchain.type", "")).lower()


def flash_method(config: Dict[str, Any]) -> str:
    return str(cfg_get(config, "flash.method", "")).lower()


def require_toolchain(config: Dict[str, Any], supported: Iterable[str]) -> str:
    toolchain = toolchain_type(config)
    if toolchain not in supported:
        raise WorkflowError(f"Unsupported toolchain adapter: {toolchain}")
    return toolchain


def shell_join(command: Any) -> str:
    if isinstance(command, list):
        return " ".join(str(part) for part in command)
    return str(command)


def split_args(value: Any) -> List[str]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return shlex.split(str(value), posix=(sys.platform != "win32"))


def test_mode_env(test_mode: bool) -> Dict[str, str]:
    env = os.environ.copy()
    if test_mode:
        env["WORKFLOW_TEST_MODE"] = "1"
        for key in ("CFLAGS", "CPPFLAGS", "CXXFLAGS"):
            old = env.get(key, "")
            env[key] = (old + " -DTEST_MODE").strip()
    return env


def run_hidden(args: List[str], timeout: int) -> subprocess.CompletedProcess[str]:
    kwargs: Dict[str, Any] = {
        "capture_output": True,
        "text": True,
        "timeout": timeout,
    }
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        kwargs["startupinfo"] = startupinfo
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.run(args, **kwargs)


def run_logged_command(
    command: str,
    log_file: Path,
    cwd: Path,
    timeout: int,
    env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess[str]:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text("", encoding="utf-8")
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    log_file.write_text(
        (result.stdout or "") + (result.stderr or "") + f"\n[workflow] exit_code={result.returncode}\n",
        encoding="utf-8",
    )
    return result


def run_logged_args(
    args: List[str],
    log_file: Path,
    cwd: Path,
    timeout: int,
    env: Optional[Dict[str, str]] = None,
    append: bool = False,
) -> subprocess.CompletedProcess[str]:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        args,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    mode = "a" if append else "w"
    with log_file.open(mode, encoding="utf-8") as f:
        f.write("$ " + " ".join(args) + "\n")
        f.write(result.stdout or "")
        f.write(result.stderr or "")
        f.write(f"\n[workflow] exit_code={result.returncode}\n")
    return result


def print_log(title: str, log_file: Path, result: subprocess.CompletedProcess[str]) -> None:
    print("")
    print(f"{title} Log:")
    print("================================")
    if log_file.exists():
        print(log_file.read_text(encoding="utf-8", errors="ignore"))
    else:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    print("================================")


def artifact_exists(root: Path, config: Dict[str, Any]) -> bool:
    for key in ("build.hex_path", "build.elf_path", "build.bin_path"):
        value = cfg_get(config, key)
        if value and resolve_project_path(root, str(value)).exists():
            return True
    return False


def inject_test_mode(project_file: Path) -> None:
    tree = ET.parse(project_file)
    root = tree.getroot()

    for target in root.iter("Target"):
        for define in target.iter("Define"):
            values = [item.strip() for item in (define.text or "").split(",") if item.strip()]
            if "TEST_MODE" not in values:
                values.append("TEST_MODE")
            define.text = ",".join(values)
            tree.write(project_file, encoding="UTF-8", xml_declaration=True)
            return

    raise WorkflowError(f"Could not find Define node in {project_file}")


def command_verify_config(root: Path, config: Dict[str, Any]) -> int:
    require_config(config, ["project.name", "toolchain.type", "layout.driver", "layout.test", "layout.reports"])
    toolchain = require_toolchain(config, ("keil", "gcc", "cmake"))

    if toolchain == "keil":
        require_config(config, ["toolchain.project_file", "toolchain.exe", "build.hex_path"])
    elif toolchain == "gcc":
        require_config(config, ["build.command"])
    elif toolchain == "cmake":
        require_config(config, ["toolchain.source_dir", "toolchain.build_dir"])

    summary = {
        "project": cfg_get(config, "project.name"),
        "board": cfg_get(config, "board.name", ""),
        "mcu": cfg_get(config, "mcu.family", ""),
        "toolchain": toolchain,
        "hex_path": str(resolve_project_path(root, str(cfg_get(config, "build.hex_path"))))
        if cfg_get(config, "build.hex_path")
        else "",
        "elf_path": str(resolve_project_path(root, str(cfg_get(config, "build.elf_path"))))
        if cfg_get(config, "build.elf_path")
        else "",
        "build_log": str(resolve_project_path(root, str(cfg_get(config, "build.log_path", "tools/build_log.txt")))),
    }
    if toolchain == "keil":
        summary["project_file"] = str(resolve_project_path(root, str(cfg_get(config, "toolchain.project_file"))))
        summary["toolchain_exe"] = str(Path(str(cfg_get(config, "toolchain.exe"))))
    elif toolchain == "gcc":
        summary["build_command"] = shell_join(cfg_get(config, "build.command"))
        summary["test_command"] = shell_join(cfg_get(config, "build.test_command", ""))
    elif toolchain == "cmake":
        summary["source_dir"] = str(resolve_project_path(root, str(cfg_get(config, "toolchain.source_dir"))))
        summary["build_dir"] = str(resolve_project_path(root, str(cfg_get(config, "toolchain.build_dir"))))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def command_build(root: Path, config: Dict[str, Any], test_mode: bool) -> int:
    toolchain = require_toolchain(config, ("keil", "gcc", "cmake"))
    if toolchain == "keil":
        return build_keil(root, config, test_mode)
    if toolchain == "gcc":
        return build_gcc(root, config, test_mode)
    if toolchain == "cmake":
        return build_cmake(root, config, test_mode)
    raise WorkflowError(f"Unsupported build adapter: {toolchain}")


def build_keil(root: Path, config: Dict[str, Any], test_mode: bool) -> int:
    require_config(config, ["project.name", "toolchain.project_file", "toolchain.exe", "build.hex_path"])

    project_name = str(cfg_get(config, "project.name"))
    project_file = resolve_project_path(root, str(cfg_get(config, "toolchain.project_file")))
    log_file = resolve_project_path(root, str(cfg_get(config, "build.log_path", "tools/build_log.txt")))
    hex_file = resolve_project_path(root, str(cfg_get(config, "build.hex_path")))
    uv4 = Path(str(cfg_get(config, "toolchain.exe")))

    if not uv4.exists():
        raise WorkflowError(f"Keil not found at {uv4}")
    if not project_file.exists():
        raise WorkflowError(f"Project file not found at {project_file}")

    print(f"Building {project_name}{' in TEST_MODE' if test_mode else ''}...")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text("", encoding="utf-8")

    backup_file: Optional[Path] = None
    try:
        if test_mode:
            backup_file = project_file.with_suffix(project_file.suffix + ".bak")
            shutil.copy2(project_file, backup_file)
            inject_test_mode(project_file)

        result = run_hidden(
            [str(uv4), "-b", str(project_file), "-j0", "-o", str(log_file)],
            timeout=180,
        )
    finally:
        if backup_file and backup_file.exists():
            shutil.copy2(backup_file, project_file)
            backup_file.unlink()

    print_log("Build", log_file, result)

    log = log_file.read_text(encoding="utf-8", errors="ignore") if log_file.exists() else ""
    if result.returncode == 0 and "0 Error(s)" in log and hex_file.exists():
        print("")
        print("Build successful!")
        print(f"Hex file: {hex_file.name}")
        print(f"Size: {hex_file.stat().st_size} bytes")
        return 0

    print("")
    print("Build failed! Check log above for details.")
    return result.returncode or 1


def build_gcc(root: Path, config: Dict[str, Any], test_mode: bool) -> int:
    require_config(config, ["project.name", "build.command"])

    project_name = str(cfg_get(config, "project.name"))
    log_file = resolve_project_path(root, str(cfg_get(config, "build.log_path", "tools/build_log.txt")))
    command_value = cfg_get(config, "build.test_command" if test_mode else "build.command")
    if not command_value:
        command_value = cfg_get(config, "build.command")
    command = shell_join(command_value)
    if not command or command == "None":
        command = shell_join(cfg_get(config, "build.command"))

    print(f"Building {project_name} with GCC command adapter{' in TEST_MODE' if test_mode else ''}...")
    print(f"Command: {command}")
    result = run_logged_command(
        command,
        log_file,
        root,
        int(cfg_get(config, "build.timeout_sec", 180)),
        env=test_mode_env(test_mode),
    )
    print_log("Build", log_file, result)

    if result.returncode == 0 and (artifact_exists(root, config) or not cfg_get(config, "build.hex_path")):
        print("")
        print("Build successful!")
        return 0

    print("")
    print("Build failed! Check log above for details.")
    return result.returncode or 1


def build_cmake(root: Path, config: Dict[str, Any], test_mode: bool) -> int:
    require_config(config, ["project.name", "toolchain.source_dir", "toolchain.build_dir"])

    project_name = str(cfg_get(config, "project.name"))
    source_dir = resolve_project_path(root, str(cfg_get(config, "toolchain.source_dir")))
    build_dir = resolve_project_path(root, str(cfg_get(config, "toolchain.build_dir")))
    log_file = resolve_project_path(root, str(cfg_get(config, "build.log_path", "tools/build_log.txt")))
    cmake = str(cfg_get(config, "toolchain.cmake", "cmake"))

    configure_args = [
        cmake,
        "-S",
        str(source_dir),
        "-B",
        str(build_dir),
    ]
    generator = cfg_get(config, "toolchain.generator")
    if generator:
        configure_args.extend(["-G", str(generator)])
    build_type = cfg_get(config, "toolchain.build_type")
    if build_type:
        configure_args.append(f"-DCMAKE_BUILD_TYPE={build_type}")
    configure_args.extend(split_args(cfg_get(config, "toolchain.configure_args")))
    if test_mode:
        configure_args.extend(split_args(cfg_get(config, "toolchain.test_configure_args", "-DTEST_MODE=ON")))

    target = cfg_get(config, "build.test_target" if test_mode else "build.target", "")
    build_args = [cmake, "--build", str(build_dir)]
    if target:
        build_args.extend(["--target", str(target)])
    build_args.extend(split_args(cfg_get(config, "build.args")))

    print(f"Configuring {project_name} with CMake{' in TEST_MODE' if test_mode else ''}...")
    print("Command: " + " ".join(configure_args))
    configure_result = run_logged_args(
        configure_args,
        log_file,
        root,
        int(cfg_get(config, "build.timeout_sec", 180)),
        env=test_mode_env(test_mode),
    )
    if configure_result.returncode != 0:
        print_log("Build", log_file, configure_result)
        print("")
        print("CMake configure failed!")
        return configure_result.returncode or 1

    print(f"Building {project_name} with CMake...")
    print("Command: " + " ".join(build_args))
    build_result = run_logged_args(
        build_args,
        log_file,
        root,
        int(cfg_get(config, "build.timeout_sec", 180)),
        env=test_mode_env(test_mode),
        append=True,
    )
    print_log("Build", log_file, build_result)

    if build_result.returncode == 0 and (artifact_exists(root, config) or not cfg_get(config, "build.hex_path")):
        print("")
        print("Build successful!")
        return 0

    print("")
    print("Build failed! Check log above for details.")
    return build_result.returncode or 1


def command_flash(root: Path, config: Dict[str, Any]) -> int:
    toolchain = require_toolchain(config, ("keil", "gcc", "cmake"))
    method = flash_method(config) or ("keil" if toolchain == "keil" else "command")
    if method == "keil":
        return flash_keil(root, config)
    if method == "command":
        return flash_command(root, config)
    raise WorkflowError(f"Unsupported flash method: {method}")


def flash_keil(root: Path, config: Dict[str, Any]) -> int:
    require_config(config, ["project.name", "toolchain.project_file", "toolchain.exe", "build.hex_path"])

    project_name = str(cfg_get(config, "project.name"))
    project_file = resolve_project_path(root, str(cfg_get(config, "toolchain.project_file")))
    log_file = resolve_project_path(root, str(cfg_get(config, "flash.log_path", "tools/flash_log.txt")))
    hex_file = resolve_project_path(root, str(cfg_get(config, "build.hex_path")))
    uv4 = Path(str(cfg_get(config, "toolchain.exe")))

    if not uv4.exists():
        raise WorkflowError(f"Keil not found at {uv4}")
    if not project_file.exists():
        raise WorkflowError(f"Project file not found at {project_file}")
    if not hex_file.exists():
        raise WorkflowError(f"Hex file not found. Please build first. Expected: {hex_file}")

    print(f"Flashing {project_name} using {cfg_get(config, 'flash.method', 'keil')}...")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text("", encoding="utf-8")

    result = run_hidden(
        [str(uv4), "-f", str(project_file), "-j0", "-o", str(log_file)],
        timeout=120,
    )

    print_log("Flash", log_file, result)

    if result.returncode == 0:
        print("")
        print("Flash successful!")
        return 0

    print("")
    print("Flash failed! Check log above for details.")
    return result.returncode or 1


def flash_command(root: Path, config: Dict[str, Any]) -> int:
    require_config(config, ["project.name", "flash.command"])

    project_name = str(cfg_get(config, "project.name"))
    log_file = resolve_project_path(root, str(cfg_get(config, "flash.log_path", "tools/flash_log.txt")))
    command = shell_join(cfg_get(config, "flash.command"))

    if not artifact_exists(root, config) and any(cfg_get(config, key) for key in ("build.hex_path", "build.elf_path", "build.bin_path")):
        raise WorkflowError("Configured firmware artifact not found. Please build first.")

    print(f"Flashing {project_name} using command adapter...")
    print(f"Command: {command}")
    result = run_logged_command(
        command,
        log_file,
        root,
        int(cfg_get(config, "flash.timeout_sec", 120)),
    )
    print_log("Flash", log_file, result)

    if result.returncode == 0:
        print("")
        print("Flash successful!")
        return 0

    print("")
    print("Flash failed! Check log above for details.")
    return result.returncode or 1


def find_group(groups: ET.Element, name: str) -> Optional[ET.Element]:
    for group in groups:
        group_name = group.find("GroupName")
        if group_name is not None and group_name.text == name:
            return group
    return None


def create_file_node(filename: str, filepath: str) -> ET.Element:
    file_node = ET.Element("File")
    fn = ET.SubElement(file_node, "FileName")
    fn.text = filename
    ft = ET.SubElement(file_node, "FileType")
    ft.text = "1" if filename.endswith(".c") else "5"
    fp = ET.SubElement(file_node, "FilePath")
    fp.text = filepath
    return file_node


def add_file_to_group(groups: ET.Element, group_name: str, filename: str, filepath: str) -> bool:
    group = find_group(groups, group_name)
    if group is None:
        group = ET.SubElement(groups, "Group")
        gn = ET.SubElement(group, "GroupName")
        gn.text = group_name
        files_node = ET.SubElement(group, "Files")
        print(f"New group: {group_name}")
    else:
        files_node = group.find("Files")
        if files_node is None:
            files_node = ET.SubElement(group, "Files")

    for existing in files_node.findall("File"):
        fp = existing.find("FilePath")
        if fp is not None and fp.text == filepath:
            print(f"Skip existing file: {filepath} in {group_name}")
            return False

    files_node.append(create_file_node(filename, filepath))
    print(f"Add file: {filepath} -> {group_name}")
    return True


def command_register_driver(root: Path, config: Dict[str, Any], name: str) -> int:
    toolchain = require_toolchain(config, ("keil", "gcc", "cmake"))
    if toolchain == "keil":
        return register_driver_keil(root, config, name)
    command = cfg_get(config, "register_driver.command")
    if command:
        return register_driver_command(root, config, name)

    driver_name = name.lower().replace(" ", "_")
    driver_dir = cfg_get(config, "layout.driver", "Driver")
    test_dir = cfg_get(config, "layout.test", "Test")
    print(
        "No project registration needed for "
        f"{toolchain}; expected files are {driver_dir}/{driver_name}_driver.c "
        f"and {test_dir}/{driver_name}_driver_test.c"
    )
    return 0


def register_driver_keil(root: Path, config: Dict[str, Any], name: str) -> int:
    require_config(config, ["toolchain.project_file", "layout.driver", "layout.test"])

    driver_name = name.lower().replace(" ", "_")
    project_file = resolve_project_path(root, str(cfg_get(config, "toolchain.project_file")))
    driver_dir = str(cfg_get(config, "layout.driver"))
    test_dir = str(cfg_get(config, "layout.test"))
    driver_group = str(cfg_get(config, "toolchain.groups.driver", "Driver"))
    test_group = str(cfg_get(config, "toolchain.groups.test", "Test"))

    if not project_file.exists():
        raise WorkflowError(f"Project file not found: {project_file}")

    tree = ET.parse(project_file)
    xml_root = tree.getroot()
    groups = xml_root.find(".//Groups")
    if groups is None:
        raise WorkflowError("Keil project has no Groups node")

    driver_c = f"{driver_name}_driver.c"
    test_c = f"{driver_name}_driver_test.c"
    driver_path = f"../{driver_dir}/{driver_c}"
    test_path = f"../{test_dir}/{test_c}"

    modified = False
    modified |= add_file_to_group(groups, driver_group, driver_c, driver_path)
    modified |= add_file_to_group(groups, test_group, test_c, test_path)

    if modified:
        tree.write(project_file, encoding="UTF-8", xml_declaration=True)
        print(f"Project updated: {project_file}")
    else:
        print("No project update needed")
    return 0


def register_driver_command(root: Path, config: Dict[str, Any], name: str) -> int:
    require_config(config, ["register_driver.command"])
    driver_name = name.lower().replace(" ", "_")
    driver_dir = str(cfg_get(config, "layout.driver", "Driver"))
    test_dir = str(cfg_get(config, "layout.test", "Test"))
    command = shell_join(cfg_get(config, "register_driver.command")).format(
        name=driver_name,
        driver_c=f"{driver_dir}/{driver_name}_driver.c",
        driver_h=f"{driver_dir}/{driver_name}_driver.h",
        test_c=f"{test_dir}/{driver_name}_driver_test.c",
    )
    log_file = resolve_project_path(root, str(cfg_get(config, "register_driver.log_path", "tools/register_driver_log.txt")))
    print(f"Registering driver with command adapter: {command}")
    result = run_logged_command(command, log_file, root, int(cfg_get(config, "register_driver.timeout_sec", 60)))
    print_log("Register Driver", log_file, result)
    return result.returncode


def command_status(root: Path, config: Dict[str, Any]) -> int:
    project_file_value = cfg_get(config, "toolchain.project_file", "")
    hex_file_value = cfg_get(config, "build.hex_path", "")
    elf_file_value = cfg_get(config, "build.elf_path", "")
    project_file = resolve_project_path(root, str(project_file_value)) if project_file_value else None
    hex_file = resolve_project_path(root, str(hex_file_value)) if hex_file_value else None
    elf_file = resolve_project_path(root, str(elf_file_value)) if elf_file_value else None
    status = {
        "project": cfg_get(config, "project.name"),
        "board": cfg_get(config, "board.name", ""),
        "toolchain": cfg_get(config, "toolchain.type", ""),
        "project_file_exists": project_file.exists() if project_file else False,
        "hex_exists": hex_file.exists() if hex_file else False,
        "elf_exists": elf_file.exists() if elf_file else False,
        "hex_path": str(hex_file) if hex_file else "",
        "elf_path": str(elf_file) if elf_file else "",
    }
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0


def refresh_runtime_context(root: Path) -> None:
    context_tool = root / "tools" / "context.py"
    if not context_tool.exists() or not (root / ".context" / "runtime.yaml").exists():
        return
    try:
        subprocess.run(
            [sys.executable, str(context_tool), "touch-runtime"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except Exception:
        pass


def main() -> int:
    ensure_utf8_stdio()

    parser = argparse.ArgumentParser(description="Reusable embedded workflow CLI")
    parser.add_argument("--config", default=".workflow/project.yaml", help="Workflow config path")
    sub = parser.add_subparsers(dest="command", required=True)

    build_parser = sub.add_parser("build", help="Build using configured toolchain adapter")
    build_parser.add_argument("--test", action="store_true", help="Inject TEST_MODE for this build")

    sub.add_parser("flash", help="Flash configured firmware artifact")
    sub.add_parser("status", help="Print workflow status as JSON")
    sub.add_parser("verify-config", help="Validate and print resolved workflow config")

    register_parser = sub.add_parser("register-driver", help="Register driver/test files in project")
    register_parser.add_argument("--name", required=True, help="Driver name, e.g. st7789")

    args = parser.parse_args()

    if args.config != ".workflow/project.yaml":
        config_path = Path(args.config)
        if not config_path.is_absolute():
            config_path = (Path.cwd() / config_path).resolve()
        root = find_project_root(config_path.parent)
        try:
            import yaml  # type: ignore

            config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except Exception:
            config = parse_simple_yaml(config_path.read_text(encoding="utf-8"))
    else:
        root = find_project_root()
        config = load_config(root)

    try:
        if args.command == "build":
            result = command_build(root, config, args.test)
            refresh_runtime_context(root)
            return result
        if args.command == "flash":
            result = command_flash(root, config)
            refresh_runtime_context(root)
            return result
        if args.command == "register-driver":
            return command_register_driver(root, config, args.name)
        if args.command == "status":
            return command_status(root, config)
        if args.command == "verify-config":
            return command_verify_config(root, config)
    except WorkflowError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
