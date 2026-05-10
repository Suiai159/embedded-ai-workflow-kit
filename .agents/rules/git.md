# 强制 Git 策略

Git 是工程工作流的一部分，不是可选的清理步骤。

## 必需流程

任何修改文件的 Agent 必须：

1. 编辑前运行 `git status --short`，识别预先存在的脏文件。
2. 避免还原或暂存与用户无关的修改。
3. 在完成一组连贯编辑后，只暂存当前任务修改的文件。
4. 运行相关验证命令。
5. 运行 `git diff --cached` 或等效的暂存差异审查。
6. 仅在暂存变更验证通过且可用后提交。
7. 在最终回复中提及提交哈希和剩余的无关脏文件。

不要为每个微小步骤创建提交。工作中使用暂存检查点，然后提交已验证通过的检查点。

## 辅助命令

尽可能使用辅助脚本：

```bash
python tools/git_guard.py status
python tools/git_guard.py stage --paths <file-or-dir>...
python tools/git_guard.py pre-final
python tools/git_guard.py commit --message "type: concise summary" --paths <file-or-dir>...
```

`stage` 是工作中正常的暂存检查点命令。`commit` 在验证通过后使用。`pre-final` 在任务所属变更未全部提交时失败。如果用户明确要求在提交前暂停，需明确说明并将工作区状态留在交接待办中。

## 提交规则

- 提交信息应简洁，描述工程变更内容。
- 在验证前暂存任务所属变更，使候选检查点明确可见。
- 不提交编译产物，除非是有意跟踪的项目文件。
- 不暂存任何 Agent 或编辑器的本地设置，例如工具特定隐藏目录下的私有配置文件。
- 不暂存无关的生成文件（如依赖 `.d` 文件），除非任务明确拥有它们。
- 如果命令因权限问题无法提交，应请求批准 git 命令，而不是留下未提交的变更。
