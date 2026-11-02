# 执行契约

## 运行前

1. 从用户请求确定环境、Case ID、spec 路径及完整测试名；有歧义时核对选择集。
2. 执行 `cd frontend && npm run test:e2e -- --list` 或加指定 spec。`--list` 不写运行结果，也不是 PASS。
3. dev 检查后端 `/healthz`、前端页面、Case 数据与清理方案。remote 还要检查 `E2E_REMOTE_BASE_URL`、认证来源和目标资源；不要在终端或报告中输出凭据值。
4. 读取目标 spec、Flow、Profile 的写入与清理范围。不能确认共享资源隔离时使用 `--workers=1`。

Playwright 只做健康检查和执行，由外部启动服务。模板默认 dev 地址为 `http://localhost:3000`；远程环境由 `E2E_REMOTE_BASE_URL` 提供。无远程地址时不要启动 remote 测试，也不要把它记为 PASS。

## 运行

```powershell
cd frontend
npm run test:e2e -- --list
npm run test:e2e -- e2e/system/<目标>.spec.ts --workers=1
```

独立 spec 同批运行可显式 `--workers=2`；保持 `fullyParallel: false`，同一文件内顺序执行。人工接管或调试时只用一个 worker。远程写入需在本轮设置 `E2E_REMOTE_CONFIRM` 为目标 Case ID，并在测试内调用 `requireRemoteWrite`；环境变量只授权该 ID，不替代目标资源和清理范围核对。

报告位于 `frontend/e2e/artifacts/system/results.json`，HTML 报告、Trace 和截图位于同一 artifacts 树。重新运行前保留需要的旧报告；同一路径会被新运行覆盖。清理失败应标记 `cleanup-failed` 并使结果失败；仅清理失败时再标记 `cleanup-only`，保留原始业务失败。保留资源应标记 `resource-note`。不要只在终端打印资源 ID。
