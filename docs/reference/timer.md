# Timer Reference

## 当前配置：TIM2

| 参数 | 值 | 说明 |
|------|---|------|
| 硬件定时器 | TIM2 | 通用定时器 |
| 时钟源 | APB1 | 72 MHz |
| 目标中断频率 | 20 kHz | 由调用方传入（当前用于 PWM） |
| 预分频器 (PSC) | 35 | 实际分频 = 36 |
| 自动重装载 (ARR) | 99 | 72M / 36 / 100 = 20kHz |
| 中断优先级 | 2 | NVIC 优先级 |

## 计算公式

```
frequency = timer_clock / (PSC + 1) / (ARR + 1)
```

示例：72MHz / 36 / 100 = 20,000 Hz

## 中断处理

- 中断向量：`TIM2_IRQn`
- 标志清除：写 `TIM2->SR &= ~TIM_SR_UIF`
- 回调注册：通过 `TIM_Driver_Init(freq, callback)` 传入

## 平台迁移注意

1. **时钟频率**：不同 MCU 的 APB1 时钟可能不同（如 48MHz、64MHz），需重新计算 PSC/ARR
2. **定时器选择**：STM32F103 的 TIM2 是 32 位，某些平台可能用 16 位定时器
3. **中断向量名**：不同平台 IRQn 名称不同（如 `TIMER2_IRQn`、`TIM2_IRQn`）
4. **寄存器命名**：如 `TIM_DIER_UIE` vs `TIM2_DIER_UIE` 等
