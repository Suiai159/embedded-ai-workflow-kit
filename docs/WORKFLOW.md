# 工作流规则

本工作流工具包是项目中立的。它编排工作，但接入项目需提供架构、硬件、工具链和测试事实。

## 标准流程

```text
上下文验证
→ 需求更新
→ 架构/设计更新
→ 代码修改
→ 审查/检查
→ 编译
→ 测试/验证
→ 报告/runtime 更新
→ 日志更新
→ 暂存检查点
→ 验证后提交
```

## 必需检查

```bash
python tools/context.py validate
python tools/workflow.py verify-config
python tools/agent_assets.py validate
python tools/log_guard.py validate --mode either
```

## 编译与烧录

使用 `tools/workflow.py`，不要在 Agent 提示中硬编码工具命令。

```bash
python tools/workflow.py build
python tools/workflow.py build --test
python tools/workflow.py flash
```

如果 `toolchain.type: none`，编译/烧录应停止并显示清晰的配置提示。

## 测试

工作流保留测试接口，但不创建默认的测试目录。

具体项目可以配置：

- `build.test_command`
- `verify.command`
- `layout.tests`
- `verify.report_path`

## 报告

所有生成的证据写入 `reports/`，使用固定的覆盖写入路径。

## Git 与日志

Agent 必须更新持久化日志、暂存任务所属文件、验证，然后提交可用的检查点。
