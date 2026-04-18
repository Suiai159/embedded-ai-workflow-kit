# 工程演进日志

记录本模板工程的结构优化、Skill 迭代、工具链完善等关键变更。

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
