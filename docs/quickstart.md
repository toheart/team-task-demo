# 5 分钟上手

## 前置条件

- Go 1.25.0 或能够获取对应版本的 Go 工具链，以 `backend/go.mod` 为准
- Node.js 22.12+（课程采用版本）
- Python 3.10+（编排状态脚本与测试环境检查）
- 你常用的 AI IDE（Cursor / Claude Code / Codex）

## Step 1: 创建项目

```bash
npx @toheart/create-go-react-app my-project
cd my-project
```

CLI 只问两个必填项：

```
◆ 项目名称 (slug)
│ order-center
│
◆ Go module 路径
│ github.com/acme/order-center
```

显示名、前端包名、环境变量前缀、后端 module 自动推导，确认后一步到位。

## Step 2: 启动开发

首次启动前，先在 `frontend/` 执行 `npm ci`，再回到项目根目录。

```bash
make dev
```

打开 `http://localhost:3000` 看到前端页面即成功。后端 API：`http://localhost:8080/api/v1/samples`。

## Step 3: 开始第一个功能

在你的 AI IDE 中说：

```text
$feature-design user-registration
```

设计阶段会依次执行：

1. **explore**（按需）— 调研受影响代码、数据模型与风险，写入 `.orchestrator/explore-report.md`
2. **propose** — 通过 OpenSpec CLI 生成 `proposal.md`、`specs/`、`design.md`、`tasks.md`
3. **design-review** — 主流程做架构级评审，产出 `.orchestrator/design-review.md` 并把错误响应契约追加进 `design.md`
4. **gate-design** — 你确认方案（回复选项编号；消息里带 `trust` 则自动通过）
5. **write-handoff** — 写入 `.orchestrator/handoff.json`，提示下一步

设计完成后继续：

```text
$feature-exec user-registration
```

执行阶段：

1. **test-design** — 决定最低有效测试层，生成 `test-guides/` 与 `.orchestrator/test-evidence.md`
2. **implement** — 按 `tasks.md` 的端别标注调度 implementer
3. **code-review** — 审查并逐条核对 `design.md` 的 Review Checklist
4. **test-run** — 执行所有 `change-gate` Required 测试并回填证据
5. **gate-delivery** — 唯一的交付 Gate，按硬条件判定
6. **archive** — 归档 change

## 目录导航

| 你要做什么 | 去哪里看 |
|-----------|---------|
| 改后端代码 | `backend/internal/` |
| 改前端页面 | `frontend/src/` |
| 看工程规范 | `openspec/specs/` |
| 看编排状态约定 | `openspec/docs/orchestrator-state-convention.md` |
| 看测试分层约定 | `openspec/docs/test-guides-convention.md` |
| 看 Skill 与 Agent 资产 | `.agents/skills/`、`.claude/agents/`、`.codex/agents/` |
| 看 OpenSpec 示例 | `openspec/changes/_example/` |
