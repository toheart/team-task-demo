# OpenSpec Apply 内嵌参考

本参考只服务于 `feature-exec` 的 `implement` 阶段，不是独立 Skill。父 Skill 的角色边界、状态脚本、Gate 规则和完成标准优先于本文。

## 使用边界

- 只参考 OpenSpec 的任务消费方式，不接管父级执行流程。
- 不能跳过 `test-design`、`code-review`、`test-run`、`gate-delivery`。
- 非 trust 模式下，任何实现进展都不能自动通过人工 Gate。
- 执行状态以 `.orchestrator/execution-state.json` 为准，不只依赖 `tasks.md` 复选框。

## 输入

实现前必须先由父 Skill 校验：

```bash
python scripts/orchestrator-state.py validate-handoff <change-name> --check-artifacts
```

然后读取：

```text
openspec/changes/<change-name>/.orchestrator/handoff.json
openspec/changes/<change-name>/.orchestrator/explore-report.md
openspec/changes/<change-name>/.orchestrator/test-evidence.md
openspec/changes/<change-name>/proposal.md
openspec/changes/<change-name>/design.md
openspec/changes/<change-name>/tasks.md
openspec/changes/<change-name>/test-guides/*.md
```

`design.md` 的「实现反模式（SubAgent 必读）」段是硬约束，实现时不得违反。

可用 OpenSpec CLI 获取当前任务上下文：

```bash
openspec status --change "<change-name>" --json
openspec instructions apply --change "<change-name>" --json
```

## 任务消费规则

- 按 `tasks.md` 的端别标注（`[共享]` / `[后端]` / `[前端]` / `[联调]`）与 `affected_ends` 分配给对应 implementer。
- 只按 `[L1]`/`[L2]`/`[L3]` 分级消费信息：L3 任务的「架构约束」与「停手条件」是必读项。
- 每次只处理当前阶段允许的任务，保持改动最小。
- 实现发现设计缺陷时，暂停并回报，不在执行阶段重写需求。
- 命中 L3 任务的「停手条件」时停止并报告，不自行决定数据模型、错误语义、接口形态或落盘位置。
- 任务完成后可以更新 `tasks.md` 复选框，但必须同步由父 Skill 维护执行阶段状态。
- 不为未要求的扩展能力、抽象或兼容层做实现。

## 交付给父流程

`implement` 完成后返回父 Skill，由父 Skill 进入：

```text
code-review -> test-run -> gate-delivery
```

不要自行宣布整个 change 完成，也不要直接归档。
