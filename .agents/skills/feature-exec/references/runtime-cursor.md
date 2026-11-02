# Runtime: Cursor

## 官方能力边界

Cursor 支持 subagents：在编辑器和 CLI 中可用、并行运行、使用独立上下文、可配置 prompt / tool access / model。

官方没有公开稳定的、可写进 Skill 的专用调用语法，因此本项目不写死伪 API。

## 本项目的 agent 定义位置

**本项目不生成 Cursor 原生 agent 定义目录（`.cursor/agents/`）。** agent 定义以 `.claude/agents/*.md` 为唯一源。

`.cursor/skills/` 由 `scripts/sync-ide-skills.ps1`（或 `.sh`）从 `.agents/skills/` 生成，只包含 Skill，不含 agent 定义。不要手工编辑镜像目录。

## 本仓库约定的委托方式

`feature-exec` 是编排型 Skill，需要在不同阶段承担不同角色。在 Cursor 主对话里显式点名角色，并要求先读取角色定义：

```text
Read .claude/agents/backend-implementer.md and follow all instructions in it.
Then complete the Backend Tasks in openspec/changes/<change-name>/tasks.md.

Read .claude/agents/frontend-reviewer.md and follow all instructions in it.
Then review the frontend diff for change <change-name>.
```

如果 Cursor UI 当前版本支持从 subagent 列表或 @-mention 里直接选择，就优先用 UI。

## 执行阶段常用角色

| 阶段 | 角色 | 定义文件 |
|------|------|----------|
| test-design | `qa-test-planner`（可选，展开场景表） | `.claude/agents/qa-test-planner.md` |
| implement | `backend-implementer` | `.claude/agents/backend-implementer.md` |
| implement | `frontend-implementer` | `.claude/agents/frontend-implementer.md` |
| implement（App/API/Integration 测试） | `test-writer` | `.claude/agents/test-writer.md` |
| code-review | `backend-reviewer` | `.claude/agents/backend-reviewer.md` |
| code-review | `backend-arch-reviewer` | `.claude/agents/backend-arch-reviewer.md` |
| code-review | `frontend-reviewer` | `.claude/agents/frontend-reviewer.md` |
| test-run | `qa-tester` | `.claude/agents/qa-tester.md` |

## Prompt 约束

- 明确当前阶段名称
- 明确输入工件路径
- 明确输出文件或报告位置
- 实现和测试写作阶段可以改代码；审查、测试执行与 Gate 阶段默认不改业务代码
