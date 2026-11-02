# (示例) 添加用户注册功能

> 此目录为 OpenSpec 变更格式示例，初始化后可删除。

## Why

当前系统没有用户管理功能，无法区分不同用户的数据。需要添加基础的用户注册能力，作为后续权限与个性化功能的基础。

## What Changes

- 新增 `User` 领域实体与仓储接口（domain 层）
- 新增 `UserService` 应用服务（application 层）
- 新增 `POST /api/v1/users/register` 接口（interfaces 层）
- 前端新增注册表单与 API 调用

## Capabilities

### New Capabilities

- `user-registration`: 用户注册的输入校验、唯一性判断与持久化行为

### Modified Capabilities

（无）

## Impact

- `backend/internal/domain/user/`、`application/user/`、`interfaces/http/handler/`、`wire/`
- `frontend/src/services/`、`src/components/`
- 新增依赖：无

## Ubiquitous Language

| 中文 | English（代码命名） | 定义 | DDD 构件类型 |
|------|-------------------|------|-------------|
| 用户 | User | 系统使用者的身份标识 | Entity |
| 用户仓储 | UserRepository | 用户持久化的接口，定义在 domain 层 | Repository |
| 用户服务 | UserService | 处理注册、校验与唯一性判断的应用服务 | Application Service |
