# Gate 模板

正常 feature 只有两个人工 Gate：设计侧 `gate-design` 和交付侧 `gate-delivery`（见 `feature-exec/references/gate-templates.md`）。

## 通用流程

1. 先汇总上一阶段的关键结果。
2. 非信任模式下，给出明确选项：通过、修改、停止，然后**停止本轮响应**，等待用户下一条消息。
3. 在用户明确选择「通过」之前，禁止调用 `set-gate ... passed`、禁止进入下一阶段、禁止归档。
4. 信任模式下，输出 `[信任通过]` 与理由后继续；仍然必须写状态文件，不能省略产物。

## gate-design

摘要至少覆盖：

- 需求目标与非目标
- 关键设计决策
- `affected_ends` 与任务端别拆分
- P0/P1 验收场景、建议最低测试层
- design-review 结论：C1-C6、M1-M5、Bad Path 四维、任务执行契约、覆盖矩阵
- 错误响应契约是否已写入 `design.md`
- 非目标能力是否被误暴露
- 剩余风险

通过条件：无 BLOCKER；P0/P1 场景可观察可验证；tasks 可路由到端别与验证命令；非目标未误暴露。

非信任模式参考输出：

```text
## Gate: 设计确认

<方案摘要>
<design-review 结论与阻断项>
<P0/P1 场景 → 建议测试层 映射>
<剩余风险>

选项：
1. 通过，进入执行阶段
2. 需要修改方案
3. 停止本次变更

请回复选项编号或明确指令。
```

输出该模板后必须停止，不得调用 `set-gate design <change-name> gate-design passed`。

信任模式参考输出：

```text
## [信任通过] Gate: 设计确认

<方案摘要>

通过理由：无 BLOCKER，验收场景与任务路由齐备，错误响应契约已写入 design.md。
```
