---
name: feature-exec
description: >
  消费 feature-design 产出的 handoff 与 OpenSpec 工件，完成测试设计、实现与同层测试、
  代码审查、Required 测试执行、统一交付 Gate 与归档。
  用于用户请求 `$feature-exec change-name`、启动或恢复 feature 交付、从 handoff.json 落地已完成的变更时。
---

# Feature 执行编排器

## 职责与流程

`feature-exec` 是 feature 的唯一交付编排器：

```text
validate-handoff
→ test-design
→ implement（实现与同层测试）
→ code-review
→ test-run
→ gate-delivery
→ archive
```

- 只做执行编排，不重新定义需求，不重做设计阶段。
- 测试是归档前的必经步骤，不是交付后的可选动作。
- 正常全绿路径只保留 `gate-delivery` 一个交付 Gate；`test-design`、`code-review`、`test-run` 是内部检查，不设独立人工 Gate。
- 测试失败时仅允许一次局部自动修复；复杂失败、重复失败或外部阻断进入条件式 `gate-test-failure`，确认前暂停。
- 测试分层、证据格式与 Gate 条件见 `references/delivery-contract.md`。

## 先读

- `AGENTS.md`
- `docs/README.md`
- `docs/testing.md`
- `openspec/docs/orchestrator-state-convention.md`
- `openspec/docs/test-guides-convention.md`

阶段内按需读取：

- `implement`：`references/openspec-apply-change.md`
- `archive`：`references/openspec-archive-change.md`
- 任一 Gate：`references/gate-templates.md`
- 完成输出：`references/completion-template.md`
- 测试交付契约：`references/delivery-contract.md`
- 调度 SubAgent：先读 `references/subagent-dispatch.md`，再按运行环境读取 `references/runtime-cursor.md`、`references/runtime-claude-code.md` 或 `references/runtime-codex.md`

设计侧唯一正式输入是：

```text
openspec/changes/<change-name>/.orchestrator/handoff.json
```

## 状态命令

```bash
python scripts/orchestrator-state.py validate-handoff <change-name> --check-artifacts
python scripts/orchestrator-state.py init-execution <change-name> [--trust]
python scripts/orchestrator-state.py set-stage execution <change-name> <stage> active
python scripts/orchestrator-state.py set-stage execution <change-name> <stage> completed
python scripts/orchestrator-state.py set-stage execution <change-name> <stage> failed --overall-status failed
python scripts/orchestrator-state.py set-stage execution <change-name> <stage> skipped
python scripts/orchestrator-state.py set-stage execution <change-name> <stage> failed \
  --overall-status paused --failure-class <business|test_asset|environment|fixture> --reason "<summary>"
python scripts/orchestrator-state.py set-gate execution <change-name> gate-delivery passed --confirmed --reason "<summary>"
python scripts/orchestrator-state.py set-gate execution <change-name> gate-delivery failed --reason "<summary>"
```

状态只能由脚本维护，不手写 JSON。旧 schema 只在恢复该 change 时按需迁移；历史 change 不批量回写。

## 信任模式

如果用户消息中包含 `trust`：

- 初始化执行状态时带上 `--trust`
- Gate 阶段可以给出摘要后直接通过
- 仍然必须写 `execution-state.json`，并保留测试与归档产物

## Gate 硬约束

非信任模式下，`gate-delivery` 是强制人工确认点：

1. 按 `references/gate-templates.md` 输出 Gate 摘要。
2. 给出明确选项：通过、修改、停止。
3. **立即停止本轮响应**，等待用户下一条消息。
4. 在用户明确选择「通过」之前，禁止调用 `set-gate ... passed`、禁止后续阶段的 `set-stage ... active` 与 `archive`。

只有满足以下任一条件，才允许自动调用 `set-gate ... passed`：

- `execution-state.json` 中 `trust == true`
- 用户当前消息明确包含对该 Gate 的通过确认

非 trust 模式写入 passed 时带 `--confirmed`，仅用于记录已获得的明确用户确认；不得自行模拟确认。

如果只是构建通过或测试通过，但用户没有明确确认，仍然必须停在 Gate 摘要处。**信任模式也必须满足全部硬条件**：存在 `change-gate` Required 的 FAIL / SKIP / NOT_RUN 时，只能失败。

## 启动与恢复

1. 检测 `trust`，确定 `change-name`。
2. 校验 `handoff.json.status` 为 `design_ready` 或 `execution_in_progress`，且 required artifacts 存在。
3. 读取 `proposal.md`、`design.md`、`tasks.md`、`handoff.json` 和实际 diff。
4. 初始化或迁移 execution state，从首个未完成阶段继续。
5. `handoff.json.status` 为 `draft`、`needs_design_revision` 或产物缺失时停止，返回设计侧。

## 执行阶段

### 1. test-design

读取 `.agents/skills/test-design/SKILL.md` 并由主流程决定分层，按 3KU 生成实际需要的：

```text
openspec/changes/<change-name>/test-guides/unit.md
openspec/changes/<change-name>/test-guides/component.md
openspec/changes/<change-name>/test-guides/app.md
openspec/changes/<change-name>/test-guides/api-smoke.md
openspec/changes/<change-name>/test-guides/integration.md
openspec/changes/<change-name>/test-guides/browser-ui.md
openspec/changes/<change-name>/test-guides/e2e.md
```

要求：

- 不按文件数量或「变更很小」决定跳过；小变更也可能需要一个最低层回归测试。
- 每个 P0/P1 场景必须映射到至少一个 `change-gate` Required 测试或显式 waiver。
- 每个场景必须写出该层「独有证明」；写不出来的层不保留。
- 涉及前端组件交互、effect 依赖与清理、异步数据回填、受控组件、Portal/Modal 时，
  `component` 必须是 Required（若项目尚未接入前端测试运行器，见下条）。
- 真实 CSS、拖拽、焦点、viewport、遮罩、滚动或虚拟列表无法由 jsdom 证明时规划 `browser-ui`；
  需要真实后端、权限、跨页面状态或外部副作用时规划系统 E2E。
- 把层级、Required/Optional、执行通道、独有证明、实际依赖、场景和计划命令写入
  `.orchestrator/test-evidence.md`。
- **测试运行器前置检查**：生成 guide 前先确认对应层有可执行的测试运行器（后端 `go test`、
  前端读 `frontend/package.json` 的 `scripts.test`）。缺失时该层不得登记为 `change-gate` Required，
  只能登记为 waiver 并写明替代验证（人工验收 / `browser-ui` 脚本）与遗留风险，不得声称已覆盖。
- `browser-ui` 与系统 E2E 记录为按需通道，不接入 `gate-delivery` 自动计算；未触发时保留
  `NOT_RUN` 与风险，不写成 PASS。
- 无法从设计提取业务断言时返回设计侧补充，不得从实现代码臆造 P0 规则。

`test-design` 是内部步骤，不增加人工 Gate。

### 2. implement（实现与同层测试）

实现前必须先读：

- `.orchestrator/handoff.json`
- `.orchestrator/explore-report.md`（如存在）
- `proposal.md`、`design.md`、`tasks.md`
- `design.md` 的「实现反模式（SubAgent 必读）」段
- 本次涉及的 `test-guides/*.md`
- `references/openspec-apply-change.md`

按 `tasks.md` 的端别标注与 `affected_ends` 路由：

- 后端实现与同包 unit：`backend-implementer`
- 前端实现与 unit/component：`frontend-implementer`
- App / API smoke / integration 测试：`test-writer`
- `tasks.md` 两端任务都为空时，停止并说明 `tasks.md` 不可执行，不要自行发明任务

实施约束：

- 每个实现任务关联 AS 场景和 Required 测试。
- `Backend Tasks` 只由后端消费，`Frontend Tasks` 只由前端消费。
- 后端 domain/application 与前端自定义 hook 按「测试失败 → 最小实现 → 测试通过」推进。
- 前端组件先稳定用户可观察的行为契约，再补齐 component 测试；缺陷修复先写复现测试。
- App / API / Integration 可在主体接口稳定后补齐，属于 implement 完成条件；按需的
  Browser UI / E2E 只需先有测试资产与运行计划，执行由对应通道触发。
- Implementer 必须回报业务文件、测试文件、命令、Red/Green 或无法获得 Red 的原因。
- 禁止弱化断言、删除用例、扩大非目标范围，或把环境失败算作通过。
- 如果任务拆分与实际需要改动的端不一致，先停止并说明不一致点，不默默扩大实现范围。

只有业务实现与全部 Required 测试资产就绪后，才能完成 `implement`。

### 3. code-review

按任务范围、实际 diff 与调度规则决定审查：

- 后端有任务或 diff 涉及 `backend/`：调度 `backend-reviewer`
- 后端 diff 涉及新增/修改包结构、跨层依赖、接口定义、依赖注入或 DTO/domain/entity 映射时，
  额外调度 `backend-arch-reviewer`
- 前端有任务或 diff 涉及 `frontend/`：调度 `frontend-reviewer`
- 没有相关 diff 的一端不调度 reviewer

Reviewer 除常规审查外，必须验证：

```text
验收场景 → 实现 diff → 测试文件
```

- 前端重点检查生命周期、effect 依赖与清理、API 加载与回填、创建/编辑/复制/查看一致性、
  表单与弹窗状态、受控组件语义。
- 后端重点检查状态机、权限、幂等、部分成功、重试恢复、回滚实际状态与外部契约。
- 逐条核对 `design.md` 的「Review Checklist（本次变更专用）」。
- 主流程依据审查证据把已通过项标为 `[x]`；未通过项保持 `[ ]`，不得仅为通过脚本而勾选。
- Required 场景无有效测试、仅有 snapshot，或 Mock 改变了真实行为时，返回 `implement`，不进入 `test-run`。
- 后端变更必须执行 ```cd backend && make lint```；**本次变更新增的 lint 问题一律为阻断项**，
  必须返回 `implement` 修复后重新审查。不得因问题属于复杂度、风格或可维护性类别而降级为提示。
- 不得以新增或扩大 `//nolint` 跳过本次变更引入的 lint 问题。工具规则确有错误时，修正对应 lint
  配置并在审查报告中说明，不能在业务代码里逐处压制。

`code-review` 是内部检查，无阻断问题后直接继续。

### 4. test-run

按 `.orchestrator/test-evidence.md` 执行所有 `change-gate` Required 测试，并回填实际命令、环境与结果：

- Backend Unit：收敛到受影响包的 `go test`
- Frontend Unit / Component：`cd frontend && npm test -- <files>`
- App / API Smoke / Integration：调度 `test-writer` 补齐后由 `qa-tester` 执行
- Browser UI / System E2E：仅在按需通道被用户或外部流水线触发时执行

结果必须按层报告：

```text
required / executed / PASS / FAIL / SKIP / NOT_RUN
```

- 测试代码问题返回 `implement` 的测试写作任务。
- 业务问题返回 `implement`。
- 环境问题保持 `NOT_RUN`，等待环境就绪；不能算通过。
- `change-gate` Required 零执行、FAIL、SKIP 或 NOT_RUN 时，`test-run` 失败。
- 未触发的按需 Browser UI / System E2E 保持 `NOT_RUN` 并进入风险摘要；不能当作 PASS，
  也不自动阻断普通代码交付。
- Optional SKIP 可以继续，但必须进入风险摘要。

执行前先做与测试层匹配的环境 Gate，使用：

```bash
python scripts/check-test-env.py integration   # 或 backend / frontend / qa
```

### 5. 失败处置

按 `references/delivery-contract.md` 分类失败并计算当前 `failure_cycle`。

只允许一次自动修复，且必须同时满足：只有一个明确根因、修复不扩大设计范围、不修改共享测试
基础设施、预计修复与重跑不超过 10 分钟。修复后必须重新审查并只重跑受影响层及必要回归。

以下任一情况必须进入 `gate-test-failure`：

1. 同一 `test-run` 第二次失败
2. 一次发现两个及以上业务问题
3. Review 将已完成阶段退回
4. 需要新增契约、改变副作用顺序或扩大模块范围
5. 需要修改共享测试 helper / 基础设施
6. `change-gate` Required 因外部凭据、fixture、授权或真实资源 `NOT_RUN`
7. E2E 恢复环境后仍未进入业务断言
8. 下一轮预计超过 10 分钟

进入时执行：

```bash
python scripts/orchestrator-state.py set-stage execution <change-name> <failed-stage> failed \
  --overall-status paused --failure-class <class> --reason "<summary>"
```

脚本会持久化 `failure_cycle`、`last_failure` 与 `requires_confirmation=true`。随后按
`references/gate-templates.md` 汇总并等待用户选择「继续修复 / 暂缓外部测试 / 停止」。
确认前不得继续实现、复审或重跑。

用户明确选择继续后，激活目标阶段时必须带 `--resume-confirmed --reason "<确认与修复范围>"`。

### 6. gate-delivery

按 `references/gate-templates.md` 汇总一次。通过条件：

1. 实现任务全部完成，Reviewer 无阻断项
2. P0/P1 场景全部完成映射
3. `change-gate` Required 测试执行数大于零
4. `change-gate` Required 没有 FAIL、SKIP、NOT_RUN
5. waiver 有明确原因、替代验证、批准记录与风险接受

非信任模式等待用户「通过 / 修改 / 停止」；信任模式只有满足全部硬条件时才能自动通过。
失败后返回对应阶段，不得 archive。硬条件不满足时不提供「跳过并归档」选项。

### 7. archive

归档前确认：

- 设计与执行阶段都已完成
- `gate-delivery` 已 passed
- 需要保留的测试资产已经落盘
- 已读取 `references/openspec-archive-change.md`

归档时优先使用 OpenSpec CLI：

```bash
openspec archive <change-name> --yes
```

## 恢复规则

1. 启动时先读取 `.orchestrator/execution-state.json` 是否存在。
2. 首次启动执行阶段时，校验 `handoff.json.status = "design_ready"`，并运行 `validate-handoff <change-name> --check-artifacts`。
3. 已存在 `execution-state.json` 时，允许 `handoff.json.status = "execution_in_progress"` 并从未完成阶段继续。
4. 如果 `handoff.json.status = "completed"`，提示执行阶段已经完成，不要重复推进。
5. 如果 `handoff.json.status` 是 `draft`、`needs_design_revision` 或缺少 required artifacts，停止并回到设计侧。

## 完成输出

按 `references/completion-template.md` 输出收尾摘要，至少包含：

- `openspec/changes/<change-name>/.orchestrator/execution-state.json`
- `openspec/changes/<change-name>/.orchestrator/test-evidence.md`
- 新增或更新的测试文件

正常交付完成后不得再提示用户补跑 Required 测试。
