#!/usr/bin/env python3
"""
需求解析器 - 从需求文档提取测试用例
"""

import re
from pathlib import Path
from typing import List, Dict


class RequirementParser:
    """解析需求文档，提取测试用例"""

    def __init__(self):
        self.test_cases = []

    def parse(self, filepath: str) -> List[Dict]:
        """解析需求文档"""
        path = Path(filepath)

        if not path.exists():
            # 尝试其他默认路径
            alternatives = [
                '需求.md',
                'requirements.md',
                './docs/需求.md',
                './docs/requirements.md'
            ]
            for alt in alternatives:
                if Path(alt).exists():
                    path = Path(alt)
                    break

        if not path.exists():
            raise FileNotFoundError(f"找不到需求文档: {filepath}")

        content = path.read_text(encoding='utf-8')

        # 尝试解析测试用例
        test_cases = self._parse_test_cases(content)

        # 如果没有找到测试用例，尝试从功能描述生成默认测试用例
        if not test_cases:
            test_cases = self._generate_default_test_cases(content)

        return test_cases

    def _parse_test_cases(self, content: str) -> List[Dict]:
        """解析文档中的测试用例"""
        test_cases = []

        # 查找"测试用例"章节
        test_section = self._extract_section(content, '测试用例')
        if not test_section:
            return []

        # 匹配测试用例块
        # 格式: ### TC001: 描述
        pattern = r'###\s*(TC\d+):\s*(.+?)\n(.*?)(?=###|$)'
        matches = re.findall(pattern, test_section, re.DOTALL)

        for tc_id, description, body in matches:
            tc = {
                'id': tc_id.strip(),
                'description': description.strip(),
                'input': self._extract_field(body, '输入'),
                'expected_pattern': self._extract_field(body, '预期输出'),
                'match_type': self._extract_field(body, '匹配模式') or 'contains',
                'timeout_ms': int(self._extract_field(body, '超时') or '1000'),
            }

            # 解析数值范围
            if tc['match_type'] == 'range' and '-' in tc['expected_pattern']:
                range_parts = tc['expected_pattern'].split('-')
                tc['range'] = {
                    'min': float(range_parts[0]),
                    'max': float(range_parts[1])
                }

            test_cases.append(tc)

        return test_cases

    def _extract_section(self, content: str, section_name: str) -> str:
        """提取指定章节内容"""
        # 支持 ## 测试用例 或 ## 测试用例\n 格式
        pattern = rf'##\s*{section_name}\s*\n(.*?)(?=##\s|$)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        return match.group(1) if match else ''

    def _extract_field(self, content: str, field_name: str) -> str:
        """提取字段值"""
        # 匹配: - **字段**: 值  或  字段: 值
        patterns = [
            rf'\*\*{field_name}\*\*[:：]\s*(.+)',
            rf'{field_name}[:：]\s*(.+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        return ''

    def _generate_default_test_cases(self, content: str) -> List[Dict]:
        """从功能描述生成默认测试用例"""
        test_cases = []

        # 提取功能点
        func_pattern = r'(?:功能|模块|外设)[:：]\s*(.+?)(?=\n|$)'
        functions = re.findall(func_pattern, content, re.IGNORECASE)

        for i, func in enumerate(functions, 1):
            tc = {
                'id': f'TC{i:03d}',
                'description': func.strip(),
                'input': f'TEST {i}',
                'expected_pattern': 'OK',
                'match_type': 'contains',
                'timeout_ms': 1000
            }
            test_cases.append(tc)

        # 如果没有找到功能点，添加一个基础测试
        if not test_cases:
            test_cases.append({
                'id': 'TC001',
                'description': '系统基础响应测试',
                'input': 'INIT',
                'expected_pattern': 'Ready',
                'match_type': 'contains',
                'timeout_ms': 2000
            })

        return test_cases
