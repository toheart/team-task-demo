## Purpose

Define the mandatory testing layering, writing-order, test-double and continuous integration requirements for backend and frontend changes in this repository. The operational details, examples and commands live in `docs/testing.md`.
## Requirements
### Requirement: New behavior must be covered by tests written first or alongside implementation
Behavior changes MUST be driven by tests, and the writing order MUST match the target of the change.

#### Scenario: Implementing backend domain or application behavior
- **WHEN** a contributor adds or changes behavior in `internal/domain/` or `internal/application/`
- **THEN** the test MUST be written before the implementation
- **AND** the work MUST follow a red-green cycle in which the test fails first for the expected reason
- **AND** the failing assertion MUST express the business rule rather than the current implementation

#### Scenario: Implementing a custom frontend hook
- **WHEN** a contributor adds or changes a custom hook under `frontend/src/hooks/`
- **THEN** the test MUST be written before the implementation
- **AND** the hook MUST be driven through `renderHook` as its public entry point

#### Scenario: Implementing a React component
- **WHEN** a contributor adds or changes a React component
- **THEN** the observable behavior contract MUST be settled before tests are written
- **AND** the component change MUST NOT be required to start from a failing test
- **AND** tests MUST be added once the contract is stable

#### Scenario: Fixing a defect
- **WHEN** a defect is reported
- **THEN** a test that reproduces the defect MUST be added before the fix
- **AND** the test MUST fail before the fix and pass after it

### Requirement: Go tests must use the standard library testing package
Backend tests MUST use the Go standard library `testing` package with table-driven structure.

#### Scenario: Writing a backend test
- **WHEN** a Go test is authored or modified
- **THEN** it MUST use only the standard library `testing` package
- **AND** it MUST NOT depend on Ginkgo, Gomega, or any third-party assertion library
- **AND** the unique require entries of `backend/go.mod` MUST remain limited to the runtime dependencies already declared there

#### Scenario: Structuring a table-driven Go test
- **WHEN** a test covers multiple inputs, states, or boundary cases
- **THEN** it MUST be expressed as a table of cases iterated with `t.Run` subtests
- **AND** each subtest MUST be independent from the others
- **AND** tests that declare `t.Parallel()` MUST NOT share mutable state with other tests

#### Scenario: Using Go test helpers and cleanup
- **WHEN** a test needs shared setup or owns a resource
- **THEN** the helper function MUST call `t.Helper()`
- **AND** resource cleanup MUST be registered with `t.Cleanup()` or use `t.TempDir()`
- **AND** tests MUST NOT rely on `time.Sleep` to synchronize

### Requirement: Test files must stay colocated with the code they verify
Test files MUST live beside the code they cover and follow the repository naming convention.

#### Scenario: Adding backend test files
- **WHEN** a Go test is created
- **THEN** it MUST live in the same directory as the source file it covers
- **AND** it MUST use the `*_test.go` naming pattern
- **AND** it MUST use the same package as the code under test
- **AND** public functions and methods that are added or changed MUST have corresponding tests

#### Scenario: Adding frontend test files
- **WHEN** a frontend test is created
- **THEN** it MUST live beside the source file it covers under `frontend/src/`
- **AND** it MUST use the `*.test.ts` or `*.test.tsx` naming pattern

#### Scenario: Adding an HTTP endpoint
- **WHEN** a new API endpoint is introduced
- **THEN** a handler test that exercises the route through `httptest` MUST be added
- **AND** the test MUST verify the shared response envelope

### Requirement: Test doubles must be handwritten fakes by default
Backend tests MUST use small handwritten fakes for isolation instead of generated mock code.

#### Scenario: Isolating a repository dependency
- **WHEN** a test needs to isolate a dependency behind an interface
- **THEN** it MUST use a small handwritten fake implementing that interface
- **AND** the fake MUST assert interface conformance at compile time
- **AND** the fake MUST live in the test file that uses it

#### Scenario: Reusing a test double across packages
- **WHEN** a test double is needed by more than one package
- **THEN** the underlying interface MUST be narrowed before the double is shared
- **AND** the repository MUST NOT introduce a mock generation tool, a `.mockery.yaml` file, or a `mocks/` directory

### Requirement: Testing layers must follow the seven-layer contract
Changes MUST be mapped to the lowest effective layer among the seven defined layers.

#### Scenario: Selecting the lowest effective layer
- **WHEN** a change is mapped to a test layer
- **THEN** the layer MUST be one of `unit`, `component`, `app`, `api-smoke`, `integration`, `browser-ui`, or `e2e`
- **AND** the selected layer MUST be the lowest layer that can prove the assertion
- **AND** every layer above the lowest one MUST state a distinct fact that the lower layer cannot prove
- **AND** the same input combination MUST NOT be re-enumerated in a higher layer

#### Scenario: Selecting a frontend layer
- **WHEN** a frontend change is mapped to a test layer
- **THEN** the `component` layer MUST be selected when the change matches a React trigger listed in `.agents/skills/test-design/SKILL.md`
- **AND** behavior that jsdom cannot prove MUST be escalated to `browser-ui`

#### Scenario: Registering an on-demand channel
- **WHEN** a scenario requires `browser-ui` or `e2e`
- **THEN** it MUST be registered as `on-demand-browser` or `on-demand-system`
- **AND** it MUST NOT participate in the automatic delivery gate computation
- **AND** it MUST NOT be the only delivery proof for a P0 or P1 scenario
- **AND** its trigger condition, environment, command, and unexecuted risk MUST be recorded

### Requirement: Layers without an executable runner must be recorded as waivers
A layer MUST NOT be claimed as covered when the repository has no executable runner for it.

#### Scenario: The frontend test runner is not installed
- **WHEN** a frontend layer is planned while `frontend/package.json` declares no `scripts.test`
- **THEN** the layer MUST NOT be registered as a delivery-gate required layer
- **AND** it MUST be registered as a waiver with documented substitute verification and residual risk
- **AND** its evidence status MUST remain `NOT_RUN` and MUST NOT be reported as passing

#### Scenario: The layer runner is available
- **WHEN** a layer has an executable entry point, using `go test` for backend layers or `frontend/package.json` `scripts.test` for frontend layers
- **THEN** the layer MUST be eligible for registration as a delivery-gate required layer

#### Scenario: Substitute verification for a waived layer
- **WHEN** a waiver is recorded for a layer without a runner
- **THEN** the waiver MUST name the substitute verification actually performed
- **AND** the waiver MUST state the residual risk that the layer would have covered

### Requirement: Delivery-gate required tests must pass before delivery
A change MUST NOT be delivered while a delivery-gate required test is failing, skipped, or not executed.

#### Scenario: Computing the delivery gate
- **WHEN** the delivery gate is evaluated
- **THEN** every P0 and P1 scenario MUST appear in the scenario mapping
- **AND** the count of delivery-gate required tests MUST be greater than zero
- **AND** failed, skipped, and not-executed delivery-gate required tests MUST all be zero
- **AND** every waiver MUST record substitute verification, approval, and residual risk
- **AND** a delivery with zero executed cases, all-skipped cases, or only waivers MUST NOT be treated as passing

### Requirement: Repository test workflows must remain standardized
Backend and frontend test workflows MUST expose stable commands for contributors.

#### Scenario: Running backend tests
- **WHEN** a contributor runs the standard backend test workflow
- **THEN** the full backend suite MUST remain runnable through `cd backend && make test`
- **AND** a single package or test MUST remain runnable through `go test <package> -run <TestName> -count=1`
- **AND** the repository MUST NOT document Ginkgo CLI commands or a `make mock` target

#### Scenario: Running frontend tests
- **WHEN** a contributor runs the standard frontend test workflow
- **THEN** frontend tests MUST be runnable through `cd frontend && npm test -- <files>` once a runner is installed
- **AND** the repository MUST NOT document a frontend test command that no installed runner can execute

### Requirement: Continuous integration must pass make check
Backend changes MUST pass the repository check target before they are committed.

#### Scenario: Committing a backend change
- **WHEN** a backend change is prepared for commit
- **THEN** `cd backend && make check` MUST pass
- **AND** `make check` MUST remain composed of formatting, linting, testing, and building
- **AND** a change that fails linting MUST NOT be merged

#### Scenario: Committing a frontend change
- **WHEN** a frontend change is prepared for commit
- **THEN** `npm run lint` and `npm run build` MUST pass
- **AND** `npm test` MUST also pass once a frontend test runner is installed

### Requirement: Test cases must remain isolated and deterministic
Repository test cases MUST be readable, isolated, deterministic, and independent of execution order.

#### Scenario: Structuring individual tests
- **WHEN** a contributor writes or updates a repository test
- **THEN** the test name MUST describe the expected behavior
- **AND** each case MUST verify exactly one behavior
- **AND** tests MUST remain independent and MUST NOT share mutable state
- **AND** assertions MUST target observable results rather than internal implementation steps

#### Scenario: Avoiding test anti-patterns
- **WHEN** a contributor implements repository tests
- **THEN** tests MUST NOT rely on `time.Sleep` for synchronization
- **AND** tests MUST NOT ignore error return values
- **AND** tests MUST NOT assert the behavior of a third-party library as repository behavior
- **AND** tests MUST NOT depend on the execution order of other tests
