# Subagent Dispatch

## 目标

把执行阶段的 subagent 调度规则集中管理，主 Skill 只保留阶段边界与工件契约。

## 什么时候调度

| 阶段 | 调度的 agent | 说明 |
|---|---|---|
| test-design | 主流程决定分层；可调度 `qa-test-planner` 展开各层场景表 | 分层是设计判断，最终层级由主流程确定并写入 `test-evidence.md` |
| implement | `backend-implementer`、`frontend-implementer` | 按 `tasks.md` 端别分流 |
| implement（App/API/Integration 测试） | `test-writer` | 只写测试与必要 fixture，不改业务逻辑 |
| code-review | `backend-reviewer`；后端结构性变更额外调度 `backend-arch-reviewer`；`frontend-reviewer` | 无相关 diff 的一端不调度 |
| test-run | `qa-tester` | 严格按 `test-guides/` 与 `test-evidence.md` 执行并回填 |
| archive | 不调度 | 由主流程执行 |

`test-writer` 与 `qa-tester` 的分工：Writer 产出测试代码，Runner 执行并报告，两者不合并。
`reviewer` 是通用审查备用角色，仅在没有对应端别 reviewer 时使用。

## 调度前强制步骤

调度任一 subagent 前，必须执行以下步骤，不得跳过：

1. **Read subagent 定义文件**，了解它的系统提示、职责边界、必须执行的检查步骤：
   - `.claude/agents/<agent-name>.md`（Claude Code）
   - `.codex/agents/<agent-name>.toml`（Codex）
   - Cursor：见 `runtime-cursor.md`，本项目不生成 Cursor 原生 agent 定义

   读定义的目的：让编排器知道 subagent 能做什么、需要什么输入、输出什么格式，据此写出精确的委托 prompt，避免 subagent 自己再花 token 探索自己的职责范围。

2. 当前阶段名称。
3. subagent 角色名称。
4. 输入工件路径。
5. 预期输出文件或报告格式。
6. 是否允许改代码。

支持命名 subagent 的 runtime，必须把调度绑定到对应 agent 类型；不能只在 prompt 中写「你是 xxx 专家」来模拟角色。

## 输入契约

- `change-name`
- 当前阶段目标
- `handoff.json`
- 对应的 OpenSpec 文档（`proposal.md`、`design.md`、`tasks.md`）
- `.orchestrator/` 下的 `explore-report.md`、`design-review.md`、`test-evidence.md`
- 本次涉及的 `test-guides/*.md`
- 输出路径

## 输出契约

- `backend-implementer` / `frontend-implementer`：代码实现、测试文件、执行命令、Red/Green 或无法获得 Red 的原因
- `backend-reviewer`：审查问题与阻断项，必须逐条核对 `design.md` 的 Review Checklist
- `backend-arch-reviewer`：包结构、依赖方向、DDD 分层与依赖注入复杂度审查报告
- `frontend-reviewer`：生命周期、effect 清理、受控组件语义与交互一致性审查报告
- `test-writer`：测试代码与执行结果
- `qa-tester`：回填后的 `test-evidence.md` 与执行报告

## 安全边界

- `implement`、`test-write` 允许改代码，其余阶段只修改约定产物。
- 测试 Writer 只修改测试及必要 fixture / helper，不修改业务逻辑；发现业务缺陷时返回 `implement`。
- 如果某个 subagent 失败，只重跑该分支，不重置整个执行流程。
- SubAgent 返回业务失败、测试资产失败或环境阻断后，先应用失败处置规则；不得因为仍有空闲 Agent 就自动发起下一轮。
- 所有关键信息都要落盘，不要只停留在会话里。

## Runtime 分流

- Cursor: 读 `runtime-cursor.md`
- Claude Code: 读 `runtime-claude-code.md`
- Codex: 读 `runtime-codex.md`
