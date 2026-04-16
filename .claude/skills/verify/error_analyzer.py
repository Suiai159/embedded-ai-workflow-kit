#!/usr/bin/env python3
"""
错误分析器 - 分析测试失败原因
"""

from typing import Dict, Any


class ErrorAnalyzer:
    """错误分析器"""

    # 错误类型定义
    ERROR_TYPES = {
        'NO_OUTPUT': '无输出',
        'TIMEOUT': '响应超时',
        'FORMAT_MISMATCH': '格式不匹配',
        'VALUE_MISMATCH': '数值不匹配',
        'PARTIAL_MATCH': '部分匹配',
        'UNEXPECTED_OUTPUT': '意外输出',
    }

    def analyze(self, test_result: Dict) -> Dict[str, Any]:
        """
        分析测试失败原因

        Args:
            test_result: 测试结果字典

        Returns:
            分析报告
        """
        actual = test_result.get('actual', '')
        expected = test_result.get('expected', '')
        error = test_result.get('error', '')

        # 确定错误类型
        error_type = self._classify_error(actual, expected, error)

        # 生成修复建议
        analysis = {
            'error_type': error_type,
            'error_type_name': self.ERROR_TYPES.get(error_type, '未知错误'),
            'description': self._get_description(error_type, actual, expected),
            'possible_causes': self._get_possible_causes(error_type, actual, expected),
            'fixable': self._is_fixable(error_type),
            'fix_strategy': self._get_fix_strategy(error_type),
            'test_result': test_result
        }

        return analysis

    def _classify_error(self, actual: str, expected: str, error: str) -> str:
        """分类错误类型"""
        if not actual or actual.strip() == '':
            return 'NO_OUTPUT'

        if '超时' in error or 'timeout' in error.lower():
            return 'TIMEOUT'

        if '数值超出范围' in error:
            return 'VALUE_MISMATCH'

        if '匹配失败' in error:
            # 检查是否有部分匹配
            if len(set(actual) & set(expected)) > len(expected) * 0.5:
                return 'PARTIAL_MATCH'
            return 'FORMAT_MISMATCH'

        return 'UNEXPECTED_OUTPUT'

    def _get_description(self, error_type: str, actual: str, expected: str) -> str:
        """获取错误描述"""
        descriptions = {
            'NO_OUTPUT': f'串口无输出，预期收到: {expected}',
            'TIMEOUT': '等待响应超时',
            'FORMAT_MISMATCH': f'输出格式不匹配，预期: {expected}，实际: {actual}',
            'VALUE_MISMATCH': f'输出数值不正确，预期范围: {expected}，实际: {actual}',
            'PARTIAL_MATCH': f'输出部分匹配，预期: {expected}，实际: {actual}',
            'UNEXPECTED_OUTPUT': f'收到意外输出，预期: {expected}，实际: {actual}',
        }
        return descriptions.get(error_type, '未知错误')

    def _get_possible_causes(self, error_type: str, actual: str, expected: str) -> list:
        """获取可能的原因"""
        causes = {
            'NO_OUTPUT': [
                'USART未正确初始化（波特率/时钟配置错误）',
                'printf重定向未实现',
                '程序崩溃或卡在死循环',
                '串口连接问题'
            ],
            'TIMEOUT': [
                '主循环阻塞，未及时处理输入',
                '中断未触发',
                '处理逻辑耗时过长',
                '死循环或无限等待'
            ],
            'FORMAT_MISMATCH': [
                'printf格式字符串错误',
                '字符串拼接错误',
                '编码问题',
                '缺少换行符'
            ],
            'VALUE_MISMATCH': [
                '计算公式错误',
                '传感器驱动错误',
                'ADC/DMA配置错误',
                '单位换算错误'
            ],
            'PARTIAL_MATCH': [
                '输出信息不完整',
                '缺少前缀/后缀',
                '大小写不匹配',
                '多余空格'
            ],
            'UNEXPECTED_OUTPUT': [
                '逻辑判断错误',
                '状态机转换错误',
                '未处理的异常分支',
                '内存污染'
            ]
        }
        return causes.get(error_type, ['未知原因'])

    def _is_fixable(self, error_type: str) -> bool:
        """判断是否可自动修复"""
        fixable_types = {
            'NO_OUTPUT': True,           # 可以尝试添加printf
            'TIMEOUT': False,            # 难以自动修复，可能涉及架构问题
            'FORMAT_MISMATCH': True,     # 可以修正printf格式
            'VALUE_MISMATCH': True,      # 可以修正计算公式
            'PARTIAL_MATCH': True,       # 可以调整输出字符串
            'UNEXPECTED_OUTPUT': False,  # 需要理解业务逻辑
        }
        return fixable_types.get(error_type, False)

    def _get_fix_strategy(self, error_type: str) -> str:
        """获取修复策略"""
        strategies = {
            'NO_OUTPUT': '添加调试输出或修复USART初始化',
            'FORMAT_MISMATCH': '修正printf格式字符串',
            'VALUE_MISMATCH': '修正计算公式或传感器读取',
            'PARTIAL_MATCH': '调整输出字符串匹配预期格式',
        }
        return strategies.get(error_type, '需要手动修复')
