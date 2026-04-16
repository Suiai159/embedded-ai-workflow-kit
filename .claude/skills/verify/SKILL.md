---
schema: skill-1.0
name: verify
description: 验证嵌入式代码是否满足需求 - 先检查一致性，再编译烧录，最后通过串口测试自动验证
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

# /verify — 验证嵌入式代码

**完整验证流程**：需求一致性检查 → 编译 → 烧录 → 串口测试 → 自动修复（最多3次）。

## 使用方式

```
/verify                          # 完整验证流程
/verify --req ./需求.md          # 指定需求文档路径
/verify --max-retries 5          # 设置最大重试次数
/verify --test-only              # 只测试不自动修复
```

## 执行流程

### 1. 解析需求文档
- 读取 `需求.md` 或指定路径的需求文件
- 提取测试用例（输入命令 + 预期输出）

### 2. 编译项目
- 调用 `build` skill 编译当前Keil项目（**build 会自动执行 check-req**）
- 编译失败则停止并报告

### 3. 烧录固件
- 调用 `flash` skill 烧录到STM32
- 烧录失败则停止并报告

### 5. 串口测试
- 自动检测或连接指定串口
- 按测试用例顺序发送命令
- 捕获输出并与预期比对
- 支持多种匹配模式：精确匹配、包含匹配、正则匹配、数值范围

### 6. 结果处理
- **全部通过**：生成验证报告，结束
- **存在失败**：分析错误原因 → 自动修复代码 → 回到步骤3（最多3次）

## 测试用例格式

需求文档中需包含测试用例章节：

```markdown
## 测试用例

### TC001: LED控制测试
- **输入**: `LED ON`
- **预期输出**: `LED is ON`
- **匹配模式**: contains
- **超时**: 1000ms

### TC002: 温度读取测试
- **输入**: `GET TEMP`
- **预期输出**: `TEMP:20-30`
- **匹配模式**: range
- **超时**: 500ms
```

## 匹配模式说明

| 模式 | 说明 | 示例 |
|------|------|------|
| `exact` | 完全匹配 | `"LED ON"` |
| `contains` | 包含子串 | `"LED"` 匹配 `"LED is ON"` |
| `regex` | 正则匹配 | `"TEMP:(\d+)"` |
| `range` | 数值范围 | `"20-30"` 匹配 `"25"` |

## 配置文件

项目根目录可放置 `verify_config.yaml`：

```yaml
serial:
  port: "COM3"          # auto或指定端口
  baudrate: 115200

test:
  timeout_ms: 2000
  reset_before_test: true

validation:
  max_retries: 3
  auto_fix: true
```

## 验证报告

验证完成后生成报告 `verify_report.md`：
- 测试用例执行结果
- 通过/失败统计
- 失败原因分析
- 代码修改历史（如有自动修复）

## 依赖

- Python 3.8+
- pyserial 库
- Keil MDK（编译）
- ST-Link/J-Link（烧录）

## 完整执行步骤

1. **需求一致性检查**：调用 `/check-req`，不一致则停止
2. **解析需求**：读取并解析需求文档中的测试用例
3. **编译检查**：执行构建，检查是否生成hex文件
4. **烧录固件**：下载到STM32目标板
5. **串口连接**：打开串口，复位目标板
6. **执行测试**：遍历所有测试用例
   - 发送输入命令
   - 等待预期输出（带超时）
   - 记录实际输出
7. **结果比对**：比对实际输出与预期
8. **失败处理**：
   - 分析错误类型（无输出/格式错/数值错/超时）
   - 尝试自动修复代码
   - 重试编译烧录测试（最多3次）
9. **生成报告**：输出验证结果到 `verify_report.md`
