# STM32F103 模板工程

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

- 修改 Keil 工程文件名（如 `MDK-ARM/very_test.uvprojx` → `MDK-ARM/my_project.uvprojx`）
- 修改 `CLAUDE.md` 和 `README.md` 中的项目名称
- 清空 `PROJECT_LOG.md` 中的历史记录

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
├── Core/
│   ├── App/           # 业务逻辑层（无硬件依赖）
│   ├── Service/       # 功能服务层（组合 Driver 提供高级接口）
│   ├── Driver/        # 硬件驱动层（封装 HAL）
│   ├── Src/           # CubeMX 生成的 main.c、中断等
│   ├── Test/          # 驱动测试代码（持久保留）
│   └── Inc/           # 头文件
├── MDK-ARM/           # Keil 工程文件
├── tools/             # 自动化脚本和工具
│   ├── build_keil.sh
│   ├── flash_keil.sh
│   ├── code_reviewer.py
│   ├── driver_dev.py      # 驱动开发辅助
│   └── dev_orchestrator.py # 项目总控脚本
├── .claude/skills/    # Claude Code Skill 定义
├── CLAUDE.md          # 项目开发规范（AI 必读）
├── docs/              # 规范文档与参考资料
│   ├── ARCHITECTURE.md
│   ├── WORKFLOW.md
│   └── 外设驱动花名册.md
├── PROJECT_LOG.md     # 项目进度日志
├── 需求.md             # 当前项目需求文档
├── reports/           # 临时报告输出
└── README.md          # 本文件
```

**重要规则**：所有分层代码必须放在 `Core/` 下，禁止创建 `USER/` 目录存放分层代码。

---

## 可用 Skill 清单

### 需求与架构
- `/req` — 将口头需求转为标准 `需求.md`
- `/arch` — 基于需求生成交互式架构设计 `ARCHITECTURE_PLAN.md`
- `/sync-req` — 需求变更的唯一入口

### 构建与验证
- `/build` — 编译 Keil 工程（自动先执行 `/check-req`）
- `/flash` — 烧录到 STM32
- `/bf` — `build` + `flash` 组合
- `/verify` — 完整验证：检查一致性 → 编译 → 烧录 → 串口测试

### 代码质量
- `/check-req` — 检测代码与需求文档是否一致
- `/code-reviewer` — 静态代码审查（ISR 安全、死循环、栈溢出、时钟使能等）

### 驱动开发
- `/driver-dev` — 读取 datasheet/参考代码，生成 Driver 层代码和测试代码，自动加入 Keil 工程

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
   - `docs/` 目录
   - `.claude/skills/` 目录
   - `tools/` 目录

2. **需要清空的文件**：
   - `PROJECT_LOG.md`
   - `需求.md`
   - `docs/ARCH_PLAN_DESIGN.md`
   - `App/`、`Service/`、`Driver/`、`Test/` 下的业务代码

---

## 依赖环境

- **Keil MDK-ARM**（建议安装于 `D:/Keil5/UV4/UV4.exe`，路径可在全局 `CLAUDE.md` 修改）
- **Git Bash**（Windows）或 **WSL**（用于运行 `.sh` 构建脚本）
- **ST-Link / DAP-Link** 调试器
- **Claude Code**（用于调用 Skill 工作流）

---

## 许可证

本模板工程内的代码和文档可自由复制和修改，用于个人或商业项目。
