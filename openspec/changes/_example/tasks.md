# (示例) 添加用户注册功能 — 任务分解

> 此文件为 OpenSpec tasks 格式示例，初始化后可删除。

## 1. 后端领域与应用层

- **验证入口**: `V-BE = cd backend && go build ./... && go test ./...`

- [ ] 1.1 [L1] [后端] `internal/domain/user/user.go#User`：新增 User 实体与 `Validate()` 格式校验；验证 V-BE
- [ ] 1.2 [L1] [后端] `internal/domain/user/repository.go#UserRepository`：定义 `Create` / `ExistsByEmail` 接口；验证 V-BE
- [ ] 1.3 [L2] [后端] `internal/application/user/service.go#Register`：实现注册用例
  - **实现**: `User.Validate()` → `ExistsByEmail` 判重 → `Create`；契约 `specs/user-registration/spec.md#Scenario: 邮箱已注册`
  - **DoD**: 合法输入返回用户 DTO；邮箱重复返回 `ErrEmailTaken`；不修改仓储接口
  - **验证**: `go test ./internal/application/user/...`

## 2. 后端接口层

- [ ] 2.1 [L3] [后端] `internal/interfaces/http/handler/user_handler.go#RegisterHandler`：实现注册 HTTP 入口
  - **前置/契约**: 1.3；`design.md#错误响应契约`
  - **步骤**:
    1. 绑定 `RegisterRequest`，绑定失败映射为 400 INVALID_PARAMS
    2. 调用 `UserService.Register`，把 `ErrEmailTaken` 映射为 409
    3. 成功时用统一 envelope 返回 200，响应 DTO 剔除密码字段
  - **架构约束（必须遵守）**:
    - 校验规则不得写在 handler，必须复用 `User.Validate()`
    - 不得在 handler 内 `new` 依赖，装配走 `internal/wire/container.go`
    - 响应必须使用 `interfaces/http/response` 的统一结构
  - **DoD**: 三种结果（成功 / 400 / 409）返回码与 body 均符合 design 的错误响应契约
  - **停手条件**: 统一响应封装无法表达 409 时停止并报告，不自行新增响应结构
  - **验证**: `go test ./internal/interfaces/http/... -run TestRegister`
- [ ] 2.2 [L1] [后端] `internal/interfaces/http/server.go`：注册 `POST /api/v1/users/register` 路由；验证 V-BE

## 3. 前端

- [ ] 3.1 [L1] [前端] `frontend/src/types/user.ts#RegisterRequest`：新增请求与响应类型；验证 `npm run build`
- [ ] 3.2 [L2] [前端] `frontend/src/services/userApi.ts#registerUser`：新增注册 API 调用
  - **实现**: 调用 `api.post('/api/v1/users/register')`，返回类型化结果
  - **DoD**: 组件不直接依赖 axios；服务层错误统一抛出可识别类型
  - **验证**: `npm run lint`
- [ ] 3.3 [L3] [前端] `frontend/src/components/RegisterForm.tsx#RegisterForm`：实现注册表单
  - **前置/契约**: 3.2；`design.md#影响端与验收契约` AS-2
  - **步骤**:
    1. 受控 `value` + `onChange` 管理邮箱与密码
    2. 提交时经 `registerUser` 调用，把 409 映射为「邮箱已存在」提示
    3. 提交中禁用按钮，避免重复提交
  - **架构约束（必须遵守）**:
    - 不得在组件内直接调用 axios，必须经 `src/services/`
    - 不得用 `useEffect` 做表单同步，受控值直接来自 state
    - 密码字段不得写入任何日志或错误提示文案
  - **DoD**: 合法提交提示成功；409 提示「邮箱已存在」且表单内容保留
  - **停手条件**: 错误码无法从响应中稳定取到时停止并报告
  - **验证**: `npm run build`

## 4. 验证

- [ ] 4.1 [L1] [共享] 执行 `V-BE` 与 `cd frontend && npm run lint && npm run build`，全部通过
