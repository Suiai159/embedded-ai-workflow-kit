#!/usr/bin/env python3
"""
Agent验证Skill主程序
实现编译→烧录→测试→修复的闭环验证
"""

import sys
import argparse
import yaml
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# 导入验证模块
from requirement_parser import RequirementParser
from serial_executor import SerialTestExecutor
from comparator import OutputComparator
from error_analyzer import ErrorAnalyzer
from code_fixer import CodeFixer


@dataclass
class ValidationResult:
    """验证结果"""
    passed: bool
    test_results: List[Dict]
    retry_count: int
    fixes_applied: List[str]
    error_message: Optional[str] = None


class ValidationController:
    """验证流程控制器"""

    def __init__(self, config: Dict[str, Any], single_run: bool = False):
        self.config = config
        self.project_root = Path(config.get('project_root', Path.cwd()))
        self.single_run = single_run
        self.parser = RequirementParser()
        self.executor = SerialTestExecutor(config.get('serial', {}))
        self.comparator = OutputComparator()
        self.analyzer = ErrorAnalyzer()
        self.fixer = CodeFixer()
        self.retry_count = 0
        self.max_retries = config.get('validation', {}).get('max_retries', 3)
        self.auto_fix = config.get('validation', {}).get('auto_fix', True)
        self.fixes_applied = []

    def run(self, req_file: str) -> ValidationResult:
        """执行完整验证流程"""
        print("="*60)
        print("Agent验证Skill启动")
        print("="*60)

        # 1. 解析需求文档
        print("\n[1/7] 解析需求文档...")
        try:
            test_cases = self.parser.parse(req_file)
            print(f"  ✓ 解析到 {len(test_cases)} 个测试用例")
        except Exception as e:
            return ValidationResult(
                passed=False,
                test_results=[],
                retry_count=0,
                fixes_applied=[],
                error_message=f"解析需求文档失败: {e}"
            )

        # 进入验证循环
        while self.retry_count <= self.max_retries:
            if self.retry_count > 0:
                print(f"\n[重试 {self.retry_count}/{self.max_retries}]")

            # 2. 编译项目
            print("\n[2/7] 编译项目...")
            if not self._build():
                return ValidationResult(
                    passed=False,
                    test_results=[],
                    retry_count=self.retry_count,
                    fixes_applied=self.fixes_applied,
                    error_message="编译失败"
                )
            print("  ✓ 编译成功")

            # 3. 烧录固件
            print("\n[3/7] 烧录固件...")
            if not self._flash():
                return ValidationResult(
                    passed=False,
                    test_results=[],
                    retry_count=self.retry_count,
                    fixes_applied=self.fixes_applied,
                    error_message="烧录失败"
                )
            print("  ✓ 烧录成功")

            # 4. 执行测试
            print("\n[4/7] 执行串口测试...")
            test_results = self._run_tests(test_cases)

            # 5. 检查是否全部通过
            print("\n[5/7] 分析测试结果...")
            all_passed = all(r['passed'] for r in test_results)

            if all_passed:
                print(f"  ✓ 全部 {len(test_results)} 个测试用例通过")
                return ValidationResult(
                    passed=True,
                    test_results=test_results,
                    retry_count=self.retry_count,
                    fixes_applied=self.fixes_applied
                )

            # 有测试失败
            failed_tests = [r for r in test_results if not r['passed']]
            print(f"  ✗ {len(failed_tests)} 个测试用例失败")

            # 6. 是否尝试修复
            if self.single_run:
                print("\n[6/7] 单次运行模式，跳过自动修复，交由外部调度器处理")
                break

            if self.retry_count >= self.max_retries or not self.auto_fix:
                print("\n[6/7] 达到最大重试次数或自动修复已禁用")
                break

            print("\n[6/7] 分析错误并尝试修复...")
            fix_applied = self._try_fix(failed_tests)

            if not fix_applied:
                print("  ! 无法自动修复，停止")
                break

            self.retry_count += 1

        # 7. 生成失败报告
        print("\n[7/7] 验证失败")
        return ValidationResult(
            passed=False,
            test_results=test_results,
            retry_count=self.retry_count,
            fixes_applied=self.fixes_applied,
            error_message=f"验证失败，共重试 {self.retry_count} 次"
        )

    def _build(self) -> bool:
        """编译测试固件（带 TEST_MODE 宏）"""
        try:
            result = subprocess.run(
                [sys.executable, 'tools/workflow.py', 'build', '--test'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("  ✗ 编译超时")
            return False
        except Exception as e:
            print(f"  ✗ 编译出错: {e}")
            return False

    def _flash(self) -> bool:
        """烧录固件"""
        try:
            result = subprocess.run(
                [sys.executable, 'tools/workflow.py', 'flash'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("  ✗ 烧录超时")
            return False
        except Exception as e:
            print(f"  ✗ 烧录出错: {e}")
            return False

    def _run_tests(self, test_cases: List[Dict]) -> List[Dict]:
        """执行固件自验证测试：烧录后读取 JSON 输出"""
        import json

        results = []

        with self.executor:
            print("  等待测试开始标记...")

            # 等待 ===TEST_BEGIN=== 标记
            begin_found = False
            start_time = time.time()
            while time.time() - start_time < 10:
                line = self.executor.receive_line(timeout=1.0)
                if line == '===TEST_BEGIN===':
                    begin_found = True
                    break

            if not begin_found:
                print("  ✗ 未收到 TEST_BEGIN 标记")
                return [{
                    'id': 'SYS',
                    'description': '固件测试启动',
                    'input': '',
                    'expected': 'TEST_BEGIN',
                    'actual': 'timeout',
                    'passed': False,
                    'error': '未收到测试开始标记，固件可能未正确编译为 TEST_MODE'
                }]

            print("  ✓ 测试开始，读取 JSON 结果...")

            # 读取 JSON 直到 ===TEST_END===
            while time.time() - start_time < 30:
                line = self.executor.receive_line(timeout=2.0)

                if not line:
                    continue

                if line == '===TEST_END===':
                    break

                try:
                    data = json.loads(line)
                    if data.get('type') == 'test':
                        passed = data.get('result') == 'PASS'
                        result = {
                            'id': data['id'],
                            'description': data.get('desc', ''),
                            'input': data.get('check', ''),
                            'expected': str(data.get('expected', '')),
                            'actual': str(data.get('actual', '')),
                            'passed': passed,
                            'error': None if passed else str(data.get('actual', ''))
                        }
                        results.append(result)

                        status = "✓" if passed else "✗"
                        print(f"    {status} {data['id']}: {data.get('desc', '')}")

                    elif data.get('type') == 'suite' and data.get('action') == 'end':
                        passed_cnt = data.get('passed', 0)
                        failed_cnt = data.get('failed', 0)
                        print(f"  测试完成: {passed_cnt} 通过, {failed_cnt} 失败")
                except json.JSONDecodeError:
                    continue

        if not results:
            return [{
                'id': 'SYS',
                'description': '测试结果读取',
                'input': '',
                'expected': '测试用例结果',
                'actual': '空',
                'passed': False,
                'error': '未读取到任何测试结果'
            }]

        return results

    def _try_fix(self, failed_tests: List[Dict]) -> bool:
        """尝试自动修复"""
        for test in failed_tests:
            # 分析错误
            analysis = self.analyzer.analyze(test)
            print(f"  分析 {test['id']}: {analysis['error_type']}")

            if analysis.get('fixable'):
                # 尝试修复
                fix_result = self.fixer.fix(analysis)
                if fix_result['success']:
                    print(f"    ✓ 应用修复: {fix_result['description']}")
                    self.fixes_applied.append(fix_result['description'])
                    return True
                else:
                    print(f"    ! 修复失败: {fix_result.get('error')}")

        return False

    def generate_report(self, result: ValidationResult, output_path: str):
        """生成验证报告"""
        report_lines = [
            "# 验证报告",
            "",
            f"**验证时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**重试次数**: {result.retry_count}",
            f"**最终结果**: {'✓ 通过' if result.passed else '✗ 失败'}",
            "",
            "## 统计",
            "",
            f"- 总测试数: {len(result.test_results)}",
            f"- 通过: {sum(1 for r in result.test_results if r['passed'])}",
            f"- 失败: {sum(1 for r in result.test_results if not r['passed'])}",
            "",
            "## 详细结果",
            "",
        ]

        for r in result.test_results:
            status_icon = "✓" if r['passed'] else "✗"
            report_lines.extend([
                f"### {r['id']}: {r['description']}",
                "",
                f"- **状态**: {status_icon} {'通过' if r['passed'] else '失败'}",
                f"- **输入**: `{r['input']}`",
                f"- **预期输出**: `{r['expected']}`",
                f"- **实际输出**: `{r['actual']}`",
            ])
            if r.get('error'):
                report_lines.append(f"- **错误**: {r['error']}")
            report_lines.append("")

        if result.fixes_applied:
            report_lines.extend([
                "## 自动修复记录",
                "",
            ])
            for i, fix in enumerate(result.fixes_applied, 1):
                report_lines.append(f"{i}. {fix}")
            report_lines.append("")

        if result.error_message:
            report_lines.extend([
                "## 错误信息",
                "",
                f"```\n{result.error_message}\n```",
                "",
            ])

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        print(f"\n报告已生成: {output_path}")


def load_config(project_root: Path) -> Dict[str, Any]:
    """加载配置文件"""
    config_path = project_root / 'verify_config.yaml'

    default_config = {
        'project_root': str(project_root),
        'serial': {
            'port': 'auto',
            'baudrate': 115200,
        },
        'test': {
            'timeout_ms': 2000,
            'reset_before_test': True,
            'delay_after_reset_ms': 500,
        },
        'validation': {
            'max_retries': 3,
            'auto_fix': True,
        },
        'report': {
            'output_path': './reports/verify_report.md'
        }
    }

    workflow_config_path = project_root / '.workflow' / 'project.yaml'
    if workflow_config_path.exists():
        tools_dir = project_root / 'tools'
        if str(tools_dir) not in sys.path:
            sys.path.insert(0, str(tools_dir))
        try:
            from workflow import cfg_get, load_config as load_workflow_config

            workflow_config = load_workflow_config(project_root)
            default_config['serial'].update({
                'port': cfg_get(workflow_config, 'serial.port', default_config['serial']['port']),
                'baudrate': cfg_get(workflow_config, 'serial.baudrate', default_config['serial']['baudrate']),
            })
            reports_dir = cfg_get(workflow_config, 'layout.reports', 'reports')
            default_config['report']['output_path'] = f'./{reports_dir}/verify_report.md'
        except Exception as e:
            print(f"  ! workflow 配置读取失败，使用 verify 默认配置: {e}")

    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = yaml.safe_load(f)
            # 合并配置
            for key, value in user_config.items():
                if key in default_config and isinstance(value, dict):
                    default_config[key].update(value)
                else:
                    default_config[key] = value

    return default_config


def main():
    parser = argparse.ArgumentParser(description='Agent验证Skill')
    parser.add_argument('--req', default='需求.md', help='需求文档路径')
    parser.add_argument('--max-retries', type=int, help='最大重试次数')
    parser.add_argument('--test-only', action='store_true', help='只测试不修复')
    parser.add_argument('--single-run', action='store_true', help='单次运行，失败不重试，用于外部调度器控制循环')
    parser.add_argument('--port', help='串口端口')
    parser.add_argument('--report', help='报告输出路径')

    args = parser.parse_args()

    # 查找项目根目录
    project_root = Path.cwd()
    while project_root != project_root.parent:
        if (project_root / '.workflow' / 'project.yaml').exists() or \
           (project_root / 'tools' / 'workflow.py').exists():
            break
        project_root = project_root.parent

    # 加载配置
    config = load_config(project_root)

    # 命令行参数覆盖配置
    if args.max_retries is not None:
        config['validation']['max_retries'] = args.max_retries
    if args.test_only:
        config['validation']['auto_fix'] = False
    if args.port:
        config['serial']['port'] = args.port

    # 执行验证
    controller = ValidationController(config, single_run=args.single_run)
    result = controller.run(args.req)

    # 生成报告
    controller.generate_report(result, args.report or config.get('report', {}).get('output_path', 'reports/verify_report.md'))

    context_tool = project_root / 'tools' / 'context.py'
    if context_tool.exists():
        subprocess.run(
            [sys.executable, str(context_tool), 'touch-runtime'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

    # 返回状态码
    sys.exit(0 if result.passed else 1)


if __name__ == '__main__':
    main()
