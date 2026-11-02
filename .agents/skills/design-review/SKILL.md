---
name: design-review
description: >
  架构级方案评审与 Bad Path 审查。在 feature-design 的 propose 之后、
  gate-design 之前由主流程执行。审查方案完整性、DDD 分层与数据模型一致性、
  bad path 覆盖度、任务执行契约，产出审查报告并把错误响应契约追加到 design.md。
  说「方案评审」「design review」「架构评审」「审查方案」时触发。
---

# Design Review — 架构级方案评审与 Bad Path 审查

加载本 Skill 后，主 Agent 必须亲自执行方案评审。不要委托给 SubAgent。

## 为什么主流程执行

方案评审涉及跨模块推理、一致性判断、架构边界和 bad path 推导。这里最容易出现「看起来合理，落地时返工」的问题，SubAgent 做这类评审容易流于表面，尤其在 M1-M5 数据模型审查和 bad path 推导上产出质量不足。

## 必读

执行前必须先读取：

- `AGENTS.md`
- `docs/README.md`
- `docs/quickstart.md`
- `docs/testing.md`
- `openspec/specs/backend-go-style/spec.md`
- `openspec/specs/frontend-typescript-style/spec.md`
- `openspec/specs/api-conventions/spec.md`
- `openspec/specs/testing-standards/spec.md`
- `openspec/changes/<change-name>/proposal.md`
- `openspec/changes/<change-name>/design.md`
- `openspec/changes/<change-name>/tasks.md`
- `openspec/changes/<change-name>/specs/**/*.md`（如存在）
- `openspec/changes/<change-name>/.orchestrator/explore-report.md`（如存在）
- `openspec/changes/<change-name>/model-validation.md`（如存在）

如果某个文件不存在，记录为事实，不要臆造其内容。

## 工作流程

### Phase 1：方案完整性审查

逐项检查 `proposal.md`、`design.md` 和 `tasks.md`：

| # | 检查项 | 要回答的问题 |
|---|--------|-------------|
| C1 | 目标清晰 | 问题定义是否清晰？解决了什么用户痛点或工程痛点？ |
| C2 | 方案可行 | 设计方案在当前代码库中是否可落地？有没有忽略已有约束？ |
| C3 | 任务完整 | tasks 是否覆盖 proposal、specs 和 design 中描述的全部变更？有没有遗漏文件或模块？ |
| C4 | 复杂度分布 | L3 任务占比是否 ≤ 30%？超过则说明分解不够细 |
| C5 | 反模式清单 | `design.md` 是否包含「实现反模式（SubAgent 必读）」段？内容是否覆盖易违反的架构约束？ |
| C6 | 执行确定性 | tasks 是否按 L1/L2/L3 提供与风险匹配的最低信息，并利用分组共享上下文去重，使执行 Agent 无需补做设计决策？ |

### Phase 2：DDD 分层与数据模型审查（M1-M5）

当提案涉及新增实体、修改数据结构、变更 API DTO、跨层数据流或前后端契约时执行。若存在 `model-validation.md`，必须基于调研报告回答，不能凭空推断。

| # | 检查项 | 要回答的问题 |
|---|--------|-------------|
| M1 | 同类对齐 | 本次涉及的实体或 DTO 在系统中有无同类？现有模型如何？新模型是否对齐既有模式？ |
| M2 | 数据穿透 | storage → Domain → Application → DTO → API → 前端的路径是否自然？哪里需要「不自然的适配」？ |
| M3 | 标识一致性 | ID、key、slug、状态字段在所有消费方中的语义是否一致？ |
| M4 | 扩展性 | 未来新增同类实体或字段时，当前模型能否零改动或低成本适配？ |
| M5 | 状态归属 | 状态由哪一层写入？谁读取？是否存在同步散落或双写风险？ |
| M6 | 依赖方向 | 新增代码是否保持 `domain` 不依赖 `infrastructure` / `interfaces`？跨域编排是否落在 application 层？ |

每项给出结论：`OK` / `WARN` / `BLOCKER`，并说明依据。

### Phase 3：Bad Path 四维审查

对 proposal、specs 和 design 中的每个功能点，系统性推导 bad path。

#### 3.1 输入边界

对每个 API 端点或表单入口，列出：

| 场景 | 输入 | 期望 HTTP Status | 期望 Error Code | 处理方式 |
|------|------|-----------------|----------------|---------|
| 必填参数缺失 | `<field>` 为空 | 400 | INVALID_PARAMS | 前端校验 + 后端兜底 |
| 参数类型错误 | `<field>` 类型错误 | 400 | INVALID_PARAMS | 绑定或解析层拦截 |
| 参数越界 | `<field>` 超出范围 | 400 | INVALID_PARAMS | 业务校验返回明确错误 |

#### 3.2 状态冲突

对每个涉及状态变更的操作，列出：

| 操作 | 当前状态 | 结果 | 幂等性 |
|------|---------|------|--------|
| `<operation>` | `<valid-state>` | 正常流转 | — |
| `<operation>` | `<invalid-state>` | 409 CONFLICT | 说明是否幂等 |

#### 3.3 依赖失败

对每个外部依赖或基础设施调用，列出：

| 依赖 | 失败场景 | Fallback | 重试 | 日志级别 |
|------|---------|----------|------|---------|
| Database | 连接超时 | 无，返回错误 | 否 | ERROR |
| External API | 请求失败 | 按设计约定处理 | 视场景 | WARN / ERROR |

#### 3.4 权限与资源边界

| 操作 | 无权限用户 | 跨资源 / 越权访问 |
|------|-----------|-----------------------|
| `<operation>` | 403 FORBIDDEN | 按资源归属隔离 |

### Phase 4：验收场景覆盖矩阵

基于 `design.md` 的「影响端与验收契约」验收矩阵，逐项检查：

| 验收场景 | 覆盖的 Task | 对应测试层级 | 覆盖状态 |
|---------|------------|------------|---------|
| AS-1: Happy Path | Task 1.1, 1.2 | 单元 / api-smoke | OK |
| AS-2: Bad Path | 无 Task 覆盖 | — | BLOCKER |

- 覆盖矩阵中标记为 `BLOCKER` 的场景必须在审查报告中列为阻断项。
- 建议最低测试层必须能在执行阶段落地，不依赖尚未准备的环境才能证明核心逻辑。

### Phase 4.5：任务执行契约审查

逐项检查 `tasks.md`，不能只抽查。审查报告只汇总通过数量并列出不合格项，避免复制整份任务清单。

| Task | 级别 / 端别 | 代码定位 | 执行信息 | DoD | 验证入口 | 结果 |
|------|-----------|----------|----------|-----|----------|------|
| 1.1 | L1 / 后端 | `path#symbol` | 动作明确 | 可观察 | V-BE | OK |

全部通过时只写：`共检查 N 项，L1/L2/L3 = x/y/z，无需重写。`

判定规则：

- 分组级前置、契约、边界和验证命令可被任务继承，不得因任务未重复这些字段判失败。
- L1 必须在一行内给出精确代码定位、确定动作、可观察完成态和验证入口。
- L2 在 L1 基础上必须给出实现链路、DoD 和局部验证；仅非顺序依赖、签名变化或特殊风险需要额外展开。
- L3 必须给出前置、具体步骤、任务特有架构约束、DoD、验证和停手条件，并引用 design 决策或反模式段。
- 任一级别存在 `TBD`、`待确认`、`二选一`、`按实际情况`、`自行决定`，结论 MUST 为 `NEEDS_REVISION`。
- 引用现有文件或符号但无法从代码事实定位，结论 MUST 为 `NEEDS_REVISION`；不得把搜索工作转嫁给执行 Agent。
- 单项任务包含多个 owner、多个独立调用链或多个可独立验证结果时，要求继续拆分。
- 执行 Agent 仍需决定数据模型、错误语义、接口形态、落盘位置或跨端契约时，列为 `BLOCKER`。

### Phase 4.6：Review Checklist 可判定性

检查 `design.md` 的「Review Checklist（本次变更专用）」：

- 每条是否能用「是 / 否」机械判定？
- 是否覆盖本次变更的主要风险点（错误契约、权限、状态、依赖方向、生成文件）？
- 是否存在「代码质量良好」这类无法判定的条目？有则要求重写。

### Phase 5：产出审查报告

审查报告必须写入：

```text
openspec/changes/<change-name>/.orchestrator/design-review.md
```

格式：

```markdown
## 方案评审报告

### 一、方案完整性
| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| C1 | 目标清晰 | OK/WARN/BLOCKER | <详情> |

### 二、DDD 分层与数据模型
| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| M1 | 同类对齐 | OK/WARN/BLOCKER | <详情> |

### 三、Bad Path 审查
<Phase 3 的四张表>

### 四、验收场景覆盖矩阵
<Phase 4 的覆盖表>

### 五、任务执行契约
<Phase 4.5 的逐项审查表；列出所有需要重写的 Task>

### 六、Review Checklist 可判定性
<Phase 4.6 结论>

### 七、错误响应契约完整性检查
- [ ] design.md 是否包含「错误响应契约」段落？
- [ ] 错误响应契约是否覆盖四维：输入边界 / 状态冲突 / 依赖失败 / 权限边界？
- [ ] 每个错误场景是否有明确 HTTP Status + Error Code？
- [ ] 错误响应契约中的场景是否能映射到验收矩阵中的 bad path？

### 八、结论
- BLOCKER: <如有>
- 建议修改: <如有>
- 结论: APPROVE / NEEDS_REVISION / REJECT
```

如果存在 BLOCKER，结论必须是 `NEEDS_REVISION` 或 `REJECT`。如果 `design.md` 缺少错误响应契约或四维覆盖不完整，结论 MUST 为 `NEEDS_REVISION`。

### Phase 6：追加错误响应契约

如果 Phase 3 产出了错误响应、状态冲突、依赖失败或权限边界行为定义，必须追加写入：

```text
openspec/changes/<change-name>/design.md
```

追加格式：

```markdown
## 错误响应契约（design-review 产出，implement 必读）

### 输入边界
| 端点/入口 | 场景 | HTTP Status | Error Code | 处理方式 |
|-----------|------|-------------|------------|---------|

### 状态冲突
| 操作 | 非法前置状态 | 行为 | 幂等性 |
|------|--------------|------|--------|

### 依赖失败
| 依赖 | 失败场景 | Fallback | 重试 | 日志级别 |
|------|----------|----------|------|---------|

### 权限与资源边界
| 操作 | 无权限用户 | 越权访问 | 行为 |
|------|----------|----------|------|
```

如果 `design.md` 已有同名段落，更新该段落，不要重复追加多个同名段落。

## 约束

- 主流程执行：不委托给 SubAgent。
- 可读可写文档：可以写 `.orchestrator/design-review.md`，可以更新 `design.md` 的错误响应契约，不修改业务代码。
- 基于事实：数据模型审查优先基于 `model-validation.md` 和代码搜索，不凭空推断。
- Bad path 必须具体：至少到 `HTTP Status + Error Code + 处理方式` 的粒度，不能只说「需要处理错误」。
- 不替用户拍板：只给出 `APPROVE` / `NEEDS_REVISION` / `REJECT` 和依据；Gate 仍由 `feature-design` 处理。
