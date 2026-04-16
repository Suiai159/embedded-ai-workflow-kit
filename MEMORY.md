# Memory Index — 工程关键路径

> 本文件随工程复制而迁移，用于快速定位核心文件。

---

## 工程定位

- **目标芯片**：STM32F103
- **IDE 工程**：`MDK-ARM/very_test.uvprojx`
- **CubeMX 配置**：`very_test.ioc`
- **需求文档**：`需求.md`
- **外设驱动花名册**：`外设驱动花名册.md`

---

## 规范文档

| 文件 | 说明 |
|------|------|
| [`CLAUDE.md`](CLAUDE.md) | 项目概述 + 需求驱动开发强制规范 |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | 四层分层架构详细规范 |
| [`WORKFLOW.md`](WORKFLOW.md) | 开发工作流程与代码审查规范 |

---

## 代码分层目录

```text
Core/
├── App/        → 纯业务逻辑
│   └── breathe_app.c / .h
├── Service/    → 功能抽象
│   ├── led_service.c / .h
│   ├── pwm_service.c / .h
│   └── log_service.c / .h
├── Driver/     → 硬件封装
│   ├── gpio_driver.c / .h
│   ├── tim_driver.c / .h
│   └── uart_driver.c / .h
└── Src/        → CubeMX 生成代码 + main.c
    └── main.c
```

---

## 工具脚本

| 文件 | 用途 |
|------|------|
| `tools/build_keil.sh` | 编译 Keil 工程 |
| `tools/flash_keil.sh` | 烧录到 STM32 |
| `tools/code_reviewer.py` | 代码审查脚本 |

---

## 报告输出

| 文件 | 说明 |
|------|------|
| `code_review_report.md` | 最近一次代码审查报告 |
| `verify_report.md` | 最近一次验证报告 |

---

*最后更新：2026-03-30*
