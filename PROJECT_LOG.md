# 项目开发日志

## 活跃任务
- [x] [cleanup] 清理旧项目事实，将仓库切换为未配置的 workflow kit。

## 阻塞项
<!-- 需要外部资源或人类决策才能继续的事项 -->
*暂无阻塞项*

---

## 2026-05-10

### 已完成
- [x] [skill] 新增 `/project-port` Skill，用问答方式引导真实工程接入 workflow kit。
- [x] [doc] README 和 `.agents/README.md` 补充 `/project-port` 作为接入真实工程的推荐入口。

### 问题 & 解决
- [x] [workflow] 手工从第二步开始修改配置容易遗漏上下文、测试接口和校验。已沉淀为可复用 Skill。

### 待跟进
*无*

---

## 2026-05-07

### 已完成
- [x] [arch] 将目录策略拆分为 `workflow_invariant` 与 `project_architecture`。
- [x] [tool] 更新 `context.py` 和 `project_structure.py`，摘要和结构快照不再把 App/Service/Driver 写死为 workflow 不变量。
- [x] [doc] 更新 Agent 入口、上下文说明、README、CLAUDE 和测试清单，明确其他项目可声明不同架构。

### 问题 & 解决
- [x] [architecture] 之前把当前模板的 App/Service/Driver 误表达为工作流框架绑定。已修正为“当前项目架构声明”。

### 待跟进
*无*

---

## 2026-05-10

### 已完成
- [x] [cleanup] 将 `.workflow/project.yaml` 改为 `workflow_kit` 模式，默认 `toolchain.type: none`。
- [x] [cleanup] 清空旧 STM32/Keil/CubeMX 上下文事实，改为未配置占位。
- [x] [cleanup] 删除旧板卡、CubeMX、架构示例文档和 Keil wrapper 工具。
- [x] [test] 保留测试接口，但默认不创建 `Test/` 目录。
- [x] [test] `context validate`、`workflow verify-config`、`agent_assets validate` 已通过。

### 问题 & 解决
- [x] [config] 旧 context 仍要求 `App/Service/Driver` 和 `very_test.ioc` 存在。已改为 workflow kit 模式下不要求项目架构目录。
- [x] [config] 旧 workflow 默认 Keil。已改为未配置 adapter，并在 build/flash 时给出清晰配置提示。

### 待跟进
*无*

---

## 2026-05-07

### 已完成
- [x] [doc] 新增 `docs/TEST_CHECKLIST.md`，整理近期工程框架改造后的测试顺序和通过标准。
- [x] [test] 清单覆盖无硬件检查、Keil 构建、烧录、verify、GCC/CMake adapter 预留、reports 目录、git/log guard。

### 问题 & 解决
- [x] [process] 改动范围较大，不容易知道从哪里开始测试。已按“低风险无硬件 → 本机工具链 → 真板闭环”的顺序组织清单。

### 待跟进
*无*

---

## 2026-05-06

### 已完成
- [x] [tool] 新增 `tools/log_guard.py`，用于检查本次改动是否更新了持久日志。
- [x] [tool] 扩展 `tools/git_guard.py stage`，支持先暂存任务拥有的文件作为验证前检查点。
- [x] [doc] 更新 Agent 入口文档，要求修改文件后必须写日志、先暂存、验证后再提交。

### 问题 & 解决
- [x] [process] 原规则容易被理解成“每一步都 commit”。已改为 staged checkpoint → validation → commit。
- [x] [process] Agent 容易忘记记录日志。已新增 `.agents/rules/logging.md` 和 `log_guard`。

### 待跟进
*无*

---

## 2026-04-16

### 已完成
- [x] [tool] 补全 `code-reviewer` 外设初始化检查（`clock_enable`）
- [x] [tool] 删除冗余 `review` Skill 及脚本
- [x] [tool] 新增 `/driver-dev` Skill 支持从零开发驱动

### 问题 & 解决
*无*

### 待跟进
*无*
