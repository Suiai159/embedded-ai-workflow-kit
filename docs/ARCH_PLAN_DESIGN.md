# 架构规划方案设计

## 概述

设计一个新的 `/arch` Skill，用于在编写代码前进行架构规划。采用 **Skill + SubAgent** 的两层架构。

---

## 实现思路

### 1. 整体架构

```
用户调用 /arch
    ↓
/arch Skill (入口层)
    • 参数解析
    • 前置检查
    • 启动 Arch Planner SubAgent (第1轮)
    ↓
Arch Planner SubAgent (第1轮 - 分析&澄清)
    • 读取需求.md
    • 分析模块结构
    • 识别模糊点/待确认项
    • 返回：初步分析 + 问题清单
    ↓
/arch Skill (协调层)
    • 向用户展示问题清单
    • 收集用户回答
    • 启动 Arch Planner SubAgent (第2轮)
    ↓
Arch Planner SubAgent (第2轮 - 设计&生成)
    • 基于澄清后的需求
    • 设计接口
    • 检查资源冲突
    • 生成 ARCHITECTURE_PLAN.md
    ↓
返回架构文档
```

### 关键特性：交互式澄清

SubAgent 是**临时的**，但通过**多轮调用**实现交互：

| 轮次 | SubAgent 任务 | 交互动作 |
|------|--------------|----------|
| 第1轮 | 需求分析 | 返回问题清单 → Skill 展示给用户 → 收集回答 |
| 第2轮 | 架构设计 | 基于回答生成最终架构文档 |

**为什么这样设计？**
- 保持 SubAgent 临时性（符合 Claude Code 架构）
- 实现交互式澄清（避免架构设计基于模糊需求）
- 主 Skill 作为协调者（管理多轮调用状态）

### 2. 组件设计

#### 2.1 /arch Skill

**职责**：
- 接收用户调用，解析参数
- 检查 `需求.md` 是否存在
- 调用 Arch Planner SubAgent
- 处理 SubAgent 返回结果

**输入参数**：
- `--req`: 需求文档路径（默认 `./需求.md`）
- `--output`: 输出路径（默认 `./ARCHITECTURE_PLAN.md`）

**前置检查**：
- 若 `需求.md` 不存在 → 报错，提示先运行 `/req`
- 若 `ARCHITECTURE_PLAN.md` 已存在 → 询问是否覆盖

#### 2.2 Arch Planner SubAgent (交互式设计)

**设计哲学**：SubAgent 是临时的，但通过**多轮调用**实现交互式架构设计。

##### 第1轮：需求分析与澄清

**目标**：识别需求中的模糊点，向用户确认。

**输入**：
- 需求.md 路径
- 项目架构规范 (ARCHITECTURE.md)

**工作流程**：

```
1. 深度阅读需求.md
   • 提取外设清单
   • 提取功能需求
   • 提取时序参数
   • 提取测试用例

2. 模糊点识别 (必须输出)
   检查以下常见问题：
   
   □ 引脚定义
     - 需求是否指定了具体引脚？
     - 示例："PC13（低电平有效）" → 清晰
     - 示例："接一个LED" → 模糊，需确认
   
   □ 时序参数
     - 所有时间值是否具体？
     - 示例："周期8秒" → 清晰
     - 示例："快速闪烁" → 模糊，需确认
   
   □ 阈值边界
     - 阈值比较是否包含等于？
     - 示例："温度>30度报警" → 需确认≥30还是>30
   
   □ 模式切换
     - 状态切换条件是否完整？
     - 示例："自动/手动模式" → 切换条件是什么？
   
   □ 资源冲突
     - 是否多个外设使用相同资源？
     - 示例：TIM2 同时用于 PWM 和定时

3. 输出结构
   
   ```json
   {
     "analysis": {
       "peripherals": ["LED", "TIM2"],
       "functions": ["呼吸灯", "PWM输出"],
       "timing": {"period_ms": 8000}
     },
     "clarifications": [
       {
         "id": "Q1",
         "question": "需求中提到PWM频率≥100Hz，请问具体使用什么频率？",
         "suggestion": "建议使用20kHz，可避免肉眼闪烁并留出足够分辨率",
         "impact": "影响TIM_Driver的分频系数配置"
       }
     ],
     "can_proceed": false
   }
   ```

4. 返回结果
   - 如果有 clarifications → 返回问题清单，等待用户回答
   - 如果无 clarifications → can_proceed = true，直接进入第2轮
```

##### 第2轮：架构设计与文档生成

**目标**：基于澄清后的需求，生成完整架构设计。

**输入**：
- 需求.md 路径
- 澄清回答（用户提供的答案）

**工作流程**：

```
1. 整合需求
   • 原始需求 + 澄清回答 = 完整需求规格

2. 模块划分 (严格遵循四层架构)
   
   Driver层：
   • 每个物理外设一个Driver
   • 封装HAL库，提供统一接口
   
   Service层：
   • 按功能领域划分
   • 组合Driver提供高级功能
   
   App层：
   • 纯业务逻辑
   • 调用Service实现功能

3. 接口设计
   • 为每个模块设计C语言接口
   • 明确参数类型和返回值
   • 标注回调函数

4. 资源检查
   • 引脚冲突检查
   • 定时器冲突检查
   • 中断优先级检查

5. 生成 ARCHITECTURE_PLAN.md
```

**输出**：完整的架构设计文档

### 3. 输出文档结构

**ARCHITECTURE_PLAN.md** 包含：

```markdown
# 架构设计文档

## 1. 需求摘要
• 原始需求概述
• 关键参数提取

## 2. 模块清单

### Driver层
| 模块 | 职责 | 头文件 | 依赖 |
|------|------|--------|------|
| gpio_driver | PC13引脚控制 | gpio_driver.h | HAL_GPIO |
| tim_driver | TIM2定时器管理 | tim_driver.h | HAL_TIM |

### Service层
| 模块 | 职责 | 头文件 | 依赖Driver |
|------|------|--------|-----------|
| led_service | LED控制逻辑 | led_service.h | gpio_driver |
| pwm_service | PWM输出 | pwm_service.h | tim_driver |

### App层
| 模块 | 职责 | 头文件 | 依赖Service |
|------|------|--------|------------|
| breathe_app | 呼吸灯算法 | breathe_app.h | led_service, pwm_service |

## 3. 接口定义

### Driver层接口
```c
// gpio_driver.h
void GPIO_Driver_Init(void);
void GPIO_Driver_WritePin(uint16_t pin, uint8_t state);
```

### Service层接口
```c
// led_service.h
typedef enum { LED_OFF, LED_ON, LED_BREATHE } LED_Mode_t;
void LED_Service_SetMode(LED_Mode_t mode);
```

### App层接口
```c
// breathe_app.h
void Breathe_App_Init(void);
void Breathe_App_Tick(uint32_t timestamp_ms);
```

## 4. 资源分配

| 资源 | 用途 | 所属模块 |
|------|------|----------|
| PC13 | LED输出 | LED_Service |
| TIM2_CH1 | PWM输出 | PWM_Service |
| TIM2_IRQn | 定时器中断 | TIM_Driver |

## 5. 初始化顺序

```
System_Init()
  ├── GPIO_Driver_Init()
  ├── TIM_Driver_Init(period_ms, callback)
  ├── PWM_Service_Init()
  ├── LED_Service_Init()
  └── Breathe_App_Init()
```

## 6. 数据流

```
Breathe_App (算法)
    ↓ 计算亮度
LED_Service (控制逻辑)
    ↓ 设置占空比
PWM_Service (PWM抽象)
    ↓ 操作寄存器
TIM_Driver (硬件驱动)
    ↓ 输出波形
PC13 (物理引脚)
```
```

---

## 使用方法

### 基本用法

```bash
# 基于当前目录的需求.md生成架构设计
/arch

# 指定需求文件
/arch --req ./需求.md

# 指定输出路径
/arch --output ./docs/arch_plan.md
```

### 完整工作流

```
1. 创建需求
   /req "STM32C8T6实现呼吸灯，周期8秒，PC13低电平有效"
   → 生成 需求.md

2. 架构规划（交互式）
   /arch
   → 读取 需求.md
   → 启动 Arch Planner SubAgent (第1轮)
   → 识别模糊点，返回问题清单
   → 向用户展示问题，收集回答
   → 启动 Arch Planner SubAgent (第2轮)
   → 生成 ARCHITECTURE_PLAN.md

3. 查看架构设计
   （阅读 ARCHITECTURE_PLAN.md）

4. 确认或调整
   如需调整：修改需求.md → 重新运行 /arch
   确认无误：开始编写代码

5. 编写代码
   根据 ARCHITECTURE_PLAN.md 的接口定义编写各层代码

6. 检查一致性
   /check-req

7. 编译验证
   /build
```

### 交互式澄清示例

```
用户: /arch

系统: 正在分析需求...
      启动 Arch Planner SubAgent (第1轮)

系统: ┌─────────────────────────────────────────┐
      │ 发现以下需要澄清的问题：                 │
      ├─────────────────────────────────────────┤
      │ Q1: PWM频率需求为"≥100Hz"，请问具体使用  │
      │     什么频率？                           │
      │     建议：20kHz（无肉眼闪烁，分辨率高）  │
      │                                          │
      │ Q2: 呼吸曲线需求为"类正弦波"，请问使用    │
      │     哪种具体算法？                       │
      │     建议：正弦表查找 + Gamma校正(2.2)    │
      └─────────────────────────────────────────┘

用户: 同意建议

系统: 收到确认，正在生成架构设计...
      启动 Arch Planner SubAgent (第2轮)
      → 生成 ARCHITECTURE_PLAN.md

系统: 架构设计已完成！
      查看 ARCHITECTURE_PLAN.md 了解详细设计。
```

### 与需求变更的配合

当需求变更时：

```
/sync-req "周期改成10秒"
   → 更新 需求.md

/arch
   → 基于新需求重新生成架构设计
   → 对比变更，提示影响范围（如：哪些模块需要修改）

（根据新的架构设计修改代码）
```

---

## 预期效果

### 1. 设计阶段清晰化

**Before**：
- 用户口头描述需求
- 直接开始写代码
- 边写边想架构
- 写到一半发现资源冲突

**After**：
- 需求标准化为需求.md
- 先规划架构，明确模块边界
- 提前发现资源冲突
- 按架构文档编写代码

### 2. 代码质量提升

- **接口一致性**：所有模块接口在架构阶段就已定义
- **分层清晰**：严格按照Driver/Service/App分层
- **资源可控**：提前识别引脚、定时器冲突
- **可维护性**：架构文档作为代码地图

### 3. 协作效率提升

- **需求可追踪**：从需求→架构→代码，链路清晰
- **变更可追溯**：需求变更可快速定位影响范围
- **新人友好**：通过架构文档快速理解系统

### 4. 示例场景

#### 场景1：新项目启动（交互式澄清）

```
用户：/req "我要做温度监测，DS18B20传感器，超过30度报警"
系统：生成需求.md

用户：/arch
系统：
  启动 Arch Planner SubAgent (第1轮)...
  
  ┌─────────────────────────────────────────┐
  │ 需求分析完成，发现以下问题需要澄清：     │
  ├─────────────────────────────────────────┤
  │ Q1: DS18B20 数据引脚未指定              │
  │     建议：PA0（可配置为开漏输出）        │
  │                                          │
  │ Q2: "超过30度" 是否包含30度？            │
  │     选项：>30度 / ≥30度                  │
  │                                          │
  │ Q3: 报警方式未指定                       │
  │     建议：蜂鸣器 + LED闪烁               │
  │                                          │
  │ Q4: 采样频率未指定                       │
  │     建议：每秒1次（1Hz）                 │
  └─────────────────────────────────────────┘

用户：Q1同意，Q2选≥30度，Q3只要蜂鸣器，Q4同意

系统：
  收到澄清回答
  启动 Arch Planner SubAgent (第2轮)...
  
  划分模块：
    Driver: onewire_driver (PA0), gpio_driver (蜂鸣器引脚待确认)
    Service: temp_service, alarm_service
    App: monitor_app
  
  ⚠️ 提示：蜂鸣器引脚未确定，请在架构文档中标注
  
  生成 ARCHITECTURE_PLAN.md

用户：（查看架构设计，确认无误）
用户：（根据架构文档编写代码）
用户：/build
系统：（编译前自动/check-req，验证代码符合需求）
```

#### 场景2：需求变更（影响分析）

```
用户：/sync-req "增加OLED显示温度，删除蜂鸣器报警"
系统：更新需求.md

用户：/arch
系统：
  启动 Arch Planner SubAgent (第1轮)...
  
  检测到需求变更，进行差异分析：
  
  ┌─────────────────────────────────────────┐
  │ 变更影响分析：                           │
  ├─────────────────────────────────────────┤
  │ [新增] OLED显示 (I2C接口)                │
  │   影响：新增 i2c_driver, oled_service    │
  │   资源：I2C1 (SDA-PB7, SCL-PB6)          │
  │                                          │
  │ [删除] 蜂鸣器报警                        │
  │   影响：移除 alarm_service               │
  │   注意：原有代码需清理                   │
  └─────────────────────────────────────────┘
  
  Q1: 确认以上变更影响？

用户：确认

系统：
  启动 Arch Planner SubAgent (第2轮)...
  生成更新后的 ARCHITECTURE_PLAN.md
  
  提示："请根据新架构修改代码：
        1. 删除 alarm_service 相关文件
        2. 新增 i2c_driver.c/h, oled_service.c/h
        3. 修改 monitor_app 添加显示逻辑"

用户：（根据提示修改代码）
用户：/verify
系统：（验证通过）
```

---

## 下一步实现

### 需要创建的文件

1. **.agents/skills/arch/SKILL.md** - canonical Skill 入口定义
   - 参数解析（--req, --output）
   - 前置检查（需求.md 存在性）
   - 多轮 SubAgent 调用协调
   - 用户交互处理（展示问题、收集回答）

2. **.agents/skills/arch/planner/SYSTEM.md** - SubAgent 系统提示
   - 第1轮：需求分析 + 模糊点识别
   - 第2轮：架构设计 + 文档生成
   - 输出格式规范（JSON + Markdown）

### 实现步骤

1. **创建 /arch Skill**
   - 实现参数解析
   - 实现前置检查
   - 实现多轮调用逻辑

2. **设计 SubAgent 提示词**
   - 第1轮提示词：聚焦需求分析
   - 第2轮提示词：聚焦架构设计

3. **测试验证**
   - 测试呼吸灯项目（有明确需求）
   - 测试模糊需求（触发澄清流程）
   - 测试需求变更（触发影响分析）

4. **集成到工作流**
   - 更新 CLAUDE.md 文档
   - 添加 /arch 到标准工作流

---

*本文档为架构规划方案设计，具体实现待后续完成。*
