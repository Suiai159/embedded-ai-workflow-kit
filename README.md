# Embedded AI Workflow Kit

一套可复用的嵌入式 AI 开发工作流工具包。不绑定板子、MCU、IDE、工具链、目录结构，也不绑定特定 AI 工具。

---

## 这是什么

把开发规范、项目事实、常用命令组织成一套文件，让你的 AI 工具能真正理解你的嵌入式工程。

你可能处于下面任意一种情况：

- 刚用 CubeMX 生成了一个新工程，想试试让 AI 帮你写代码
- 手里有一套维护了几年的老工程，想看看 AI 能不能帮上忙
- 已经用 AI 写了一段时间代码，但总觉得它不了解项目全貌，改出来的东西对不上
- 只是想先看看这套东西适不适合你的团队

都可以。这套 kit 可以在任何时候接入。

---

## 接入方式

两种方式，看你的情况选一种。

### 方式一：直接克隆（新工程，或还没建仓的工程）

把本仓库克隆到本地，直接在它里面开发。kit 自带的 `.gitignore` 已经拦住了不该推上云的文件。

```bash
git clone <本仓库地址> 我的工程
cd 我的工程
```

然后建一个桥接文件，告诉 AI 工具去读 `AGENTS.md`：

- **Claude Code** → 在工程根目录新建 `CLAUDE.md`，写入：`请先阅读 AGENTS.md，遵循其中的工作流规则。`
- **Cursor** → 新建 `.cursorrules`，内容同上
- **其他工具** → 查阅该工具的入口文件约定，同样写一句指向 `AGENTS.md`

就这一行。不需要把 `.agents/rules/` 里的内容复制到桥接文件里。`AGENTS.md` 是工具无关的根入口，它已经写好了所有规则文件的读取顺序 — AI 读到它之后，会自己去找 `.agents/rules/git.md`、`logging.md` 等具体策略。

之后在 AI 工具里输入：

```text
用 /project-port 把这个工作流工具包接入我的工程。
```

向导会分轮问你项目信息（架构、工具链、硬件等），回答完就配好了。最后验证一下：

```bash
python tools/context.py validate
python tools/workflow.py verify-config
python tools/agent_assets.py validate
```

### 方式二：手动复制（已有工程，不想挪地方）

把以下文件从 kit 复制到你的工程根目录：

```text
你的工程/
├── AGENTS.md
├── .agents/            # AI 行为规则
├── .context/           # 项目事实（架构、硬件、版本）
├── .workflow/          # 工具链配置
├── tools/              # 命令行工具脚本
├── reports/            # 报告输出目录
├── docs/               # 项目文档
├── PROJECT_LOG.md      # 项目日志
└── EVOLUTION.md        # 架构演进记录
```

不需要复制 `README.md`。然后同样建桥接文件、运行向导（见方式一）。

> 复制之后建议把 kit 自带的 `.gitignore` 也合并到你的工程里，避免报告、编译产物等被误推送。

### 不想用向导？

两种方式都可以跳过向导，手动配置：

1. 编辑 `.workflow/project.yaml` — 项目名、工具链、编译/烧录/验证命令、目录布局
2. 编辑 `.context/*.yaml` — 架构分层、硬件信息、工具版本
3. 运行上面的验证命令

### 用的不是 Claude Code / Cursor？

这套 kit 的核心规则写在 `AGENTS.md` 里，是工具无关的。只要你的 AI 工具有办法读一个入口文件，你就可以建一个相似的桥接文件指向它。

---

## Kit 与业务代码的分层

clone 完 kit 之后，你的业务代码放哪？如果直接在 kit 目录里混着写，后续没法独立提 PR 改进 kit。

**推荐做法**：业务代码和 kit 各是一个独立 git 仓库，通过兄弟目录 + 目录链接来分层。

### 目录结构

```text
你的工作区/
├── your-project/                 ← 业务代码，独立 git 仓库
│   ├── .agents -/> ../Kit/…/.agents    ← 目录链接（junction / symlink）
│   ├── tools -/> ../Kit/…/tools        ← 目录链接
│   ├── .context/                       ← 真实目录，项目事实
│   ├── .workflow/                      ← 真实目录，工作流配置
│   ├── reports/                        ← 真实目录，报告输出
│   ├── docs/                           ← 真实目录，项目文档
│   ├── PROJECT_LOG.md                  ← 真实文件
│   ├── EVOLUTION.md                    ← 真实文件
│   └── CLAUDE.md                       ← 桥接文件
│
└── Kit/                                ← 文件夹名必须叫 Kit
    └── embedded-ai-workflow-kit/       ← 本 kit，独立 git 仓库
```

> `Kit` 是固定名称，不能改成 `kit`、`KIT` 或其他，因为业务项目里的链接路径写死了 `../Kit/`。
>
> AGENTS.md 不需要链接到业务项目根目录，桥接文件直接用相对路径引用它。

### 初始化步骤

**第一步**：在工作区根目录下创建 `Kit` 文件夹，clone kit：

```bash
mkdir Kit
cd Kit
git clone <本仓库地址> embedded-ai-workflow-kit
cd ..
```

**第二步**：在业务项目根目录下创建目录链接：

```bash
# Linux / macOS
ln -s ../Kit/embedded-ai-workflow-kit/.agents .agents
ln -s ../Kit/embedded-ai-workflow-kit/tools tools

# Windows（不需要管理员权限）
mklink /J .agents ..\Kit\embedded-ai-workflow-kit\.agents
mklink /J tools ..\Kit\embedded-ai-workflow-kit\tools
```

> Windows 用 `mklink /J`（junction），不是 `mklink /D`。junction 不需要管理员权限或开发者模式。

**第三步**：在业务项目根目录下创建真实目录：

```bash
mkdir .context .workflow reports docs
```

**第四步**：在业务项目根目录下创建（或合并）桥接文件 `CLAUDE.md`：

如果项目还没有桥接文件，新建：

```text
请先阅读 ../Kit/embedded-ai-workflow-kit/AGENTS.md，遵循其中的工作流规则。
```

如果项目已有 `.claude/CLAUDE.md`（或对应的桥接文件），在文件**最顶部**加入这一行，原内容保持不变。

> 目录链接让 AI 看到 `.agents/` 和 `tools/` 就像在业务项目根目录下一样。AGENTS.md 里的路径（`.context/`、`.workflow/` 等）从业务项目根目录解析，链接自动指向 kit。AI 无需额外适配。

### 哪些文件归 kit，哪些归业务项目

| 路径 | 类型 | 归属 | 说明 |
| ------ | ------ | ------ | ------ |
| `.agents/` | 目录链接 | kit | AI 行为规则，跟随 kit 更新 |
| `tools/` | 目录链接 | kit | 命令行工具，跟随 kit 更新 |
| `AGENTS.md` | kit 内部 | kit | AI 入口文件，桥接文件直接引用 |
| `.context/` | 真实目录 | 业务项目 | 架构、硬件、版本等项目事实 |
| `.workflow/` | 真实目录 | 业务项目 | 编译命令、烧录方法、目录布局 |
| `reports/` | 真实目录 | 业务项目 | 工具报告输出 |
| `docs/` | 真实目录 | 业务项目 | 项目文档 |
| `PROJECT_LOG.md` | 真实文件 | 业务项目 | 项目日志 |
| `EVOLUTION.md` | 真实文件 | 业务项目 | 架构演进记录 |
| `CLAUDE.md` | 真实文件 | 业务项目 | 桥接文件 |

### 更新 kit

kit 有更新时，在 `Kit/embedded-ai-workflow-kit/` 下拉取最新代码，目录链接自动生效：

```bash
cd Kit/embedded-ai-workflow-kit
git pull
```

### 多项目共用同一份 kit

多个业务项目可以共享同一个 `Kit` 目录：

```text
你的工作区/
├── project-a/            ← 项目 A
│   └── .agents -> ../Kit/…/.agents
├── project-b/            ← 项目 B
│   └── .agents -> ../Kit/…/.agents
└── Kit/
    └── embedded-ai-workflow-kit/
```

---

## 接入后你的 AI 能做什么

| 行为 | 对应的规则/工具 |
| --- | --- |
| 修改代码前先暂存检查点，验证通过再提交 | `.agents/rules/git.md` |
| 每次改动自动更新 `PROJECT_LOG.md` 和 `EVOLUTION.md` | `.agents/rules/logging.md` |
| 了解你的项目架构、分层、依赖方向 | `.context/engineering.yaml` |
| 知道你的硬件平台、MCU 型号、引脚分配 | `.context/hardware.yaml` |
| 知道工具链版本和代码生成边界 | `.context/version.yaml` |
| 一键编译、烧录、运行测试 | `tools/workflow.py` |

规则文件都可以按你的项目需求修改。

---

## 常用命令

```bash
python tools/context.py summary          # 项目事实总览
python tools/context.py validate         # 校验项目事实配置
python tools/workflow.py verify-config   # 校验 workflow 配置
python tools/workflow.py build           # 编译（需先配置 adapter）
python tools/workflow.py build --test    # 运行测试（需先配置）
python tools/workflow.py flash           # 烧录（需先配置 adapter）
python tools/workflow.py status          # 当前任务状态
python tools/agent_assets.py validate    # 校验 Agent 规则文件
python tools/project_structure.py generate  # 生成工程结构快照
python tools/log_guard.py validate --mode either  # 校验日志是否更新
python tools/git_guard.py status         # 查看 git 状态
```

在未配置真实工程时，`build` 和 `flash` 会提示你先配置 adapter。

---

## 不强制你的架构

workflow 不要求你改目录结构。你的项目可以是：

- `App / Service / Driver`
- `Application / Domain / Platform`
- `src / include / tests`
- RTOS task / module / component 风格

唯一要做的事：在 `.context/engineering.yaml` 中写清楚你的架构目录、依赖方向、所有权和生成代码边界。

---

## 测试

kit 默认不创建 `Test/` 目录（你的项目可能已有测试布局）。但保留测试接口：

- `.workflow/project.yaml` 的 `build.test_command`
- `.workflow/project.yaml` 的 `verify.command`
- `.workflow/project.yaml` 的 `layout.tests`
- `reports/verify_report.md`
- `.context/runtime.yaml` 的 verify 快照

---

## 报告

所有工具报告写入 `reports/`，使用固定文件名覆盖旧结果。历史结论写入 `PROJECT_LOG.md` 或 `EVOLUTION.md`。

固定文件：

- `reports/build_log.txt`
- `reports/flash_log.txt`
- `reports/check_req_report.md`
- `reports/code_review_report.md`
- `reports/verify_report.md`

---

## Git 与日志

Agent 修改文件后的默认行为：

1. 运行 `python tools/git_guard.py status`
2. 更新 `PROJECT_LOG.md` 或 `EVOLUTION.md`
3. 只暂存本次任务相关的文件
4. 验证通过后提交

不要求每个小步骤都 commit；用 staged checkpoint 表示当前候选状态。
