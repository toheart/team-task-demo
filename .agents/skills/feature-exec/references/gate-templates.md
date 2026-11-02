# Gate 模板

正常 feature 只有两个人工 Gate：设计侧 `gate-design`（见 `feature-design/references/gate-templates.md`）
和交付侧 `gate-delivery`。

## gate-delivery

摘要必须覆盖：

- 实现任务完成情况
- Reviewer 阻断项
- P0/P1 场景映射（covered / total）
- 各测试层与执行通道的 required / executed / PASS / FAIL / SKIP / NOT_RUN
- Red/Green 或替代证据
- 人工或灰度验证
- waiver 与遗留风险
- 按需 Browser UI / System E2E 的触发情况与未运行风险

```text
## Gate: Feature 交付

实现任务：<完成 / 未完成>
代码审查：<阻断项>
P0/P1 场景映射：<covered/total>

| 层级 / 执行通道 | Required | Executed | PASS | FAIL | SKIP | NOT_RUN |
|---|---:|---:|---:|---:|---:|---:|
|  |  |  |  |  |  |  |

Red/Green 或替代证据：<摘要>
人工/灰度验证：<摘要>
Waiver 与遗留风险：<摘要>
按需 Browser UI / System E2E：<触发情况、结果或 NOT_RUN 风险>

选项：
1. 通过并归档
2. 返回修改
3. 停止
```

硬条件不满足时只能失败，不提供「跳过并归档」。信任模式也必须满足全部硬条件，通过时输出
`[信任通过]` 和可审计理由。

输出该模板后必须停止本轮响应，不得调用 `set-gate execution <change-name> gate-delivery passed`。

## gate-test-failure（条件 Gate）

该 Gate 只在测试失败控制触发时出现，不属于正常全绿路径。

```text
## Gate: 测试失败处置

失败分类：<business / test_asset / environment / fixture>
失败轮次：<failure_cycle>
已完成证据：<摘要>
失败或 NOT_RUN：<摘要>
建议方案：<建议及原因>
预计成本：<时间 / 环境 / 授权>

选项：
1. 继续修复
2. 暂缓外部测试，保留 NOT_RUN
3. 停止
```

进入该 Gate 前必须已经执行：

```bash
python scripts/orchestrator-state.py set-stage execution <change-name> <failed-stage> failed \
  --overall-status paused --failure-class <class> --reason "<summary>"
```

选择 1 后只激活明确的目标阶段，并把其下游阶段重置为 `pending`；选择 2 或 3 时保持 `paused`，
不得进入 `gate-delivery` 或 `archive`。

用户选择继续后使用：

```bash
python scripts/orchestrator-state.py set-stage execution <change-name> <target-stage> active \
  --resume-confirmed --reason "<用户确认与本轮修复范围>"
```

脚本拒绝在缺少上述确认记录时清除 `requires_confirmation`；`trust` 不绕过失败暂停。
