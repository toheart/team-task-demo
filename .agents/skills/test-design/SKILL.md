---
name: test-design
description: >
  为 feature 选择最低有效测试层并生成 test-guides 与 test-evidence。由 feature-exec 在
  test-design 阶段调用，把验收场景映射为可执行测试。覆盖后端 unit、前端 unit/component、
  app、api-smoke、integration、browser-ui 与系统 E2E。
---

# Test Design

测试分层是设计判断，由主流程亲自完成。本 Skill 只读业务代码，只写 `test-guides/` 与
`.orchestrator/test-evidence.md`，不写业务实现或测试代码。

## 必读

- `AGENTS.md`
- `docs/testing.md`
- `openspec/docs/test-guides-convention.md`
- `openspec/changes/<change-name>/proposal.md`、`design.md`、`tasks.md`
- `openspec/changes/<change-name>/.orchestrator/explore-report.md`、`design-review.md`
- 实际受影响代码和已有测试

## 设计原则

1. 先提取业务断言和 Bad Path，再选择测试层；顺序颠倒会得到「跟着实现写测试」。
2. 遵循 3KU：规则输入组合下沉到最低有效层；跨层只保留各层独有的证明，禁止复制同一组输入
   和同一实现断言。
3. 不按文件数或「变更很小」决定跳过；小变更也可能需要一个最低层回归测试。
4. P0/P1 场景必须映射到 `change-gate` Required 测试；无法自动化时记录 waiver、替代验证和风险。
5. 没有可提取的业务断言时返回设计侧补充，不从实现代码臆造 P0 规则。
6. 分层前先确认该层有可执行运行器（后端 `go test`；前端读 `frontend/package.json` 的
   `scripts.test`）。缺失时该层只能登记为 waiver，不得登记为 `change-gate` Required。

## 断言来源

按优先级使用：

1. `design.md` 的「影响端与验收契约」验收矩阵（AS-*）
2. `proposal.md` / specs 的业务规则
3. `design.md` 的错误响应契约
4. `tasks.md` 的 DoD
5. API 与共享常量契约
6. 代码事实——仅用于定位切入点，**不作为 P0 业务规则来源**

Bad Path 至少判断输入异常、状态冲突、依赖失败、权限边界四类；涉及状态机、重试、并行或回滚时，
追加部分成功、幂等恢复和实际状态验证。

每个场景先建立「断言归属 + 执行依赖」记录：断言来源、主测试层、该层独有证明、真实/Fake 依赖、
是否写入数据及清理方式、建议命令。已有测试只在逐项读过动作和断言后才能复用；文件名、目录和
`P0` 命名不是覆盖证据。

## 测试层选择

| 层级 | 适用行为 | 主要消费者 |
|---|---|---|
| unit | 纯函数、converter、serializer、domain、纯自定义 hook | backend / frontend implementer |
| component | 组件渲染分支、effect 与清理、受控回写、Context 联动、Portal | frontend-implementer |
| app | Application Service 编排、状态冲突、Fake 依赖 | test-writer |
| api-smoke | 路由、DTO、HTTP 错误码、鉴权、统一 envelope | test-writer |
| integration | 真实 Repository / 基础设施、外部依赖 wiring、跨组件装配 | test-writer |
| browser-ui | 真实浏览器中的布局、遮罩、焦点、滚动、虚拟列表与可操作性；允许 Mock 请求 | 按需通道 |
| e2e | 真实后端、外部副作用与完整用户旅程 | 按需通道 |

### 跨层断言归属

- Unit 证明规则、状态迁移和边界组合；不得在 UI 或 HTTP 层重复穷举同一组合。
- App 证明 Application 编排、持久化事实与 Fake Port 的交互；api-smoke 只证明路由、DTO、
  鉴权和错误 envelope。
- `integration` 只保留 App 无法证明的事实：真实 Repository 行为、外部依赖 wiring、
  跨组件装配。Fake 依赖的证据与真实基础设施的证据是不同证明，不能互相替代。
- Component 证明框架侧状态与用户可观察交互；`browser-ui` 证明 jsdom 不能证明的真实浏览器
  可操作性。系统 E2E 再证明真实后端、权限、数据与外部副作用构成的用户旅程。
- 同一场景可以有多个层级，但每一行必须写出不同的「独有证明」；写不出来时保留最低层，
  删除计划中的重复项。

### 执行通道

- `change-gate`：本次改动必须自动执行的低层、App、API Smoke 或 Integration 测试。
  每个 P0/P1 至少有一条此通道的 Required 测试或明确 waiver。
- `on-demand-browser`：真实浏览器 UI 回归，按影响面登记，由人或外部流水线按需执行；
  不参与 `gate-delivery` 自动计算。
- `on-demand-system`：系统 E2E，按影响面登记，由人或外部流水线按需执行；不参与
  `gate-delivery` 自动计算。

`on-demand-*` 不是「遗漏的 Required 测试」：它们不能作为 P0/P1 唯一的 change-gate 证明，
也不因普通代码交付未运行而阻断 Gate；必须在证据中保留计划场景、触发条件和未运行风险。

### Component 必选触发器（React）

前端变更命中任一项时，至少一个关联场景必须进入 `component`：

- 组件按 props / state 分支渲染，或 `key` 变化导致 remount
- `useEffect` / `useLayoutEffect` 的触发条件与依赖数组变化
- effect cleanup 的幂等性（React StrictMode 下 effect 会双调用）
- 异步数据加载后的回填、刷新与竞态（AbortController、请求序号）
- 受控与非受控切换，`value` + `onChange` 回写
- Context Provider 变更引起的重渲染范围
- 表单校验、提交时机、按钮 disabled
- Modal / Drawer / Popover / Tooltip 与 `createPortal` 的挂载与卸载
- 自定义 hook 在 rerender 下的行为
- 创建 / 编辑 / 复制 / 查看入口的一致性
- 保存 → 查询 → 回填 → 再编辑的数据往返

真实 CSS、拖拽、focus、viewport、遮罩、滚动定位、虚拟列表或键盘操作无法由 jsdom 证明时，
优先转为 `browser-ui`；只有还需要真实后端、跨页面状态、权限或外部副作用时才转为系统 E2E。

**不要写伪 component 断言**。反例：

- 断言 effect 的调用次数（`expect(fetch).toHaveBeenCalledTimes(1)`）在 StrictMode 下会失败；
  能断言次数的场景只有「cleanup 幂等性」，最终状态应作为主要断言。
- 用 snapshot 作为唯一断言。
- 直接调用组件内部函数来「证明」交互。

### 测试编写时机

- 后端 domain / application 与前端自定义 hook：**先写测试**（Red → Green）。`renderHook`
  是自定义 hook 的公开 API，可以直接驱动。
- 前端组件：**先定行为契约再补测试**，不做 TDD。组件结构在契约稳定前会反复改写，
  先写的测试会大量作废。
- App / api-smoke / integration：主体接口稳定后补齐，属于 `implement` 的完成条件。
- browser-ui / e2e：按需通道，先有测试资产与运行计划即可。

## 产出

只生成实际需要的文件：

```text
openspec/changes/<change-name>/test-guides/
├── unit.md
├── component.md
├── app.md
├── api-smoke.md
├── integration.md
├── browser-ui.md
└── e2e.md
```

每个 guide 必须包含：

- 场景 ID、P0/P1/P2、Required/Optional
- 断言来源
- 测试切入点和建议文件
- 输入、动作、用户可观察结果
- 该层独有证明
- Mock / Fake / fixture、真实依赖、数据写入与清理策略
- `change-gate` / `on-demand-browser` / `on-demand-system` 执行通道
- 建议执行命令
- 不覆盖风险和理由

同时创建：

```text
openspec/changes/<change-name>/.orchestrator/test-evidence.md
```

使用 `feature-exec/references/delivery-contract.md` 的证据表，先写计划列，执行结果由
`qa-tester` 回填。

## 自检

- 每个 P0/P1 至少有一条 `change-gate` 映射，且跨层测试写明了独有证明
- 前端风险触发器命中时存在 component 场景
- 每个用于 `change-gate` 的层都有可执行运行器；没有运行器的层已降级为 waiver 并写明替代验证
- Required 测试有明确文件或生成任务、命令、环境及实际依赖
- 每个 on-demand 场景有触发条件、命令和未运行风险
- 没有空 guide，没有以「文件少」为由跳过
- E2E 只保留无法在更低层证明的关键旅程
- 规划 `on-demand-system` 时按 `.agents/skills/system-e2e/references/case-contract.md` 声明 Case、环境路径与系统层独有证明；不把登记当成执行结果
