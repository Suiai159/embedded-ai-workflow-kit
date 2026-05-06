# UART Reference

## 当前配置：USART1

| 参数 | 值 | 说明 |
|------|---|------|
| 硬件串口 | USART1 | 全双工异步串口 |
| 波特率 | 115200 | 标准速率 |
| 数据位 | 8 | 固定 |
| 停止位 | 1 | 固定 |
| 校验 | None | 无校验 |
| 流控 | None | 无硬件流控 |

## 缓冲区策略

- **发送**：无环形缓冲区，直接调用 `HAL_UART_Transmit()` 阻塞发送
- **缓冲区大小**：`UART_Driver_Printf` 使用 128 字节栈缓冲区
- **超时**：100ms（`HAL_UART_Transmit` 的 timeout 参数）

## 关键行为

1. `UART_Driver_Init()` 内部延时 100ms 等待串口稳定
2. `printf` 重定向到 UART1（通过 `fputc`）
3. `UART_Driver_IsTxReady()` 查询 `USART_SR_TXE` 标志判断发送寄存器是否空闲

## 平台迁移注意

1. **波特率精度**：不同 MCU 的 UART 分频器精度不同，115200 在某些时钟下可能有误差
2. **HAL 依赖**：当前实现依赖 `HAL_UART_Transmit`，换平台需确认 HAL API 一致性
3. **重定向冲突**：`fputc` 重定向可能与平台标准库的 `printf` 实现冲突
4. **缓冲区大小**：128 字节对于长日志可能不够，需根据需求调整
