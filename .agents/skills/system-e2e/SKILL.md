---
name: system-e2e
description: 设计、编写和按需运行 Go/React 项目的真实系统 E2E；处理业务旅程覆盖、Playwright 结果、环境写入和失败诊断。组件交互或纯浏览器可操作性优先使用低层或 Browser UI 测试。
---

# 系统 E2E

系统 E2E 证明真实浏览器、前后端和所声明外部副作用组成的用户旅程。入口在 `frontend/e2e/`；按需运行，不加入 `make check` 或普通 feature 交付 Gate。先读 `docs/testing.md` 和 `frontend/e2e/README.md`。

## 设计与编写

设计或收口场景时读 [Case 契约](references/case-contract.md)。先列验收事实与来源，再说明系统层独有证明；规则输入组合留在 Unit/App。一个独立场景对应一个 `test()`，连续业务关口用 `test.step()`。每条测试自己建立并清理可变状态，不消费其他测试留下的草稿或执行结果。

按 `profiles/`（环境）、`components/`（页面封装）、`flows/`（用户操作）、`support/`（认证、清理和结果）、`system/`（Case）组织实际需要的文件，不为空目录造代码。只读场景可使用明确登记的现有数据；声明了创建、提交或执行的场景，必须通过 UI 完成这些动作，不用 API 伪造目标状态。需写入远程环境时，用 `requireRemoteWrite(Case ID)` 校验本轮 `E2E_REMOTE_CONFIRM`；还要在运行前确认目标资源与清理方式。远程环境未配置时标为未覆盖，不把 dev 通过当作远程通过。

定位优先 `data-testid`，其次唯一的 `role + name`。业务实体的 testid 使用稳定 ID；不能靠 CSS 层级、XPath、坐标或固定等待猜测目标。定位缺失时补页面可测性并在组件层验证唯一性。纯 CSS、焦点、遮罩或虚拟列表的浏览器事实放 Browser UI；系统 Case 只保留真实链路独有断言。

## 执行与判定

运行前读 [执行契约](references/execution.md)，用 `npm run test:e2e -- --list` 核对具体测试名，再检查服务、认证、数据、写入目标与清理。收集模式不是通过证据。独立 spec 可由同一 Playwright 进程用两个 worker；共享资源、人工接管和调试场景串行。不能仅凭不同文件名或 run ID 推断资源隔离。

先读 `frontend/e2e/artifacts/system/results.json` 的业务结果，再看 Trace、截图与资源注解。至少一条 PASS 且其余均为 PASS/NOT_APPLICABLE 才可汇总通过。NOT_RUN、HANDOFF_PENDING、DIAGNOSTIC_ONLY、CLEANUP_FAILED 和 FAIL 均不能算通过。每次结论说明环境、被测版本、Case ID、完整测试名、实际断言范围和未覆盖部分。

失败时读 [诊断契约](references/diagnosis.md)。先分析已有证据，再定向复现；同一失败无代码变更最多重跑一次。复现需新 run，不能在失败现场补状态后宣称原 Case 通过。
