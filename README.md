# Team Task Demo

Go + React 全栈项目，DDD 分层架构 + OpenSpec 规范驱动 + AI feature 工作流。

## Quick Start

```bash
make dev    # 启动 backend(:8080) + frontend(:3000)
```

## What You Get

- **Go 后端**：Cobra CLI + Gin HTTP + Viper 配置 + `log/slog` 日志，DDD 四层分层
- **React 前端**：TypeScript + Vite，共享 API Service 层
- **OpenSpec**：`spec-driven-custom` schema（capability spec + L1/L2/L3 任务分级），4 套工程规范，context 自动注入
- **AI 工作流**：`$feature-design` / `$feature-exec` 编排 Skill，跨 IDE 共享 `.orchestrator/` 状态
- **系统 E2E**：`$system-e2e` 按需运行真实前后端旅程，Playwright 输出可追溯的业务结果
- **CI/CD**：GitHub Actions 流水线
- **容器化**：Dockerfile + docker-compose

## Structure

```
├── Makefile                          # make dev / check
├── docker-compose.yml
├── AGENTS.md                         # 项目规则与 AI 工作流入口
├── CLAUDE.md                         # Claude Code 入口
├── .agents/skills/                   # Skill 源目录
├── .claude/agents/                   # Claude Code subagent 定义
├── .codex/agents/                    # Codex subagent 定义
├── scripts/
│   ├── orchestrator-state.py         # 设计/执行共享状态机
│   ├── check-test-env.py             # 测试环境检查
│   └── sync-ide-skills.*             # Skill 镜像同步
├── backend/
│   ├── Dockerfile
│   ├── Makefile
│   ├── cmd/                          # Cobra 入口
│   ├── conf/                         # Viper 配置
│   ├── etc/                          # YAML 配置文件
│   └── internal/
│       ├── domain/sample/            # 领域层
│       ├── application/sample/       # 应用层
│       ├── infrastructure/storage/   # 基础设施层
│       ├── interfaces/http/          # 接口层
│       ├── logging/
│       └── wire/                     # 依赖装配（手写工厂）
├── frontend/
│   ├── Dockerfile
│   ├── e2e/                        # Playwright 系统 Case、环境与结果
│   └── src/
│       ├── components/
│       ├── hooks/
│       ├── services/                 # API 调用层
│       └── types/
├── openspec/
│   ├── config.yaml                   # 项目上下文
│   ├── schemas/spec-driven-custom/   # 定制 artifact 模板与写作约束
│   ├── specs/                        # 工程规范
│   ├── docs/                         # 编排状态与 test-guides 约定
│   └── changes/_example/             # 格式示例
└── .github/workflows/ci.yml
```

## Commands

| Command | Description |
|---------|-------------|
| `make dev` | 启动前后端开发服务器 |
| `make check` | 运行 lint + test + build |
| `make clean` | 清理构建产物 |

系统 E2E 的启动方式见 [frontend/e2e/README.md](frontend/e2e/README.md)；它不属于 `make check`。

## Feature Workflow

功能开发统一走两个编排 Skill：

```text
$feature-design <change-name>
  explore（按需）→ propose → design-review → gate-design → write-handoff

$feature-exec <change-name>
  test-design → implement → code-review → test-run → gate-delivery → archive
```

- 设计与执行通过 `openspec/changes/<change-name>/.orchestrator/` 共享状态，契约见 `openspec/docs/orchestrator-state-convention.md`。
- 用户消息中包含 `trust` 时进入信任模式，Gate 可自动通过；硬条件仍必须满足。
- 状态只能由 `scripts/orchestrator-state.py` 写入，不手写 JSON。

## OpenSpec

- 变更工件：`proposal.md`、`specs/<capability>/spec.md`、`design.md`、`tasks.md`
- `design.md` 必填「影响端与验收契约」「实现反模式（SubAgent 必读）」「Review Checklist（本次变更专用）」
- `tasks.md` 每项任务带 `[L1]/[L2]/[L3]` 复杂度与 `[共享]/[后端]/[前端]/[联调]` 端别
- 示例格式见 `openspec/changes/_example/`

## Docker

```bash
docker compose up --build
# backend → localhost:8080
# frontend → localhost:3000
```

## License

MIT
