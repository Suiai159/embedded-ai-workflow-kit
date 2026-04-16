# Code Reviewer SubAgent

专门的代码审查助手，用于分析嵌入式 C 代码的安全性、质量和需求符合性。

## 执行命令

当用户调用 `skill: code-reviewer` 时，执行：

```bash
python tools/code_reviewer.py {{args}}
```

## 调用方式

### 方式 1: 直接调用 Skill
```
skill: code-reviewer
args: <文件路径或目录>
```

### 方式 2: 主 Agent 通过 subAgent 调用
```
Agent: code-reviewer
Prompt: 请审查 Core/Src/main.c 文件，检查安全问题和需求符合性
```

## 功能范围

### 1. 安全检查
| 检查项 | 说明 |
|--------|------|
| ISR 安全 | 检测中断服务程序中的阻塞操作 |
| 死循环超时 | 检查无超时的轮询等待 |
| 栈溢出风险 | 检测大 Buffer 的局部变量分配 |
| 外设初始化 | 验证时钟使能配置 |
| FreeRTOS 任务 | 检查任务是否正确让出 CPU |

### 2. 需求符合性检查
| 检查项 | 说明 |
|--------|------|
| GPIO 配置 | 验证引脚配置是否符合需求 |
| PWM/定时器 | 验证频率、占空比配置 |
| 算法实现 | 验证呼吸算法、波形生成等 |
| 时序要求 | 验证延时、周期是否符合 |

### 3. 代码质量检查
| 检查项 | 说明 |
|--------|------|
| 代码规范 | 命名规范、缩进风格 |
| 注释完整性 | 关键逻辑是否有注释 |
| 魔法数字 | 检测未命名的常量 |
| 资源释放 | 检查是否有内存/资源泄漏 |

## 输出格式

生成结构化的审查报告：

```markdown
# 代码审查报告

## 概要
- 检查文件: 3 个
- 发现问题: 5 个（严重: 1, 警告: 2, 建议: 2）
- 需求符合度: 85%

## 详细发现

### 🔴 [严重] ISR 中调用阻塞函数
**文件**: Core/Src/interrupt.c:45
**问题**: HAL_Delay() 在中断服务程序中被调用
**风险**: 阻塞整个系统中断响应
**修复建议**: 使用标志位 + 主循环处理

### 🟡 [警告] 死循环缺少超时
...

### 💡 [建议] 建议使用宏定义替代魔法数字
...

## 需求符合性分析

| 需求项 | 状态 | 说明 |
|--------|------|------|
| PC13 引脚配置 | ✅ | 已正确配置为输出模式 |
| PWM 100Hz | ⚠️ | 实际 50Hz，建议调整分频系数 |
| 呼吸周期 8s | ❌ | 未实现，当前为固定频率 |
```

## 工作流程

```
主 Agent                   Code Reviewer SubAgent
   │                              │
   │── 1. 调用 subAgent 审查代码 ──▶│
   │   (提供文件路径和需求信息)     │
   │                              │
   │                              ├── 2. 扫描源代码
   │                              ├── 3. 执行安全检查
   │                              ├── 4. 验证需求符合性
   │                              ├── 5. 生成审查报告
   │                              │
   │◀─ 6. 返回结构化报告 ──────────│
   │                              │
   │── 7. 根据报告决策修复方案     │
   │                              │
```

## 使用示例

### 示例 1: 审查单个文件
```
请审查 Core/Src/main.c，关注：
1. 是否有死循环等待
2. GPIO 配置是否符合需求
```

### 示例 2: 审查整个项目
```
请审查 Core/Src 目录下的所有代码，生成完整报告。
```

### 示例 3: 针对特定需求的审查
```
请审查 PWM 相关代码，验证：
- 频率是否达到 100Hz
- 占空比范围是否为 0-100%
- 是否实现了呼吸算法
```

## 配置

在 `tools/code_reviewer_config.json` 中配置：

```json
{
  "source_dirs": ["Core/Src", "User/Src"],
  "exclude_dirs": ["Middlewares", "Drivers"],
  "isr_functions": [
    "HAL_GPIO_EXTI_Callback",
    "HAL_TIM_PeriodElapsedCallback",
    "HAL_UART_RxCpltCallback"
  ],
  "max_stack_buffer": 256,
  "check_rules": {
    "isr_blocking": true,
    "infinite_loop": true,
    "stack_usage": true,
    "magic_number": true,
    "gpio_config": true,
    "pwm_config": true
  }
}
```

## 注意事项

1. **Code Reviewer 只负责分析，不修改代码**
2. **主 Agent 负责决策** - 哪些问题需要修复、如何修复
3. **复杂场景需要人工确认** - 如特定的时序要求
4. **报告使用结构化格式** - 便于主 Agent 解析和处理
