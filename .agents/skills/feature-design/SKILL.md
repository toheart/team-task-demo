---
name: feature-design
description: >
  在 Go/React OpenSpec 项目中把需求推进到可执行、可验收的设计：调研代码、生成
  OpenSpec proposal/design/tasks、做架构级 design-review，产出 handoff 交接给执行阶段。
  用于用户请求 `$feature-design change-name`、启动或恢复 feature 设计阶段、
  需要把模糊需求收敛为可执行设计时。
---

# Feature 设计编排器

## 职责

只负责：

```text
explore（按需）→ propose → design-review → gate-design → write-handoff
```

- 不写业务代码和测试代码。
- 设计阶段只确定验收场景、影响端和建议最低测试层，不生成 `test-guides/`，不增加测试 Gate。
- 测试设计与测试执行由 `$feature-exec <change-name>` 在归档前完成，不是交付后的可选动作。

## 先读

- `AGENTS.md`
- `docs/README.md`
- `docs/quickstart.md`
- `docs/testing.md`
- `openspec/docs/orchestrator-state-convention.md`

阶段内按需读取：

- `explore`：`references/openspec-explore.md`
- `propose`：`references/openspec-propose.md`
- `design-review`：`.agents/skills/design-review/SKILL.md`
- `gate-design`：`references/gate-templates.md`
- 调度 SubAgent：先读 `references/subagent-dispatch.md`，再按运行环境读取 `references/runtime-cursor.md`、`references/runtime-claude-code.md` 或 `references/runtime-codex.md`

## 项目入口与 Schema

- 所有 feature 均在仓库根运行 OpenSpec CLI 与状态脚本，工件写入 `openspec/changes/<change-name>/`。
- 新建 change 使用根 `openspec/config.yaml` 默认的 `spec-driven-custom`；用 `openspec status --change <change-name> --json` 核对 `schemaName`。已有 change 保留自身 Schema，不批量迁移。
- 写作约束（proposal 段落、tasks 的 L1/L2/L3 分级、design 必须包含的两节）由 `openspec/schemas/spec-driven-custom/schema.yaml` 定义，不在这里重复。
- 设计完成后只交接给 `$feature-exec <change-name>`；不要提示用户运行通用 OpenSpec apply 命令。

## 状态命令

```bash
python scripts/orchestrator-state.py init-design <change-name> [--trust]
python scripts/orchestrator-state.py set-stage design <change-name> <stage> active
python scripts/orchestrator-state.py set-stage design <change-name> <stage> completed
python scripts/orchestrator-state.py set-stage design <change-name> <stage> failed --overall-status failed
python scripts/orchestrator-state.py set-stage design <change-name> <stage> skipped
python scripts/orchestrator-state.py set-gate design <change-name> gate-design passed --confirmed --reason "<summary>"
python scripts/orchestrator-state.py set-gate design <change-name> gate-design failed --reason "<summary>"
```

状态只允许由脚本维护，不手写 JSON。恢复旧 change 时脚本按需迁移 state schema，不批量回写历史。

## 信任模式

如果用户消息中包含 `trust`：

- 初始化状态时带上 `--trust`
- Gate 阶段可给出摘要后直接通过
- 仍然必须写状态与交接文件，不能省略产物

## 阶段说明

### 1. 启动或恢复

1. 检测用户消息中的 `trust`，确定 `change-name`。
2. 初始化设计状态；已有状态时从首个未完成阶段继续。
3. 读取 `.orchestrator/design-state.json` 判断进度；`handoff.json.status = design_ready` 时说明设计已完成，不重复推进。

### 2. explore（按需）

新功能、跨端变更或需求边界不清时执行；小且明确的变更可以跳过，跳过后不得凭想象补事实。

1. 调度 `explorer` 获取代码事实、依赖、数据模型和风险。
2. 主流程形成验收场景：Happy Path 2～3 个；Bad Path 至少覆盖输入异常、状态冲突、依赖失败、权限边界四类。
3. 把结论写入 `openspec/changes/<change-name>/.orchestrator/explore-report.md`。
4. 明确影响范围、关键文件、约束、风险和测试入口。

### 3. propose

读取 `references/openspec-propose.md`，通过 OpenSpec CLI 生成 `proposal.md`、`specs/**/*.md`、`design.md`、`tasks.md`。

#### 影响端与验收契约

`design.md` 必须填好模板中的 `affected_ends` 与验收矩阵：

```yaml
affected_ends:
  backend: true|false
  frontend: true|false
  external_systems: []
```

| 场景 ID | 优先级 | 验收行为（用户可观察） | 影响端 | 建议最低测试层 |
|---|---|---|---|---|
| AS-1 | P1 | | | unit / component / app / api-smoke / integration / browser-ui / e2e |

- 这里只选择建议层级，不写具体测试文件。
- P0/P1 场景不得没有验收行为；暂时无法自动化时必须标出人工/灰度验证方式和原因。
- 涉及前端组件交互、`useEffect` 依赖与清理、异步数据回填、受控组件、Modal/Portal、
  保存→查询→回填→再编辑的数据往返时，建议最低层必须包含 `component`。
- 只有跨页面、真实浏览器或真实系统链路才建议 `browser-ui` / `e2e`。

#### tasks 执行路由

- 跨端任务按共享契约 → 后端 → 前端 → 联调排序；纯单端只保留实际分组。
- 每项任务标注 `[共享]`、`[后端]`、`[前端]` 或 `[联调]`，并给出文件、符号、包、组件、路由或 API 定位。
- 一个任务只有一个 owner，控制在单次会话可完成范围。
- 每个实现任务关联 AS 场景和局部验证命令；禁止「按设计实现」「补测试」这类不可判定描述。
- 禁止 `TBD`、`待确认`、`自行决定`。证据不足时停止并询问。

### 4. design-review

读取并执行 `.agents/skills/design-review/SKILL.md`。由主流程亲自完成，不委托 SubAgent。

固定产出：

```text
openspec/changes/<change-name>/.orchestrator/design-review.md
openspec/changes/<change-name>/design.md 中的「错误响应契约（design-review 产出，implement 必读）」段落
```

有 BLOCKER 时返回 `propose`，不进入 Gate。

### 5. gate-design

按 `references/gate-templates.md` 输出摘要，只保留一个设计 Gate，统一确认方案、任务与可验收性。

- 非信任模式：输出通过、修改、停止三个选项后**停止本轮响应**，等待用户确认。
- 信任模式：无 BLOCKER 时输出 `[信任通过]` 与理由，调用 `set-gate design <change-name> gate-design passed` 后继续。
- 用户明确通过后调用 `set-gate design <change-name> gate-design passed --confirmed --reason "<summary>"`。
- `--confirmed` 只表示已获得本 Gate 的明确用户确认，不用于模拟确认。trust 模式无需此标记，硬条件仍校验。

### 6. write-handoff

```bash
python scripts/orchestrator-state.py write-handoff <change-name> \
  --required proposal.md \
  --required design.md \
  --required tasks.md \
  --optional .orchestrator/explore-report.md \
  --executor-note "feature-exec 必须在归档前完成测试设计、Required 测试执行和 gate-delivery" \
  --gate-decision "<decision>"

python scripts/orchestrator-state.py validate-handoff <change-name> --check-artifacts
```

- `handoff.json` 必须包含 `status=design_ready`、`design_gate_passed=true`、required artifacts、pending risks 和 gate decisions。
- `required_artifacts` 只放 `proposal.md`、`design.md`、`tasks.md`。测试设计产物（`test-plan.md`、`test-guides/`）属于执行侧，不得写入 required。

## 恢复规则

1. 恢复时优先读取 `.orchestrator/design-state.json`。
2. 如果 `handoff.json.status = "design_ready"`，说明设计阶段已完成，不要重复推进。
3. 只从未完成阶段继续。

## 完成标准

设计阶段完成时至少具备：

- `openspec/changes/<change-name>/proposal.md`
- `openspec/changes/<change-name>/specs/`（如 proposal 声明了 capability）
- `openspec/changes/<change-name>/design.md`（含 `affected_ends`、验收矩阵、实现反模式、Review Checklist、错误响应契约）
- `openspec/changes/<change-name>/tasks.md`
- `openspec/changes/<change-name>/.orchestrator/explore-report.md`（执行过 explore 时）
- `openspec/changes/<change-name>/.orchestrator/design-review.md`
- `openspec/changes/<change-name>/.orchestrator/design-state.json`
- `openspec/changes/<change-name>/.orchestrator/handoff.json`

## 结束回复

当 `handoff.json.status = "design_ready"` 后，最终回复不能只说「完成」。必须包含：

```text
设计阶段已完成，后续可以执行：

$feature-exec <change-name>

如需执行阶段自动通过人工确认 gate，请明确使用：

$feature-exec <change-name> trust
```

如果当前不是信任模式，不能替用户启动 `$feature-exec`；只提示下一步，等待用户确认。
