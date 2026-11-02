## Orchestrator Shared State Convention

本约定定义 Cursor / Claude Code / Codex 之间共享的编排状态、交接文件与恢复规则。

目标：

1. 不依赖任何外部流水线服务或 HTTP 上报状态
2. 不把编排真相放在 `.cursor/` 或 `.claude/` 的私有状态目录
3. 让设计阶段与执行阶段围绕同一个 OpenSpec change 目录协作

### 公共目录

每个 change 的共享状态目录固定为：

```text
openspec/changes/<change-name>/.orchestrator/
```

这个目录中的文件是跨 IDE 的共享事实，不属于某一个 IDE 的私有缓存。

### 标准文件

```text
openspec/changes/<change-name>/.orchestrator/
├── design-state.json
├── execution-state.json
├── handoff.json
├── explore-report.md
├── design-review.md
└── test-evidence.md
```

说明：

- `design-state.json`：`feature-design` 维护
- `execution-state.json`：`feature-exec` 维护
- `handoff.json`：设计到执行的正式交接契约
- `explore-report.md`：设计侧调研结论
- `design-review.md`：架构级方案评审报告
- `test-evidence.md`：场景映射、分层结果、Red/Green 证据与 waiver

设计阶段不产生 `brief.md`。需求背景与目标由 `proposal.md` 和 `explore-report.md` 承载，
重复登记会让状态机出现两个事实来源；脚本会拒绝把 `.orchestrator/brief.md` 写进 handoff。

### `design-state.json`

```json
{
  "schema_version": 2,
  "change_name": "example-change",
  "role": "design",
  "owner_ide": "cursor",
  "skill": "feature-design",
  "trust": false,
  "status": "active",
  "current_stage": "design-review",
  "stages": {
    "explore": "completed",
    "propose": "completed",
    "design-review": "active",
    "gate-design": "pending",
    "write-handoff": "pending"
  },
  "updated_at": "2026-06-27T02:00:00Z"
}
```

### `execution-state.json`

```json
{
  "schema_version": 2,
  "change_name": "example-change",
  "role": "execution",
  "owner_ide": "claude-code",
  "skill": "feature-exec",
  "trust": false,
  "status": "active",
  "current_stage": "test-run",
  "stages": {
    "test-design": "completed",
    "implement": "completed",
    "code-review": "completed",
    "test-run": "active",
    "gate-delivery": "pending",
    "archive": "pending"
  },
  "failure_cycle": 0,
  "requires_confirmation": false,
  "updated_at": "2026-06-27T03:00:00Z"
}
```

阶段状态统一使用：

- `pending`
- `active`
- `completed`
- `failed`
- `skipped`

同一时刻最多只有一个 `active`；脚本在激活某阶段时会把它下游已结束的阶段重置为 `pending`，
避免出现「下游已完成但上游刚回退」的非法组合。

### 失败暂停字段

测试失败进入 `gate-test-failure` 时，脚本会在 execution state 中写入：

- `failure_cycle`：累计失败轮次
- `requires_confirmation`：为 `true` 时不得继续调度
- `last_failure`：`{ stage, class, reason, recorded_at }`

`class` 取值范围：`business`、`test_asset`、`environment`、`fixture`。
写入需要同时提供 `--failure-class` 与 `--reason`，否则脚本报错退出。

### `handoff.json`

设计阶段通过 `gate-design` 后必须写入该文件。执行阶段启动前必须先读取并校验它。

```json
{
  "schema_version": 2,
  "change_name": "example-change",
  "status": "design_ready",
  "design_gate_passed": true,
  "producer": {
    "ide": "cursor",
    "skill": "feature-design",
    "updated_at": "2026-06-27T02:30:00Z"
  },
  "required_artifacts": [
    "proposal.md",
    "design.md",
    "tasks.md"
  ],
  "optional_artifacts": [
    ".orchestrator/explore-report.md"
  ],
  "executor_notes": [
    "feature-exec 必须在归档前完成测试设计、Required 测试执行和 gate-delivery"
  ],
  "pending_risks": [],
  "gate_decisions": [
    "design-review passed"
  ]
}
```

`handoff.json.status` 允许值：

- `draft`
- `design_ready`
- `execution_in_progress`
- `needs_design_revision`
- `completed`

**`required_artifacts` 只允许 `proposal.md`、`design.md`、`tasks.md`。** 测试设计产物
（`test-plan.md`、`test-guides/`）属于执行侧，写进 required 会导致执行阶段被设计侧阻塞；
`validate-structure` 会把它判为错误。

### 测试产物

测试分层与执行通道的约定见 `openspec/docs/test-guides-convention.md`：

```text
openspec/changes/<change-name>/test-guides/*.md
openspec/changes/<change-name>/.orchestrator/test-evidence.md
```

- `test-design` 生成 guide 与 evidence 的计划列
- 测试 Writer 填写实际测试文件
- `qa-tester` 回填 executed / PASS / FAIL / SKIP / NOT_RUN / 命令 / 环境
- Gate 填写 waiver 与遗留风险

### 写入规则

1. 设计编排器只写 `design-state.json`、`handoff.json` 以及设计产物。
2. 执行编排器只写 `execution-state.json`，并同步 `handoff.json.status`。
3. 任一阶段开始时把对应 stage 标记为 `active`；完成时标记为 `completed`。
4. 失败暂停时必须带 `--failure-class` 与 `--reason`，脚本据此写入 `failure_cycle`。
5. 状态只能由脚本维护，不手写 JSON。

### 读取规则

1. `feature-design` 恢复时优先读取 `design-state.json`。
2. `feature-exec` 启动时必须先读取并校验 `handoff.json`。
3. 如果缺少 `handoff.json`，或 `status` 不是 `design_ready` / `execution_in_progress`，
   执行编排器必须停止并提示回到设计侧。
4. 不读取 `.cursor/`、`.claude/` 下的任何私有状态目录作为编排真相。

### 归档

`openspec archive <change-name> --yes` 会把 change 目录移到
`openspec/changes/archive/<YYYY-MM-DD>-<change-name>/`。`scripts/orchestrator-state.py`
能识别归档目录：归档后继续跑 `set-stage` 会写入归档目录，
不会重建一个空的活跃目录（那会让历史状态看起来「阶段全 pending」）。

### 约束

1. `handoff.json` 是设计与执行之间唯一正式交接契约。
2. 执行侧可以补充实现细节，但不能绕过 `design.md`、`tasks.md` 重做需求定义。
3. 编排定义变更后运行 `python scripts/orchestrator-state.py validate-structure` 自检；
   它会校验阶段集合、状态文件的阶段键、以及 handoff 的产物契约。
