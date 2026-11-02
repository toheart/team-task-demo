# 完成输出模板

```text
**Change**: <name>

### 产出物
- 设计交接：openspec/changes/<name>/.orchestrator/handoff.json
- 执行状态：openspec/changes/<name>/.orchestrator/execution-state.json
- 测试证据：openspec/changes/<name>/.orchestrator/test-evidence.md
- 测试指导：openspec/changes/<name>/test-guides/
- 测试代码：<新增或更新的测试文件>
- OpenSpec：openspec/changes/archive/<date>-<name>/

### 测试结果
| 层级 / 执行通道 | Required | Executed | PASS | FAIL | SKIP | NOT_RUN | 命令/环境 |
|---|---:|---:|---:|---:|---:|---:|---|

### 证据与风险
- Red/Green 或替代证据：
- 人工/灰度验证：
- 按需 Browser UI / System E2E：<触发情况、结果或 NOT_RUN 风险>
- Waiver：
- 遗留风险：

### 关键决定
- gate-design: <decision>
- gate-delivery: <decision>
- gate-test-failure: <如触发，decision；否则写「未触发」>
```

正常交付完成后不得再提示用户补跑 Required 测试。
