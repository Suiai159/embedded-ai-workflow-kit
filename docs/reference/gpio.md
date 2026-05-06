# GPIO Reference

## 端口映射

| 逻辑端口 | 实际寄存器 | 范围 |
|----------|-----------|------|
| GPIO_PORT_A | GPIOA | PA0 ~ PA15 |
| GPIO_PORT_B | GPIOB | PB0 ~ PB15 |
| GPIO_PORT_C | GPIOC | PC0 ~ PC15 |
| GPIO_PORT_D | GPIOD | PD0 ~ PD15 |
| GPIO_PORT_E | GPIOE | PE0 ~ PE15 |

## 引脚编号

0 ~ 15，与芯片物理引脚编号一致。

## 电平状态

| 枚举 | 值 | 说明 |
|------|---|------|
| GPIO_STATE_RESET | 0 | 低电平 (Low) |
| GPIO_STATE_SET | 1 | 高电平 (High) |

## 操作方式

采用**寄存器直接操作**（非 HAL 函数调用）：
- 置高：`BSRR = (1U << pin)`
- 置低：`BRR = (1U << pin)`
- 读取：`IDR & (1U << pin)`
- 翻转：读 `ODR` 判断当前状态后写 `BRR`/`BSRR`

## 平台迁移注意

1. **时钟使能**：本工程依赖 CubeMX 生成的 `MX_GPIO_Init()` 使能时钟
2. **引脚配置**：推挽/开漏、上拉/下拉等也由 CubeMX 配置
3. 换平台时只需修改 `GPIO_PORT_MAP[]` 映射表和时钟使能逻辑
