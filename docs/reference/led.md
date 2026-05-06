# LED Reference

## 硬件参数

| 参数 | 值 | 说明 |
|------|---|------|
| 控制引脚 | PC13 | 板载 LED（STM32F103C8T6 核心板） |
| 驱动方式 | GPIO + 软件 PWM | 非硬件 PWM |
| 极性 | 低电平有效 (Active Low) | `GPIO_STATE_RESET` = 亮，`GPIO_STATE_SET` = 灭 |
| PWM 频率 | 20 kHz | 避免可见闪烁 |
| PWM 分辨率 | 100 级 | 0 ~ 100 的占空比 |

## 工作模式

| 模式 | 行为 |
|------|------|
| OFF | 引脚置高 → LED 灭 |
| ON | 引脚置低 → LED 亮（全亮） |
| BREATHE | 软件 PWM 呼吸效果，周期由 App 层控制 |
| BLINK | 翻转引脚，翻转频率由调用 `LED_Service_Tick()` 的频率控制 |

## 亮度控制

- 范围：0 ~ 100
- 仅在 `BREATHE` 模式下通过 `PWM_Service_SetDuty()` 生效
- `LED_MODE_ON` 时亮度固定为 100%（全亮）

## 平台迁移注意

1. **引脚变更**：不同开发板的 LED 引脚不同（如 PA5、PB13 等）
2. **极性确认**：有些板子是**高电平有效**（如 ESP32 开发板），需修改 `LED_Service_Init` 和 `SetMode` 中的电平逻辑
3. **PWM 方式**：当前是软件 PWM（定时器中断翻转），换平台时若硬件 PWM 可用建议改用硬件方案
4. **电流限制**：若驱动外部 LED，需确认 GPIO 驱动能力（STM32 一般 8mA），必要时加三极管/MOS
