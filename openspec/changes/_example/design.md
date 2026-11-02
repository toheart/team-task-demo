# (示例) 用户注册 — 技术设计

> 此文件为 design.md 格式示例，初始化后可删除。

## Context

现有代码只有 `sample` 域。HTTP 层已有统一响应封装（`internal/interfaces/http/response`），错误码约定见 `openspec/specs/api-conventions/spec.md`。仓储实现目前只有内存版本。

## Goals / Non-Goals

**Goals:**

- 提供可被前端调用的注册接口，输入非法时返回明确错误码
- 保持 domain 层不依赖 infrastructure

**Non-Goals:**

- 不包含登录与 JWT 认证
- 不包含邮箱验证、密码复杂度策略
- 不引入持久化数据库（沿用内存实现）

## 影响端与验收契约

```yaml
affected_ends:
  backend: true
  frontend: true
  external_systems: []
```

| 场景 ID | 验收行为（用户可观察） | 影响端 | 建议最低测试层 |
|---|---|---|---|
| AS-1 | 提交合法邮箱与密码后提示注册成功 | frontend/backend | unit + api-smoke |
| AS-2 | 邮箱已被注册时表单提示「邮箱已存在」，不刷新页面 | frontend/backend | app |
| AS-3 | 邮箱格式非法时前端拦截，后端同样返回 400 INVALID_PARAMS | backend | api-smoke |

## Decisions

- **校验放在 domain 而非 handler**：`User.Validate()` 承载格式与长度规则，handler 只做绑定与错误映射。理由：同一规则在 application 与其他入口需要复用；替代方案是在 handler 里用 binding tag，被否决因为规则无法单测且无法复用。
- **唯一性判断走仓储 `Exists`，不在 domain 内查库**：domain 不感知持久化。理由：保持依赖方向；替代方案是在 service 里注入 repository，那正是 application 层职责。

## Risks / Trade-offs

- [内存仓储重启即丢数据] → 示例范围为可接受；接入真实存储时需补唯一索引，避免并发下的重复注册
- [并发注册同名邮箱] → 当前实现先查后写，存在竞态；生产化前需改为依赖存储层唯一约束

## 实现反模式（SubAgent 必读）

1. **不要在 domain 层 import infrastructure 或 interfaces** — 会破坏 DDD 依赖方向，`make check` 无法发现这类问题
2. **不要在 handler 里写业务校验规则** — 规则必须放在 `User.Validate()`，否则无法被 application 层复用
3. **不要在 handler 里直接 `new` 依赖** — 装配统一在 `internal/wire/container.go` 的 `BuildHTTPServer`，否则新增依赖会漏改且无法单测
4. **不要在前端组件里直接调用 fetch/axios** — 必须经过 `frontend/src/services/`

## Review Checklist（本次变更专用）

- [ ] `POST /api/v1/users/register` 在邮箱重复时返回 409 且 body 为统一 envelope？
- [ ] 邮箱格式非法时返回 400 INVALID_PARAMS，且错误信息不泄漏内部字段名？
- [ ] `UserRepository` 接口是否定义在 domain 层，实现放在 infrastructure 层？
- [ ] 密码字段是否在响应 DTO 中被剔除？
- [ ] 前端注册表单是否只通过 `src/services/` 发起请求？
- [ ] `tasks.md` 中标注的 AS 场景是否都有对应测试或 waiver？
