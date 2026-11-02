# 测试规范

本文定义本仓库的测试分层、测试编写时机、Go 与前端测试写法，以及可直接执行的运行命令。

规范性要求见 `openspec/specs/testing-standards/spec.md`；分层选择与交付 Gate 的完整契约见
`.agents/skills/feature-exec/references/delivery-contract.md`；`test-guides/` 的文件格式见
`openspec/docs/test-guides-convention.md`。

## 测试分层

测试分为 7 层。选择层级时先取能满足断言的最低层，再按「该层独有证明」决定是否上升。

| 层级 | 最低有效验证对象 | 默认命令 |
|---|---|---|
| `unit` | 后端：domain 纯逻辑、converter、校验规则；前端：纯函数、格式化、纯自定义 hook 的返回值 | 后端 `go test <受影响包>`；前端 `cd frontend && npm test -- <files>` |
| `component` | 组件渲染分支、用户交互、effect 与清理、受控值回写、Context 联动、Portal | `cd frontend && npm test -- <files>` |
| `app` | Application Service 编排、状态冲突、fake 依赖的交互 | `go test <受影响包>` |
| `api-smoke` | HTTP 路由、DTO、错误码、鉴权、统一 envelope | `go test <受影响包>` |
| `integration` | 真实 Repository、基础设施连接、外部依赖 wiring、跨组件装配 | `go test <受影响包>` |
| `browser-ui` | 真实浏览器中的布局、遮罩、焦点、滚动、虚拟列表与可操作性（允许 mock 请求） | 按需通道 |
| `e2e` | 真实后端、外部副作用与完整用户旅程 | 按需通道 |

前端的两条命令以 `frontend/package.json` 提供 `scripts.test` 为前提，见「React / TypeScript 测试」。

分层规则：

- 运行器前置检查：分层前确认该层有可执行入口。后端有 `go test`；前端读
  `frontend/package.json` 的 `scripts.test`。缺失时该层不得登记为必测，只能登记为 waiver 并写明
  替代验证与遗留风险。
- `browser-ui` 与 `e2e` 是按需执行通道，分别标为 `on-demand-browser` 与 `on-demand-system`。
  两者不参与交付 Gate 的自动计算，也不能作为 P0/P1 唯一的 Gate 证明。
- 跨层只保留各层独有的证明。fake 依赖的证据与真实基础设施的证据是不同证明，不能互相替代。
- 同一个断言组合只下沉到最低层一次，不在 UI 层或 HTTP 层重复穷举。
- P0/P1 场景至少有一条 `change-gate` 的必测测试，或一条写明替代验证的 waiver。
- 前端 component 层的 React 必选触发器见 `.agents/skills/test-design/SKILL.md` 的
  「Component 必选触发器（React）」，本文不重复该列表。

## 测试编写时机

| 对象 | 时机 |
|---|---|
| 后端 domain / application | 先写测试（Red → Green） |
| 前端自定义 hook | 先写测试（Red → Green），`renderHook` 是 hook 的公开入口 |
| 前端组件 | 先定行为契约再补测试，不做 TDD |
| app / api-smoke / integration | 主体接口稳定后补齐，属于 `implement` 阶段的完成条件 |
| browser-ui / e2e | 按需，先进运行计划与测试资产，不进交付 Gate |

前端组件不做 TDD 的原因：组件结构在行为契约稳定前会反复改写，先写的测试会随结构调整作废。
契约指 props 形状、状态分支、用户可观察结果与错误呈现方式；契约稳定后再补测试。

## Go 测试规范

### 框架与依赖

Go 测试使用标准库 `testing`，配合表驱动与 `t.Run` 子测试。不引入第三方断言库、测试运行器或
mock 代码生成工具。

`backend/go.mod` 的 `require` 只有 `gin-gonic/gin`、`spf13/cobra`、`spf13/viper`，其余均为
`indirect`。不存在 Ginkgo、Gomega、mockery 或 `google/wire` 依赖。

### 文件组织

- 测试文件与被测代码同目录，命名 `*_test.go`。
- 使用同包测试（`package sample`）而非外部测试包（`package sample_test`），便于直接测试未导出的
  纯函数。
- 公开函数与方法的新增或修改必须有对应测试。
- 不生成 mock 文件，不创建 `mocks/` 目录。

```text
backend/internal/application/sample/
├── service.go
└── service_test.go
```

### 标准库 testing 要点

`t.Parallel()`

- 顶层测试与子测试都可以调用，声明该测试可与其他并行测试同时运行。
- `golangci-lint` 启用了 `tparallel`，声明并行却漏调会告警。
- 调用后不得再依赖或修改包级、跨测试共享的可变状态。
- Go 1.25 的循环变量为每轮迭代独立，表驱动测试不需要写 `tt := tt`。

`t.Helper()`

- 在测试辅助函数的第一行调用，失败信息与行号指向调用者而非辅助函数内部。
- `golangci-lint` 启用了 `thelper`，辅助函数漏写会告警。

`t.Cleanup()`

- 注册测试结束时的清理逻辑。放在辅助函数里比 `defer` 合适：`defer` 在辅助函数返回时执行，
  `t.Cleanup` 在测试（或子测试）结束时执行。
- 资源创建后就近注册，不依赖注册顺序之外的控制流。
- 临时目录优先用 `t.TempDir()`，它自带清理，不需要手写 `t.Cleanup`。

`httptest`

- `httptest.NewRequest` 构造请求，`httptest.NewRecorder` 捕获响应。
- 用 `server.Handler.ServeHTTP(recorder, request)` 在进程内跑完整路由，不监听真实端口。
- 断言状态码、统一 envelope 的 `code` / `message`，以及 `data` 的结构。

### 示例一：domain 纯逻辑（表驱动）

`internal/domain/sample` 当前只定义类型与常量。下例以新增纯函数 `IsReady` 说明结构，照抄时替换为
你的实际纯函数。

```go
package sample

import "testing"

// IsReady 是被测的纯函数。
func IsReady(status Status) bool {
	return status == StatusReady
}

func TestIsReady(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name   string
		status Status
		want   bool
	}{
		{name: "ready", status: StatusReady, want: true},
		{name: "in progress", status: StatusInProgress, want: false},
		{name: "done", status: StatusDone, want: false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()

			if got := IsReady(tt.status); got != tt.want {
				t.Fatalf("IsReady(%q) = %v, want %v", tt.status, got, tt.want)
			}
		})
	}
}
```

### 示例二：application 编排 + 手写 fake 仓储

`internal/application/sample.Service.List` 依赖 `domainsample.Repository`。用手写 fake 替换仓储，
验证 DTO 映射与错误包装；辅助函数演示 `t.Helper()` 与 `t.Cleanup()`。

```go
package sample

import (
	"context"
	"errors"
	"testing"
	"time"

	domainsample "github.com/toheart/go-react-openspec-starter/backend/internal/domain/sample"
)

type fakeRepository struct {
	items     []domainsample.Sample
	err       error
	listCalls int
}

var _ domainsample.Repository = (*fakeRepository)(nil)

func (f *fakeRepository) List(ctx context.Context) ([]domainsample.Sample, error) {
	_ = ctx

	f.listCalls++

	if f.err != nil {
		return nil, f.err
	}

	return f.items, nil
}

func newTestService(t *testing.T, repo *fakeRepository) *Service {
	t.Helper()

	t.Cleanup(func() {
		if repo.listCalls == 0 {
			t.Error("expected Repository.List to be called at least once")
		}
	})

	return NewService(repo)
}

func TestServiceList(t *testing.T) {
	t.Parallel()

	updatedAt := time.Date(2024, 5, 1, 8, 0, 0, 0, time.UTC)
	repoErr := errors.New("repository unavailable")

	tests := []struct {
		name    string
		repo    *fakeRepository
		wantLen int
		wantErr error
	}{
		{
			name: "maps domain items to DTO",
			repo: &fakeRepository{items: []domainsample.Sample{{
				ID:        "sample-001",
				Name:      "Backend module",
				Category:  domainsample.CategoryBackend,
				Status:    domainsample.StatusReady,
				UpdatedAt: updatedAt,
			}}},
			wantLen: 1,
		},
		{
			name:    "wraps repository error",
			repo:    &fakeRepository{err: repoErr},
			wantErr: repoErr,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()

			items, err := newTestService(t, tt.repo).List(context.Background())
			if !errors.Is(err, tt.wantErr) {
				t.Fatalf("List() error = %v, want %v", err, tt.wantErr)
			}

			if tt.wantErr != nil {
				return
			}

			if len(items) != tt.wantLen {
				t.Fatalf("expected %d items, got %d", tt.wantLen, len(items))
			}

			if items[0].UpdatedAt != updatedAt.Format(time.RFC3339) {
				t.Fatalf("expected RFC3339 timestamp, got %q", items[0].UpdatedAt)
			}
		})
	}
}
```

### 示例三：HTTP 路由 + httptest

`internal/interfaces/http/server_test.go` 已在用这个结构。下例把公共装配提取成 `t.Helper()`
辅助函数，并用 `t.Cleanup()` 关闭 server 持有的资源。

```go
package httpserver

import (
	"context"
	"encoding/json"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/toheart/go-react-openspec-starter/backend/conf"
	appsample "github.com/toheart/go-react-openspec-starter/backend/internal/application/sample"
	"github.com/toheart/go-react-openspec-starter/backend/internal/infrastructure/storage/memory"
	"github.com/toheart/go-react-openspec-starter/backend/internal/interfaces/http/handler"
)

func newTestServer(t *testing.T) *Server {
	t.Helper()

	cfg := conf.Config{
		App:  conf.AppConfig{Name: "go-react-openspec-starter", RunMode: "test"},
		HTTP: conf.HTTPConfig{Host: "127.0.0.1", Port: 8080},
	}
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	service := appsample.NewService(memory.NewSampleRepository())

	server := New(cfg, logger, handler.NewSampleHandler(service))

	t.Cleanup(func() {
		if err := server.Shutdown(context.Background()); err != nil {
			t.Errorf("shutdown test server: %v", err)
		}
	})

	return server
}

func TestServerHealthz(t *testing.T) {
	t.Parallel()

	request := httptest.NewRequest(http.MethodGet, "/healthz", nil)
	recorder := httptest.NewRecorder()

	newTestServer(t).server.Handler.ServeHTTP(recorder, request)

	if recorder.Code != http.StatusOK {
		t.Fatalf("expected status 200, got %d", recorder.Code)
	}

	var payload struct {
		Code    int               `json:"code"`
		Message string            `json:"message"`
		Data    map[string]string `json:"data"`
	}
	if err := json.Unmarshal(recorder.Body.Bytes(), &payload); err != nil {
		t.Fatalf("unmarshal healthz response: %v", err)
	}

	if payload.Code != 0 || payload.Message != "success" {
		t.Fatalf("unexpected envelope: code=%d message=%q", payload.Code, payload.Message)
	}

	if payload.Data["status"] != "ok" {
		t.Fatalf("expected health status ok, got %q", payload.Data["status"])
	}
}
```

## 测试替身

优先级：

1. 手写 fake（默认）。
2. 模板自带的内存实现（`internal/infrastructure/storage/memory`），用于 `app` 与 `api-smoke` 层的装配。
3. 生成式 mock：模板没有对应工具，不引入。

模板不存在 mockery、`.mockery.yaml` 或 `mocks/` 目录；`google/wire` 也不在依赖中。
`internal/wire/container.go` 是手写工厂的 `BuildHTTPServer`，目录名沿用 `wire` 但没有代码生成步骤，
也不存在 `generate` 目标。

手写 fake 的约定：

- 只在小接口（1-3 个方法）上手写。接口偏大时先拆接口，而不是写一个大 fake。
- 用 `var _ domainsample.Repository = (*fakeRepository)(nil)` 在编译期断言接口实现一致。
- 只实现测试用到的方法，不补未使用的成员。
- 需要验证编排行为时记录调用次数或入参，如示例二的 `listCalls`。
- fake 与被测代码放在同一个测试文件里，不导出、不跨包复用；跨包复用会把它变成需要维护的共享资产。

反例：只为了断言「被调用一次」而为一个方法写几十行生成式 mock。手写三行 fake 就能覆盖，
且不引入依赖与生成步骤。

## React / TypeScript 测试

### 当前运行器

模板已接入 Vitest + jsdom + React Testing Library，`npm test` 单次执行，
`npm run test:watch` 进入监听。测试位于 `src/**/*.test.ts` 与 `src/**/*.test.tsx`，
`vitest.config.ts` 通过 `mergeConfig` 继承 Vite 配置，仅收集 `src/` 内的低层测试，
不收集 `e2e/` 的 Playwright Case。

`src/test/setup.ts` 加载 jest-dom matcher 并在每个测试后清理 DOM。测试显式导入
`describe`、`it`、`expect` 等 Vitest API，不开启全局测试变量。

前端 unit/component 可以登记为 `change-gate` Required；移除或替换运行器的项目仍须
先检查实际入口。没有运行器时登记 waiver、已执行的替代验证和遗留风险，不写成 PASS。
例如首页组件测试 Mock 服务层数据，证明展示与失败重试；它不证明真实 HTTP 或后端链路。

## 运行方式

### 后端

```bash
cd backend

make test
make check

go test ./... -count=1
go test ./internal/domain/... -run <TestName> -count=1
go test ./internal/application/sample/ -run TestServiceList -count=1 -v
go test ./... -race

make fmt
make lint
make lint-fix
```

说明：

- `make test` 等价于 `go test ./...`，命中测试缓存；改动后确认结果时用 `-count=1` 绕过缓存。
- `make check` 为 `fmt + lint + test + build`，是提交前的检查目标。
- 模板现有测试文件为 `internal/application/sample/service_test.go` 与
  `internal/interfaces/http/server_test.go`；`internal/domain/` 下暂无测试文件。
- 模板当前没有 `testing.Short()` 分支，`go test -short ./...` 不会跳过任何测试。
- 并发相关改动加 `-race`。
- `make lint` 通过
  `go run github.com/golangci/golangci-lint/v2/cmd/golangci-lint@v2.11.3` 执行，不需要全局安装。
- `_test.go` 豁免了 `cyclop`、`funlen`、`gocognit`、`gosec`、`nestif`、`wrapcheck`；
  `errcheck`、`lll`（120 字符）等仍然生效。

### 前端

```bash
cd frontend

npm run lint
npm run build

npm test
npm test -- src/components/Home.test.tsx
npm run test:watch
```

`npm run lint` 的匹配范围是 `src/**/*.{ts,tsx}`，测试文件也在其中。
`npm run build` 执行 `tsc && vite build`。

### 按需通道

`browser-ui` 与 `e2e` 不进入 `make check` 或 `npm test`。按
`openspec/docs/test-guides-convention.md` 记录触发条件、环境、命令与未运行风险，状态为
`NOT_RUN` 时不得写成 PASS。

系统 E2E 使用 `frontend/e2e/` 的 Playwright 入口：`cd frontend && npm run test:e2e -- --list`
核对选择集，再用 `npm run test:e2e -- e2e/system/<目标>.spec.ts` 执行。模板的
`STARTER-READ-001` 验证首页加载真实 Go API；Case 设计、远程环境写入与结果判定见
`.agents/skills/system-e2e/SKILL.md`。`--list` 只收集测试，不生成通过证据。

## 编写约定

Do：

- 测试名描述预期行为。
- 一个用例验证一个行为。
- 表驱动加 `t.Run`，子测试相互独立。
- 用 `t.Helper()`、`t.Cleanup()`、`t.TempDir()` 管理辅助逻辑与资源。
- 断言业务可观察结果。

Don't：

- 不引入第三方断言库或 mock 生成工具。
- 不在测试里使用 `time.Sleep`。等待异步结果用显式同步点。
- 不忽略错误返回值。`errcheck` 对 `_test.go` 同样生效。
- 不跨测试共享可变状态。
- 不把第三方库的行为当作本仓库行为来测。
- 不断言内部实现步骤（调用顺序、未导出字段取值）。未导出的纯函数可以在同包测试里直接测，
  但断言应落在可观察结果上。
