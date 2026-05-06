#!/usr/bin/env python3
"""
代码修复器 - 自动修复代码中的常见问题
"""

import re
import shutil
from pathlib import Path
from typing import Dict, Any


class CodeFixer:
    """代码修复器"""

    def __init__(self, project_root: str = '.'):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / '.verify_backup'
        self.modified_files = []

    def fix(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        尝试自动修复代码

        Args:
            analysis: 错误分析报告

        Returns:
            修复结果
        """
        error_type = analysis.get('error_type')
        test_result = analysis.get('test_result', {})

        fix_methods = {
            'NO_OUTPUT': self._fix_no_output,
            'FORMAT_MISMATCH': self._fix_format_mismatch,
            'VALUE_MISMATCH': self._fix_value_mismatch,
            'PARTIAL_MATCH': self._fix_partial_match,
        }

        fix_method = fix_methods.get(error_type)
        if not fix_method:
            return {
                'success': False,
                'error': f'不支持的修复类型: {error_type}'
            }

        try:
            return fix_method(analysis)
        except Exception as e:
            return {
                'success': False,
                'error': f'修复过程出错: {e}'
            }

    def _backup_file(self, filepath: Path):
        """备份文件"""
        self.backup_dir.mkdir(exist_ok=True)
        backup_path = self.backup_dir / f"{filepath.name}.{len(self.modified_files)}"
        shutil.copy2(filepath, backup_path)

    def _find_main_c(self) -> Path:
        """查找main.c文件"""
        patterns = [
            'USER/main.c',
            'Src/main.c',
            'Core/Src/main.c',
            'main.c'
        ]
        for pattern in patterns:
            path = self.project_root / pattern
            if path.exists():
                return path
        raise FileNotFoundError("未找到main.c")

    def _fix_no_output(self, analysis: Dict) -> Dict[str, Any]:
        """修复无输出问题 - 添加printf支持"""
        try:
            main_c = self._find_main_c()
            self._backup_file(main_c)

            content = main_c.read_text(encoding='utf-8')

            # 检查是否已有printf重定向
            if 'fputc' in content or '_write' in content:
                # 已有重定向，可能是printf没调用，在main开始处添加测试输出
                if 'printf("System Ready' not in content:
                    # 在main函数开始处添加启动信息
                    pattern = r'(int main\s*\([^)]*\)\s*\{)'
                    replacement = r'\1\n    printf("System Ready\\r\\n");'
                    content = re.sub(pattern, replacement, content)

                    main_c.write_text(content, encoding='utf-8')
                    self.modified_files.append(str(main_c))

                    return {
                        'success': True,
                        'description': '添加系统启动printf输出',
                        'file': str(main_c)
                    }
            else:
                # 缺少printf重定向，添加fputc实现
                fputc_impl = '''
// printf重定向到USART
#ifdef __GNUC__
  #define PUTCHAR_PROTOTYPE int __io_putchar(int ch)
#else
  #define PUTCHAR_PROTOTYPE int fputc(int ch, FILE *f)
#endif

PUTCHAR_PROTOTYPE
{
    HAL_UART_Transmit(&huart1, (uint8_t *)&ch, 1, 0xFFFF);
    return ch;
}

'''
                # 在#include后添加
                lines = content.split('\n')
                insert_idx = 0
                for i, line in enumerate(lines):
                    if '#include' in line:
                        insert_idx = i + 1

                lines.insert(insert_idx, fputc_impl)
                content = '\n'.join(lines)

                # 同时在main开始处添加启动信息
                pattern = r'(int main\s*\([^)]*\)\s*\{)'
                replacement = r'\1\n    printf("System Ready\\r\\n");'
                content = re.sub(pattern, replacement, content)

                main_c.write_text(content, encoding='utf-8')
                self.modified_files.append(str(main_c))

                return {
                    'success': True,
                    'description': '添加printf重定向和启动输出',
                    'file': str(main_c)
                }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _fix_format_mismatch(self, analysis: Dict) -> Dict[str, Any]:
        """修复格式不匹配 - 修正printf格式"""
        try:
            main_c = self._find_main_c()
            self._backup_file(main_c)

            content = main_c.read_text(encoding='utf-8')

            # 获取预期和实际输出
            expected = analysis.get('test_result', {}).get('expected', '')
            actual = analysis.get('test_result', {}).get('actual', '')

            # 简单策略：如果预期是LED ON/OFF，查找printf并修正
            if 'LED' in expected:
                # 查找并修正LED相关的printf
                patterns = [
                    (r'printf\s*\(\s*"LED\s+(\w+)"\s*\)', r'printf("LED is \\1\\r\\n")'),
                    (r'printf\s*\(\s*"LED:\s*(\w+)"\s*\)', r'printf("LED is \\1\\r\\n")'),
                ]

                modified = False
                for pattern, replacement in patterns:
                    if re.search(pattern, content):
                        content = re.sub(pattern, replacement, content)
                        modified = True

                if modified:
                    main_c.write_text(content, encoding='utf-8')
                    self.modified_files.append(str(main_c))
                    return {
                        'success': True,
                        'description': '修正LED输出格式',
                        'file': str(main_c)
                    }

            return {'success': False, 'error': '未找到可修复的格式模式'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _fix_value_mismatch(self, analysis: Dict) -> Dict[str, Any]:
        """修复数值不匹配 - 修正计算公式"""
        try:
            main_c = self._find_main_c()
            self._backup_file(main_c)

            content = main_c.read_text(encoding='utf-8')

            # 常见的温度计算公式修正
            # LM35: temp = adc * 330 / 4096
            # STM32内部温度: temp = (1430 - adc * 3300 / 4096) / 4.3 + 25

            temp_patterns = [
                # 修正除以4096而不是1024
                (r'adc\s*\*\s*\d+\s*/\s*1024', lambda m: m.group().replace('1024', '4096')),
                # 修正电压计算
                (r'adc\s*\*\s*3\.3', 'adc * 3300 / 4096'),
            ]

            modified = False
            for pattern, replacement in temp_patterns:
                if re.search(pattern, content):
                    if callable(replacement):
                        content = re.sub(pattern, replacement, content)
                    else:
                        content = re.sub(pattern, replacement, content)
                    modified = True

            if modified:
                main_c.write_text(content, encoding='utf-8')
                self.modified_files.append(str(main_c))
                return {
                    'success': True,
                    'description': '修正温度计算公式',
                    'file': str(main_c)
                }

            return {'success': False, 'error': '未找到可修复的计算公式'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _fix_partial_match(self, analysis: Dict) -> Dict[str, Any]:
        """修复部分匹配 - 调整输出字符串"""
        try:
            main_c = self._find_main_c()
            self._backup_file(main_c)

            content = main_c.read_text(encoding='utf-8')

            expected = analysis.get('test_result', {}).get('expected', '')
            actual = analysis.get('test_result', {}).get('actual', '')

            # 尝试在printf中查找并修正
            # 例如: 预期 "LED is ON", 实际 "LED ON"
            if expected.lower() in actual.lower():
                # 可能是大小写或空格问题，暂时不自动修复
                return {'success': False, 'error': '大小写或空格差异，建议手动检查'}

            # 尝试查找相似字符串并替换
            # 简化处理：如果预期包含"is"而实际不包含，尝试添加
            if 'is' in expected and 'is' not in actual:
                # 查找LED ON/OFF模式并添加is
                pattern = r'printf\s*\(\s*"(LED)\s+(ON|OFF)"\s*\)'
                replacement = r'printf("\\1 is \\2")'

                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    main_c.write_text(content, encoding='utf-8')
                    self.modified_files.append(str(main_c))
                    return {
                        'success': True,
                        'description': '调整输出字符串格式',
                        'file': str(main_c)
                    }

            return {'success': False, 'error': '未找到可修复的字符串模式'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def restore_backup(self):
        """恢复备份文件"""
        if not self.backup_dir.exists():
            return

        for backup in self.backup_dir.iterdir():
            if backup.is_file():
                # 找到原始文件
                original = self.project_root / backup.stem.split('.')[0]
                if original.exists():
                    shutil.copy2(backup, original)

    def cleanup_backup(self):
        """清理备份"""
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
