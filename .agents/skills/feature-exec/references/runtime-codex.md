# Runtime: Codex

## 官方启动方式

Codex 官方文档明确说明：

- Codex 只有在你「显式要求」时才会 spawn subagent
- 内置 agent 有 `default`、`worker`、`explorer`
- 自定义 agent 定义文件位置是 `.codex/agents/*.toml` 或 `~/.codex/agents/*.toml`
- 可用 `/agent` 查看和切换活动 agent 线程

官方示例句式：

```text
Review this branch against main. Have pr_explorer map the affected code paths, reviewer find real risks, and docs_researcher verify the framework APIs that the patch relies on.
```

## 重要区分

- `.agents/skills/` 是 Skill 源目录，Codex 直接读取
- `.codex/agents/` 才是 Codex 的自定义 subagent 目录

不能把 `.claude/agents/*.md` 直接当 Codex subagent 用。`.codex/agents/` 与 `.claude/agents/` 由各自 IDE 原生维护，不在 `scripts/sync-ide-skills.*` 的同步范围内；两边清单需要对等，新增角色时两个目录都要补。

## 本仓库当前状态

Codex 自定义 agents 位于 `.codex/agents/*.toml`，与 `.claude/agents/*.md` 按角色一一对应，包括：

- `backend-implementer.toml`
- `frontend-implementer.toml`
- `backend-reviewer.toml`
- `backend-arch-reviewer.toml`
- `frontend-reviewer.toml`
- `test-writer.toml`
- `qa-tester.toml`

## 执行阶段建议

- 小变更可以直接在主线程完成 `implement -> test-run`
- 需要拆分时，可显式要求 `backend-implementer`、`frontend-implementer`、`test-writer`、
  `backend-reviewer`、`backend-arch-reviewer`、`frontend-reviewer`、`qa-tester`
- 所有结果必须写回 OpenSpec 与 `.orchestrator`

## Prompt 约束

- 说明当前阶段
- 说明输入工件
- 说明输出文件
- 只在实现和测试写作阶段允许改代码
