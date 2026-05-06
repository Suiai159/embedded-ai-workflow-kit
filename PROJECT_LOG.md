# 项目开发日志

## 活跃任务
- [x] [policy] 明确 Agent 工作的 git 节奏：先暂存任务检查点，验证可用后再提交，避免每个小步骤都产生 commit。
- [x] [policy] 增加强制日志记录规则：Agent 修改文件后必须更新 `PROJECT_LOG.md` 和/或 `EVOLUTION.md`。

## 阻塞项
<!-- 需要外部资源或人类决策才能继续的事项 -->
*暂无阻塞项*

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
