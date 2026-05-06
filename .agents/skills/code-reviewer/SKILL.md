---
schema: skill-1.0
name: code-reviewer
description: Review embedded C code against project requirements, App/Service/Driver architecture, hardware resource ownership, ISR safety, timing, stack, and generated-code boundaries.
user-invocable: true
---

# Code Reviewer SubAgent

专门的嵌入式代码审查助手，通过 AI 直接分析源代码，完成硬件配置验证与代码逻辑安全检查。

## 执行命令

当用户调用 `skill: code-reviewer` 时，执行：

```
Agent: code-reviewer
Prompt: 见下方「调用 Prompt」
```

## 调用方式

### 方式 1: 直接调用 Skill（默认全查）
```
skill: code-reviewer
args: Core/Src/main.c Driver/tim_driver.c Service/ App/
```

### 方式 2: 侧重硬件配置审查
```
skill: code-reviewer
args: --focus=hw Core/Src Driver/
```

### 方式 3: 侧重代码逻辑安全审查
```
skill: code-reviewer
args: --focus=logic App/ Service/
```

### 方式 4: 主 Agent 直接通过 subAgent 调用
```
Agent: code-reviewer
Prompt: 请审查 Core/Src/main.c 和 Driver/tim_driver.c，关注 TIM2 时钟配置和 ISR 安全
```

## 参数说明

| 参数 | 说明 |
|------|------|
| `--focus=hw` | 只查硬件配置（引脚、时钟、外设结构体、DMA 参数等） |
| `--focus=logic` | 只查代码逻辑（ISR 安全、死循环、栈溢出、算法逻辑等） |
| 无参数或 `--focus=all` | 全查（默认） |

## 输入源

审查前必须读取以下文件作为输入：
1. **AI 接手上下文摘要**：运行 `python tools/context.py summary`
2. **工程上下文**：`.context/engineering.yaml`
3. **硬件上下文**：`.context/hardware.yaml`
4. **待审查的源代码文件**（由 args 指定）
5. **需求文档**：`需求.md`（若存在）

## 输出

生成结构化审查报告，保存到 `reports/code_review_report.md`。

报告包含：
- 概要（文件数、问题数、需求符合度）
- 硬件配置检查项（按外设分类）
- 代码逻辑安全检查项
- 需求符合性分析
- 优先级修复列表

## 工作流程

```
主 Agent                   Code Reviewer SubAgent
   │                              │
   │── 1. 调用 Skill / subAgent ──▶│
   │   (提供文件路径 + focus 参数)  │
   │                              │
   │                              ├── 2. 读取需求.md（若存在）
   │                              ├── 3. 读取所有待审查文件
   │                              ├── 4. 逐文件逐条审查规则
   │                              ├── 5. 跨文件关联检查（时钟/引脚）
   │                              ├── 6. 生成结构化报告
   │                              │
   │◀─ 7. 返回报告路径 ───────────│
   │                              │
   │── 8. 主 Agent 决策修复方案   │
```

## 注意事项

1. **Code Reviewer 只负责分析，不修改代码**
2. **主 Agent 负责决策** — 哪些问题需要修复、如何修复
3. **AI 直接读文件做语义分析**，不依赖正则脚本
4. 旧版 Python 脚本 `tools/code_reviewer.py` 保留作为 CI/CD 无 AI 环境的兜底方案
