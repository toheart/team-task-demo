# Project Rules

## Architecture

- Backend follows DDD layering: `domain` → `application` → `interfaces` → `infrastructure`
- Domain layer MUST NOT depend on infrastructure or interfaces
- 跨域编排放在 `application` 层，不在 domain 内调用其他域的仓储
- 所有新增 API endpoint 必须有对应的 handler 测试
- Frontend API 调用统一经 `src/services/`，组件内不得直接调用 fetch / axios
- 依赖装配统一在 `internal/wire/container.go` 的 `BuildHTTPServer`，不在 handler 内 `new` 依赖

## Code Style

- Go: follow `openspec/specs/backend-go-style/spec.md`
- TypeScript/React: follow `openspec/specs/frontend-typescript-style/spec.md`
- API design: follow `openspec/specs/api-conventions/spec.md`
- Testing: follow `openspec/specs/testing-standards/spec.md` and `docs/testing.md`

## Workflow

- 新功能先走 OpenSpec proposal，再开始编码
- Commit messages follow Conventional Commits format
- 后端改动提交前 `make check` 必须通过（`fmt + lint + test + build`）
- 前端改动提交前 `npm run lint`、`npm test` 与 `npm run build` 必须通过

## Feature Skills

功能开发统一入口，详细阶段边界以 Skill 正文为准：

| Skill | 阶段 |
|-------|------|
| `.agents/skills/feature-design/` | `explore（按需）→ propose → design-review → gate-design → write-handoff` |
| `.agents/skills/design-review/` | C1-C6 方案完整性、M1-M6 分层与数据模型、Bad Path 四维、任务执行契约、错误响应契约 |
| `.agents/skills/feature-exec/` | `test-design → implement → code-review → test-run → gate-delivery → archive` |
| `.agents/skills/test-design/` | 决定最低有效测试层，产出 `test-guides/` 与 `.orchestrator/test-evidence.md` |
| `.agents/skills/system-e2e/` | 按需设计、执行真实浏览器与前后端系统旅程，并判定业务结果 |

- 设计与执行通过 `openspec/changes/<change-name>/.orchestrator/` 共享状态，契约见 `openspec/docs/orchestrator-state-convention.md`。
- 测试分层与执行通道约定见 `openspec/docs/test-guides-convention.md`。
- 系统 E2E 的运行入口与环境配置见 `frontend/e2e/README.md`；未运行的按需 Case 保持 `NOT_RUN`。
- 交付测试契约（分层、Required 判定、失败分类、Gate 计算）见 `.agents/skills/feature-exec/references/delivery-contract.md`。
- `design-review` 与 `test-design` 由主流程亲自执行，不委托 SubAgent。

## OpenSpec

- 所有 feature（含纯前端变更）在仓库根运行 OpenSpec CLI 与状态脚本，工件写入 `openspec/changes/<change-name>/`。
- 新建 change 使用 `openspec/config.yaml` 默认的 `spec-driven-custom`；写作约束定义在 `openspec/schemas/spec-driven-custom/schema.yaml`，不在 `config.yaml` 的 `rules` 里重复声明。
- `design.md` 必填「影响端与验收契约」「实现反模式（SubAgent 必读）」「Review Checklist（本次变更专用）」。
- `tasks.md` 每项任务必须带 `[L1]/[L2]/[L3]` 复杂度与 `[共享]/[后端]/[前端]/[联调]` 端别标注。

## 状态与产物不变量

- `.orchestrator/` 下的状态文件（`design-state.json`、`execution-state.json`、`handoff.json`）只能由 `scripts/orchestrator-state.py` 写入，不手写 JSON。
- 设计阶段不生成测试产物；`test-guides/` 与 `test-evidence.md` 由执行阶段的 `test-design` 生成。
- `handoff.json` 的 `required_artifacts` 只含 `proposal.md`、`design.md`、`tasks.md`。
- 编排定义变更后运行 `python scripts/orchestrator-state.py validate-structure` 自检。

## Skill 与 Agent 资产

- `.agents/skills/` 是 Skill 的唯一源目录。
- `.cursor/skills/`、`.claude/skills/` 是由源目录生成的 IDE 投影，不要手工编辑；改动源目录后运行：

```bash
scripts/sync-ide-skills.sh --target all --mode auto
```

```powershell
powershell -ExecutionPolicy Bypass -File scripts/sync-ide-skills.ps1 -Target all -Mode auto
```

- 同步脚本只支持 `cursor` 与 `claude` 两个 target；Codex 直接读取 `.agents/skills/`，没有投影目录。
- `.claude/agents/` 与 `.codex/agents/` 是各自 IDE 的原生 subagent 目录，不在同步范围内。两边角色需要保持对等，新增角色时两个目录都要补。
- **本项目不生成 Cursor 原生 agent 定义目录（`.cursor/agents/`）**。Cursor 侧通过读取 `.claude/agents/<name>.md` 获得角色定义，约定见 `feature-design/references/runtime-cursor.md`。
