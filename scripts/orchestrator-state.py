#!/usr/bin/env python3
"""Feature 编排共享状态脚本。

设计阶段（feature-design）与执行阶段（feature-exec）通过本脚本维护
`openspec/changes/<change-name>/.orchestrator/` 下的状态与交接文件。
状态只允许由本脚本写入，不手写 JSON。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGES_DIR = REPO_ROOT / "openspec" / "changes"
ARCHIVE_DIR = CHANGES_DIR / "archive"
ARCHIVE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")
ARCHIVE_PREFIX_LEN = 11
_ARCHIVE_NOTE_EMITTED: set[str] = set()

DESIGN_STAGES = [
    "explore",
    "propose",
    "design-review",
    "gate-design",
    "write-handoff",
]

EXECUTION_STAGES = [
    "test-design",
    "implement",
    "code-review",
    "test-run",
    "gate-delivery",
    "archive",
]

ROLE_CONFIG = {
    "design": {
        "owner_ide": "cursor",
        "file_name": "design-state.json",
        "stages": DESIGN_STAGES,
        "skill_name": "feature-design",
    },
    "execution": {
        "owner_ide": "claude-code",
        "file_name": "execution-state.json",
        "stages": EXECUTION_STAGES,
        "skill_name": "feature-exec",
    },
}

STAGE_STATUSES = {"pending", "active", "completed", "failed", "skipped"}
GATE_RESULTS = {"passed", "failed", "skipped"}
FAILURE_CLASSES = {"business", "test_asset", "environment", "fixture"}

# 设计阶段不得包含的产物阶段：需求摘要与测试设计分别由 proposal/design/tasks
# 和执行侧 test-design 承担，重复登记会让状态机出现两个事实来源。
FORBIDDEN_DESIGN_STAGES = {"brief", "test-design"}
REQUIRED_HANDOFF_ARTIFACTS = {"proposal.md", "design.md", "tasks.md"}
FORBIDDEN_HANDOFF_OPTIONAL_ARTIFACTS = {".orchestrator/brief.md"}

CURRENT_SCHEMA_VERSION = 2


def now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def change_dir(change_name: str) -> Path:
    """定位 change 目录：优先活跃目录，其次已归档的 `<YYYY-MM-DD>-<name>`。

    `openspec archive` 会把 `openspec/changes/<name>/` 整体移到
    `openspec/changes/archive/<YYYY-MM-DD>-<name>/`。若此处只认活跃目录，
    归档后再跑 `set-stage` 会重建一个空的活跃目录：
    写进去的状态文件没有历史（阶段全 pending），而归档目录中的真实历史被忽略；
    读取类命令（`validate-structure`）也会因文件不存在而静默通过。
    """
    active = CHANGES_DIR / change_name
    if active.exists():
        return active
    if ARCHIVE_DIR.is_dir():
        # 逐个目录精确比对后缀，避免把 change_name 当 glob 模式解释。
        matches = sorted(
            entry
            for entry in ARCHIVE_DIR.iterdir()
            if entry.is_dir()
            and ARCHIVE_PREFIX_RE.match(entry.name)
            and entry.name[ARCHIVE_PREFIX_LEN:] == change_name
        )
        if matches:
            resolved = matches[-1]
            if change_name not in _ARCHIVE_NOTE_EMITTED:
                _ARCHIVE_NOTE_EMITTED.add(change_name)
                print(f"note: '{change_name}' is archived; using {resolved}", file=sys.stderr)
            return resolved
    return active


def orchestrator_dir(change_name: str) -> Path:
    return change_dir(change_name) / ".orchestrator"


def state_path(role: str, change_name: str) -> Path:
    return orchestrator_dir(change_name) / ROLE_CONFIG[role]["file_name"]


def handoff_path(change_name: str) -> Path:
    return orchestrator_dir(change_name) / "handoff.json"


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(path)


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"invalid json in {path}: {exc}")


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def ensure_role(role: str) -> None:
    if role not in ROLE_CONFIG:
        fail(f"unsupported role: {role}")


def ensure_stage(role: str, stage: str) -> None:
    if stage not in ROLE_CONFIG[role]["stages"]:
        fail(f"unknown stage for role '{role}': {stage}")


def base_state(role: str, change_name: str, trust: bool) -> dict[str, Any]:
    return {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "change_name": change_name,
        "role": role,
        "owner_ide": ROLE_CONFIG[role]["owner_ide"],
        "skill": ROLE_CONFIG[role]["skill_name"],
        "trust": trust,
        "status": "active",
        "current_stage": "",
        "stages": {stage: "pending" for stage in ROLE_CONFIG[role]["stages"]},
        "updated_at": now_iso(),
    }


def normalize_active_stage(data: dict[str, Any]) -> bool:
    """保证状态中最多只有一个 active，并以 current_stage 为权威。"""
    stages = data.get("stages", {})
    active_stages = [name for name, status in stages.items() if status == "active"]
    if len(active_stages) <= 1:
        return False

    current_stage = data.get("current_stage", "")
    keep = current_stage if current_stage in active_stages else active_stages[0]
    for stage in active_stages:
        if stage != keep:
            stages[stage] = "pending"
    data["current_stage"] = keep
    return True


def migrate_state(role: str, data: dict[str, Any]) -> bool:
    """按需迁移被恢复的旧状态；不批量回写历史 change。"""
    expected_stages = ROLE_CONFIG[role]["stages"]
    old_stages = data.get("stages", {})
    if data.get("schema_version") == CURRENT_SCHEMA_VERSION and list(old_stages) == expected_stages:
        return normalize_active_stage(data)

    migrated_stages = {stage: old_stages.get(stage, "pending") for stage in expected_stages}
    previous_version = data.get("schema_version", 1)
    data["schema_version"] = CURRENT_SCHEMA_VERSION
    data["migrated_from_schema_version"] = previous_version
    data["stages"] = migrated_stages

    current_stage = data.get("current_stage", "")
    if current_stage not in migrated_stages or migrated_stages.get(current_stage) != "active":
        current_stage = next(
            (stage for stage, status in migrated_stages.items() if status == "active"),
            "",
        )
    if not current_stage:
        current_stage = next(
            (stage for stage, status in migrated_stages.items() if status == "pending"),
            "",
        )
    data["current_stage"] = current_stage
    normalize_active_stage(data)
    data["status"] = recompute_overall_status(data)
    return True


def ensure_state(
    role: str,
    change_name: str,
    *,
    trust: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    ensure_role(role)
    path = state_path(role, change_name)
    if path.exists() and not force:
        data = load_json(path)
        changed = migrate_state(role, data)
        if trust and not data.get("trust"):
            data["trust"] = True
            changed = True
        if changed:
            data["updated_at"] = now_iso()
            atomic_write_json(path, data)
        return data
    data = base_state(role, change_name, trust)
    atomic_write_json(path, data)
    return data


def save_state(role: str, change_name: str, data: dict[str, Any]) -> None:
    data["updated_at"] = now_iso()
    atomic_write_json(state_path(role, change_name), data)
    if role == "execution":
        sync_handoff_from_execution(change_name, data)


def recompute_overall_status(data: dict[str, Any]) -> str:
    values = list(data["stages"].values())
    if any(value == "failed" for value in values):
        return "failed"
    if values and all(value in {"completed", "skipped"} for value in values):
        return "completed"
    if any(value == "active" for value in values):
        return "active"
    if any(value == "pending" for value in values):
        return "active"
    return data.get("status", "active")


def sync_handoff_from_execution(change_name: str, execution_state: dict[str, Any]) -> None:
    path = handoff_path(change_name)
    if not path.exists():
        return
    handoff = load_json(path)
    if handoff.get("status") in {"draft", "needs_design_revision"}:
        return
    if execution_state.get("status") == "completed":
        target_status = "completed"
    else:
        target_status = "execution_in_progress"
    if handoff.get("status") != target_status:
        handoff["status"] = target_status
        handoff["updated_at"] = now_iso()
        atomic_write_json(path, handoff)


def init_state_command(args: argparse.Namespace) -> None:
    role = args.role
    if role == "execution":
        validate_execution_input(args.change_name)
    data = ensure_state(role, args.change_name, trust=args.trust, force=args.force)
    if role == "execution":
        sync_handoff_from_execution(args.change_name, data)
    print_json(
        {
            "status": "ok",
            "role": role,
            "change_name": args.change_name,
            "path": str(state_path(role, args.change_name)),
        }
    )


def read_artifact(change_name: str, relative_path: str) -> str:
    path = change_dir(change_name) / relative_path
    if not path.is_file():
        fail(f"missing artifact: {relative_path}")
    content = re.sub(r"<!--.*?-->", "", path.read_text(encoding="utf-8"), flags=re.S).strip()
    if not content:
        fail(f"empty artifact: {relative_path}")
    return content


def table_rows(content: str, first_header: str) -> list[dict[str, str]]:
    """读取契约中的 Markdown 表；支持单元格内转义的竖线。"""
    headers: list[str] = []
    rows: list[dict[str, str]] = []
    for line in content.splitlines():
        if not line.strip().startswith("|"):
            headers = []
            continue
        cells = [cell.strip().strip("`") for cell in re.split(r"(?<!\\)\|", line.strip())[1:-1]]
        if cells and cells[0] == first_header:
            headers = cells
        elif headers and cells and not all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            if len(cells) != len(headers):
                fail(f"malformed table row: {line}")
            rows.append(dict(zip(headers, cells)))
    return rows


def require_predecessors(role: str, data: dict[str, Any], stage: str) -> None:
    for predecessor in ROLE_CONFIG[role]["stages"][:ROLE_CONFIG[role]["stages"].index(stage)]:
        status = data["stages"].get(predecessor)
        if status != "completed" and not (predecessor == "explore" and status == "skipped"):
            fail(f"{stage} requires completed stage: {predecessor}")


def validate_design_artifacts(change_name: str) -> None:
    for name in REQUIRED_HANDOFF_ARTIFACTS:
        read_artifact(change_name, name)
    design = read_artifact(change_name, "design.md")
    for heading in ["影响端与验收契约", "实现反模式（SubAgent 必读）", "Review Checklist（本次变更专用）", "错误响应契约"]:
        section = re.search(rf"^## {re.escape(heading)}[^\n]*\n(.*?)(?=^## |\Z)", design, re.M | re.S)
        if section is None or not section.group(1).strip():
            fail(f"design.md requires populated section: {heading}")
    scenarios = table_rows(design, "场景 ID")
    if not scenarios or any(not row.get("验收行为（用户可观察）") for row in scenarios):
        fail("design.md requires observable acceptance scenarios")
    review = read_artifact(change_name, ".orchestrator/design-review.md")
    if not re.search(r"结论\s*[:：]\s*APPROVE\b", review):
        fail("design review must conclude APPROVE")


def validate_design_ready(change_name: str) -> None:
    data = load_json(state_path("design", change_name))
    require_predecessors("design", data, "write-handoff")
    if not any(item.get("gate") == "gate-design" and item.get("result") == "passed" for item in data.get("gate_decisions", [])):
        fail("handoff requires a passed design gate decision")
    validate_design_artifacts(change_name)


def validate_delivery(change_name: str) -> None:
    validate_execution_input(change_name)
    for name in ["tasks.md", "design.md"]:
        content = read_artifact(change_name, name)
        if name == "design.md":
            content = content.split("## Review Checklist（本次变更专用）", 1)[1].split("\n## ", 1)[0]
        if not re.search(r"^- \[[xX]\]", content, re.M) or re.search(r"^- \[ \]", content, re.M):
            fail(f"incomplete checklist: {name}")

    evidence = read_artifact(change_name, ".orchestrator/test-evidence.md")
    mapping = table_rows(evidence.split("## 分层结果", 1)[0], "场景 ID")
    required = [row for row in mapping if row.get("Required/Optional") == "Required" and row.get("执行通道") == "change-gate"]
    if not required:
        fail("delivery requires at least one change-gate Required test")
    for row in required:
        if row.get("状态") != "PASS":
            fail(f"required test is not PASS: {row.get('场景 ID')}")
        if row.get("层级") in {"browser-ui", "e2e"}:
            fail("browser-ui/e2e cannot be used as change-gate proof")
        if not row.get("计划命令") or not row.get("独有证明 / 运行依赖"):
            fail("required test needs a command and distinct proof")
        # 交付时测试文件必须已经存在，不能仍是写作任务。
        for test_path in row.get("测试文件/任务", "").split(","):
            path = (REPO_ROOT / test_path.strip().strip("`")).resolve()
            if not path.is_relative_to(REPO_ROOT.resolve()) or not path.is_file():
                fail(f"missing required test file: {test_path}")

    acceptance = table_rows(read_artifact(change_name, "design.md"), "场景 ID")
    scenarios = {row["场景 ID"] for row in acceptance}
    mapped = {row.get("场景 ID") for row in mapping}
    if scenarios - mapped:
        fail(f"unmapped acceptance scenarios: {sorted(scenarios - mapped)}")
    waiver_section = evidence.split("## Waiver 与遗留风险", 1)[-1] if "## Waiver 与遗留风险" in evidence else ""
    waivers = table_rows(waiver_section, "场景 ID")
    for row in waivers:
        if not all(row.get(field) for field in ["原因", "替代验证", "批准/确认", "遗留风险"]) or row.get("替代验证结果") != "PASS":
            fail("waiver requires substitute verification, approval and residual risk")
    covered = {row.get("场景 ID") for row in required} | {row.get("场景 ID") for row in waivers}
    # 旧验收矩阵未标注优先级时按 P1 校验，避免缺省字段绕过门禁。
    for row in acceptance:
        priority = row.get("优先级", "P1")
        if priority not in {"P0", "P1", "P2"}:
            fail("acceptance priority must be P0, P1 or P2")
        if priority != "P2" and row["场景 ID"] not in covered:
            fail("P0/P1 scenarios require change-gate proof or an approved waiver")

    results = table_rows(evidence, "层级")
    if not results:
        fail("missing layer results")
    def layer_key(label: str) -> str:
        return label.lower().removeprefix("frontend ").removeprefix("backend ").replace("system e2e", "e2e").replace("browser ui", "browser-ui").replace("api smoke", "api-smoke")

    actual: dict[str, dict[str, int]] = {}
    for row in results:
        try:
            counts = {key: int(row[key]) for key in ["Required", "Executed", "PASS", "FAIL", "SKIP", "NOT_RUN"]}
        except (KeyError, ValueError):
            fail("invalid layer result counts")
        if min(counts.values()) < 0 or counts["Executed"] != counts["PASS"] + counts["FAIL"] + counts["SKIP"]:
            fail("inconsistent layer result counts")
        if not row.get("命令") or not row.get("环境"):
            fail("layer results require actual command and environment")
        key = layer_key(row["层级"])
        total = actual.setdefault(key, {field: 0 for field in counts})
        for field, count in counts.items():
            total[field] += count
    expected: dict[str, dict[str, int]] = {}
    for row in mapping:
        key = layer_key(row.get("层级", ""))
        status = row.get("状态")
        if key not in {"unit", "component", "app", "api-smoke", "integration", "browser-ui", "e2e"} or status not in {"PASS", "FAIL", "SKIP", "NOT_RUN"}:
            fail("invalid mapping layer or result")
        if row.get("Required/Optional") not in {"Required", "Optional"} or row.get("执行通道") not in {"change-gate", "on-demand-browser", "on-demand-system"}:
            fail("invalid mapping requirement or execution channel")
        total = expected.setdefault(key, {field: 0 for field in ["Required", "Executed", "PASS", "FAIL", "SKIP", "NOT_RUN"]})
        total["Required"] += row["Required/Optional"] == "Required"
        total["Executed"] += status != "NOT_RUN"
        total[status] += 1
    if actual != expected:
        fail("layer result counts do not match scenario mapping")


def validate_execution_input(change_name: str) -> None:
    validate_design_ready(change_name)
    design = load_json(state_path("design", change_name))
    handoff = load_json(handoff_path(change_name))
    if design["stages"].get("write-handoff") != "completed":
        fail("execution requires completed write-handoff")
    if handoff.get("change_name") != change_name or handoff.get("design_gate_passed") is not True:
        fail("invalid design handoff")
    if handoff.get("status") not in {"design_ready", "execution_in_progress", "completed"}:
        fail("handoff is not ready for execution")
    if set(handoff.get("required_artifacts", [])) != REQUIRED_HANDOFF_ARTIFACTS:
        fail("handoff must require exactly proposal.md, design.md and tasks.md")


def set_stage_command(args: argparse.Namespace) -> None:
    role = args.role
    ensure_role(role)
    ensure_stage(role, args.stage)
    if args.status not in STAGE_STATUSES:
        fail(f"invalid stage status: {args.status}")

    data = ensure_state(role, args.change_name, trust=args.trust)

    if data.get("requires_confirmation") and args.status in {"active", "completed"}:
        if not args.resume_confirmed or args.status != "active" or not args.reason:
            fail("paused failure requires --resume-confirmed and --reason to activate a stage")
    if args.stage.startswith("gate-") and args.status in {"completed", "skipped"}:
        fail("gate decisions must use set-gate; gates cannot be skipped")
    if args.status == "skipped" and args.stage != "explore":
        fail("only explore may be skipped")
    if args.status in {"active", "completed"}:
        require_predecessors(role, data, args.stage)
        if role == "execution":
            validate_execution_input(args.change_name)
    if args.stage == "write-handoff" and args.status == "completed":
        fail("handoff completion must use write-handoff")
    if role == "execution" and args.stage == "archive" and args.status in {"active", "completed"}:
        validate_delivery(args.change_name)

    if args.status == "active":
        # 激活某阶段时，把其他 active 阶段和它下游已结束的阶段重置为 pending，
        # 避免出现「两个 active」或「下游已完成但上游刚回退」的非法组合。
        stage_order = ROLE_CONFIG[role]["stages"]
        target_index = stage_order.index(args.stage)
        for index, stage in enumerate(stage_order):
            if stage == args.stage:
                continue
            if data["stages"][stage] == "active" or (
                index > target_index
                and data["stages"][stage] in {"completed", "failed", "skipped"}
            ):
                data["stages"][stage] = "pending"
        data["stages"][args.stage] = args.status
        data["current_stage"] = args.stage
        if data.get("requires_confirmation"):
            data["resume_decision"] = {"reason": args.reason, "recorded_at": now_iso()}
        data["requires_confirmation"] = False
        data["gate_decisions"] = [item for item in data.get("gate_decisions", []) if item.get("gate") in stage_order and stage_order.index(item["gate"]) < target_index]
        if role == "design" and handoff_path(args.change_name).exists():
            handoff = load_json(handoff_path(args.change_name))
            handoff.update(status="needs_design_revision", design_gate_passed=False)
            atomic_write_json(handoff_path(args.change_name), handoff)
    else:
        data["stages"][args.stage] = args.status

    if args.overall_status == "completed" and recompute_overall_status(data) != "completed":
        fail("overall completion requires every mandatory stage to be completed")

    if args.overall_status == "paused":
        if not args.failure_class or not args.reason:
            fail("paused stage requires --failure-class and --reason")
        if args.failure_class not in FAILURE_CLASSES:
            fail(f"invalid failure class: {args.failure_class}")
        data["failure_cycle"] = int(data.get("failure_cycle", 0)) + 1
        data["requires_confirmation"] = True
        data["last_failure"] = {
            "stage": args.stage,
            "class": args.failure_class,
            "reason": args.reason,
            "recorded_at": now_iso(),
        }
        data["current_stage"] = args.stage
    elif data.get("current_stage") == args.stage and args.status in {
        "completed",
        "failed",
        "skipped",
    }:
        next_pending = next(
            (name for name, status in data["stages"].items() if status == "pending"),
            "",
        )
        data["current_stage"] = next_pending

    if args.overall_status:
        data["status"] = args.overall_status
    else:
        data["status"] = recompute_overall_status(data)

    if args.trust:
        data["trust"] = True

    save_state(role, args.change_name, data)
    print_json(
        {
            "status": "ok",
            "role": role,
            "change_name": args.change_name,
            "stage": args.stage,
            "stage_status": args.status,
            "state_path": str(state_path(role, args.change_name)),
        }
    )


def set_gate_command(args: argparse.Namespace) -> None:
    role = args.role
    ensure_role(role)
    ensure_stage(role, args.gate)
    if not args.gate.startswith("gate-") or args.result == "skipped":
        fail("set-gate requires a gate stage and gates cannot be skipped")
    if args.result not in GATE_RESULTS:
        fail(f"invalid gate result: {args.result}")

    data = ensure_state(role, args.change_name, trust=args.trust)
    if args.result == "passed":
        if not data.get("trust") and not args.confirmed:
            fail("non-trust gate requires --confirmed after explicit user approval")
        require_predecessors(role, data, args.gate)
        if data.get("requires_confirmation"):
            fail("paused failure must be resolved before passing a gate")
        if role == "design":
            validate_design_artifacts(args.change_name)
        else:
            validate_delivery(args.change_name)
    gate_history = data.setdefault("gate_decisions", [])
    gate_history = [item for item in gate_history if item.get("gate") != args.gate]
    record: dict[str, Any] = {
        "gate": args.gate,
        "result": args.result,
        "decided_at": now_iso(),
        "confirmed": args.confirmed,
        "trust": bool(data.get("trust")),
    }
    if args.reason:
        record["reason"] = args.reason
    gate_history.append(record)
    data["gate_decisions"] = gate_history

    data["stages"][args.gate] = (
        "completed"
        if args.result == "passed"
        else "skipped"
        if args.result == "skipped"
        else "failed"
    )
    data["status"] = recompute_overall_status(data)
    if data.get("current_stage") == args.gate and data["stages"][args.gate] != "active":
        next_pending = next(
            (name for name, status in data["stages"].items() if status == "pending"),
            "",
        )
        data["current_stage"] = next_pending
    save_state(role, args.change_name, data)

    if role == "design" and args.result == "failed":
        handoff_file = handoff_path(args.change_name)
        if handoff_file.exists():
            handoff = load_json(handoff_file)
            handoff["status"] = "needs_design_revision"
            handoff["design_gate_passed"] = False
            handoff["updated_at"] = now_iso()
            atomic_write_json(handoff_file, handoff)

    print_json(
        {
            "status": "ok",
            "role": role,
            "change_name": args.change_name,
            "gate": args.gate,
            "result": args.result,
        }
    )


def write_handoff_command(args: argparse.Namespace) -> None:
    ensure_state("design", args.change_name, trust=args.trust)
    validate_design_ready(args.change_name)
    optional_artifacts = args.optional or []
    required_artifacts = args.required or ["proposal.md", "design.md", "tasks.md"]

    if set(required_artifacts) != REQUIRED_HANDOFF_ARTIFACTS:
        fail("handoff must require exactly proposal.md, design.md and tasks.md")

    forbidden_optional = sorted(
        FORBIDDEN_HANDOFF_OPTIONAL_ARTIFACTS
        & set(str(item) for item in optional_artifacts)
    )
    if forbidden_optional:
        fail(f"handoff optional artifacts contain deprecated files: {forbidden_optional}")
    if args.status == "design_ready" and not args.design_gate_passed:
        fail("design_ready handoff requires design_gate_passed=true")

    payload = {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "change_name": args.change_name,
        "status": args.status,
        "design_gate_passed": args.design_gate_passed,
        "producer": {
            "ide": args.producer_ide,
            "skill": args.producer_skill,
            "updated_at": now_iso(),
        },
        "required_artifacts": required_artifacts,
        "optional_artifacts": optional_artifacts,
        "executor_notes": args.executor_note or [],
        "pending_risks": args.pending_risk or [],
        "gate_decisions": args.gate_decision or [],
    }
    atomic_write_json(handoff_path(args.change_name), payload)

    design_state = ensure_state("design", args.change_name, trust=args.trust)
    design_state["stages"]["write-handoff"] = "completed"
    design_state["current_stage"] = "write-handoff"
    design_state["status"] = (
        "completed" if args.status == "design_ready" else design_state.get("status", "active")
    )
    save_state("design", args.change_name, design_state)

    print_json(
        {
            "status": "ok",
            "change_name": args.change_name,
            "handoff_path": str(handoff_path(args.change_name)),
        }
    )


def validate_handoff_command(args: argparse.Namespace) -> None:
    handoff = load_json(handoff_path(args.change_name))
    errors: list[str] = []

    for field in ["schema_version", "change_name", "status", "design_gate_passed"]:
        if field not in handoff:
            errors.append(f"missing field: {field}")

    allowed_statuses = args.allow_status or [args.expect_status]
    if handoff.get("status") not in allowed_statuses:
        errors.append(
            "handoff status mismatch: expected one of "
            f"{allowed_statuses}, got '{handoff.get('status')}'"
        )

    if handoff.get("design_gate_passed") is not True:
        errors.append("design_gate_passed must be true")
    if handoff.get("change_name") != args.change_name:
        errors.append("handoff change_name mismatch")
    if set(handoff.get("required_artifacts", [])) != REQUIRED_HANDOFF_ARTIFACTS:
        errors.append("handoff must require exactly proposal.md, design.md and tasks.md")

    if args.check_artifacts:
        validate_execution_input(args.change_name)

    if errors:
        for item in errors:
            print(item, file=sys.stderr)
        raise SystemExit(1)

    print_json(
        {
            "status": "ok",
            "change_name": args.change_name,
            "handoff_path": str(handoff_path(args.change_name)),
            "handoff_status": handoff.get("status"),
        }
    )


def compare_stage_keys(role: str, data: dict[str, Any], errors: list[str]) -> None:
    expected = set(ROLE_CONFIG[role]["stages"])
    actual = set(data.get("stages", {}).keys())
    extra = sorted(actual - expected)
    missing = sorted(expected - actual)
    if extra:
        errors.append(f"{role} state has unexpected stages: {extra}")
    if missing:
        errors.append(f"{role} state misses stages: {missing}")


def validate_pipeline_structure_command(args: argparse.Namespace) -> None:
    """校验编排定义本身：阶段集合、状态文件阶段键、handoff 产物契约。"""
    errors: list[str] = []

    forbidden = sorted(FORBIDDEN_DESIGN_STAGES & set(DESIGN_STAGES))
    if forbidden:
        errors.append(f"design stages contain forbidden stages: {forbidden}")

    for stage in ["test-design", "implement", "code-review", "test-run", "gate-delivery", "archive"]:
        if stage not in EXECUTION_STAGES:
            errors.append(f"execution stages must include {stage}")

    if args.change_name:
        design_file = state_path("design", args.change_name)
        if design_file.exists():
            compare_stage_keys("design", load_json(design_file), errors)

        execution_file = state_path("execution", args.change_name)
        if execution_file.exists():
            compare_stage_keys("execution", load_json(execution_file), errors)

        for role in ROLE_CONFIG:
            path = state_path(role, args.change_name)
            if not path.exists():
                continue
            data = load_json(path)
            gate = "gate-design" if role == "design" else "gate-delivery"
            if data.get("stages", {}).get(gate) == "completed":
                try:
                    require_predecessors(role, data, gate)
                    if role == "design":
                        validate_design_artifacts(args.change_name)
                    else:
                        validate_delivery(args.change_name)
                except SystemExit:
                    errors.append(f"invalid completed gate: {gate}")

        handoff_file = handoff_path(args.change_name)
        if handoff_file.exists():
            handoff = load_json(handoff_file)
            required_artifacts = set(handoff.get("required_artifacts", []))
            missing = sorted(REQUIRED_HANDOFF_ARTIFACTS - required_artifacts)
            if missing:
                errors.append(f"handoff misses required artifacts: {missing}")
            forbidden_optional = sorted(
                FORBIDDEN_HANDOFF_OPTIONAL_ARTIFACTS
                & set(str(item) for item in handoff.get("optional_artifacts", []))
            )
            if forbidden_optional:
                errors.append(
                    f"handoff optional artifacts contain deprecated files: {forbidden_optional}"
                )
            test_plan = [
                item
                for item in handoff.get("required_artifacts", [])
                if str(item) == "test-plan.md"
            ]
            if test_plan:
                errors.append(
                    "handoff must not require test-plan.md: "
                    "测试设计由执行侧 test-design 生成 test-guides/，见 feature-exec"
                )

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise SystemExit(1)

    print_json(
        {
            "status": "ok",
            "checked": "pipeline-structure",
            "change_name": args.change_name or "",
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Shared orchestrator state helper for feature-design and feature-exec."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_design = subparsers.add_parser("init-design")
    init_design.add_argument("change_name")
    init_design.add_argument("--trust", action="store_true")
    init_design.add_argument("--force", action="store_true")
    init_design.set_defaults(role="design", handler=init_state_command)

    init_execution = subparsers.add_parser("init-execution")
    init_execution.add_argument("change_name")
    init_execution.add_argument("--trust", action="store_true")
    init_execution.add_argument("--force", action="store_true")
    init_execution.set_defaults(role="execution", handler=init_state_command)

    set_stage = subparsers.add_parser("set-stage")
    set_stage.add_argument("role", choices=sorted(ROLE_CONFIG.keys()))
    set_stage.add_argument("change_name")
    set_stage.add_argument("stage")
    set_stage.add_argument("status", choices=sorted(STAGE_STATUSES))
    set_stage.add_argument(
        "--overall-status",
        choices=["active", "completed", "failed", "paused", "skipped"],
    )
    set_stage.add_argument("--failure-class", choices=sorted(FAILURE_CLASSES))
    set_stage.add_argument("--reason")
    set_stage.add_argument("--resume-confirmed", action="store_true")
    set_stage.add_argument("--trust", action="store_true")
    set_stage.set_defaults(handler=set_stage_command)

    set_gate = subparsers.add_parser("set-gate")
    set_gate.add_argument("role", choices=sorted(ROLE_CONFIG.keys()))
    set_gate.add_argument("change_name")
    set_gate.add_argument("gate")
    set_gate.add_argument("result", choices=sorted(GATE_RESULTS))
    set_gate.add_argument("--reason")
    set_gate.add_argument("--confirmed", action="store_true")
    set_gate.add_argument("--trust", action="store_true")
    set_gate.set_defaults(handler=set_gate_command)

    write_handoff = subparsers.add_parser("write-handoff")
    write_handoff.add_argument("change_name")
    write_handoff.add_argument("--status", default="design_ready")
    write_handoff.add_argument(
        "--design-gate-passed",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    write_handoff.add_argument("--producer-ide", default=ROLE_CONFIG["design"]["owner_ide"])
    write_handoff.add_argument("--producer-skill", default=ROLE_CONFIG["design"]["skill_name"])
    write_handoff.add_argument("--required", action="append")
    write_handoff.add_argument("--optional", action="append")
    write_handoff.add_argument("--executor-note", action="append")
    write_handoff.add_argument("--pending-risk", action="append")
    write_handoff.add_argument("--gate-decision", action="append")
    write_handoff.add_argument("--trust", action="store_true")
    write_handoff.set_defaults(handler=write_handoff_command)

    validate_handoff = subparsers.add_parser("validate-handoff")
    validate_handoff.add_argument("change_name")
    validate_handoff.add_argument("--expect-status", default="design_ready")
    validate_handoff.add_argument("--allow-status", action="append")
    validate_handoff.add_argument("--check-artifacts", action="store_true")
    validate_handoff.set_defaults(handler=validate_handoff_command)

    validate_structure = subparsers.add_parser("validate-structure")
    validate_structure.add_argument("change_name", nargs="?", default="")
    validate_structure.set_defaults(handler=validate_pipeline_structure_command)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
