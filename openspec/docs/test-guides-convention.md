# test-guides 文档约定

`test-guides/` 由 `feature-exec` 的 `test-design` 阶段生成，描述验收场景如何落到最低有效测试层。
生成后由 `implement`、`test-run` 与 `gate-delivery` 消费。

## 目录

```text
openspec/changes/<change-name>/
├── proposal.md
├── design.md
├── tasks.md
├── .orchestrator/
│   └── test-evidence.md
└── test-guides/
    ├── unit.md
    ├── component.md
    ├── app.md
    ├── api-smoke.md
    ├── integration.md
    ├── browser-ui.md
    └── e2e.md
```

只创建实际需要的 guide，不为完整目录生成空文件。

## 选择规则

| Guide | 适用行为 | 消费者 |
|---|---|---|
| `unit.md` | 纯函数、converter、serializer、domain、纯自定义 hook | backend / frontend implementer |
| `component.md` | 组件渲染分支、effect 与清理、受控回写、Context、Portal | frontend-implementer |
| `app.md` | Application Service 编排、状态冲突、Fake 依赖 | test-writer |
| `api-smoke.md` | HTTP 路由、DTO、错误码、鉴权、统一 envelope | test-writer |
| `integration.md` | 真实 Repository / 基础设施、外部依赖 wiring、跨组件装配 | test-writer |
| `browser-ui.md` | 真实浏览器的布局、遮罩、焦点、滚动、虚拟列表和可操作性；允许 Mock 请求 | 按需通道 |
| `e2e.md` | 真实浏览器、前后端及外部副作用构成的完整用户旅程 | 按需通道 |

- 不按文件数或变更规模决定跳过；小变更也应选择一个最低有效层。
- P0/P1 场景至少有一条 `change-gate` 的 Required 测试；无法自动化时记录 waiver、替代验证和风险。
- 遵循 3KU，规则输入组合下沉到最低有效层；跨层只能验证各层独有事实，不得重复同一实现细节。
- `browser-ui.md` 与 `e2e.md` 是按需执行通道，分别标为 `on-demand-browser` 和
  `on-demand-system`。它们不参与 `gate-delivery` 的自动计算，也不能作为 P0/P1 唯一的
  `change-gate` 证明。
- 分层前确认该层有可执行运行器。后端默认有 `go test`；前端要读 `frontend/package.json`
  的 `scripts.test`。没有运行器时该层只能登记为 waiver。

## 通用格式

每个 guide 包含：

```markdown
# <层级>测试指导

## 场景
| 场景 ID | 优先级 | Required/Optional | 执行通道 | 断言来源 | 该层独有证明 | 输入/前置 | 动作 | 可观察结果 |
|---|---|---|---|---|---|---|---|---|

## 测试切入点
| 目标文件/符号 | 建议测试文件 | Mock/Fake/fixture | 真实依赖、写入与清理 | 建议命令 |
|---|---|---|---|---|

## 不覆盖风险
| 场景 ID | 原因 | 替代验证 | 风险 |
|---|---|---|---|
```

## component.md 专项要求

命中以下任一行为时生成：

- 组件按 props / state 分支渲染，或 `key` 变化导致 remount
- `useEffect` / `useLayoutEffect` 的触发条件与依赖数组变化
- effect cleanup 的幂等性（StrictMode 双调用）
- 异步加载后的回填、刷新与竞态
- 受控与非受控切换，`value` + `onChange` 回写
- Context Provider 变更引起的重渲染范围
- 表单校验、提交时机、disabled
- Modal / Drawer / Popover / Tooltip 与 `createPortal` 的挂载与卸载
- 自定义 hook 在 rerender 下的行为
- 创建 / 编辑 / 复制 / 查看入口一致性
- 保存 → 查询 → 回填 → 再编辑

组件测试断言用户可观察行为，不直接调用内部函数；snapshot 不能作为唯一断言。jsdom 无法证明
真实 CSS、拖拽、focus、viewport、遮罩或滚动时先转到 `browser-ui`；需要真实后端或跨页面链路时
才转到系统 E2E 或人工/灰度验证。

## integration.md 专项要求

只覆盖 App 与 api-smoke 无法证明的事实：真实 Repository 行为、真实基础设施连接、外部依赖
wiring、跨组件装配。必须注明使用的是 Fake、真实依赖还是外部服务替身，不能把替身写成真实覆盖。

执行前先读取目标包的 `TestMain`：带初始化或清理的包即使只用 `-list` 或不命中 `-run`，
也可能连接、写入或清理测试数据。

## browser-ui.md 与 e2e.md 专项要求

`browser-ui.md` 证明真实浏览器中的可见、可点击、焦点、遮罩、滚动或虚拟列表行为，允许 Mock 请求。
`e2e.md` 证明真实后端及外部副作用的完整旅程。

二者均记录为按需执行：测试设计写明触发它的改动面、环境、命令和未运行风险。用户或外部流水线
要求执行时，必须遵守 `feature-exec/references/delivery-contract.md` 的分层环境 Gate。
系统 E2E 的 Case 边界、双环境声明和执行证据见 `.agents/skills/system-e2e/SKILL.md`；例如
同一验收事实在 App 层验证状态规则，在系统层只验证真实 UI 到后端的旅程。

## test-evidence

`test-design` 同时按 `feature-exec/references/delivery-contract.md` 创建
`.orchestrator/test-evidence.md`：

- 设计阶段填写场景、层级、Required/Optional、执行通道、独有证明、实际依赖、计划文件和命令
- Writer 填写实际测试文件
- Runner 填写 executed、PASS、FAIL、SKIP、NOT_RUN、命令和环境
- Gate 填写 waiver 与遗留风险

`change-gate` 的 Required 零执行、FAIL、SKIP、NOT_RUN 不得通过交付 Gate。按需浏览器或系统场景
必须登记；未触发时保留 `NOT_RUN` 与风险，不能写成 PASS，也不自动阻断普通代码交付 Gate。
