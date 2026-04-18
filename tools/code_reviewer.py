#!/usr/bin/env python3
"""
Code Reviewer - 嵌入式代码审查脚本
由 skill: code-reviewer 调用
"""

import sys
import os
import re
import json
from pathlib import Path

# 修复 Windows 终端编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def load_config():
    """加载配置文件"""
    config_path = Path("tools/code_reviewer_config.json")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "source_dirs": ["Core/Src"],
        "exclude_dirs": ["Middlewares", "Drivers"],
        "forbidden_in_isr": ["HAL_Delay", "printf", "sprintf", "malloc", "free"],
        "max_stack_buffer": 256
    }

def load_requirements():
    """加载需求文档"""
    req_files = ["需求.md", "requirements.md", "doc/需求.md", "docs/需求.md"]
    for req_file in req_files:
        if Path(req_file).exists():
            with open(req_file, 'r', encoding='utf-8') as f:
                return f.read()
    return None

def parse_requirements(content):
    """解析需求文档，提取关键参数"""
    reqs = {}
    # GPIO 引脚
    gpio_match = re.search(r'(P[A-F]\d+).*?低电平有效', content)
    if gpio_match:
        reqs['gpio_pin'] = gpio_match.group(1)
        reqs['gpio_active_low'] = True

    # 呼吸周期
    period_match = re.search(r'呼吸周期[:：]\s*(\d+)\s*秒', content)
    if period_match:
        reqs['breath_period_sec'] = int(period_match.group(1))

    # PWM 频率
    pwm_match = re.search(r'刷新频率[:：]\s*≥(\d+)Hz', content)
    if pwm_match:
        reqs['pwm_freq_hz'] = int(pwm_match.group(1))

    # 占空比范围
    duty_match = re.search(r'占空比范围[:：]\s*(\d+)%[~-](\d+)%', content)
    if duty_match:
        reqs['duty_min'] = int(duty_match.group(1))
        reqs['duty_max'] = int(duty_match.group(2))

    # 呼吸曲线
    if '正弦' in content or 'sin' in content.lower():
        reqs['breath_curve'] = 'sine'

    return reqs

def find_isr_functions(content, isr_list):
    """查找 ISR 函数定义"""
    isrs = []
    for isr_name in isr_list:
        # 匹配函数定义: void TIM2_IRQHandler(void)
        pattern = rf'void\s+{re.escape(isr_name)}\s*\([^)]*\)\s*{{'
        match = re.search(pattern, content)
        if match:
            isrs.append(isr_name)
    return isrs

def extract_function_body(content, func_name):
    """提取函数体内容"""
    pattern = rf'void\s+{re.escape(func_name)}\s*\([^)]*\)\s*{{'
    match = re.search(pattern, content)
    if not match:
        return None

    start = match.end()
    brace_count = 1
    end = start

    while brace_count > 0 and end < len(content):
        if content[end] == '{':
            brace_count += 1
        elif content[end] == '}':
            brace_count -= 1
        end += 1

    return content[start:end-1]

def check_isr_safety(file_path, content, config):
    """检查 ISR 安全性"""
    issues = []
    isr_functions = config.get('isr_functions', [])
    forbidden = config.get('forbidden_in_isr', [])

    isrs = find_isr_functions(content, isr_functions)

    for isr in isrs:
        body = extract_function_body(content, isr)
        if not body:
            continue

        # 检查禁止的函数调用
        for forbidden_func in forbidden:
            pattern = rf'\b{re.escape(forbidden_func)}\s*\('
            matches = re.finditer(pattern, body)
            for match in matches:
                # 计算行号
                line_num = content[:content.find(body) + match.start()].count('\n') + 1
                issues.append({
                    'severity': 'critical',
                    'category': 'ISR安全',
                    'title': f'ISR中调用{forbidden_func}()',
                    'file': str(file_path),
                    'line': line_num,
                    'description': f'中断服务程序 {isr} 中调用了 {forbidden_func}()，可能导致系统阻塞',
                    'suggestion': f'移除 {forbidden_func}()，改用标志位通知主循环处理'
                })

    return issues

def check_infinite_loops(file_path, content):
    """检查死循环"""
    issues = []

    # 危险模式: while(flag); while(!flag); while(flag == 0);
    dangerous_patterns = [
        (r'while\s*\(\s*\w+\s*\)\s*;\s*', '无超时保护的while等待'),
        (r'while\s*\(\s*!\w+\s*\)\s*;\s*', '无超时保护的while等待'),
        (r'while\s*\(\s*\w+\s*==\s*0\s*\)\s*;\s*', '无超时保护的while等待'),
        (r'while\s*\(\s*HAL_GPIO_ReadPin\s*\([^)]+\)\s*[!=]=\s*\w+\s*\)\s*;\s*', '无超时保护的GPIO轮询'),
    ]

    for pattern, desc in dangerous_patterns:
        matches = re.finditer(pattern, content, re.MULTILINE)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            # 检查附近是否有超时处理
            context_start = max(0, match.start() - 200)
            context_end = min(len(content), match.end() + 200)
            context = content[context_start:context_end]

            if 'timeout' not in context.lower() and '计数' not in context:
                issues.append({
                    'severity': 'warning',
                    'category': '死循环',
                    'title': desc,
                    'file': str(file_path),
                    'line': line_num,
                    'description': f'检测到可能的死循环，没有超时保护机制',
                    'code_snippet': match.group(0)[:50],
                    'suggestion': '添加超时计数器或时间戳检查，防止无限等待'
                })

    return issues

def check_stack_usage(file_path, content, max_buffer):
    """检查栈使用情况"""
    issues = []

    # 查找大数组定义
    # 模式: uint8_t buffer[1024]; 或 char data[512];
    pattern = r'(uint8_t|uint16_t|uint32_t|char|int)\s+(\w+)\s*\[(\d+)\]\s*;'
    matches = re.finditer(pattern, content)

    for match in matches:
        array_size = int(match.group(3))
        var_type = match.group(1)

        # 计算实际字节数
        type_sizes = {'uint8_t': 1, 'char': 1, 'uint16_t': 2, 'int': 4, 'uint32_t': 4}
        type_size = type_sizes.get(var_type, 4)
        total_bytes = array_size * type_size

        if total_bytes > max_buffer:
            line_num = content[:match.start()].count('\n') + 1
            issues.append({
                'severity': 'warning',
                'category': '栈溢出风险',
                'title': f'局部变量分配 {total_bytes} 字节',
                'file': str(file_path),
                'line': line_num,
                'description': f'函数内分配了 {total_bytes} 字节的数组，可能导致栈溢出',
                'code_snippet': match.group(0),
                'suggestion': f'建议将大数组改为静态变量 (static) 或全局变量，超过 {max_buffer} 字节阈值'
            })

    return issues

def check_clock_enable(file_path, content, config):
    """检查外设初始化是否有对应的时钟使能"""
    issues = []
    if not config.get('check_rules', {}).get('clock_enable', True):
        return issues

    clock_pairs = [
        ('HAL_GPIO_Init', r'__HAL_RCC_GPIO[A-K]_CLK_ENABLE', 'GPIO'),
        ('HAL_UART_Init', r'__HAL_RCC_USART\d+_CLK_ENABLE', 'UART'),
        ('HAL_TIM_Base_Init', r'__HAL_RCC_TIM\d+_CLK_ENABLE', '定时器'),
        ('HAL_TIM_PWM_Init', r'__HAL_RCC_TIM\d+_CLK_ENABLE', '定时器PWM'),
        ('HAL_SPI_Init', r'__HAL_RCC_SPI\d+_CLK_ENABLE', 'SPI'),
        ('HAL_I2C_Init', r'__HAL_RCC_I2C\d+_CLK_ENABLE', 'I2C'),
        ('HAL_ADC_Init', r'__HAL_RCC_ADC\d*_CLK_ENABLE', 'ADC'),
        ('HAL_DMA_Init', r'__HAL_RCC_DMA\d+_CLK_ENABLE', 'DMA'),
    ]

    for init_func, clk_pattern, periph_name in clock_pairs:
        init_regex = rf'\b{re.escape(init_func)}\s*\('
        if re.search(init_regex, content):
            if not re.search(clk_pattern, content):
                init_match = re.search(init_regex, content)
                line_num = content[:init_match.start()].count('\n') + 1 if init_match else 0
                issues.append({
                    'severity': 'warning',
                    'category': '外设初始化',
                    'title': f'{periph_name}初始化缺少时钟使能',
                    'file': str(file_path),
                    'line': line_num,
                    'description': f'代码中调用了 {init_func}()，但在同一文件中未找到对应的 {clk_pattern}()',
                    'suggestion': f'在 {init_func} 之前添加对应的 __HAL_RCC_xxx_CLK_ENABLE()'
                })

    return issues

def check_gpio_config(file_path, content, reqs):
    """检查 GPIO 配置"""
    issues = []
    checks = {'pin_configured': False, 'mode_correct': False}

    gpio_pin = reqs.get('gpio_pin', 'PC13')

    # 检查是否配置了指定引脚
    pin_pattern = rf'GPIO_PIN_\d+.*{gpio_pin[-2:]}|{gpio_pin}'
    if re.search(pin_pattern, content) or 'LED_PIN' in content:
        checks['pin_configured'] = True

    # 检查模式配置
    if 'GPIO_MODE_OUTPUT' in content or 'GPIOC->' in content:
        checks['mode_correct'] = True

    if not checks['pin_configured']:
        issues.append({
            'severity': 'critical',
            'category': '需求符合性',
            'title': f'未配置需求指定的 {gpio_pin} 引脚',
            'file': str(file_path),
            'line': 0,
            'description': f'需求要求使用 {gpio_pin}，但代码中未找到该引脚配置',
            'suggestion': f'在 GPIO_Init 中添加 {gpio_pin} 配置'
        })

    return issues, checks

def check_pwm_config(file_path, content, reqs):
    """检查 PWM 配置"""
    issues = []
    checks = {'pwm_enabled': False, 'freq_correct': False}

    # 检查 PWM 是否启动
    if 'HAL_TIM_PWM_Start' in content or 'TIM2->CR1 |= TIM_CR1_CEN' in content:
        checks['pwm_enabled'] = True

    # 检查频率配置
    pwm_freq = reqs.get('pwm_freq_hz', 100)

    # 尝试提取 PSC 和 ARR 值
    psc_match = re.search(r'PSC\s*=\s*(\d+)', content)
    arr_match = re.search(r'ARR\s*=\s*(\d+)', content)

    if psc_match and arr_match:
        psc = int(psc_match.group(1))
        arr = int(arr_match.group(1))
        # 72MHz / ((PSC+1) * (ARR+1))
        actual_freq = 72000000 / ((psc + 1) * (arr + 1))

        if actual_freq < pwm_freq:
            line_num = content[:psc_match.start()].count('\n') + 1
            issues.append({
                'severity': 'warning',
                'category': '需求符合性',
                'title': f'PWM 频率约 {actual_freq:.1f}Hz，低于需求要求的 {pwm_freq}Hz',
                'file': str(file_path),
                'line': line_num,
                'description': f'当前配置 PSC={psc}, ARR={arr}，计算频率为 {actual_freq:.1f}Hz',
                'suggestion': f'减小 Prescaler 或 Period 以提高频率到 {pwm_freq}Hz 以上'
            })
        else:
            checks['freq_correct'] = True

    return issues, checks

def check_breath_algorithm(file_path, content, reqs):
    """检查呼吸算法实现"""
    issues = []
    checks = {'has_algorithm': False, 'period_correct': False}

    period_sec = reqs.get('breath_period_sec', 8)

    # 检查是否有占空比更新逻辑
    if 'pwm_duty' in content and ('sine' in content.lower() or 'sin' in content.lower() or 'breath' in content.lower()):
        checks['has_algorithm'] = True

    # 检查周期配置
    if f'{period_sec * 1000}' in content or f'{period_sec}s' in content.lower() or 'BREATH_PERIOD_MS' in content:
        checks['period_correct'] = True

    if not checks['has_algorithm']:
        issues.append({
            'severity': 'warning',
            'category': '需求符合性',
            'title': '未检测到呼吸算法实现',
            'file': str(file_path),
            'line': 0,
            'description': '代码中未找到占空比动态更新逻辑或正弦表',
            'suggestion': '建议使用正弦查找表或指数曲线实现平滑呼吸效果'
        })

    return issues, checks

def check_magic_numbers(file_path, content):
    """检查魔法数字"""
    issues = []

    # 排除的常用数字
    excluded = ['0', '1', '2', '4', '8', '10', '16', '32', '64', '100', '128', '256', '1000', '1024']

    # 查找裸数字（不在宏定义或注释中）
    # 简单检查: HAL_Delay(1000) 中的 1000
    delay_pattern = r'HAL_Delay\s*\(\s*(\d+)\s*\)'
    matches = re.finditer(delay_pattern, content)

    for match in matches:
        num = match.group(1)
        if num not in excluded:
            line_num = content[:match.start()].count('\n') + 1
            # 只报告几个示例
            if len([i for i in issues if i['category'] == '魔法数字']) < 3:
                issues.append({
                    'severity': 'suggestion',
                    'category': '代码质量',
                    'title': f'建议使用宏定义替代魔法数字 {num}',
                    'file': str(file_path),
                    'line': line_num,
                    'description': f'HAL_Delay({num}) 中的 {num} 是魔法数字',
                    'suggestion': f'定义有意义的宏，如 #define DELAY_MS {num}'
                })

    return issues

def generate_report(file_path, all_issues, all_checks, reqs):
    """生成审查报告"""
    report = []
    report.append("# 代码审查报告\n")
    report.append(f"**目标文件**: `{file_path}`\n")

    # 概要
    critical = len([i for i in all_issues if i['severity'] == 'critical'])
    warning = len([i for i in all_issues if i['severity'] == 'warning'])
    suggestion = len([i for i in all_issues if i['severity'] == 'suggestion'])

    report.append("## 概要\n")
    report.append(f"- 发现问题: {len(all_issues)} 个")
    report.append(f"  - 🔴 严重: {critical}")
    report.append(f"  - 🟡 警告: {warning}")
    report.append(f"  - 💡 建议: {suggestion}")

    # 需求符合度
    passed_checks = sum(1 for c in all_checks.values() if c)
    total_checks = len(all_checks)
    compliance = (passed_checks / total_checks * 100) if total_checks > 0 else 100
    report.append(f"- 需求符合度: {compliance:.0f}%\n")

    # 详细发现
    if all_issues:
        report.append("## 详细发现\n")

        # 按严重级别分组
        severity_order = {'critical': '🔴 [严重]', 'warning': '🟡 [警告]', 'suggestion': '💡 [建议]'}

        for severity, label in severity_order.items():
            issues_of_severity = [i for i in all_issues if i['severity'] == severity]
            for issue in issues_of_severity:
                report.append(f"### {label} {issue['title']}")
                report.append(f"**文件**: {issue['file']}:{issue['line']}")
                report.append(f"**类别**: {issue['category']}")
                if 'code_snippet' in issue:
                    report.append(f"**代码片段**: `{issue['code_snippet']}`")
                report.append(f"**问题描述**: {issue['description']}")
                report.append(f"**修复建议**: {issue['suggestion']}\n")

    # 需求符合性分析
    report.append("## 需求符合性分析\n")
    report.append("| 检查项 | 状态 | 说明 |")
    report.append("|--------|------|------|")

    check_items = [
        ('GPIO引脚配置', all_checks.get('pin_configured', False), 'PC13 已配置'),
        ('GPIO模式正确', all_checks.get('mode_correct', False), '输出模式'),
        ('PWM已启用', all_checks.get('pwm_enabled', False), '定时器已启动'),
        ('PWM频率达标', all_checks.get('freq_correct', False), f"≥{reqs.get('pwm_freq_hz', 100)}Hz"),
        ('呼吸算法', all_checks.get('has_algorithm', False), '占空比动态更新'),
        ('呼吸周期', all_checks.get('period_correct', False), f"{reqs.get('breath_period_sec', 8)}秒周期"),
    ]

    for name, passed, desc in check_items:
        status = '✅' if passed else '❌'
        report.append(f"| {name} | {status} | {desc} |")

    report.append("")

    # 安全检查摘要
    report.append("## 安全检查摘要\n")
    isr_issues = [i for i in all_issues if i['category'] == 'ISR安全']
    loop_issues = [i for i in all_issues if i['category'] == '死循环']
    stack_issues = [i for i in all_issues if i['category'] == '栈溢出风险']

    report.append(f"- **ISR安全检查**: {'通过' if not isr_issues else '发现问题'}")
    report.append(f"- **死循环检查**: {'通过' if not loop_issues else '发现问题'}")
    report.append(f"- **栈溢出检查**: {'通过' if not stack_issues else '发现风险'}\n")

    # 总结与建议
    report.append("## 总结与建议\n")
    if critical > 0:
        report.append("⚠️ **存在严重问题，建议立即修复后再进行测试**\n")
        report.append("### 优先级修复列表")
        for i, issue in enumerate([i for i in all_issues if i['severity'] == 'critical'], 1):
            report.append(f"{i}. **{issue['title']}** - {issue['category']}")
    elif warning > 0:
        report.append("✅ **代码基本可用，但建议修复警告问题以提升质量**\n")
    else:
        report.append("✅ **代码通过审查，未发现明显问题**\n")

    return '\n'.join(report)

def main():
    if len(sys.argv) < 2:
        target = "Core/Src"
    else:
        target = sys.argv[1]

    print(f"开始审查: {target}\n")

    config = load_config()
    req_content = load_requirements()
    reqs = parse_requirements(req_content) if req_content else {}

    all_issues = []
    all_checks = {}

    target_path = Path(target)
    if target_path.is_file():
        files = [target_path]
    else:
        files = list(target_path.rglob("*.c"))

    for file_path in files:
        # 检查是否在排除目录中
        if any(excl in str(file_path) for excl in config.get('exclude_dirs', [])):
            continue

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"无法读取文件 {file_path}: {e}")
            continue

        # 执行各项检查
        all_issues.extend(check_isr_safety(file_path, content, config))
        all_issues.extend(check_infinite_loops(file_path, content))
        all_issues.extend(check_stack_usage(file_path, content, config.get('max_stack_buffer', 256)))
        all_issues.extend(check_clock_enable(file_path, content, config))

        gpio_issues, gpio_checks = check_gpio_config(file_path, content, reqs)
        all_issues.extend(gpio_issues)
        all_checks.update(gpio_checks)

        pwm_issues, pwm_checks = check_pwm_config(file_path, content, reqs)
        all_issues.extend(pwm_issues)
        all_checks.update(pwm_checks)

        breath_issues, breath_checks = check_breath_algorithm(file_path, content, reqs)
        all_issues.extend(breath_issues)
        all_checks.update(breath_checks)

        all_issues.extend(check_magic_numbers(file_path, content))

    # 生成报告
    report = generate_report(target, all_issues, all_checks, reqs)
    print(report)

    # 保存报告
    report_path = Path("reports/code_review_report.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n报告已保存至: {report_path}")

    # 返回状态码
    critical_count = len([i for i in all_issues if i['severity'] == 'critical'])
    return 1 if critical_count > 0 else 0

if __name__ == '__main__':
    sys.exit(main())
