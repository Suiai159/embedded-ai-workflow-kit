# Platform Migration Notes

## 通用迁移检查清单

换 MCU 平台时，按此清单逐一确认：

### 1. 时钟系统
- [ ] 主频是否变化？（如 72MHz → 168MHz）
- [ ] APB1/APB2 分频系数是否变化？
- [ ] 定时器时钟源是否变化？

### 2. GPIO
- [ ] 端口数量是否一致？（A~E vs A~H）
- [ ] 寄存器命名差异（`GPIOA` vs `PA`）
- [ ] 时钟使能寄存器位置（`RCC->APB2ENR` vs `RCC->AHB1ENR`）

### 3. 定时器
- [ ] 定时器位宽（16位 vs 32位）
- [ ] 中断向量名称
- [ ] 寄存器前缀（`TIM2->` vs `TIMER2->`）

### 4. UART
- [ ] 波特率分频器计算
- [ ] HAL API 兼容性
- [ ] printf 重定向方式

### 5. 编译工具链
- [ ] Keil 器件包（DFP）是否支持新 MCU
- [ ] 启动文件（startup_xxx.s）是否需要替换
- [ ] 链接脚本（scatter file）是否需要调整

## 已验证平台

| 平台 | 状态 | 备注 |
|------|------|------|
| STM32F103C8T6 | ✅ 当前主力 | 72MHz, Cortex-M3 |

## 待验证平台

- STM32F4xx 系列（168MHz, Cortex-M4）
- GD32F103（兼容 STM32F103）
- ESP32（FreeRTOS + 双核）

## 分层代码的移植性

以下代码**无需修改**即可跨平台使用（只要底层 Driver 接口一致）：
- `App/breathe_app.c`
- `Service/led_service.c`
- `Service/pwm_service.c`

以下代码**必须适配**新平台：
- `Driver/gpio_driver.c` — 寄存器映射
- `Driver/tim_driver.c` — 定时器寄存器
- `Driver/uart_driver.c` — HAL 句柄和寄存器
