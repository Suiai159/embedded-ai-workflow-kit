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

    def __init__(self, config: Dict[str, Any]):
        self.config = config
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
        """编译项目"""
        try:
            result = subprocess.run(
                ['bash', 'USER/Build/build_keil.sh'],
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
                ['bash', 'USER/Build/flash_keil.sh'],
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
        """执行所有测试用例"""
        results = []

        with self.executor:
            # 等待系统启动
            time.sleep(self.config.get('test', {}).get('delay_after_reset_ms', 500) / 1000)

            for tc in test_cases:
                print(f"\n  测试 {tc['id']}: {tc['description']}")
                print(f"    输入: {repr(tc['input'])}")
                print(f"    预期: {tc['expected_pattern']}")

                # 清空缓冲区
                self.executor.clear_buffer()

                # 发送命令
                self.executor.send(tc['input'])

                # 等待输出
                timeout = tc.get('timeout_ms', 2000) / 1000
                actual_output = self.executor.receive_until(
                    tc['expected_pattern'],
                    timeout
                )

                # 比对结果
                match_result = self.comparator.compare(
                    actual_output,
                    tc['expected_pattern'],
                    tc.get('match_type', 'contains')
                )

                result = {
                    'id': tc['id'],
                    'description': tc['description'],
                    'input': tc['input'],
                    'expected': tc['expected_pattern'],
                    'actual': actual_output,
                    'passed': match_result['passed'],
                    'error': match_result.get('error'),
                    'duration_ms': match_result.get('duration_ms', 0)
                }

                results.append(result)

                if result['passed']:
                    print(f"    ✓ 通过")
                else:
                    print(f"    ✗ 失败: {result['error']}")

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
            'output_path': './verify_report.md'
        }
    }

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
    parser.add_argument('--port', help='串口端口')
    parser.add_argument('--report', default='verify_report.md', help='报告输出路径')

    args = parser.parse_args()

    # 查找项目根目录
    project_root = Path.cwd()
    while project_root != project_root.parent:
        if (project_root / 'USER' / 'Build').exists():
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
    controller = ValidationController(config)
    result = controller.run(args.req)

    # 生成报告
    controller.generate_report(result, args.report)

    # 返回状态码
    sys.exit(0 if result.passed else 1)


if __name__ == '__main__':
    main()
