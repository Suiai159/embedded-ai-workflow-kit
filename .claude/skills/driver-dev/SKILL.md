---
schema: skill-1.0
name: driver-dev
description: 从零开发外设驱动——读取商家资料，生成Driver层代码和测试代码，并自动加入Keil工程。无需需求文档。
parameters:
  - name: source
    type: string
    required: true
    description: 资料路径，如 @ST7789.pdf 或 @参考代码.c
  - name: name
    type: string
    required: true
    description: 驱动名称，如 st7789、mpu6050
  - name: interface
    type: string
    required: false
    default: ""
    description: 通信接口，如 SPI、I2C、UART、OneWire、FSMC
user-invocable: true
---

# /driver-dev — 外设驱动开发

**从零写驱动 + 自动生成测试代码 + 自动注册 Keil 工程。**

这是个人项目/驱动开荒阶段的专用入口，**不依赖 `需求.md`**。你只需提供商家给的资料（datasheet、参考 C 代码、甚至 FPGA 代码），AI 会帮你提取关键信息并按本项目的四层架构规范生成 Driver 层代码。

---

## 使用方式

```bash
/driver-dev @ST7789_datasheet.pdf --name st7789 --interface SPI
/driver-dev @mpu6050_reference.c --name mpu6050 --interface I2C
/driver-dev @DS18B20_资料.pdf --name ds18b20 --interface OneWire
```

- `source`: 资料文件路径，用 `@` 前缀表示本地文件（支持 PDF、C、H、图片）
- `name`: 驱动名称，将生成 `xxx_driver.c` / `xxx_driver.h`
- `interface`: 通信接口，影响初始化模板和测试代码结构

---

## 工作流程

```
用户: /driver-dev @资料 --name xxx --interface SPI
        ↓
1. 启动 Driver Dev SubAgent
   - 读取用户提供的资料（PDF/代码/图片）
   - 提取关键信息：
     □ 初始化序列/上电时序
     □ 寄存器地址与位定义
     □ 通信协议细节（SPI模式、I2C地址、时序参数）
     □ 数据读取/写入流程
     □ 状态机或工作模式
        ↓
2. 生成 Driver 层代码
   - Core/Driver/xxx_driver.h   (标准接口头文件)
   - Core/Driver/xxx_driver.c   (纯 HAL 封装，不反向依赖)
        ↓
3. 生成测试代码
   - Core/Test/xxx_driver_test.c (包含 xxx_Driver_Test() 函数)
        ↓
4. 自动注册 Keil 工程
   - 运行: python tools/driver_dev.py --name xxx --add-to-keil
   - 把 driver.c 加入 "Driver" Group
   - 把 test.c 加入 "Test" Group
        ↓
5. 输出总结
   - 驱动接口说明
   - 测试方法（如何在 main.c 中调用）
   - 可能的风险/待确认项
```

---

## 输出规范

### Driver 层代码约束（强制）

| 约束 | 说明 |
|------|------|
| **不反向依赖** | Driver 只能 `#include` HAL 头文件和标准库，**禁止**包含 Service/App 层头文件 |
| **接口命名** | `xxx_Driver_Init()`、`xxx_Driver_Read()`、`xxx_Driver_Write()`、`xxx_Driver_DeInit()` |
| **错误处理** | 返回 `int` 错误码（0=成功，-1=失败），或提供 `xxx_Driver_GetError()` |
| **资源隔离** | 不直接操作其他外设的 GPIO/定时器，假设已由对应 Driver 初始化 |
| **可重复初始化** | `Init()` 内部做好去初始化再重新配置的保护 |

### 测试代码模板

测试代码固定放在 `Core/Test/xxx_driver_test.c`，包含：

```c
void xxx_Driver_Test(void);
```

用户需在 `main.c` 中手动调用：

```c
// 在 while(1) 之前调用
xxx_Driver_Test();
```

测试内容至少覆盖：
1. **初始化测试** — 上电初始化是否成功
2. **ID/寄存器读取测试** — 读芯片 ID 或版本寄存器验证通信
3. **基础功能测试** — 一次完整的数据读取或写入
4. **错误提示** — 失败时通过串口打印具体错误位置

---

## 资料解析策略

### 如果是 C/H 参考代码
- 提取初始化函数、寄存器宏定义、读写时序
- 转换为符合本项目分层规范的 Driver 接口
- **去除** 与具体应用绑定的逻辑（如固定引脚、特定平台延时函数）

### 如果是 FPGA 代码（Verilog/VHDL）
- 提取状态机、时序图、寄存器操作顺序
- 用 C 语言实现等效的控制流程
- 重点还原：CS/RS/WR 时序、命令/数据切换、延时要求

### 如果是 PDF datasheet
- 读取初始化章节、时序图、寄存器表
- 提取关键数值（VCC 范围、上电延时、SPI 模式、时钟最大频率）
- 如果有图片无法 OCR，标记为 "待确认"

---

## 执行步骤

当用户调用 `/driver-dev` 时：

### Step 1: 资料读取
```
agent:
  prompt: |
    请读取用户提供的资料文件: {{source}}
    任务：提取该外设的驱动开发关键信息。
    以 JSON 格式输出：
    {
      "chip_name": "芯片型号",
      "interface": "SPI/I2C/UART/...",
      "key_info": {
        "init_sequence": [...],
        "registers": [{"name": "...", "addr": "0xXX", "desc": "..."}],
        "timing": {...},
        "data_format": "..."
      },
      "uncertainties": ["待确认项1", "待确认项2"]
    }
```

### Step 2: 代码生成
由主 Agent 直接生成以下文件：
- `Core/Driver/{{name}}_driver.h`
- `Core/Driver/{{name}}_driver.c`
- `Core/Test/{{name}}_driver_test.c`

生成前先执行：
```bash
python tools/driver_dev.py --name {{name}} --skeleton
```
以创建目录和确认文件路径。

### Step 3: 注册 Keil 工程
代码生成后执行：
```bash
python tools/driver_dev.py --name {{name}} --add-to-keil
```

### Step 4: 编译验证（可选但推荐）
执行 `/build` 检查是否能通过编译。

---

## 与现有工作流的关系

| 阶段 | 使用 Skill | 说明 |
|------|------------|------|
| **驱动开荒** | `/driver-dev` | 不需要 `需求.md`，快速验证硬件 |
| **应用开发** | `/req` → `/arch` → `/sync-req` | 驱动调通后，回到标准需求驱动流程 |

当驱动稳定后，建议：
1. 把该驱动记录到 `外设驱动花名册.md`
2. 后续项目可直接复用

---

## 注意事项

1. **不生成需求文档** — `/driver-dev` 专注于让硬件动起来，文档可在稳定后补
2. **不自动修改 main.c** — 测试函数需要用户手动在 `main.c` 中调用
3. **可能遇到待确认项** — 如果资料 OCR 不完整或时序模糊，会明确标出
4. **Keil 工程自动更新** — 依赖 `tools/driver_dev.py` 修改 `.uvprojx`
