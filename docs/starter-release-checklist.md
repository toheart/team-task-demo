# Starter Release Checklist

发布脚手架基线前逐项核对。

## Repository Identity

- Backend module path uses the starter baseline module.
- Backend CLI name, config defaults, frontend package name, and page title all use starter metadata.
- The sample feature remains neutral and does not use product-specific business naming.
- `backend/.golangci.yml` 的 `gofumpt.module-path` 与 `goimports.local-prefixes` 是脚手架自身
  module，不含其他项目的残留值。

## OpenSpec Scope

- `openspec/config.yaml`、`openspec/schemas/spec-driven-custom/`、`openspec/specs/` 均包含。
- `openspec/docs/orchestrator-state-convention.md` 与 `openspec/docs/test-guides-convention.md` 均包含。
- `openspec/changes/` 只保留 `_example/`，其余 change 目录不入库。

## AI 工作流资产

- `.agents/skills/` 下的 Skill 与 `AGENTS.md`「Feature Skills」一节列出的阶段一致。
- `.claude/agents/` 与 `.codex/agents/` 的角色清单对等；两边都包含 `backend-arch-reviewer`。
- 不存在对 `.cursor/agents/` 的引用（本项目不生成该目录）。
- 不存在对 `test-plan.md`、`qa-report.md`、`gate-code`、`gate-test-code`、`.orchestrator/brief.md`
  的引用。
- `scripts/sync-ide-skills.ps1` 与 `.sh` 的 target 覆盖实际存在的镜像目录。

## Verification

在生成的项目中（或直接在 `create-app/templates/` 内）执行：

```bash
# 编排定义自检
python scripts/orchestrator-state.py validate-structure

# 后端
cd backend && make check

# 前端
cd frontend && npm run lint && npm run build
```

在脚手架仓库根执行，验证生成流程端到端可用：

```bash
make test    # 在真实终端里生成 .tmpbin/smoke-test 并检查产物存在
make clean   # 清理测试产物
```

`make test` 依赖交互式终端；没有 TTY 时生成会被取消，Makefile 会因产物缺失而报错退出，
不会静默通过。想在没有终端的环境里做静态检查，用上面的 `validate-structure`。

## Handoff

- 根 `README.md` 说明如何创建项目与 feature 工作流入口。
- 生成项目的 `docs/quickstart.md` 说明第一个功能的完整走法。
