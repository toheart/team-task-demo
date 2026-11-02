# 系统 E2E

`system/` 的 Playwright Case 连接真实前端和后端。模板自带 `STARTER-READ-001`，验证首页通过真实 API 显示数据。新业务旅程按 `.agents/skills/system-e2e/SKILL.md` 设计；纯组件交互、布局和规则输入组合分别留在 Component、Browser UI、Unit/App 层。

先在两个终端启动服务，再执行：

```powershell
make dev-backend
make dev-frontend
cd frontend
npm ci
npx playwright install chromium
npm run test:e2e -- --list
npm run test:e2e -- e2e/system/starter-read-001.spec.ts
```

Playwright 不启动或关闭服务。默认运行 dev (`http://localhost:3000`)；其他环境设置 `E2E_ENV=remote` 与 `E2E_REMOTE_BASE_URL`，并按项目实现认证。远程环境的写入 Case 还须在测试中调用 `requireRemoteWrite(Case ID)`，运行时提供本轮 `E2E_REMOTE_CONFIRM=<Case ID>`。确认 Case ID 前还需核对目标资源和清理范围；不要把凭据写进仓库或测试报告。

`npm run test:e2e -- --list` 仅核对选择集，不生成通过证据。正式结果见 `e2e/artifacts/system/results.json`，HTML 报告、Trace 和截图在 `artifacts/system/`。系统 E2E 按需触发，不属于 `make check`；未运行时在 `test-evidence.md` 中记 `NOT_RUN`。
