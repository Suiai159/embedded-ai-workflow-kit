#!/usr/bin/env python3
"""
输出比对器 - 比较实际输出与预期模式
"""

import re
import time
from typing import Dict, Any


class OutputComparator:
    """输出比对器"""

    def compare(self, actual: str, expected: str, match_type: str = 'contains') -> Dict[str, Any]:
        """
        比对实际输出与预期模式

        Args:
            actual: 实际输出
            expected: 预期模式
            match_type: 匹配类型 (exact/contains/regex/range)

        Returns:
            比对结果字典
        """
        start_time = time.time()

        if match_type == 'exact':
            passed = actual.strip() == expected.strip()
            error = None if passed else f"精确匹配失败: 预期 '{expected}', 实际 '{actual}'"

        elif match_type == 'contains':
            passed = expected in actual
            error = None if passed else f"包含匹配失败: 未找到 '{expected}'"

        elif match_type == 'regex':
            try:
                pattern = re.compile(expected)
                match = pattern.search(actual)
                passed = match is not None
                error = None if passed else f"正则匹配失败: 模式 '{expected}' 未匹配"
            except re.error as e:
                passed = False
                error = f"正则表达式错误: {e}"

        elif match_type == 'range':
            passed, error = self._compare_range(actual, expected)

        else:
            passed = False
            error = f"未知的匹配类型: {match_type}"

        duration_ms = int((time.time() - start_time) * 1000)

        return {
            'passed': passed,
            'error': error,
            'duration_ms': duration_ms,
            'actual': actual,
            'expected': expected,
            'match_type': match_type
        }

    def _compare_range(self, actual: str, expected: str) -> tuple:
        """
        数值范围比对
        expected格式: "20-30" 或 "20.5-30.5"
        """
        try:
            # 解析范围
            if '-' not in expected:
                return False, f"范围格式错误: {expected}"

            parts = expected.split('-')
            min_val = float(parts[0])
            max_val = float(parts[1])

            # 从actual中提取数值
            numbers = re.findall(r'-?\d+\.?\d*', actual)

            if not numbers:
                return False, f"未在输出中找到数值"

            # 取第一个数值进行比对
            actual_val = float(numbers[0])

            if min_val <= actual_val <= max_val:
                return True, None
            else:
                return False, f"数值超出范围: {actual_val} 不在 [{min_val}, {max_val}] 内"

        except ValueError as e:
            return False, f"范围比对错误: {e}"

    def extract_value(self, text: str, pattern: str, group: int = 1) -> Any:
        """
        从文本中提取值

        Args:
            text: 待提取文本
            pattern: 正则表达式
            group: 捕获组索引

        Returns:
            提取的值或None
        """
        try:
            match = re.search(pattern, text)
            if match:
                value = match.group(group)
                # 尝试转换为数字
                try:
                    if '.' in value:
                        return float(value)
                    return int(value)
                except ValueError:
                    return value
            return None
        except re.error:
            return None
