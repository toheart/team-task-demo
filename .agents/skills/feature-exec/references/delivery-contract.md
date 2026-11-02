# Feature 共享交付测试契约

本文件定义 feature 交付的测试分层、Required 判定、证据格式与 Gate 计算。`feature-exec`、
`test-design` 与任何测试 Writer / Runner 都以本文为准。

## 分层

| 层级 | 最低有效验证对象 | 默认命令 / 执行者 |
|---|---|---|
| Frontend Unit | 纯函数、格式化、纯自定义 hook 的返回值 | `cd frontend && npm test -- <files>` |
| Frontend Component | 组件生命周期、用户交互、effect 与清理、受控值回写 | `cd frontend && npm test -- <files>` |
| Backend Unit | domain / application 局部逻辑、converter、校验规则 | `go test <受影响包>` |
| App | Application Service 编排 + Fake 仓储 | `test-writer` 编写，`qa-tester` 执行 |
| API Smoke | HTTP 路由、DTO、错误码、鉴权、统一 envelope | `test-writer` 编写，`qa-tester` 执行 |
| Integration | 真实基础设施、Repository、外部依赖 wiring、跨组件装配 | `test-writer` 编写，`qa-tester` 执行 |
| Browser UI | 真实浏览器的布局、遮罩、焦点、滚动与可操作性；允许 Mock 请求 | 按需通道 |
| System E2E | 真实后端、外部副作用与完整系统旅程 | 按需通道 |

**运行器前置检查**：分层前先确认该层有可执行入口（后端 `go test`；前端读
`frontend/package.json` 的 `scripts.test`）。缺失时该层不得登记为 `change-gate` Required，
只能登记为 waiver 并写明替代验证与遗留风险。

## Required 判定

- P0/P1 场景至少有一个 `change-gate` 的 Required 测试。
- 前端变更命中 component 触发器（见 `test-design`）时，`component` 为 Required。
- 跨层场景必须注明每层独有证明；不能说明新增事实时，只保留最低有效层。
  真实基础设施的集成证据与 Fake 依赖的证据是不同证明，不能互相替代。
- `browser-ui` 与系统 E2E 是按需执行通道：登记为 `on-demand-browser` / `on-demand-system`，
  不参与 `gate-delivery` 的自动计算，也不作为 P0/P1 唯一的 `change-gate` 证明。
- Required 无法自动化时必须记录 waiver、替代验证、批准信息和遗留风险；不得伪装为 PASS。
- Optional 可以 SKIP，但必须进入风险摘要。

## `.orchestrator/test-evidence.md` 模板

```markdown
# 测试证据

## 场景映射

| 场景 ID | 层级 | Required/Optional | 执行通道 | 独有证明 / 运行依赖 | 测试文件/任务 | 计划命令 | 状态 |
|---|---|---|---|---|---|---|---|
| AS-1 | component | Required | change-gate | effect 清理与受控回写；jsdom + API mock | frontend/src/...test.tsx | npm test -- ... | NOT_RUN |

## 分层结果

| 层级 | Required | Executed | PASS | FAIL | SKIP | NOT_RUN | 命令 | 环境 |
|---|---:|---:|---:|---:|---:|---:|---|---|
| Frontend Component | 1 | 0 | 0 | 0 | 0 | 1 | `npm test -- ...` | local |

## Red/Green 或替代证据

| 场景 ID | Red | Green | 说明 |
|---|---|---|---|

## Waiver 与遗留风险

| 场景 ID | 原因 | 替代验证 | 替代验证结果 | 批准/确认 | 遗留风险 |
|---|---|---|---|---|---|
```

由 `test-design` 填计划列，Writer 填实际测试文件，Runner 填 executed / PASS / FAIL / SKIP /
NOT_RUN / 命令 / 环境，Gate 填 waiver 与遗留风险。

## 执行通道与 Gate 计算

- `change-gate`：本次普通交付必须执行；Required 行参与 Gate 计算。
- `on-demand-browser`、`on-demand-system`：按影响面登记，不自动运行。记录触发条件、环境、
  命令和未运行风险；状态为 `NOT_RUN` 时不得写成 PASS。

`gate-delivery` 通过前检查：

1. P0/P1 场景均在映射表中
2. `change-gate` Required 总数大于零
3. 每层 `Executed = PASS + FAIL + SKIP`
4. `change-gate` Required 的 FAIL、SKIP、NOT_RUN 均为零
5. Reviewer 无阻断项，`design.md` 的 Review Checklist 已逐条核对
6. waiver 包含替代验证、批准/确认和遗留风险，且替代验证已实际执行

零用例、全 skip、全部场景仅有 waiver，或只生成测试文件未执行，均不得视为通过。

脚本在 `set-gate ... passed` 与进入 `archive` 时校验前序阶段、任务和 Review Checklist、
验收映射、实际测试文件及分层计数。映射表一行记录一个测试证据项，分层结果按这些行汇总；
测试路径相对仓库根，多个路径用逗号分隔。计划命令由 Runner 回填为实际执行命令。
验收矩阵的优先级使用 P0/P1/P2；旧矩阵缺少该列时按 P1 校验。P2 可以登记 Optional，
P0/P1 必须有通过的 `change-gate` Required 证明或已批准的 waiver，替代验证结果必须为 PASS。
这些校验验证落盘证据的一致性，业务断言是否正确仍由 Reviewer 判断。

## 测试失败控制

### 失败分类

| 分类 | 判定 | 默认处置 |
|---|---|---|
| `business` | 业务断言、状态、副作用或契约不符合设计 | 第一次且局部时允许自动修复一次 |
| `test_asset` | 测试 fixture、selector、helper 或断言本身错误 | 返回对应测试写作任务；修改共享资产前确认 |
| `environment` | 服务、网络、依赖、认证或测试基础设施不可用 | 恢复一次；仍失败则确认 |
| `fixture` | 缺少真实目标、凭据、历史数据、故障注入或执行授权 | 立即确认，不自动选择真实资源 |

### 一次自动修复上限

同一个 `test-run` 只允许一次自动返回 `implement`，且必须同时满足：只有一个明确根因、
修复不扩大设计范围、不修改共享测试基础设施、预计修复与重跑不超过 10 分钟。修复后必须
重新审查并重跑失败层。

以下任一情况必须进入 `gate-test-failure`：

1. 同一 `test-run` 第二次失败
2. 一次发现两个及以上业务问题
3. Review 将已完成阶段退回
4. 需要新增契约、改变副作用顺序或扩大模块范围
5. 需要修改共享测试 helper / 基础设施
6. `change-gate` Required 因外部凭据、fixture、授权或真实资源 `NOT_RUN`
7. E2E 恢复环境后仍未进入业务断言
8. 下一轮预计超过 10 分钟

确认摘要必须包含失败分类、失败轮次、已完成证据、未执行项、建议方案、预计成本与三个选项：
继续修复 / 暂缓外部测试 / 停止。确认前把失败阶段设为 `failed`、整体状态设为 `paused`，
并持久化 `failure_cycle`、`last_failure` 与 `requires_confirmation=true`，不得继续调度。

## 分层环境 Gate

启动集成或 E2E 之前，按层级检查：

| 层级 | 必检项 |
|---|---|
| L0 服务 | backend `/healthz` 与 frontend URL 可达（`python scripts/check-test-env.py qa`） |
| L1 数据 | 当前 change 所需 fixture、种子数据或历史记录齐全 |
| L2 外部 | 真实凭据、允许操作的目标资源、故障注入与清理授权明确 |
| L3 清理 | 测试数据的写入与清理方式已确定，可重复执行 |

只执行当前已触发层级所需的最低检查；任一必检项失败时不启动测试，将对应测试记为 `NOT_RUN`
并应用失败控制规则。仅检查端口可用不足以启动系统 E2E。
