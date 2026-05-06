# Hardware Context

This file explains the board facts in `.context/hardware.yaml`.

## Confirmed Board Facts

- MCU family: STM32F1xx
- Device: STM32F103C8
- System clock assumption: 72 MHz
- Board LED: PC13, active low
- UART log channel: USART1, 115200 8N1
- PWM tick source: TIM2 at 20 kHz

## Resource Ownership

- `LED_Service` owns PC13 behavior.
- `TIM_Driver` owns TIM2 and exposes callback-driven timing.
- `UART_Driver` owns USART1; `LOG_Service` uses it indirectly.

If a new driver or service wants one of these resources, stop and update the resource ownership decision first.

## Debugging Use

When behavior disagrees with code, check these facts before editing:

- LED polarity may invert expected output.
- Timer frequency depends on APB1 timer clock.
- UART logs may truncate if messages exceed the 128-byte stack buffer in `UART_Driver_Printf`.
