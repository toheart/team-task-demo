# Runtime: Claude Code

## 官方启动方式

Claude Code 官方文档给了三种明确路径：

1. 用 `/agents` 管理和创建 subagent
2. 在主对话里用自然语言显式调用
3. 用 `@` 直接点名某个 subagent

官方示例：

```text
Use the test-runner subagent to fix failing tests
Have the code-reviewer subagent look at my recent changes
@"code-reviewer (agent)" look at the auth changes
```

## 定义文件位置

官方约定：

- 项目级：`.claude/agents/`
- 用户级：`~/.claude/agents/`

Claude Code 会从当前工作目录一路向上扫描 `.claude/agents/`。如果直接手改磁盘文件，官方文档要求重启 session 才会重新加载；通过 `/agents` 创建则立即生效。

## 本仓库建议

设计阶段用自然语言显式委托：

```text
Use the explorer subagent to survey the code paths affected by <change-name>,
then write openspec/changes/<change-name>/.orchestrator/explore-report.md.
```

如果需要强制指定某个 agent，而不让 Claude 自己选，可以用 `@` 点名。

## 设计阶段常用 agent

| 阶段 | agent 名 | 定义文件 |
|------|----------|----------|
| explore（只读调研） | `explorer` | `.claude/agents/explorer.md` |

说明：`design-review` 固定由主流程读取并执行 `.agents/skills/design-review/SKILL.md`，不要调度 Claude subagent。

## 调度前置步骤（强制）

调用 Agent 工具前，必须先 Read 目标 agent 的定义文件：

```
Read .claude/agents/explorer.md
```

读完后在 prompt 中引用 agent 定义中的具体步骤名称和检查命令，不要只泛泛写「调研一下」。目的是让 subagent 直接执行定义中的步骤，不需要自己再探索。读 agent 定义只需执行一次，同阶段多个 agent 可并行 Read。
