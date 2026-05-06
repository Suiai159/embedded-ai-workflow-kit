# STM32F103 模板工程

## 可复用工作流配置

本模板现在把工程工作流配置集中放在 `.workflow/project.yaml`。Skill 负责流程编排，`tools/workflow.py` 负责确定性动作，当前支持 Keil、GCC 命令式构建和 CMake adapter。

常用入口：

```bash
python tools/workflow.py verify-config
python tools/workflow.py build
python tools/workflow.py build --test
python tools/workflow.py flash
python tools/workflow.py register-driver --name st7789
python tools/workflow.py status
```

复制到新项目时，优先修改 `.workflow/project.yaml` 中的 `project.name`、`toolchain.*`、`build.*`、`flash.*` 和 `layout.*`，不要在 Skill 或脚本里写死板子、工程名和工具路径。

工具链选择：

- `toolchain.type: keil`：使用 `.uvprojx` 和 Keil MDK。
- `toolchain.type: gcc`：使用 `build.command` / `build.test_command`，适合 Makefile、脚本化 GCC 工程。
- `toolchain.type: cmake`：使用 `cmake -S/-B` 和 `cmake --build`，适合跨平台工程。

## AI 接手上下文

本模板使用 `.context/` 保存 AI 接手所需事实：

- `engineering.*`：工程结构、分层规则、初始化现实
- `hardware.*`：MCU、时钟、引脚、外设、资源所有权
- `version.*`：工具链、生成代码边界、关键脚本
- `runtime.*`：最近一次构建、烧录、验证状态

常用入口：

```bash
python tools/context.py validate
python tools/context.py summary
python tools/context.py touch-runtime
```

换 AI、换工具链或排查硬件问题前，先看 `python tools/context.py summary`，它是当前工程的事实快照。

> **工程定位**：这是一个**通用可复制的 STM32 嵌入式开发模板**，用于作为新项目的基础起点。
>
> 它不仅包含一个可编译的 Keil 工程，还包含完整的 **Claude Code 辅助开发工作流**、**四层分层架构规范**和**自动化工具链**。

---

## 核心特性

| 特性 | 说明 |
|------|------|
| **四层分层架构** | App → Service → Driver → HAL，依赖方向严格向下 |
| **需求驱动开发** | `需求.md` 是唯一真相源，代码从需求文档生成 |
| **Claude Code Skill 工作流** | 从需求分析、架构设计、代码生成到编译烧录的全流程自动化辅助 |
| **驱动开发支持** | 支持从零根据 datasheet 生成 Driver 层代码和测试代码 |
| **AI 代码审查** | `code-reviewer` 升级为 AI SubAgent 语义分析，覆盖硬件配置与时序计算 |
| **固件自验证框架** | `verify` 编译 TEST_MODE 固件，自动跑测试并输出结构化 JSON |
| **项目日志总控** | `/dev` Skill 自动管理任务链、记录进度、推进工作流 |
| **Keil 自动集成** | 新增文件自动注册到 `.uvprojx` 工程，无需手动添加 |

---

## 快速开始

### 1. 复制本模板到新项目

```bash
# 方法1: 直接复制目录
cp -r very_test my_new_project
cd my_new_project
rm -rf .git
git init

# 方法2: 从本模板 fork 后修改项目名
```

### 2. 修改项目标识

- 修改 `.workflow/project.yaml` 中的项目名、工程文件、hex 输出、工具链路径和目录布局
- 如需重命名 Keil 工程文件，再同步修改 `toolchain.project_file` 和 `build.hex_path`
- 修改 `CLAUDE.md` 和 `README.md` 中仍需展示给人的项目名称
- 清空 `PROJECT_LOG.md` 中的历史记录
- 清空 `EVOLUTION.md` 中的历史记录（保留文件）

### 3. 开始你的第一个需求

```bash
# 创建需求文档
/req "STM32F103C8T6 实现 xxx 功能"

# 架构规划
/arch

# 生成代码后自动审查和编译
/dev --go
```

---

## 目录结构

```text
very_test/
├── App/                 # 业务逻辑层（无硬件依赖）
│   ├── breathe_app.c
│   ├── test_breathe.h      # 固件自验证用例
│   └── test_framework.h    # 轻量 JSON 测试框架
├── Service/             # 功能服务层（组合 Driver 提供高级接口）
├── Driver/              # 硬件驱动层（封装 HAL）
├── Core/                # CubeMX 生成的 main.c、中断等平台代码
│   ├── Inc/
│   └── Src/
├── Drivers/             # HAL 库、CMSIS
├── Test/                # 驱动测试代码（持久保留）
├── MDK-ARM/             # Keil 工程文件
├── tools/               # 自动化脚本和工具
│   ├── build_keil.sh
│   ├── flash_keil.sh
│   ├── code_reviewer.py      # 静态代码审查（CI 兜底）
│   ├── driver_dev.py         # 驱动开发辅助 + Keil 工程自动注册
│   ├── inject_test_mode.py   # 向 uvprojx 注入 TEST_MODE 宏
│   └── dev_orchestrator.py   # 项目总控脚本
├── .claude/skills/      # Claude Code Skill 定义
├── docs/                # 规范文档与参考资料
│   ├── ARCHITECTURE.md
│   ├── WORKFLOW.md
│   ├── 外设驱动花名册.md
│   └── reference/          # 跨平台复用参考知识库
│       ├── gpio.md
│       ├── timer.md
│       ├── uart.md
│       ├── led.md
│       └── platform-notes.md
├── reports/             # Skill 审查报告输出（不纳入 git）
├── CLAUDE.md            # 项目开发规范（AI 必读）
├── EVOLUTION.md         # 工程演进日志（结构变更、Skill 迭代）
├── PROJECT_LOG.md       # 项目进度日志（日常开发任务）
├── 需求.md               # 当前项目需求文档
└── README.md            # 本文件
```

**重要规则**：

- 所有分层代码必须放在 `App/`、`Service/`、`Driver/`、`Test/` 下
- ❌ **禁止**创建 `USER/` 目录存放分层代码
- ❌ **禁止**把 `App/Service/Driver/Test` 放进 `Core/` 内（`Core/` 只放 CubeMX 生成代码）

---

## 可用 Skill 清单

### 需求与架构
- `/req` — 将口头需求转为标准 `需求.md`
- `/arch` — 基于需求生成交互式架构设计 `ARCHITECTURE_PLAN.md`
- `/sync-req` — 需求变更的唯一入口

### 构建与验证
- `/build` — 按 `.workflow/project.yaml` 编译当前工程（自动先执行 `/check-req`）
- `/flash` — 烧录到 STM32
- `/bf` — `build` + `flash` 组合
- `/verify` — 完整验证：检查一致性 → 编译 TEST_MODE 测试固件 → 烧录 → 固件自动输出 JSON 测试结果 → AI 智能修复失败项

### 代码质量
- `/check-req` — 检测代码与需求文档是否一致
- `/code-reviewer` — AI SubAgent 语义代码审查（ISR 安全、死循环、栈溢出、时钟使能、硬件时序计算、跨文件分析等）

### 驱动开发
- `/driver-dev` — 读取 datasheet/参考代码，生成 Driver 层代码和测试代码，并通过 adapter 注册到当前工程

### 项目总控
- `/dev` — 查看项目状态和下一步建议
- `/dev --go` — 自动推进当前任务链
- `/dev --plan` — 生成今日开发计划
- `/dev --wrap` — 结束今日工作并建议 commit

---

## 工作流示例

### 标准应用开发流程

```
/req "实现呼吸灯，周期8秒，PC13低电平有效"
    ↓
/arch
    ↓
（基于 ARCHITECTURE_PLAN.md 生成代码）
    ↓
/dev --go  →  自动: check-req → build → verify
```

### 驱动开荒流程

```
/driver-dev @ST7789_datasheet.pdf --name st7789 --interface SPI
    ↓
/dev --go  →  自动: code-reviewer → build
    ↓
在 main.c 中调用 st7789_Driver_Test()
    ↓
/bf 编译烧录，用逻辑分析仪抓波形验证
```

---

## 复制时的注意事项

1. **保留的规范文件**（必须跟着走）：
   - `CLAUDE.md`
   - `docs/` 目录（含 `reference/`）
   - `.claude/skills/` 目录
   - `tools/` 目录

2. **需要清空的文件**：
   - `PROJECT_LOG.md`
   - `EVOLUTION.md`
   - `需求.md`
   - `docs/ARCH_PLAN_DESIGN.md`
   - `App/`、`Service/`、`Driver/`、`Test/` 下的业务代码

---

## 依赖环境

- **Keil MDK-ARM**（当前 adapter 使用；路径在 `.workflow/project.yaml` 的 `toolchain.exe` 修改）
- **Git Bash**（Windows）或 **WSL**（用于运行 `.sh` 构建脚本）
- **ST-Link / DAP-Link** 调试器
- **Python 3.8+**（`verify` Skill 需要 `pyserial`、`pyyaml`）
- **Claude Code**（用于调用 Skill 工作流）

---

## 许可证

本模板工程内的代码和文档可自由复制和修改，用于个人或商业项目。
