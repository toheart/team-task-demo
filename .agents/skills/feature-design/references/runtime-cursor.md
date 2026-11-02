# Runtime: Cursor

## 官方能力边界

根据 Cursor 官方 Subagents 文档与 2.4 更新说明，Cursor 已支持 subagents，并且这些 subagents：

- 在编辑器和 CLI 中可用
- 会并行运行
- 使用自己的上下文
- 可配置自定义 prompt、tool access、model

官方文档当前可确认的是「支持 custom subagents」，但没有稳定、可直接写死在仓库里的专用调用语法。因此这里不要编造 `Task(...)` 之类的伪 API。

## 本项目的 agent 定义位置

**本项目不生成 Cursor 原生 agent 定义目录（`.cursor/agents/`）。** agent 定义以 `.claude/agents/*.md` 为唯一源，Cursor 侧通过读取这些文件获得角色指令。

`.cursor/skills/` 由 `scripts/sync-ide-skills.ps1`（或 `.sh`）从 `.agents/skills/` 生成，只包含 Skill，不含 agent 定义。不要手工编辑镜像目录。

## 本仓库约定的委托方式

在 Cursor 主对话里显式要求当前 agent 承担某个角色，并**要求它先读取角色定义文件**：

```text
Read .claude/agents/explorer.md and follow all instructions in it.
Then complete the explore stage for change <change-name>: report affected files,
data model impact, risks and test entry points, and write the result to
openspec/changes/<change-name>/.orchestrator/explore-report.md.
```

如果 Cursor UI 当前版本支持从 subagent 列表或 @-mention 里直接选择，就优先用 UI。

## 设计阶段常用角色

| 阶段 | 角色 | 定义文件 |
|------|------|----------|
| explore | `explorer` | `.claude/agents/explorer.md` |

说明：`design-review` 固定由主流程读取并执行 `.agents/skills/design-review/SKILL.md`，不要调度 Cursor subagent。

## Prompt 约束

- 明确当前阶段名称
- 明确输入文件路径
- 明确输出应写回哪个 OpenSpec 或 `.orchestrator` 文件
- 明确是否允许修改代码；设计阶段默认不允许
