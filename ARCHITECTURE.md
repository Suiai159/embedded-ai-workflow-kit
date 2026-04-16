# STM32 分层架构规范

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│  App层 (Application)                                        │
│  - 纯业务逻辑，无硬件依赖                                    │
│  - 示例: breathe_app (呼吸灯算法)                           │
├─────────────────────────────────────────────────────────────┤
│  Service层 (服务层)                                         │
│  - 硬件功能抽象，组合Driver提供高级功能                       │
│  - 示例: led_service, pwm_service, log_service              │
├─────────────────────────────────────────────────────────────┤
│  Driver层 (驱动层)                                          │
│  - 直接操作寄存器，封装硬件细节                               │
│  - 示例: gpio_driver, tim_driver, uart_driver               │
├─────────────────────────────────────────────────────────────┤
│  HAL层 (Hardware Abstraction)                               │
│  - CubeMX生成的标准库代码                                    │
│  - 示例: stm32f1xx_hal_gpio, stm32f1xx_hal_tim              │
└─────────────────────────────────────────────────────────────┘
```

## 核心原则

### 1. 依赖方向（绝对禁止反向依赖）

```
App → Service → Driver → HAL
 ↑
 └── 只能向下依赖，禁止向上或跨层依赖
```

**禁止示例：**
```c
// ❌ 错误：Driver层不能包含Service层头文件
tim_driver.c 包含 #include "pwm_service.h"

// ❌ 错误：App层不能直接调用Driver层
breathe_app.c 调用 GPIO_Driver_WritePin()
```

### 2. 各层职责约束

| 层级 | 职责 | 禁止事项 | 检查方法 |
|------|------|----------|----------|
| **App** | 纯业务逻辑、算法、状态机 | 包含任何硬件头文件 | grep -l "stm32" Core/App/*.c |
| **Service** | 硬件功能抽象、资源协调 | 直接操作寄存器 | 检查是否只调用Driver层API |
| **Driver** | 寄存器操作、中断处理 | 调用Service/App层 | 检查头文件包含列表 |
| **HAL** | CubeMX标准库 | 手动修改 | 仅通过MX_函数调用 |

### 3. 初始化规则（防止重复初始化）

**原则**：遵循"系统统一初始化"模式

```c
// main.c - 系统启动时统一初始化
static void System_Init(void) {
    // 1. 先初始化底层
    GPIO_Driver_Init();
    TIM_Driver_Init(20000, PWM_Service_Tick);
    UART_Driver_Init();

    // 2. 再初始化上层（不重复初始化Driver）
    PWM_Service_Init();   // 假设GPIO/TIM已就绪
    LED_Service_Init();   // 假设PWM/GPIO已就绪
    LOG_Service_Init();   // 假设UART已就绪

    // 3. 最后初始化App层
    Breathe_App_Init(&cfg);
}
```

**约束规则：**
- Driver层初始化函数可以被多次调用（内部做好防护）
- Service层禁止调用Driver_Init()，假设Driver已就绪
- 新加Service时，检查其依赖的Driver是否已在系统初始化中

### 4. 资源所有权（防止职责重叠）

**原则**：每个硬件资源只能有一个"所有者"

| 硬件资源 | 所有者 | 其他层如何访问 |
|----------|--------|----------------|
| GPIO PC13 | LED_Service | 通过LED_Service_SetMode() |
| TIM2 | TIM_Driver | Driver提供通用接口 |
| USART1 | UART_Driver | Log_Service间接使用 |

**禁止示例：**
```c
// ❌ 错误：PWM_Service和LED_Service都直接操作PC13
// pwm_service.c
GPIO_Driver_WritePin(GPIO_PORT_C, 13, state);  // PWM_Service操作

// led_service.c
GPIO_Driver_WritePin(GPIO_PORT_C, 13, state);  // LED_Service也操作！

// ✅ 正确：LED_Service是PC13的唯一所有者
// led_service.c 根据模式决定是否使用PWM
if (mode == LED_MODE_BREATHE) {
    PWM_Service_SetDuty(brightness);  // 通过PWM间接控制
} else {
    GPIO_Driver_WritePin(LED_PORT, LED_PIN, state);  // 直接控制
}
```

### 5. 添加新模块的检查清单

创建新文件前，必须回答：

```
□ 这个模块属于哪一层？（App/Service/Driver）
□ 它需要依赖哪些下层模块？（列出头文件）
□ 是否有上层模块会依赖它？（确认无循环依赖）
□ 它操作的硬件资源是否已被其他模块占用？
□ 初始化流程中，它的依赖是否已先初始化？
□ 是否需要在System_Init()中添加它的初始化？
```

## 快速检查命令

```bash
# 检查App层是否违规包含硬件头文件
grep -r "stm32f1xx\|stm32f103" Core/App/

# 检查Driver层是否包含上层头文件（应该是干净的）
grep -r "service\|app" Core/Driver/ --include="*.c"

# 检查重复初始化模式
grep -r "_Init()" Core/ --include="*.c" | grep -v "System_Init\|MX_"
```

## 常见错误模式

| 错误 | 症状 | 修复方案 |
|------|------|----------|
| 重复初始化 | 系统启动时某个Driver被Init多次 | 统一到System_Init，Service层去掉Init调用 |
| 资源冲突 | 同一引脚被两个Service操作 | 明确资源所有权，其他Service通过API访问 |
| 循环依赖 | A.h包含B.h，B.h又包含A.h | 提取公共定义到独立头文件，或使用前向声明 |
| 跨层调用 | App直接操作GPIO | 增加Service层封装 |

## 文件模板

### 新增 App 层模块

```c
// my_app.h
#ifndef MY_APP_H
#define MY_APP_H
#include <stdint.h>  // 只允许标准C头文件

typedef struct { ... } MyApp_Config_t;
void MyApp_Init(const MyApp_Config_t* config);
void MyApp_Tick(uint32_t timestamp_ms);
#endif
```

### 新增 Service 层模块

```c
// my_service.h
#ifndef MY_SERVICE_H
#define MY_SERVICE_H
#include <stdint.h>
#include "xxx_driver.h"  // 只允许包含Driver层头文件

void MyService_Init(void);  // 不调用Driver_Init()
void MyService_DoSomething(void);
#endif
```

### 新增 Driver 层模块

```c
// my_driver.h
#ifndef MY_DRIVER_H
#define MY_DRIVER_H
#include <stdint.h>
#include "stm32f1xx_hal.h"  // 可包含HAL头文件

void MyDriver_Init(void);  // 由System_Init()调用
void MyDriver_IRQHandler(void);
#endif
```
