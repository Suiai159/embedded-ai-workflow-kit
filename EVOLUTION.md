# 工程演进日志

记录本模板工程的结构优化、Skill 迭代、工具链完善等关键变更。

---

## 2026-05-06

### [doc] 明确 Agent-neutral 工程定位

**目标**：避免工程默认绑定 Claude Code，让任意能读写文件和运行命令的 AI Agent 都能利用同一套嵌入式工程框架。

**改造**：
- [structure] 新增 `AGENTS.md`，作为通用 AI Agent 接手入口
- [structure] 新增 `.agents/`，用 `.agents/skills/` 管理通用 canonical Skills
- [structure] 新增 `.agents/rules/`，作为通用 Agent 规则源；根目录 `AGENTS.md`、`CLAUDE.md` 保留为发现入口/兼容入口
- [tool] 新增 `tools/agent_assets.py`，支持校验 Agent 资产并同步 `.claude/skills/` 兼容镜像
- [tool] 新增 `tools/git_guard.py`，把修改前 git 状态检查和最终提交要求变成可执行约束
- [tool] 扩展 `tools/git_guard.py stage`，把“先暂存任务检查点，验证可用后提交”变成可执行流程
- [tool] 新增 `tools/log_guard.py`，检查 Agent 是否更新 `PROJECT_LOG.md` 和/或 `EVOLUTION.md`
- [doc] 更新 `README.md`、`CLAUDE.md`、`docs/项目介绍.md`，明确 `.claude/skills/` 只是 Claude/Codex 兼容镜像
- [doc] 更新 `.context/version.*`、`.context/engineering.md`，把 Agent-neutral 入口纳入上下文事实
- [arch] 将默认叙事从 “Claude Code Skill 工作流” 调整为 “Agent 工作流 + tools 确定性命令 + 可选 Skill 适配器”
- [arch] 明确 `App/Service/Driver` 是工程框架不变量，不随主机平台、IDE、工具链或 Agent 变化
- [arch] 明确工程稳定目录与平台/工具适配目录的边界：`App/Service/Driver/Test/docs/.context/.workflow/.agents/tools/reports` 属于工程本身，`Core/Drivers/MDK-ARM/.vscode/.claude/*.ioc` 属于平台、工具或可选 adapter 边界
- [tool] 新增 `tools/project_structure.py` 和 `python tools/workflow.py structure`，让 `.project_structure` 从上下文与 workflow 配置一键生成
- [policy] 规定 Agent 修改文件后必须先暂存本次任务文件，验证可用后再提交，除非用户明确说不要提交
- [policy] 规定 Agent 修改文件后必须更新持久日志：日常进展写 `PROJECT_LOG.md`，框架演进写 `EVOLUTION.md`

---

### [tool] 统一报告输出到 `reports/`

**目标**：让 build、flash、check、review、verify 的输出都成为固定路径的当前证据快照，避免报告散落和多版本堆积。

**改造**：
- [tool] `.workflow/project.yaml` 中 `build.log_path`、`flash.log_path` 迁移到 `reports/build_log.txt`、`reports/flash_log.txt`
- [tool] `workflow.py`、`dev_orchestrator.py`、`context.py` 默认读取 reports 下的 build/flash 日志
- [tool] 删除旧位置 `tools/build_log.txt`、`tools/flash_log.txt`，避免继续把 `tools/` 当作日志目录
- [doc] 新增 `reports/README.md`，明确固定文件名和覆盖写入规则
- [doc] 更新 `AGENTS.md`、`CLAUDE.md`、`README.md`、`docs/项目介绍.md`，禁止默认生成散乱报告文件

---

### [tool] 新增可复用工作流适配层

**目标**：把工程工作流从具体板子、Keil 路径和工程名中解耦，形成可迁移到不同开发平台和工具链的统一入口。

**改造**：
- [structure] 新增 `.workflow/project.yaml`，集中声明项目名、板卡、MCU、工具链、构建/烧录产物、串口和目录布局
- [tool] 新增 `tools/workflow.py`，提供 `build`、`flash`、`register-driver`、`status`、`verify-config` 统一 CLI
- [tool] `build_keil.sh`、`flash_keil.sh` 改为兼容 wrapper，实际逻辑转入 `workflow.py`
- [tool] `driver_dev.py`、`dev_orchestrator.py` 改为读取 workflow 配置，不再硬编码 `Driver/Test/reports` 和 Keil 工程路径
- [tool] 新增 Keil、GCC command、CMake 三类 adapter；GCC/CMake 当前作为跨平台预留入口
- [skill] 更新 `/build`、`/flash`、`/bf`、`/driver-dev`、`/verify`，统一通过 workflow adapter 执行确定性动作

### [structure] 新增 AI 可接手上下文体系

**目标**：让换 AI、换平台或排查硬件问题时有稳定事实入口，减少靠对话历史和猜测继续开发。

**改造**：
- [structure] 新增 `.context/engineering.*`、`hardware.*`、`version.*`、`runtime.*` 四组上下文
- [tool] 新增 `tools/context.py`，支持 `validate`、`summary`、`touch-runtime`
- [tool] `workflow.py` 在 build/flash 后刷新 runtime，上报最新构建和烧录证据
- [tool] `verify.py` 在验证报告生成后刷新 runtime，把失败状态写入 `.context/runtime.*`
- [skill] 更新 `/dev`、`/build`、`/verify`、`/driver-dev`、`/code-reviewer`，要求先读取上下文摘要
- [doc] 更新 `CLAUDE.md` 和 `README.md`，明确必读顺序：`.context/*` → `.workflow/project.yaml` → `需求.md` → 相关源码

**当前状态**：
- `python tools/context.py validate` 通过
- `python tools/workflow.py verify-config` 可解析当前 Keil 配置
- runtime 快照记录：build pass，flash fail（现有 `reports/flash_log.txt` 显示 Target DLL cancelled），verify fail（现有报告显示需求文档编码问题）

---

## 2026-04-20

### [skill] 重构 `code-reviewer` 为 AI SubAgent 语义分析

**问题**：旧版 `tools/code_reviewer.py` 用正则做静态分析，天花板太低：
- 看不懂 `GPIO_InitTypeDef` 结构体字段赋值
- 算不出 `TIM2->PSC=35, ARR=99` 的实际频率
- 跨不了文件（时钟使能在 `main.c`，外设初始化在 `Driver/`）
- DMA 循环模式、数据宽度对齐、缓冲区位置完全查不了

**改造**：
- `SKILL.md`：执行命令从 `python tools/code_reviewer.py` 改为 `Agent: code-reviewer` SubAgent 调用
- `SYSTEM.md`：新增完整硬件配置审查知识库（GPIO/TIM/DMA/UART/ADC/SPI/I2C/时钟/NVIC），共 10 大检查模块
- 支持 `--focus=hw` / `--focus=logic` 参数，硬件配置与代码逻辑可分阶段审查
- 旧版 Python 脚本保留为 CI/CD 无 AI 环境的兜底方案

---

## 2026-04-18

### [structure] 解耦分层目录与 CubeMX Core/ ✅ 已完成

**目标**：将 `App/`、`Service/`、`Driver/`、`Test/` 从 `Core/` 下移到工程根目录，实现四层架构与平台无关。

**执行结果**：
- 物理目录迁移：`Core/App`→`App/`, `Core/Service`→`Service/`, `Core/Driver`→`Driver/`, `Core/Test`→`Test/`
- Keil 工程路径更新（`uvprojx`）：文件路径和 Include Path 全部改为根目录引用
- 规范文件同步：`.project_structure`、`CLAUDE.md`、`README.md`、`docs/ARCHITECTURE.md`
- 脚本更新：`tools/dev_orchestrator.py`、`tools/driver_dev.py`
- Skill 更新：`verify`、`driver-dev`、`req` 的路径引用
- **编译验证通过**：0 Error(s), 0 Warning(s)

**迁移后结构**：
```
very_test/
├── App/              ← 业务层（原 Core/App）
├── Service/          ← 服务层（原 Core/Service）
├── Driver/           ← 驱动层（原 Core/Driver）
├── Test/             ← 测试代码（原 Core/Test）
├── Core/             ← 纯 CubeMX 生成
│   ├── Inc/
│   └── Src/
├── Drivers/          ← HAL 库
└── MDK-ARM/
```

---

### [doc] 新增 `docs/reference/` 参考知识库

**目标**：沉淀从 datasheet 提取的关键参数，实现跨平台复用。

**内容**：
- `gpio.md` — 端口映射、寄存器操作方式、电平极性
- `timer.md` — TIM2 配置参数（72MHz、PSC=35、ARR=99、20kHz）
- `uart.md` — 115200 波特率、128B 缓冲区、printf 重定向策略
- `led.md` — PC13 低电平有效、软件 PWM 20kHz/100级
- `platform-notes.md` — 迁移检查清单、已验证/待验证平台

**用途**：
- 换 MCU 时不用重新翻 datasheet
- AI 生成新平台代码时的知识输入

---

## 2026-04-18

### [skill] 重构 verify 为固件自验证框架

**目标**：Agent 不再"发命令拷问"固件，而是固件自动跑测试、输出结构化 JSON，Agent 只负责读取解析。

**改动**：
- [structure] 新增 `App/test_framework.h` — 轻量 JSON 测试框架（`TestSuite_Start/ReportNum/ReportStr/End`）
- [structure] 新增 `App/test_breathe.h` — breathe_app 自验证用例（5 个 TC：LED 模式、PWM 占空比、亮度、相位、模式切换）
- [tool] 新增 `tools/inject_test_mode.py` — 临时向 uvprojx 注入 `TEST_MODE` 宏
- [tool] `build_keil.sh` 支持 `--test` 参数，自动编译测试固件并恢复 uvprojx
- [tool] `verify.py` 改为：编译(TEST_MODE) → 烧录 → 读取 `===TEST_BEGIN===` ... `===TEST_END===` JSON → 解析报告
- [doc] 更新 `verify/SKILL.md` 描述和流程文档

**设计要点**：
- 测试代码全放 `.h` 文件（`static inline`），避免改 Keil 工程文件列表
- `===TEST_BEGIN===` / `===TEST_END===` 标记隔离 log_service 初始化日志
- `trap EXIT` 确保 uvprojx 异常时恢复

---

## 2026-04-18

### 新增记录机制
- [structure] 新增 `EVOLUTION.md`，用于追踪工程结构的长期演进

### 规范整合
- [structure] `.project_structure` 保留为目录规范专项文件（被 `CLAUDE.md` 强制要求读取）
- [doc] 删除根目录冗余文档：`ARCHITECTURE.md`、`ARCH_PLAN_DESIGN.md`、`WORKFLOW.md`、`外设驱动花名册.md`
- [doc] 新增 `docs/` 目录，集中存放规范文档与参考资料（ARCHITECTURE.md、WORKFLOW.md 等迁移至此）
- [doc] 重写 `README.md`，明确模板工程定位、复制流程和快速开始指南

### 报告输出规范化
- [structure] 新增 `reports/` 目录，统一 Skill 审查报告输出位置
- [tool] 更新 `dev_orchestrator.py`：报告路径改为 `reports/code_review_report.md` 等
- [tool] 更新 `code_reviewer.py`：报告输出路径同步指向 `reports/`
- [skill] 更新 `verify` Skill 配置与脚本，适配新的报告目录结构

---

## 2026-04-16

### Skill 迭代
- [skill] 新增 `/driver-dev` Skill — 支持从零读取商家资料并生成 Driver 层代码
- [skill] 补全 `code-reviewer` 外设初始化检查项（`clock_enable` 验证）
- [skill] 删除冗余的 `review` Skill 及配套脚本

---

## 2026-04-14

### 工程初始化
- [structure] 建立四层分层目录：`Core/App`、`Core/Service`、`Core/Driver`
- [skill] 初始化基础 Skill 集：`/build`、`/flash`、`/bf`、`/req`、`/arch`、`/sync-req`、`/check-req`、`/code-reviewer`、`/verify`
- [tool] 引入 `dev_orchestrator.py` 作为项目自动化总控
