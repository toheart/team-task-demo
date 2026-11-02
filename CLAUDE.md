# Claude Code Instructions

Follow the project rules in `AGENTS.md`.

## Feature Workflow

功能开发统一使用 `$feature-design <change-name>` → `$feature-exec <change-name>`。
阶段边界、Gate 规则与共享状态契约以 `.agents/skills/feature-design/SKILL.md`、
`.agents/skills/feature-exec/SKILL.md` 和 `openspec/docs/orchestrator-state-convention.md` 为准。

## Claude Code Integration

- Project subagents for Claude Code live in `.claude/agents/`.
- Project skills are maintained in `.agents/skills/` as the source of truth.
- Do not manually edit generated skill projections under `.claude/skills/`.
- When project skills change, regenerate IDE projections with:

```bash
scripts/sync-ide-skills.sh --target all --mode auto
```

```powershell
powershell -ExecutionPolicy Bypass -File scripts/sync-ide-skills.ps1 -Target all -Mode auto
```
