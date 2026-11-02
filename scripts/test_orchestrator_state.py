"""按交付契约验证门禁；所有状态与产物只写临时目录。"""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "orchestrator_state", Path(__file__).with_name("orchestrator-state.py")
)
state = importlib.util.module_from_spec(spec)
spec.loader.exec_module(state)


class GateTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(os.environ.get("TEMP", tempfile.gettempdir())) / "dsh-scratch/ai-template-tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name, value in {
            "REPO_ROOT": self.root,
            "CHANGES_DIR": self.root / "openspec/changes",
            "ARCHIVE_DIR": self.root / "openspec/changes/archive",
        }.items():
            replacement = patch.object(state, name, value)
            replacement.start()
            self.addCleanup(replacement.stop)
        self.change = state.change_dir("sample")
        self.change.mkdir(parents=True)
        output = patch.object(state, "print_json")
        output.start()
        self.addCleanup(output.stop)

    def run_command(self, *args):
        # 测试中的通过操作代表已获确认；单独用例验证缺少确认标记时拒绝。
        if args[0] == "set-gate" and args[4] == "passed":
            args = (*args, "--confirmed")
        parsed = state.build_parser().parse_args(args)
        parsed.handler(parsed)

    def write(self, name, content):
        path = self.change / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def ready_design(self):
        self.write("proposal.md", "## Why\n明确的需求\n")
        self.write("design.md", """## 影响端与验收契约
affected_ends:
  backend: true
  frontend: false
| 场景 ID | 验收行为（用户可观察） | 影响端 | 建议最低测试层 |
|---|---|---|---|
| AS-1 | 返回合法数据 | backend | unit |
## 实现反模式（SubAgent 必读）
1. 不绕过输入校验。
## Review Checklist（本次变更专用）
- [ ] 返回值符合接口契约？
## 错误响应契约（design-review 产出，implement 必读）
非法输入返回 400 INVALID_PARAMS。
""")
        self.write("tasks.md", "- [ ] 1.1 [L1] [后端] 修改目标字段；验证 go test\n")
        self.write(".orchestrator/design-review.md", "结论: APPROVE\n")
        data = state.base_state("design", "sample", False)
        for stage in ["explore", "propose", "design-review"]:
            data["stages"][stage] = "completed"
        state.save_state("design", "sample", data)

    def ready_execution(self):
        self.ready_design()
        self.run_command("set-gate", "design", "sample", "gate-design", "passed")
        self.run_command("write-handoff", "sample")
        data = state.base_state("execution", "sample", False)
        for stage in ["test-design", "implement", "code-review", "test-run"]:
            data["stages"][stage] = "completed"
        state.save_state("execution", "sample", data)
        for name in ["design.md", "tasks.md"]:
            path = self.change / name
            path.write_text(path.read_text(encoding="utf-8").replace("[ ]", "[x]"), encoding="utf-8")
        test_file = self.root / "backend/sample_test.go"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("package sample\n", encoding="utf-8")
        self.evidence = """## 场景映射
| 场景 ID | 层级 | Required/Optional | 执行通道 | 独有证明 / 运行依赖 | 测试文件/任务 | 计划命令 | 状态 |
|---|---|---|---|---|---|---|---|
| AS-1 | unit | Required | change-gate | 输入校验；Go | backend/sample_test.go | go test | PASS |
## 分层结果
| 层级 | Required | Executed | PASS | FAIL | SKIP | NOT_RUN | 命令 | 环境 |
|---|---:|---:|---:|---:|---:|---:|---|---|
| Backend Unit | 1 | 1 | 1 | 0 | 0 | 0 | go test | local |
## Waiver 与遗留风险
| 场景 ID | 原因 | 替代验证 | 批准/确认 | 遗留风险 |
|---|---|---|---|---|
"""
        self.write(".orchestrator/test-evidence.md", self.evidence)

    def delivery(self):
        self.run_command("set-gate", "execution", "sample", "gate-delivery", "passed")

    def test_delivery_rejects_pending_stages_even_in_trust_mode(self):
        self.ready_execution()
        data = state.base_state("execution", "sample", False)
        state.save_state("execution", "sample", data)
        self.run_command("init-execution", "sample", "--trust")
        with self.assertRaises(SystemExit):
            self.delivery()

    def test_non_trust_gate_requires_confirmation_marker(self):
        self.ready_execution()
        parsed = state.build_parser().parse_args(["set-gate", "execution", "sample", "gate-delivery", "passed"])
        with self.assertRaises(SystemExit):
            parsed.handler(parsed)

    def test_handoff_requires_passed_design_gate(self):
        self.ready_design()
        with self.assertRaises(SystemExit):
            self.run_command("write-handoff", "sample")

    def test_design_gate_rejects_empty_artifact(self):
        self.ready_design()
        self.write("design.md", "<!-- 未填写 -->")
        with self.assertRaises(SystemExit):
            self.run_command("set-gate", "design", "sample", "gate-design", "passed")

    def test_handoff_validation_rejects_emptied_artifact(self):
        self.ready_execution()
        self.write("proposal.md", "")
        with self.assertRaises(SystemExit):
            self.run_command("validate-handoff", "sample", "--allow-status", "execution_in_progress", "--check-artifacts")

    def test_valid_delivery_passes(self):
        self.ready_execution()
        self.delivery()
        self.assertEqual(state.load_json(state.state_path("execution", "sample"))["stages"]["gate-delivery"], "completed")

    def test_delivery_rejects_missing_evidence(self):
        self.ready_execution()
        (self.change / ".orchestrator/test-evidence.md").unlink()
        with self.assertRaises(SystemExit):
            self.delivery()

    def test_required_fail_skip_and_not_run_block_delivery(self):
        for result in ["FAIL", "SKIP", "NOT_RUN"]:
            with self.subTest(result=result):
                self.ready_execution()
                self.write(".orchestrator/test-evidence.md", self.evidence.replace("| PASS |", f"| {result} |"))
                with self.assertRaises(SystemExit):
                    self.delivery()

    def test_delivery_rejects_zero_required_tests(self):
        self.ready_execution()
        self.write(".orchestrator/test-evidence.md", self.evidence.replace("Required | change-gate", "Optional | change-gate").replace("| 1 | 1 | 1 |", "| 0 | 1 | 1 |"))
        with self.assertRaises(SystemExit):
            self.delivery()

    def test_delivery_rejects_inconsistent_counts(self):
        self.ready_execution()
        self.write(".orchestrator/test-evidence.md", self.evidence.replace("| 1 | 1 | 1 |", "| 1 | 0 | 1 |"))
        with self.assertRaises(SystemExit):
            self.delivery()

    def test_delivery_rejects_unmapped_acceptance_scenario(self):
        self.ready_execution()
        self.write(".orchestrator/test-evidence.md", self.evidence.replace("AS-1", "AS-2"))
        with self.assertRaises(SystemExit):
            self.delivery()

    def test_delivery_requires_completed_tasks_and_review_checklist(self):
        for name in ["tasks.md", "design.md"]:
            with self.subTest(name=name):
                self.ready_execution()
                path = self.change / name
                self.write(name, path.read_text(encoding="utf-8").replace("[x]", "[ ]"))
                with self.assertRaises(SystemExit):
                    self.delivery()

    def test_on_demand_not_run_does_not_block_delivery(self):
        self.ready_execution()
        evidence = self.evidence.replace("## 分层结果", "| AS-1 | e2e | Required | on-demand-system | 真实链路 | frontend/e2e/system/sample.spec.ts | npm run test:e2e | NOT_RUN |\n## 分层结果")
        evidence = evidence.replace("## Waiver", "| System E2E | 1 | 0 | 0 | 0 | 0 | 1 | npm run test:e2e | dev |\n## Waiver")
        self.write(".orchestrator/test-evidence.md", evidence)
        self.delivery()

    def test_set_stage_cannot_bypass_gate(self):
        self.ready_execution()
        with self.assertRaises(SystemExit):
            self.run_command("set-stage", "execution", "sample", "gate-delivery", "completed")

    def test_archive_cannot_start_before_delivery(self):
        self.ready_execution()
        with self.assertRaises(SystemExit):
            self.run_command("set-stage", "execution", "sample", "archive", "active")

    def test_upstream_retry_invalidates_gate_and_handoff(self):
        self.ready_execution()
        self.run_command("set-stage", "design", "sample", "propose", "active")
        handoff = state.load_json(state.handoff_path("sample"))
        self.assertEqual(handoff["status"], "needs_design_revision")
        self.assertFalse(handoff["design_gate_passed"])

    def test_counts_cannot_claim_pass_for_a_different_layer(self):
        self.ready_execution()
        self.write(".orchestrator/test-evidence.md", self.evidence.replace("Backend Unit", "Frontend Component"))
        with self.assertRaises(SystemExit):
            self.delivery()

    def test_trust_cannot_bypass_required_failure(self):
        self.ready_execution()
        data = state.load_json(state.state_path("execution", "sample"))
        data["trust"] = True
        state.save_state("execution", "sample", data)
        self.write(".orchestrator/test-evidence.md", self.evidence.replace("| PASS |", "| FAIL |"))
        with self.assertRaises(SystemExit):
            self.delivery()

    def test_paused_failure_requires_explicit_resume(self):
        self.ready_execution()
        self.run_command("set-stage", "execution", "sample", "test-run", "failed", "--overall-status", "paused", "--failure-class", "business", "--reason", "Input validation failed")
        with self.assertRaises(SystemExit):
            self.run_command("set-stage", "execution", "sample", "implement", "active", "--trust")
        self.run_command("set-stage", "execution", "sample", "implement", "active", "--resume-confirmed", "--reason", "User approved local fix")
        data = state.load_json(state.state_path("execution", "sample"))
        self.assertFalse(data["requires_confirmation"])
        self.assertEqual(data["stages"]["test-run"], "pending")
        self.assertEqual(data["resume_decision"]["reason"], "User approved local fix")

    def test_overall_completed_cannot_bypass_pending_stages(self):
        self.ready_execution()
        with self.assertRaises(SystemExit):
            self.run_command("set-stage", "execution", "sample", "implement", "completed", "--overall-status", "completed")

    def test_waiver_requires_passed_substitute_verification(self):
        self.ready_execution()
        design = (self.change / "design.md").read_text(encoding="utf-8")
        self.write("design.md", design.replace("## 实现反模式", "| AS-2 | 展示权限提示 | frontend | component |\n## 实现反模式"))
        evidence = self.evidence.replace("## 分层结果", "| AS-2 | component | Optional | change-gate | 权限提示 | manual | manual | NOT_RUN |\n## 分层结果")
        evidence = evidence.replace("## Waiver", "| Frontend Component | 0 | 0 | 0 | 0 | 0 | 1 | manual | local |\n## Waiver")
        evidence = evidence.replace("| 替代验证 | 批准/确认 |", "| 替代验证 | 替代验证结果 | 批准/确认 |").replace("|---|---|---|---|---|\n", "|---|---|---|---|---|---|\n")
        evidence += "| AS-2 | 外部依赖不可用 | 人工验证权限提示 | NOT_RUN | 用户批准 | 未覆盖自动回归 |\n"
        self.write(".orchestrator/test-evidence.md", evidence)
        with self.assertRaises(SystemExit):
            self.delivery()
        self.write(".orchestrator/test-evidence.md", evidence.replace("人工验证权限提示 | NOT_RUN", "人工验证权限提示 | PASS"))
        self.delivery()

    def test_p2_optional_case_can_remain_not_run(self):
        self.ready_execution()
        design = (self.change / "design.md").read_text(encoding="utf-8")
        design = design.replace("| 场景 ID |", "| 场景 ID | 优先级 |").replace("|---|---|---|---|", "|---|---|---|---|---|").replace("| AS-1 |", "| AS-1 | P1 |")
        self.write("design.md", design.replace("## 实现反模式", "| AS-2 | P2 | 次要提示 | frontend | component |\n## 实现反模式"))
        evidence = self.evidence.replace("## 分层结果", "| AS-2 | component | Optional | change-gate | 次要提示 | manual | manual | NOT_RUN |\n## 分层结果")
        evidence = evidence.replace("## Waiver", "| Frontend Component | 0 | 0 | 0 | 0 | 0 | 1 | manual | local |\n## Waiver")
        self.write(".orchestrator/test-evidence.md", evidence)
        self.delivery()

    def test_named_structure_check_rejects_gate_before_predecessors(self):
        data = state.base_state("execution", "sample", False)
        data["stages"]["gate-delivery"] = "completed"
        state.save_state("execution", "sample", data)
        with self.assertRaises(SystemExit):
            self.run_command("validate-structure", "sample")

    def test_execution_cannot_start_without_handoff(self):
        self.ready_design()
        self.run_command("set-gate", "design", "sample", "gate-design", "passed")
        with self.assertRaises(SystemExit):
            self.run_command("init-execution", "sample")

    def test_execution_does_not_override_design_revision(self):
        self.ready_execution()
        self.run_command("set-stage", "design", "sample", "propose", "active")
        with self.assertRaises(SystemExit):
            self.run_command("init-execution", "sample")
        self.assertEqual(state.load_json(state.handoff_path("sample"))["status"], "needs_design_revision")

    def test_completed_archive_keeps_state_in_archived_directory(self):
        self.ready_execution()
        self.delivery()
        self.run_command("set-stage", "execution", "sample", "archive", "active")
        archived = state.ARCHIVE_DIR / "2026-10-09-sample"
        archived.parent.mkdir(parents=True)
        self.change.rename(archived)
        self.run_command("set-stage", "execution", "sample", "archive", "completed")
        self.assertFalse(self.change.exists())
        self.assertEqual(state.load_json(archived / ".orchestrator/handoff.json")["status"], "completed")


if __name__ == "__main__":
    unittest.main()
