# 项目开发规范

> 本文件是 Claude Code 兼容入口，不代表工程默认绑定 Claude Code。通用 AI Agent 入口是 `AGENTS.md`；canonical rules 位于 `.agents/rules/`，canonical Skills 位于 `.agents/skills/`；所有 Agent 都应遵循 `.context/`、`.workflow/` 和 `tools/` 定义的事实与命令。

## 可复用工作流入口

本工程的板子、工具链、工程文件、hex 输出、串口和目录布局统一声明在 `.workflow/project.yaml`。

- Agent 工作流只负责编排流程，不直接硬编码板子、工程名、Keil 路径或 hex 路径。
- 构建、烧录、工程文件注册等确定性动作统一通过 `python tools/workflow.py ...` 执行。
- 当前支持 `toolchain.type: keil`、`gcc`、`cmake`；新增工具链时优先扩展 `tools/workflow.py`，不要复制一套新的 Agent 流程。
- 旧入口 `tools/build_keil.sh`、`tools/flash_keil.sh` 保留为兼容 wrapper。

## 规则文件位置

- `AGENTS.md` 和 `CLAUDE.md` 保留在根目录，作为 Agent 自动发现入口和兼容入口。
- 通用规则源放在 `.agents/rules/`，不要把长期规则只写进 `.claude/`。
- 通用 Skills 源放在 `.agents/skills/`，`.claude/skills/` 是兼容镜像。

## Git 强制保存

任何 Agent 修改文件后，必须先暂存本次任务变更，验证可用后再提交，除非用户明确说不要提交：

```bash
python tools/git_guard.py status
python tools/git_guard.py stage --paths <task-owned-files>
python tools/git_guard.py pre-final
python tools/git_guard.py commit --message "type: summary" --paths <task-owned-files>
```

不要每做一步都提交。用暂存区表达当前候选检查点，验证通过后再提交。只暂存本次任务拥有的文件，不要提交用户已有改动、本地设置或无关生成物。

## 日志强制记录

任何 Agent 修改文件后，必须更新持久日志：

- 普通开发、验证结果、阻塞项、下一步：写 `PROJECT_LOG.md`
- 工程框架、规则、Skill、tools、目录边界变化：写 `EVOLUTION.md`
- 当前证据快照仍写入 `reports/`，不要用报告文件代替日志

检查命令：

```bash
python tools/log_guard.py validate --mode either
```

## AI 接手上下文（必读）

本工程的接手事实源集中在 `.context/`：

- `.context/engineering.*`：工程结构、分层规则、初始化现实、AI 修改约束
- `.context/hardware.*`：MCU、时钟、引脚、外设、资源所有权、信号极性
- `.context/version.*`：工具链、生成代码边界、关键脚本和兼容性状态
- `.context/runtime.*`：最近一次构建/烧录/验证状态和当前已知运行问题

所有开发类 Agent/Skill 的必读顺序：

```text
AGENTS.md → .context/* → .agents/rules/* → .workflow/project.yaml → 需求.md → 相关源码
```

强制规则：

- 开始 `/dev`、`/build`、`/verify`、`/driver-dev`、`/code-reviewer` 或等价 Agent 流程前，先运行 `python tools/context.py summary`。
- 修改文件前运行 `python tools/git_guard.py status`，识别已有脏文件。
- 修改文件后必须更新 `PROJECT_LOG.md` 和/或 `EVOLUTION.md`，并运行 `python tools/log_guard.py validate --mode either`。
- 涉及构建、烧录、验证证据变化后，运行 `python tools/context.py touch-runtime` 更新运行快照。
- 口头描述不能覆盖 `.context/` 中已记录事实；若事实变化，先更新上下文，再继续实现。
- 如果上下文缺失或 `python tools/context.py validate` 失败，必须先报告缺失项，不要靠猜继续。
- 修改文件后必须按 `.agents/rules/git.md` 暂存本次任务变更；验证可用后再提交，除非用户明确说不要提交。

## ⚠️ 需求驱动开发强制规范

### 唯一真相源

**`需求.md` 是本项目的唯一需求标准，对话框中的口头需求≠有效需求。**

### 黄金法则

```
你的口头需求 → 我更新需求.md → 我基于需求.md生成代码
     ↑___________________________________________|
              (验证失败反馈循环)
```

### 强制规则

| 规则 | 说明 | 违规后果 |
|------|------|----------|
| **R1** | 所有需求必须先写入 `需求.md` | 直接改代码会被拒绝 |
| **R2** | 代码生成只读取 `需求.md` | 对话历史不作为输入 |
| **R3** | 需求变更必须通过 `/sync-req` | 确保变更可追溯 |

### 标准话术（我会严格执行）

- **你说**："周期改成10秒"
- **我答**："我先更新需求.md，然后重新生成代码"

- **你说**："直接改代码，不要改需求"
- **我答**："❌ 拒绝。为了保持可追溯性，我必须先更新需求文档。这是强制规范。"

### 工作流程

```
需求分析 → 写入需求.md → 代码生成 → [自动审查] → 修复问题 → 编译验证
    ↑                                                        |
    └──────────── 验证失败，回到需求分析 ─────────────────────┘
```

### 为什么这样做？

1. **可追溯**：任何时候都能知道"为什么代码这样写"
2. **一致性**：代码和需求文档永远同步
3. **可验证**：测试用例从需求.md自动生成
4. **可审计**：变更历史完整记录

---

## 分层架构（必须遵循）

### 架构不变量

`App/`、`Service/`、`Driver/` 是本工程框架的稳定分层，不随 Windows/Linux、Keil/GCC/CMake、Claude/Codex/其他 Agent 或 IDE 变化。

- 换主机平台或构建工具：只改 `.workflow/project.yaml`、`tools/workflow.py` 或工具链 adapter
- 换 MCU/开发板：可以改 `Driver` 内部实现、HAL 绑定和硬件上下文，但不得破坏 App/Service/Driver 的依赖契约
- `Core/`、`Drivers/`、`.ioc` 和工具工程文件属于平台/厂商生成边界，不承载业务分层架构
- 只有明确的架构重构任务才允许改变 App/Service/Driver 的职责边界

### 目录边界

| 类别 | 目录/文件 | 规则 |
|------|-----------|------|
| 工程稳定目录 | `App/`, `Service/`, `Driver/`, `Test/` | 随工程框架长期保留，不因 OS、IDE、工具链或 Agent 改名/搬迁 |
| 工程事实目录 | `docs/`, `.context/`, `.workflow/`, `.agents/` | 记录项目知识、AI 接手事实、工具配置、Agent 规则和 canonical Skills，是可接手工程的一部分 |
| 工程工具目录 | `tools/`, `reports/` | `tools/` 执行确定性动作，`reports/` 保存当前证据快照 |
| 平台生成边界 | `Core/`, `Drivers/`, `very_test.ioc` | 随 MCU、CubeMX、HAL/vendor 包变化 |
| 工具适配边界 | `MDK-ARM/`, `.vscode/`, `.claude/` | 随 IDE、本地环境或可选 Agent adapter 变化 |

换平台或工具链时，优先修改 `.workflow/project.yaml`、`tools/workflow.py` 和 adapter；不要移动工程稳定目录。

### 四层结构

```text
App层      → 纯业务逻辑，无硬件依赖（breathe_app）
Service层  → 功能抽象（led_service, pwm_service, log_service）
Driver层   → 硬件封装（gpio_driver, tim_driver, uart_driver）
HAL层      → CubeMX标准库
```

### 核心约束

**1. 依赖方向（绝对禁止反向）**
```
App → Service → Driver → HAL
```
- ❌ App 层不能包含任何硬件头文件（stm32f1xx_hal.h 等）
- ❌ Driver 层不能包含 Service/App 层头文件
- ✅ 只能向下依赖

**2. 初始化规则（防止重复初始化）**
```c
// main.c System_Init() 统一初始化，按层顺序：
GPIO_Driver_Init();    // 1. Driver层先初始化
TIM_Driver_Init(...);
PWM_Service_Init();    // 2. Service层不再调用Driver_Init()
LED_Service_Init();
Breathe_App_Init();    // 3. App层最后
```
- Service 层**禁止**调用 `Driver_Init()`，假设 Driver 已就绪
- Driver 层应支持重复调用（内部做好防护）

**3. 资源所有权（防止冲突）**

| 资源 | 唯一所有者 | 其他模块访问方式 |
|------|-----------|----------------|
| PC13 | LED_Service | 调用 `LED_Service_SetMode()` |
| TIM2 | TIM_Driver | 通过回调注册 |

- 禁止两个 Service 直接操作同一硬件资源
- PWM_Service 提供功能，但不直接操作 GPIO（由 LED_Service 调用）

**4. 添加新模块检查清单**
- [ ] 确定所属层级（App/Service/Driver）
- [ ] 检查依赖方向（无反向依赖）
- [ ] 确认硬件资源未被占用
- [ ] 在 `System_Init()` 中按顺序添加初始化

详细规范参见：[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

### 目录结构规范（复制工程时必须遵守）

**生成代码前必须读取 `.project_structure` 文件。该文件由 `.context/engineering.yaml` 和 `.workflow/project.yaml` 生成，不要手写维护。**

刷新命令：

```bash
python tools/workflow.py structure
```

分层代码的物理位置：

| 层级 | 目录 | 示例 |
|------|------|------|
| App | `App/` | `App/breathe_app.c` |
| Service | `Service/` | `Service/led_service.c` |
| Driver | `Driver/` | `Driver/gpio_driver.c` |

**强制规则**：
- ❌ **禁止**创建 `USER` 文件夹存放分层代码
- ❌ **禁止**把 `App/Service/Driver/Test` 放进 `Core/` 内（Core/ 只放 CubeMX 生成代码）
- ✅ 必须保持 Keil 工程的 Include Path 不变

**如果AI错误地把代码生成到USER或其他位置：**
- build/flash skill 会因找不到文件而失败
- 必须手动迁移代码到正确位置

---

## 工作流程（必须遵循）

### 标准流程

```
需求分析 → 架构规划 → 编写代码 → [自动审查] → 修复问题 → 编译验证
    ↑          ↑                                        |
    └──────────┴──────── 验证失败，回到需求分析 ─────────┘
```

### 阶段说明

| 阶段 | 触发方式 | 输入 | 输出 | 说明 |
|------|----------|------|------|------|
| **需求分析** | `/req` | 用户描述 | `需求.md` | 将模糊想法转为标准需求 |
| **架构规划** | `/arch` | `需求.md` | `ARCHITECTURE_PLAN.md` | 模块划分、接口设计 |
| **编写代码** | `/sync-req` | `需求.md` | 代码文件 | 严格基于需求生成代码 |

### Skill 输入规范（强制）

**所有涉及需求分析的 Skill，必须以 `需求.md` 为唯一输入源：**

| Skill | 输入源 | 输出 | 禁止行为 |
|-------|--------|------|----------|
| `/req` | 用户口头/文本描述 | `需求.md` | 无 |
| `/arch` | `需求.md` | `ARCHITECTURE_PLAN.md` | 禁止口头询问需求 |
| `/sync-req` | `需求.md` + 用户变更描述 | 更新后的 `需求.md` | 禁止直接改代码 |
| `/check-req` | `需求.md` + 代码 | 一致性报告 | 无 |

**核心规则**：

- 若 `需求.md` 不存在 → 提示用户先执行 `/req`
- 若需求模糊 → 提示用户更新 `需求.md`，而非口头解释
- 代码生成只读取 `需求.md`，对话历史不作为输入

### 代码审查（自动触发）

**关键规则**：
1. 代码编写完成后**自动**调用 `code-reviewer` SubAgent
2. **不需要用户说**"帮我审查""检查一下"
3. 严重问题 🔴 必须修复后才能进入下一阶段

**审查重点**：
1. **ISR 安全**：中断中无阻塞操作（HAL_Delay、printf）
2. **死循环保护**：轮询等待必须有超时
3. **共享变量**：32位变量原子访问
4. **需求符合**：GPIO、PWM、时序符合需求文档
5. **栈溢出**：大数组不分配在栈上
6. **架构合规**：分层依赖、重复初始化、资源冲突

**质量门禁**：
- 🔴 严重：必须修复（阻塞ISR、死循环、资源冲突）
- 🟡 警告：建议修复
- 💡 建议：可选优化

详细流程参见：[docs/WORKFLOW.md](docs/WORKFLOW.md)

---

## 项目日志

**文件**：`PROJECT_LOG.md`

### 记录范围

| ✅ 应该记录 | ❌ 不记录 |
|-----------|----------|
| 需求变更及原因 | 工具配置（VS Code 快捷键等） |
| 架构决策及取舍 | 环境搭建步骤 |
| 关键 bug 及修复思路 | 临时调试手段 |
| 模块开发里程碑 | 纯格式/排版调整 |
| 阻塞项及等待原因 | |

### 规则

- **按任务块记录**：每完成一个可交付的功能/修复，在 `PROJECT_LOG.md` 写一行总结
- **必须记录「问题 & 解决」**：踩过的坑要记下来，避免重复踩
- **提交前 commit**：`PROJECT_LOG.md` 随代码一起提交，纳入 git 版本管理

## 工程演进日志

**文件**：`EVOLUTION.md`

### 记录范围

| ✅ 应该记录 | ❌ 不记录 |
|-----------|----------|
| Skill 的增删改、功能迭代 | 日常开发任务（已在 PROJECT_LOG.md） |
| 目录结构变更、文件迁移 | 模块内部实现细节 |
| 工具链、脚本配置更新 | 临时调试手段 |
| 架构分层规则调整 | |

### 与 PROJECT_LOG.md 的区别

- `PROJECT_LOG.md` → 日常开发任务（修 bug、写模块、验证结果）
- `EVOLUTION.md` → 工程骨架的结构性变更（新增目录、Skill 迭代、规范重写）

### 类型标记

| 标记 | 含义 |
|------|------|
| `[skill]` | Skill 增删改 |
| `[structure]` | 目录/文件结构变更 |
| `[tool]` | 脚本、工具链、配置更新 |
| `[doc]` | 规范文档合并、重写 |
| `[arch]` | 架构规则调整 |

## 报告输出规范

**所有 Agent、Skill、脚本报告必须输出到 `reports/` 目录。`reports/` 是当前证据快照目录，不是历史归档目录。**

| 类型 | 固定文件 |
|------|----------|
| build | `reports/build_log.txt` |
| flash | `reports/flash_log.txt` |
| `/check-req` | `reports/check_req_report.md` |
| `/code-reviewer` | `reports/code_review_report.md` |
| `/verify` | `reports/verify_report.md` |

- 每类报告使用固定文件名，默认覆盖旧报告
- 禁止默认生成时间戳报告、`*_final.md`、`*_new.md` 等散乱文件
- 历史结论写入 `PROJECT_LOG.md`；工程结构变化写入 `EVOLUTION.md`
- 只有用户明确要求归档时，才允许复制到 `reports/archive/`
- 各脚本和 Agent 流程中的默认路径必须指向 `reports/`

## Git Commit 粒度（改 bug 时特别重要）

**核心原则：每次有进展就 commit，不要攒到最后。**

```
❌ 错误：修了3小时，最后一次性 commit "fix bugs"
✅ 正确：
   commit 1: "fix: 修复 UART 接收缓冲区越界（初步）"
   commit 2: "fix: 处理边界 case，消除偶发丢包"
   commit 3: "fix: 最终验证通过，UART 接收稳定"
```

**为什么这样？**
- 改崩了可以 `git checkout HEAD~1` 回退到上一个**能用的中间状态**
- `git log` 能还原完整的调试过程，第二天回来不用从头再来
- 配合 `PROJECT_LOG.md` 的「问题 & 解决」栏，能瞬间想起当时思路

## 需求文档

- 标准需求文件：`需求.md`（由 `req` Skill 生成）
