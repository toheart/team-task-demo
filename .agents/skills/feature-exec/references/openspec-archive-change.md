# OpenSpec Archive 内嵌参考

本参考只服务于 `feature-exec` 的 `archive` 阶段，不是独立 Skill。父 Skill 的角色边界、状态脚本、Gate 规则和完成标准优先于本文。

## 归档前置条件

进入 `archive` 前必须确认：

- `design-state.json` 已完成设计阶段。
- `execution-state.json` 已完成 `test-design`、`implement`、`code-review`、`test-run`。
- `.orchestrator/test-evidence.md` 已存在，且 `change-gate` Required 的 FAIL / SKIP / NOT_RUN 均为零。
- `gate-delivery` 已通过；非 trust 模式下必须有用户明确确认。
- 需要保留的测试资产已经落盘。

如果任何条件不满足，不允许归档。

## 状态检查

检查 OpenSpec artifact 状态：

```bash
openspec status --change "<change-name>" --json
```

检查 `tasks.md` 是否仍有未完成任务。若存在未完成任务，必须在 Gate 摘要中说明，并等待父流程决策；不要直接归档。

## 归档命令

优先使用 OpenSpec CLI：

```bash
python scripts/orchestrator-state.py set-stage execution <change-name> archive active
openspec archive <change-name> --yes
python scripts/orchestrator-state.py set-stage execution <change-name> archive completed
```

`openspec archive` 会把 `openspec/changes/<change-name>/` 移到
`openspec/changes/archive/<YYYY-MM-DD>-<change-name>/`。`scripts/orchestrator-state.py`
能识别归档目录，归档后继续读写状态不会重建空的活跃目录。

如果 CLI 不可用，才考虑手动移动目录；手动归档前必须说明原因，并保持 `.openspec.yaml` 随 change 一起移动。

## 输出给父流程

归档完成后返回以下信息给 `feature-exec`：

```text
change name
archive location
artifact completion summary
task completion summary
test evidence path
```
