---
schema: skill-1.0
name: verify
description: 验证嵌入式代码是否满足需求 - 先检查一致性，再编译烧录，最后通过串口测试自动验证，测试失败时调用AI Agent智能修复
parameters:
  - name: req_file
    type: string
    required: false
    default: "./需求.md"
    description: 需求文档路径
  - name: max_retries
    type: integer
    required: false
    default: 3
    description: 自动修复最大重试次数
  - name: test_only
    type: boolean
    required: false
    default: false
    description: 只测试不自动修复
user-invocable: true
---

# /verify — 验证嵌入式代码（AI增强闭环版）

**完整验证流程**：需求一致性检查 → 编译 → 烧录 → 串口测试 → **AI Agent 自动修复** → 循环验证（最多 `max_retries` 次）。

## 使用方式

```
/verify                          # 完整验证+AI自动修复流程
/verify --req ./需求.md          # 指定需求文档路径
/verify --max-retries 5          # 设置最大重试次数
/verify --test-only              # 只测试，失败时不调用AI修复
```

## 执行流程

### 模式 A：test-only（单次测试，不自动修复）

1. 执行：`python .claude/skills/verify/verify.py --test-only --req <req_file>`
2. 读取结果和 `reports/verify_report.md`
3. 展示报告，结束

### 模式 B：完整 AI 闭环（默认）

**步骤 1：单次验证**
- 运行：`python .claude/skills/verify/verify.py --single-run --max-retries 0 --req <req_file> [--port <port>]`
- `verify.py` 内部执行：解析需求 → 编译 → 烧录 → 串口测试 → 生成 `reports/verify_report.md`

**步骤 2：结果判断**
- **Exit code == 0**：验证通过
  - 读取 `reports/verify_report.md`
  - 向用户展示成功结果和测试统计
  - 结束

- **Exit code != 0**：验证失败，进入 AI 修复循环

**步骤 3：AI 修复循环**

```
retry_count = 0
max_retries = <参数值，默认 3>

while retry_count < max_retries:
    1. 读取 reports/verify_report.md，提取失败的测试用例详情
    2. 读取相关代码文件（至少包括以下路径）：
       - Core/Src/main.c
       - App/*.c, App/*.h
       - Service/*.c, Service/*.h
       - Driver/*.c, Driver/*.h
       - 需求文档（req_file）
    3. 调用 Agent 进行智能修复

       Agent Prompt 模板：
       ─────────────────────────────────────────
       你是一个资深的嵌入式工程师，负责修复一个 STM32 项目的测试失败问题。

       ## 项目架构规则（必须严格遵守）
       - 四层架构：App → Service → Driver → HAL
       - 禁止反向依赖
       - 只修复导致测试失败的 bug，不添加新功能
       - 修改必须最小化

       ## 测试失败信息
       <从 reports/verify_report.md 提取的失败用例：id, input, expected, actual, error>

       ## 相关代码
       <附上读取到的代码文件内容>

       ## 需求文档
       <附上需求文档关键内容>

       请分析失败原因，使用 Read 和 Edit 工具修改代码使其通过测试。
       修改完成后返回：修复的文件、修改点简述。
       ─────────────────────────────────────────

    4. Agent 返回后，再次运行 verify.py --single-run
    5. 如果通过：展示成功结果，结束
    6. 如果仍然失败：retry_count += 1，继续循环

    if retry_count >= max_retries:
        停止循环，向用户报告最终失败结果
        展示 reports/verify_report.md 中的详细错误
        给出下一步建议（手动检查硬件/修改需求/继续调试）
```

## Agent 调用规范

当需要调用 Agent 时，使用 `Agent` tool：
- **subagent_type**: `general-purpose`
- **prompt**: 按上述模板构建，包含完整的失败信息和代码内容
- **description**: "修复嵌入式测试失败"

## 测试用例格式

需求文档中需包含测试用例章节，格式如下：

```markdown
## 测试用例

### TC001: LED控制测试
- **输入**: `LED ON`
- **预期输出**: `LED is ON`
- **匹配模式**: contains
- **超时**: 1000ms
```

匹配模式支持：`exact`（精确）、`contains`（包含）、`regex`（正则）、`range`（数值范围）。

## 配置文件

项目根目录可放置 `verify_config.yaml`：

```yaml
serial:
  port: "COM3"          # auto 或指定端口
  baudrate: 115200

test:
  timeout_ms: 2000
  reset_before_test: true

validation:
  max_retries: 3
```

## 验证报告

验证完成后生成 `reports/verify_report.md`：
- 测试用例执行结果
- 通过/失败统计
- 失败原因分析
- 自动修复历史记录

## 依赖

- Python 3.8+
- pyserial, pyyaml
- Keil MDK（编译）
- ST-Link/J-Link（烧录）
