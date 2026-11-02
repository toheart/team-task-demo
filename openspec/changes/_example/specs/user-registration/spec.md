# user-registration

## ADDED Requirements

### Requirement: 用户注册输入校验

系统 MUST 在持久化之前校验邮箱格式与密码长度，非法输入 MUST 被拒绝且不产生副作用。

#### Scenario: 邮箱格式非法

- **WHEN** 请求体中的 `email` 不满足邮箱格式
- **THEN** 系统返回 HTTP 400，错误码为 `INVALID_PARAMS`
- **AND** 不创建任何用户记录

#### Scenario: 密码长度不足

- **WHEN** 请求体中的 `password` 长度小于 8
- **THEN** 系统返回 HTTP 400，错误码为 `INVALID_PARAMS`

### Requirement: 邮箱唯一性

系统 MUST 保证同一邮箱只能注册一次。

#### Scenario: 邮箱已注册

- **WHEN** 请求的 `email` 已存在
- **THEN** 系统返回 HTTP 409，错误码为 `EMAIL_TAKEN`
- **AND** 已存在的用户记录 MUST NOT 被修改

### Requirement: 注册响应不泄漏凭据

注册接口的响应体 MUST NOT 包含密码或其哈希。

#### Scenario: 注册成功

- **WHEN** 输入合法且邮箱未被占用
- **THEN** 系统返回 HTTP 200，body 为统一 envelope
- **AND** `data` 中只包含用户标识与邮箱，不包含密码字段
