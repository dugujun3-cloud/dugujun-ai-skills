#!/usr/bin/env python3
"""Stateful, local-only controller for the solo-business end-to-end workflow.

The controller uses only the Python standard library. It writes exclusively
inside the dedicated solo-business workflow root. It rejects projects and
status files belonging to every other workflow namespace. It never publishes,
charges, signs, registers, messages, or writes externally.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Iterator

from validate_decision_brief import validate as validate_decision_brief


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
MANIFEST_PATH = SKILL_DIR / "assets" / "workflow-stage-manifest.json"
STATUS_SCHEMA_PATH = SKILL_DIR / "assets" / "workflow-status.schema.json"
STATUS_NAME = "workflow_status.json"
HANDOFF_NAME = "handoff.md"
EVENTS_NAME = "events.jsonl"
LOCK_NAME = ".workflow.lock"
# Optional local knowledge base; set DUGUJUN_KNOWLEDGE_BASE_ROOT if you keep one.
KNOWLEDGE_BASE_DEFAULT: Path | None = None
WORKFLOW_ROOT_NAME = "一人公司项目"
WORKFLOW_NAMESPACE = "dugujun.solo_business.v1"
WORKFLOW_TYPE = "solo_business_end_to_end"

EXIT_OK = 0
EXIT_WARNING = 1
EXIT_INPUT = 2
EXIT_TRANSITION = 3
EXIT_GATE = 4
EXIT_LOCKED = 5
EXIT_BOUNDARY = 6
EXIT_CORRUPT = 7
EXIT_IO = 8

STAGE_STATUSES = {
    "pending",
    "in_progress",
    "awaiting_acceptance",
    "accepted",
    "blocked",
    "paused",
    "stopped",
}
OVERALL_STATUSES = {
    "active",
    "awaiting_acceptance",
    "blocked",
    "paused",
    "completed",
    "stopped",
    "recovery_needed",
}
EXTERNAL_KINDS = {
    "publish",
    "payment",
    "contract",
    "registration",
    "outbound_message",
    "external_write",
}
EXTERNAL_STATES = {
    "prepared",
    "awaiting_approval",
    "approved",
    "user_reported_performed",
    "verified",
    "rejected",
    "expired",
    "not_applicable",
}
EXTERNAL_TRANSITIONS = {
    "prepared": {"awaiting_approval", "expired"},
    "awaiting_approval": {"approved", "rejected", "expired"},
    "approved": {"user_reported_performed", "expired"},
    "user_reported_performed": {"verified"},
    "verified": set(),
    "rejected": set(),
    "expired": set(),
    "not_applicable": set(),
}
BRANCHES = {"consulting", "course", "product_knowledge_base", "web_app"}
HUMAN_EVIDENCE_STAGES = {
    "40_market_validation",
    "50_pilot_delivery",
    "60_pricing_economics",
    "70_acquisition_trust",
    "90_scale_transition_review",
}


class WorkflowError(Exception):
    def __init__(self, message: str, code: int) -> None:
        super().__init__(message)
        self.code = code


def now_iso() -> str:
    return dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_bytes(path, json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowError(f"cannot read JSON {path}: {exc}", EXIT_CORRUPT) from exc


def configured_workspace() -> Path:
    override = os.environ.get("DUGUJUN_WORKSPACE_ROOT")
    return Path(override).resolve() if override else SCRIPT_DIR.parents[3].resolve()


def configured_knowledge_base() -> Path | None:
    override = os.environ.get("DUGUJUN_KNOWLEDGE_BASE_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    if KNOWLEDGE_BASE_DEFAULT is not None:
        return KNOWLEDGE_BASE_DEFAULT.expanduser().resolve()
    return None


def configured_workflow_root() -> Path:
    override = os.environ.get("DUGUJUN_SOLO_BUSINESS_ROOT")
    return (
        Path(override).resolve()
        if override
        else (configured_workspace() / WORKFLOW_ROOT_NAME).resolve()
    )


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def resolve_project(raw: str, *, create: bool = False) -> Path:
    candidate = Path(raw).expanduser()
    resolved = candidate.resolve(strict=False)
    workspace = configured_workspace()
    workflow_root = configured_workflow_root()
    knowledge_base = configured_knowledge_base()
    if workflow_root == workspace or not is_within(workflow_root, workspace):
        raise WorkflowError(
            f"configured solo-business root must be a dedicated child of workspace: {workspace}",
            EXIT_BOUNDARY,
        )
    if resolved == workflow_root or not is_within(resolved, workflow_root):
        raise WorkflowError(
            f"solo-business project must be a child of the dedicated workflow root: {workflow_root}",
            EXIT_BOUNDARY,
        )
    if knowledge_base is not None and is_within(resolved, knowledge_base):
        raise WorkflowError("knowledge base is read-only and cannot be a workflow project", EXIT_BOUNDARY)
    if create:
        resolved.mkdir(parents=True, exist_ok=True)
    if not resolved.is_dir():
        raise WorkflowError(f"project directory does not exist: {resolved}", EXIT_INPUT)
    return resolved


def safe_artifact_path(project: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise WorkflowError(f"unsafe artifact path: {relative}", EXIT_BOUNDARY)
    resolved = (project / rel).resolve(strict=False)
    if not is_within(resolved, project.resolve()):
        raise WorkflowError(f"artifact escapes project root: {relative}", EXIT_BOUNDARY)
    knowledge_base = configured_knowledge_base()
    if knowledge_base is not None and is_within(resolved, knowledge_base):
        raise WorkflowError(f"artifact targets read-only knowledge base: {relative}", EXIT_BOUNDARY)
    return resolved


@contextlib.contextmanager
def project_lock(project: Path) -> Iterator[None]:
    lock_path = project / LOCK_NAME
    handle = lock_path.open("a+", encoding="utf-8")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise WorkflowError("workflow is locked by another process", EXIT_LOCKED) from exc
        handle.seek(0)
        handle.truncate()
        handle.write(json.dumps({"pid": os.getpid(), "locked_at": now_iso()}))
        handle.flush()
        yield
    finally:
        with contextlib.suppress(OSError):
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def load_manifest() -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("stages"), list):
        raise WorkflowError("invalid stage manifest", EXIT_CORRUPT)
    return manifest


def resolve_schema_ref(root: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise WorkflowError(f"unsupported schema reference: {reference}", EXIT_CORRUPT)
    node: Any = root
    for part in reference[2:].split("/"):
        node = node[part.replace("~1", "/").replace("~0", "~")]
    if not isinstance(node, dict):
        raise WorkflowError(f"schema reference is not an object: {reference}", EXIT_CORRUPT)
    return node


def json_type_matches(value: Any, type_name: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(type_name, False)


def validate_schema_node(
    value: Any,
    spec: dict[str, Any],
    root: dict[str, Any],
    path: str,
    errors: list[str],
) -> None:
    if "$ref" in spec:
        validate_schema_node(value, resolve_schema_ref(root, spec["$ref"]), root, path, errors)
        return
    expected_type = spec.get("type")
    if expected_type:
        choices = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(json_type_matches(value, item) for item in choices):
            errors.append(f"schema type mismatch at {path}: expected {choices}")
            return
    if "const" in spec and value != spec["const"]:
        errors.append(f"schema const mismatch at {path}")
    if "enum" in spec and value not in spec["enum"]:
        errors.append(f"schema enum mismatch at {path}: {value}")
    if isinstance(value, str):
        if len(value) < spec.get("minLength", 0):
            errors.append(f"schema minLength mismatch at {path}")
        if spec.get("pattern") and re.search(spec["pattern"], value) is None:
            errors.append(f"schema pattern mismatch at {path}")
    if isinstance(value, int) and not isinstance(value, bool) and value < spec.get("minimum", value):
        errors.append(f"schema minimum mismatch at {path}")
    if isinstance(value, dict):
        required = set(spec.get("required", []))
        missing = sorted(required - set(value))
        if missing:
            errors.append(f"schema missing fields at {path}: {', '.join(missing)}")
        properties = spec.get("properties", {})
        additional = spec.get("additionalProperties", True)
        for key, item in value.items():
            child_path = f"{path}.{key}"
            if key in properties:
                validate_schema_node(item, properties[key], root, child_path, errors)
            elif additional is False:
                errors.append(f"schema unknown field at {child_path}")
            elif isinstance(additional, dict):
                validate_schema_node(item, additional, root, child_path, errors)
        if len(value) < spec.get("minProperties", 0):
            errors.append(f"schema minProperties mismatch at {path}")
    if isinstance(value, list):
        if len(value) < spec.get("minItems", 0):
            errors.append(f"schema minItems mismatch at {path}")
        if len(value) > spec.get("maxItems", len(value)):
            errors.append(f"schema maxItems mismatch at {path}")
        if spec.get("uniqueItems"):
            canonical = [canonical_bytes(item) for item in value]
            if len(canonical) != len(set(canonical)):
                errors.append(f"schema uniqueItems mismatch at {path}")
        item_spec = spec.get("items")
        if isinstance(item_spec, dict):
            for index, item in enumerate(value):
                validate_schema_node(item, item_spec, root, f"{path}[{index}]", errors)


def make_stages(manifest: dict[str, Any], timestamp: str) -> dict[str, Any]:
    stages: dict[str, Any] = {}
    previous: str | None = None
    for order, spec in enumerate(manifest["stages"]):
        stage_id = spec["id"]
        artifacts = []
        for item in spec.get("artifacts", []):
            artifacts.append(
                {
                    "id": item["id"],
                    "path": item["path"],
                    "kind": item.get("kind", "file"),
                    "required": bool(item.get("required", True)),
                    "status": "missing",
                    "sha256": None,
                    "accepted_sha256": None,
                    "updated_at": None,
                }
            )
        stages[stage_id] = {
            "order": order,
            "title": spec["title"],
            "status": "in_progress" if order == 0 else "pending",
            "depends_on": [previous] if previous else [],
            "entry_criteria": ["all dependency stages accepted"] if previous else ["workflow initialized"],
            "exit_criteria": ["required artifacts exist and pass validation", "user accepts stage artifacts"],
            "artifacts": artifacts,
            "acceptance": {
                "required": True,
                "accepted_by": None,
                "accepted_at": None,
                "note": None,
                "scope": "stage_artifacts_only",
            },
            "blocker": None,
            "attempts": 1 if order == 0 else 0,
            "started_at": timestamp if order == 0 else None,
            "completed_at": None,
        }
        previous = stage_id
    return stages


def render_handoff(state: dict[str, Any]) -> str:
    lines = [
        "# 一人公司工作流交接",
        "",
        f"- 项目：{state['project']['name']}",
        f"- 本轮目标：{state['project'].get('goal') or '未填写'}",
        f"- 工作流：{state['workflow_id']}",
        f"- 独立命名空间：{state['workflow_namespace']}",
        f"- 周期：{state['cycle']}",
        f"- 修订：{state['revision']}",
        f"- 整体状态：{state['overall_status']}",
        f"- 当前阶段：{state.get('current_stage') or '无'}",
        f"- 最近更新：{state.get('updated_at') or '未知'}",
        "- 知识库：只读",
        "- 外部边界：不自动发布、不收费、不签约、不注册、不外联、不向项目外写入",
        "",
        "## 阶段",
        "",
    ]
    for stage_id, stage in sorted(state["stages"].items(), key=lambda item: item[1]["order"]):
        lines.append(f"- `{stage_id}`：{stage['status']}｜{stage['title']}")
        for artifact in stage["artifacts"]:
            lines.append(f"  - `{artifact['path']}`：{artifact['status']}")
    current = state.get("current_stage")
    if current and state["stages"][current].get("blocker"):
        blocker = state["stages"][current]["blocker"]
        lines.extend(
            [
                "",
                "## 阻塞或暂停",
                "",
                f"- 原因：{blocker['reason']}",
                f"- 恢复条件：{blocker['unblock_condition']}",
                f"- 保底：{blocker.get('fallback') or '无'}",
            ]
        )
    branch = state.get("product_branch")
    if branch:
        lines.extend(
            [
                "",
                "## 产品路线",
                "",
                f"- 主路线：{branch['primary']}",
                f"- 延后路线：{', '.join(branch['deferred']) or '无'}",
                f"- 依据：{branch['rationale']}",
            ]
        )
    lines.extend(["", "## 下一步", ""])
    for action in state.get("next_actions", []):
        lines.append(f"- {action}")
    if not state.get("next_actions"):
        lines.append("- 无")
    lines.extend(["", "## 已记录的外部动作", ""])
    if state.get("external_actions"):
        for action in state["external_actions"]:
            lines.append(
                f"- `{action['id']}` {action['kind']}：`{action['state']}`，执行者 `{action['performer']}`"
            )
    else:
        lines.append("- 无；控制器未执行任何外部动作。")
    return "\n".join(lines) + "\n"


def state_hash(state: dict[str, Any]) -> str:
    return sha256_bytes(canonical_bytes(state))


def append_event(project: Path, event: dict[str, Any]) -> None:
    path = project / EVENTS_NAME
    with path.open("ab") as handle:
        handle.write(canonical_bytes(event) + b"\n")
        handle.flush()
        os.fsync(handle.fileno())


def make_event(
    state: dict[str, Any],
    *,
    command: str,
    actor: str,
    stage: str | None,
    from_status: str | None,
    to_status: str | None,
    revision_before: int,
    request_id: str | None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "event_id": "evt_" + uuid.uuid4().hex[:16],
        "event_seq": state["event_log"]["last_seq"] + 1,
        "timestamp": now_iso(),
        "command": command,
        "actor": actor,
        "stage": stage,
        "from_status": from_status,
        "to_status": to_status,
        "revision_before": revision_before,
        "revision_after": state["revision"],
        "request_id": request_id,
        "state_hash": state_hash(state),
        "details": details or {},
    }


def commit(
    project: Path,
    state: dict[str, Any],
    *,
    command: str,
    actor: str = "codex",
    stage: str | None = None,
    from_status: str | None = None,
    to_status: str | None = None,
    request_id: str | None = None,
    details: dict[str, Any] | None = None,
    initial: bool = False,
) -> dict[str, Any]:
    before = state["revision"] if initial else state["revision"] - 1
    state["updated_at"] = now_iso()
    handoff_text = render_handoff(state)
    state["handoff"] = {
        "path": HANDOFF_NAME,
        "generated_from_revision": state["revision"],
        "sha256": sha256_bytes(handoff_text.encode("utf-8")),
    }
    event = make_event(
        state,
        command=command,
        actor=actor,
        stage=stage,
        from_status=from_status,
        to_status=to_status,
        revision_before=before,
        request_id=request_id,
        details=details,
    )
    state["event_log"]["last_seq"] = event["event_seq"]
    state["event_log"]["last_event_id"] = event["event_id"]
    if request_id:
        request_ids = state.setdefault("last_request_ids", [])
        request_ids.append(request_id)
        del request_ids[:-100]
    # Recompute because event-log metadata and request-id list are part of state.
    event["state_hash"] = state_hash(state)
    atomic_write_json(project / STATUS_NAME, state)
    append_event(project, event)
    atomic_write_bytes(project / HANDOFF_NAME, handoff_text.encode("utf-8"))
    return event


def read_state(project: Path) -> dict[str, Any]:
    path = project / STATUS_NAME
    if not path.is_file():
        raise WorkflowError(f"workflow is not initialized: {path}", EXIT_INPUT)
    state = load_json(path)
    if not isinstance(state, dict):
        raise WorkflowError("workflow status root must be an object", EXIT_CORRUPT)
    if state.get("workflow_namespace") != WORKFLOW_NAMESPACE or state.get("workflow_type") != WORKFLOW_TYPE:
        raise WorkflowError(
            "status belongs to a different workflow namespace; refusing cross-workflow access",
            EXIT_CORRUPT,
        )
    if state.get("project", {}).get("root") != str(project.resolve()):
        raise WorkflowError("status project root does not match its directory", EXIT_CORRUPT)
    return state


def check_revision(state: dict[str, Any], expected: int | None) -> None:
    if expected is not None and state.get("revision") != expected:
        raise WorkflowError(
            f"revision conflict: expected {expected}, found {state.get('revision')}", EXIT_TRANSITION
        )


def is_duplicate(state: dict[str, Any], request_id: str | None) -> bool:
    return bool(request_id and request_id in state.get("last_request_ids", []))


def hash_artifact(path: Path, kind: str) -> str:
    if kind == "file":
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    digest = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(str(child.relative_to(path)).encode("utf-8"))
        digest.update(hash_artifact(child, "file").encode("ascii"))
    return digest.hexdigest()


def inspect_artifact(project: Path, artifact: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    path = safe_artifact_path(project, artifact["path"])
    kind = artifact["kind"]
    exists = path.is_file() if kind == "file" else path.is_dir()
    if not exists:
        artifact["status"] = "missing"
        artifact["sha256"] = None
        if artifact["required"]:
            errors.append(f"missing required artifact: {artifact['path']}")
        return errors
    if kind == "file" and path.stat().st_size == 0:
        artifact["status"] = "draft"
        errors.append(f"empty artifact: {artifact['path']}")
        return errors
    suffix = path.suffix.lower()
    if kind == "file" and suffix == ".json":
        try:
            parsed_json = json.loads(path.read_text(encoding="utf-8"))
            if artifact.get("id") == "decision_brief":
                if not isinstance(parsed_json, dict):
                    errors.append("decision_brief root must be an object")
                else:
                    result = validate_decision_brief(parsed_json)
                    errors.extend(
                        f"decision_brief: {message}"
                        for message in result.get("errors", []) + result.get("warnings", [])
                    )
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON artifact {artifact['path']}: {exc}")
    if kind == "file" and suffix == ".jsonl":
        try:
            lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if not lines:
                errors.append(f"empty JSONL artifact: {artifact['path']}")
            for index, line in enumerate(lines, 1):
                json.loads(line)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSONL artifact {artifact['path']}: {exc}")
    digest = hash_artifact(path, kind)
    artifact["sha256"] = digest
    artifact["updated_at"] = now_iso()
    if artifact.get("accepted_sha256"):
        artifact["status"] = "accepted" if artifact["accepted_sha256"] == digest else "draft"
        if artifact["accepted_sha256"] != digest:
            errors.append(f"accepted artifact changed: {artifact['path']}")
    else:
        artifact["status"] = "ready" if not errors else "draft"
    return errors


def validate_state(
    project: Path,
    state: dict[str, Any],
    *,
    check_hashes: bool = True,
    check_active_artifacts: bool = False,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    schema = load_json(STATUS_SCHEMA_PATH)
    if not isinstance(schema, dict):
        errors.append("workflow status schema root must be an object")
    else:
        validate_schema_node(state, schema, schema, "$", errors)
    required = {
        "schema_version",
        "workflow_namespace",
        "workflow_id",
        "workflow_type",
        "revision",
        "cycle",
        "project",
        "guardrails",
        "overall_status",
        "current_stage",
        "stages",
        "event_log",
        "handoff",
        "external_actions",
        "next_actions",
    }
    missing = sorted(required - set(state))
    if missing:
        errors.append("missing state fields: " + ", ".join(missing))
        return errors, warnings
    if (
        state["schema_version"] != "2.0"
        or state["workflow_namespace"] != WORKFLOW_NAMESPACE
        or state["workflow_type"] != WORKFLOW_TYPE
    ):
        errors.append("unsupported schema_version, workflow_namespace, or workflow_type")
    if state.get("project", {}).get("root") != str(project.resolve()):
        errors.append("state project root does not match its directory")
    if state["overall_status"] not in OVERALL_STATUSES:
        errors.append(f"invalid overall status: {state['overall_status']}")
    for key in (
        "workspace_only_writes",
        "knowledge_base_read_only",
        "no_auto_publish",
        "no_auto_payment",
        "no_auto_contract",
        "no_external_writes",
    ):
        if state.get("guardrails", {}).get(key) is not True:
            errors.append(f"guardrail must remain true: {key}")
    stages = state.get("stages")
    if not isinstance(stages, dict) or not stages:
        errors.append("stages must be a non-empty object")
        return errors, warnings
    if any(not isinstance(stage, dict) for stage in stages.values()):
        errors.append("each stage must be an object")
        return errors, warnings
    manifest = load_manifest()
    expected_stage_ids = [item["id"] for item in manifest["stages"]]
    actual_stage_ids = [
        stage_id for stage_id, _ in sorted(stages.items(), key=lambda item: item[1].get("order", -1))
    ]
    if actual_stage_ids != expected_stage_ids:
        errors.append(f"stage set/order does not match manifest: {actual_stage_ids}")
    manifest_by_id = {item["id"]: item for item in manifest["stages"]}
    current = state.get("current_stage")
    if current is not None and current not in stages:
        errors.append(f"current_stage does not exist: {current}")
    active_ids = []
    for stage_id, stage in stages.items():
        expected_artifacts = [
            {
                "id": item["id"],
                "path": item["path"],
                "kind": item.get("kind", "file"),
                "required": bool(item.get("required", True)),
            }
            for item in manifest_by_id.get(stage_id, {}).get("artifacts", [])
        ]
        actual_artifacts = [
            {key: item.get(key) for key in ("id", "path", "kind", "required")}
            for item in stage.get("artifacts", [])
        ]
        if actual_artifacts != expected_artifacts:
            errors.append(f"artifact contract does not match manifest for {stage_id}")
        if stage.get("status") not in STAGE_STATUSES:
            errors.append(f"invalid stage status {stage_id}: {stage.get('status')}")
        if stage.get("status") in {"in_progress", "awaiting_acceptance", "blocked", "paused"}:
            active_ids.append(stage_id)
        for dependency in stage.get("depends_on", []):
            if dependency not in stages:
                errors.append(f"unknown dependency {dependency} for {stage_id}")
            elif stage.get("status") != "pending" and stages[dependency].get("status") != "accepted":
                errors.append(f"stage {stage_id} advanced before dependency {dependency} was accepted")
        for artifact in stage.get("artifacts", []):
            try:
                safe_artifact_path(project, artifact.get("path", ""))
            except WorkflowError as exc:
                errors.append(str(exc))
                continue
            if check_hashes and stage.get("status") == "accepted":
                snapshot = copy.deepcopy(artifact)
                artifact_errors = inspect_artifact(project, snapshot)
                errors.extend(artifact_errors)
        if (
            check_active_artifacts
            and stage_id == current
            and stage.get("status") in {"in_progress", "awaiting_acceptance"}
        ):
            for artifact in copy.deepcopy(stage.get("artifacts", [])):
                errors.extend(inspect_artifact(project, artifact))
    if len(active_ids) > 1:
        errors.append("more than one stage is active")
    if current is not None and active_ids and current not in active_ids:
        errors.append("current_stage does not match active stage")
    expected_overall = {
        "in_progress": "active",
        "awaiting_acceptance": "awaiting_acceptance",
        "blocked": "blocked",
        "paused": "paused",
    }
    if current in stages and stages[current].get("status") in expected_overall:
        expected = expected_overall[stages[current]["status"]]
        if state["overall_status"] != expected:
            errors.append(f"overall status should be {expected}")
    if state["overall_status"] == "completed" and any(
        stage.get("status") != "accepted" for stage in stages.values()
    ):
        errors.append("completed workflow contains unaccepted stages")
    for action in state.get("external_actions", []):
        if action.get("kind") not in EXTERNAL_KINDS:
            errors.append(f"invalid external action kind: {action.get('kind')}")
        if action.get("performer") != "user_or_authorized_human":
            errors.append("external action performer must be user_or_authorized_human")
        if action.get("state") not in EXTERNAL_STATES:
            errors.append(f"invalid external action state: {action.get('state')}")
        history = action.get("history", [])
        if history and history[-1].get("state") != action.get("state"):
            errors.append(f"external action history/state mismatch: {action.get('id')}")
        for previous, following in zip(history, history[1:]):
            if following.get("state") not in EXTERNAL_TRANSITIONS.get(previous.get("state"), set()):
                errors.append(
                    f"invalid external action history transition: {previous.get('state')} -> {following.get('state')}"
                )
    handoff_path = project / HANDOFF_NAME
    expected_handoff = render_handoff(state).encode("utf-8")
    if not handoff_path.is_file():
        errors.append("handoff.md is missing")
    else:
        actual = handoff_path.read_bytes()
        if actual != expected_handoff:
            errors.append("handoff.md is stale or was modified")
        if state["handoff"].get("sha256") != sha256_bytes(actual):
            errors.append("handoff hash mismatch")
        if state["handoff"].get("generated_from_revision") != state["revision"]:
            errors.append("handoff revision mismatch")
    events_path = project / EVENTS_NAME
    if not events_path.is_file():
        errors.append("events.jsonl is missing")
    else:
        events: list[dict[str, Any]] = []
        try:
            for raw in events_path.read_text(encoding="utf-8").splitlines():
                if raw.strip():
                    events.append(json.loads(raw))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid events.jsonl: {exc}")
        if events:
            expected_seq = list(range(1, len(events) + 1))
            if [event.get("event_seq") for event in events] != expected_seq:
                errors.append("event sequence is not contiguous")
            if state["event_log"].get("last_seq") != events[-1].get("event_seq"):
                errors.append("event last_seq mismatch")
            if state["event_log"].get("last_event_id") != events[-1].get("event_id"):
                errors.append("event last_event_id mismatch")
            if events[-1].get("state_hash") != state_hash(state):
                errors.append("latest event state_hash mismatch")
        elif state["event_log"].get("last_seq") != 0:
            errors.append("event log metadata is non-zero but log is empty")
    return errors, warnings


def response(state: dict[str, Any] | None, *, changed: bool, message: str, warnings: list[str] | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "changed": changed,
        "message": message,
        "revision": state.get("revision") if state else None,
        "status": state.get("overall_status") if state else None,
        "current_stage": state.get("current_stage") if state else None,
        "warnings": warnings or [],
        "errors": [],
        "next_action": (state.get("next_actions") or [None])[0] if state else None,
    }


def output(payload: dict[str, Any], *, json_mode: bool = True) -> None:
    if json_mode:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload.get("message", ""))


def mutate_preamble(args: argparse.Namespace) -> tuple[Path, dict[str, Any], dict[str, Any] | None]:
    project = resolve_project(args.project)
    state = read_state(project)
    check_revision(state, getattr(args, "if_revision", None))
    if is_duplicate(state, getattr(args, "request_id", None)):
        return project, state, response(state, changed=False, message="duplicate request-id; no change")
    return project, state, None


def command_init(args: argparse.Namespace) -> int:
    project = resolve_project(args.project, create=True)
    with project_lock(project):
        status_path = project / STATUS_NAME
        if status_path.exists():
            state = read_state(project)
            same = state.get("project", {}).get("name") == args.name and state.get("project", {}).get("goal") == args.goal
            if same:
                output(response(state, changed=False, message="workflow already initialized; no change"))
                return EXIT_OK
            raise WorkflowError("workflow already exists with different configuration", EXIT_TRANSITION)
        timestamp = now_iso()
        stages = make_stages(load_manifest(), timestamp)
        for stage_id in stages:
            safe_artifact_path(project, stage_id).mkdir(parents=False, exist_ok=True)
        first_stage = min(stages, key=lambda key: stages[key]["order"])
        brief_path = None
        if args.brief:
            brief = Path(args.brief).expanduser().resolve()
            if not brief.is_file():
                raise WorkflowError(f"brief does not exist: {brief}", EXIT_INPUT)
            brief_path = str(brief)
        state = {
            "schema_version": "2.0",
            "workflow_namespace": WORKFLOW_NAMESPACE,
            "workflow_id": "sbw_" + hashlib.sha256(f"{project}|{timestamp}".encode()).hexdigest()[:12],
            "workflow_type": WORKFLOW_TYPE,
            "revision": 0,
            "cycle": 1,
            "project": {"name": args.name, "root": str(project), "brief_path": brief_path, "goal": args.goal},
            "guardrails": {
                "workspace_only_writes": True,
                "knowledge_base_read_only": True,
                "no_auto_publish": True,
                "no_auto_payment": True,
                "no_auto_contract": True,
                "no_external_writes": True,
                "read_only_roots": (
                    [str(kb)] if (kb := configured_knowledge_base()) is not None else []
                ),
            },
            "overall_status": "active",
            "current_stage": first_stage,
            "stages": stages,
            "event_log": {"path": EVENTS_NAME, "last_seq": 0, "last_event_id": None},
            "handoff": {"path": HANDOFF_NAME, "generated_from_revision": 0, "sha256": None},
            "external_actions": [],
            "blocked_stage": None,
            "next_actions": [f"完成阶段 {first_stage} 的必需产物"],
            "self_check": {},
            "last_request_ids": [],
            "product_branch": None,
            "stop_reason": None,
            "stopped_at": None,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        commit(
            project,
            state,
            command="init",
            stage=first_stage,
            from_status=None,
            to_status="in_progress",
            request_id=args.request_id,
            initial=True,
        )
        output(response(state, changed=True, message="workflow initialized"))
    return EXIT_OK


def command_status(args: argparse.Namespace) -> int:
    project = resolve_project(args.project)
    state = read_state(project)
    errors, warnings = validate_state(project, state, check_hashes=False)
    payload = response(state, changed=False, message="workflow status", warnings=warnings)
    payload["ok"] = not errors
    payload["errors"] = errors
    if args.verbose:
        payload["stages"] = state["stages"]
        payload["external_actions"] = state["external_actions"]
        payload["product_branch"] = state.get("product_branch")
    output(payload, json_mode=args.json)
    return EXIT_OK if not errors else EXIT_CORRUPT


def next_pending_stage(state: dict[str, Any]) -> str | None:
    for stage_id, stage in sorted(state["stages"].items(), key=lambda item: item[1]["order"]):
        if stage["status"] != "pending":
            continue
        if all(state["stages"][dependency]["status"] == "accepted" for dependency in stage["depends_on"]):
            return stage_id
    return None


def command_next(args: argparse.Namespace) -> int:
    project = resolve_project(args.project)
    with project_lock(project):
        _, state, duplicate = mutate_preamble(args)
        if duplicate:
            output(duplicate)
            return EXIT_OK
        current = state.get("current_stage")
        if current and state["stages"][current]["status"] == "in_progress":
            stage = state["stages"][current]
            snapshot = copy.deepcopy(stage["artifacts"])
            gate_errors: list[str] = []
            if current == "80_systemization_productization" and not state.get("product_branch"):
                gate_errors.append("stage 80 requires one primary product branch before acceptance")
            for artifact in snapshot:
                gate_errors.extend(inspect_artifact(project, artifact))
            if gate_errors:
                payload = response(state, changed=False, message="stage artifact gate failed")
                payload["ok"] = False
                payload["errors"] = gate_errors
                output(payload)
                return EXIT_GATE
            if args.dry_run:
                output(response(state, changed=False, message="dry-run passed; stage can await acceptance"))
                return EXIT_OK
            old = stage["status"]
            stage["artifacts"] = snapshot
            stage["status"] = "awaiting_acceptance"
            state["overall_status"] = "awaiting_acceptance"
            state["next_actions"] = [f"请用户验收阶段 {current} 的本地产物"]
            state["revision"] += 1
            commit(project, state, command="next", stage=current, from_status=old, to_status=stage["status"], request_id=args.request_id)
            output(response(state, changed=True, message="stage is awaiting user acceptance"))
            return EXIT_OK
        if current and state["stages"][current]["status"] == "awaiting_acceptance":
            output(response(state, changed=False, message="current stage is already awaiting acceptance"))
            return EXIT_OK
        if current and state["stages"][current]["status"] in {"blocked", "paused", "stopped"}:
            raise WorkflowError(f"current stage is {state['stages'][current]['status']}; resume before next", EXIT_TRANSITION)
        candidate = next_pending_stage(state)
        if not candidate:
            if state["overall_status"] == "completed":
                output(response(state, changed=False, message="workflow is completed"))
                return EXIT_OK
            raise WorkflowError("no eligible next stage", EXIT_TRANSITION)
        stage = state["stages"][candidate]
        old = stage["status"]
        stage["status"] = "in_progress"
        stage["started_at"] = now_iso()
        stage["attempts"] += 1
        state["current_stage"] = candidate
        state["overall_status"] = "active"
        state["next_actions"] = [f"完成阶段 {candidate} 的必需产物"]
        state["revision"] += 1
        commit(project, state, command="next", stage=candidate, from_status=old, to_status="in_progress", request_id=args.request_id)
        output(response(state, changed=True, message=f"started stage {candidate}"))
    return EXIT_OK


def command_accept(args: argparse.Namespace) -> int:
    project = resolve_project(args.project)
    with project_lock(project):
        _, state, duplicate = mutate_preamble(args)
        if duplicate:
            output(duplicate)
            return EXIT_OK
        stage_id = args.stage or state.get("current_stage")
        if not stage_id or stage_id not in state["stages"]:
            raise WorkflowError("no valid stage to accept", EXIT_TRANSITION)
        stage = state["stages"][stage_id]
        if stage["status"] == "accepted":
            output(response(state, changed=False, message="stage already accepted"))
            return EXIT_OK
        if stage["status"] != "awaiting_acceptance":
            raise WorkflowError("stage must be awaiting_acceptance before accept", EXIT_TRANSITION)
        if stage_id in HUMAN_EVIDENCE_STAGES and not (args.note and args.note.strip()):
            raise WorkflowError(
                f"stage {stage_id} requires --note with the user's evidence review or decision basis",
                EXIT_GATE,
            )
        gate_errors: list[str] = []
        if stage_id == "80_systemization_productization" and not state.get("product_branch"):
            gate_errors.append("stage 80 requires one primary product branch before acceptance")
        artifacts = copy.deepcopy(stage["artifacts"])
        for artifact in artifacts:
            gate_errors.extend(inspect_artifact(project, artifact))
        if gate_errors:
            payload = response(state, changed=False, message="acceptance gate failed")
            payload["ok"] = False
            payload["errors"] = gate_errors
            output(payload)
            return EXIT_GATE
        for artifact in artifacts:
            artifact["accepted_sha256"] = artifact["sha256"]
            artifact["status"] = "accepted"
        old = stage["status"]
        stage["artifacts"] = artifacts
        stage["status"] = "accepted"
        stage["acceptance"] = {
            "required": True,
            "accepted_by": args.by,
            "accepted_at": now_iso(),
            "note": args.note,
            "scope": "stage_artifacts_only",
        }
        stage["completed_at"] = now_iso()
        state["blocked_stage"] = None
        pending = any(item["status"] == "pending" for item in state["stages"].values())
        if pending:
            state["current_stage"] = stage_id
            state["overall_status"] = "active"
            state["next_actions"] = ["运行 next 启动下一个依赖已满足的阶段"]
        else:
            state["current_stage"] = None
            state["overall_status"] = "completed"
            state["next_actions"] = ["需要新一轮验证时运行 new-cycle"]
        state["revision"] += 1
        commit(project, state, command="accept", actor=args.by, stage=stage_id, from_status=old, to_status="accepted", request_id=args.request_id, details={"scope": "stage_artifacts_only", "note": args.note})
        output(response(state, changed=True, message=f"accepted stage {stage_id}"))
    return EXIT_OK


def blocker_payload(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "reason": args.reason,
        "owner": args.owner,
        "unblock_condition": args.unblock_condition,
        "fallback": args.fallback,
        "blocked_at": now_iso(),
        "evidence_ref": args.evidence,
    }


def command_block(args: argparse.Namespace) -> int:
    project = resolve_project(args.project)
    with project_lock(project):
        _, state, duplicate = mutate_preamble(args)
        if duplicate:
            output(duplicate)
            return EXIT_OK
        stage_id = state.get("current_stage")
        if not stage_id:
            raise WorkflowError("no current stage to block", EXIT_TRANSITION)
        stage = state["stages"][stage_id]
        desired = blocker_payload(args)
        if stage["status"] == "blocked" and all(stage["blocker"].get(key) == desired.get(key) for key in ("reason", "owner", "unblock_condition", "fallback", "evidence_ref")):
            output(response(state, changed=False, message="stage already blocked with same reason"))
            return EXIT_OK
        if stage["status"] not in {"in_progress", "awaiting_acceptance"}:
            raise WorkflowError("only in_progress or awaiting_acceptance stage can be blocked", EXIT_TRANSITION)
        old = stage["status"]
        stage["status"] = "blocked"
        stage["blocker"] = desired
        state["overall_status"] = "blocked"
        state["blocked_stage"] = stage_id
        state["next_actions"] = [f"满足恢复条件：{args.unblock_condition}"]
        state["revision"] += 1
        commit(project, state, command="block", stage=stage_id, from_status=old, to_status="blocked", request_id=args.request_id, details=desired)
        output(response(state, changed=True, message=f"blocked stage {stage_id}"))
    return EXIT_OK


def command_pause(args: argparse.Namespace) -> int:
    project = resolve_project(args.project)
    with project_lock(project):
        _, state, duplicate = mutate_preamble(args)
        if duplicate:
            output(duplicate)
            return EXIT_OK
        stage_id = state.get("current_stage")
        if not stage_id:
            raise WorkflowError("no current stage to pause", EXIT_TRANSITION)
        stage = state["stages"][stage_id]
        if stage["status"] == "paused":
            output(response(state, changed=False, message="stage already paused"))
            return EXIT_OK
        if stage["status"] not in {"in_progress", "awaiting_acceptance"}:
            raise WorkflowError("only active stage can be paused", EXIT_TRANSITION)
        old = stage["status"]
        stage["status"] = "paused"
        stage["blocker"] = blocker_payload(args)
        state["overall_status"] = "paused"
        state["blocked_stage"] = stage_id
        state["next_actions"] = [f"满足恢复条件：{args.unblock_condition}"]
        state["revision"] += 1
        commit(project, state, command="pause", actor="user", stage=stage_id, from_status=old, to_status="paused", request_id=args.request_id, details=stage["blocker"])
        output(response(state, changed=True, message=f"paused stage {stage_id}; artifacts retained"))
    return EXIT_OK


def command_resume(args: argparse.Namespace) -> int:
    project = resolve_project(args.project)
    with project_lock(project):
        _, state, duplicate = mutate_preamble(args)
        if duplicate:
            output(duplicate)
            return EXIT_OK
        stage_id = state.get("current_stage")
        if not stage_id:
            raise WorkflowError("no current stage to resume", EXIT_TRANSITION)
        stage = state["stages"][stage_id]
        if stage["status"] == "in_progress":
            output(response(state, changed=False, message="stage already in progress"))
            return EXIT_OK
        if stage["status"] not in {"blocked", "paused"}:
            raise WorkflowError("only blocked or paused stage can resume", EXIT_TRANSITION)
        old = stage["status"]
        prior = stage["blocker"]
        stage["status"] = "in_progress"
        stage["blocker"] = None
        stage["attempts"] += 1
        state["overall_status"] = "active"
        state["blocked_stage"] = None
        state["next_actions"] = [f"继续完成阶段 {stage_id} 的必需产物"]
        state["revision"] += 1
        commit(project, state, command="resume", actor="user", stage=stage_id, from_status=old, to_status="in_progress", request_id=args.request_id, details={"resolution": args.resolution, "evidence": args.evidence, "previous": prior})
        output(response(state, changed=True, message=f"resumed stage {stage_id}"))
    return EXIT_OK


def command_stop(args: argparse.Namespace) -> int:
    project = resolve_project(args.project)
    with project_lock(project):
        _, state, duplicate = mutate_preamble(args)
        if duplicate:
            output(duplicate)
            return EXIT_OK
        if state["overall_status"] == "stopped":
            output(response(state, changed=False, message="workflow already stopped; artifacts retained"))
            return EXIT_OK
        if state["overall_status"] == "completed":
            raise WorkflowError("completed workflow cannot be stopped; start a new cycle if needed", EXIT_TRANSITION)
        stage_id = state.get("current_stage")
        old = state["overall_status"]
        if stage_id and state["stages"][stage_id]["status"] != "accepted":
            state["stages"][stage_id]["status"] = "stopped"
        state["overall_status"] = "stopped"
        state["stop_reason"] = args.reason
        state["stopped_at"] = now_iso()
        state["next_actions"] = ["材料已保留；如需继续，运行 new-cycle 从指定阶段恢复"]
        state["revision"] += 1
        commit(project, state, command="stop", actor="user", stage=stage_id, from_status=old, to_status="stopped", request_id=args.request_id, details={"reason": args.reason})
        output(response(state, changed=True, message="workflow stopped; no artifacts were deleted"))
    return EXIT_OK


def command_set_branch(args: argparse.Namespace) -> int:
    project = resolve_project(args.project)
    with project_lock(project):
        _, state, duplicate = mutate_preamble(args)
        if duplicate:
            output(duplicate)
            return EXIT_OK
        stage_id = state.get("current_stage")
        if stage_id != "80_systemization_productization":
            raise WorkflowError("set-branch is allowed only in stage 80_systemization_productization", EXIT_TRANSITION)
        if state["stages"][stage_id]["status"] not in {"in_progress", "awaiting_acceptance"}:
            raise WorkflowError("set-branch requires an active, unaccepted stage 80", EXIT_TRANSITION)
        deferred = [item.strip() for item in args.defer.split(",") if item.strip()]
        invalid = sorted(set(deferred) - BRANCHES)
        if invalid:
            raise WorkflowError("invalid deferred branches: " + ", ".join(invalid), EXIT_INPUT)
        if args.primary in deferred:
            raise WorkflowError("primary branch cannot also be deferred", EXIT_INPUT)
        expected_deferred = BRANCHES - {args.primary}
        if set(deferred) != expected_deferred:
            raise WorkflowError(
                "deferred branches must be exactly the other three routes: "
                + ", ".join(sorted(expected_deferred)),
                EXIT_INPUT,
            )
        desired = {"primary": args.primary, "deferred": sorted(set(deferred)), "rationale": args.rationale}
        current = state.get("product_branch")
        if current and all(current.get(key) == desired[key] for key in desired):
            output(response(state, changed=False, message="product branch already set"))
            return EXIT_OK
        desired["set_at"] = now_iso()
        state["product_branch"] = desired
        state["revision"] += 1
        commit(project, state, command="set-branch", actor="user", stage=stage_id, from_status=state["stages"][stage_id]["status"], to_status=state["stages"][stage_id]["status"], request_id=args.request_id, details=desired)
        output(response(state, changed=True, message=f"primary product branch set to {args.primary}"))
    return EXIT_OK


def command_record_external(args: argparse.Namespace) -> int:
    if not args.evidence and not args.note:
        raise WorkflowError("record-external requires --evidence or --note", EXIT_INPUT)
    project = resolve_project(args.project)
    with project_lock(project):
        _, state, duplicate = mutate_preamble(args)
        if duplicate:
            output(duplicate)
            return EXIT_OK
        timestamp = now_iso()
        history_item = {
            "state": args.state,
            "recorded_at": timestamp,
            "evidence_ref": args.evidence,
            "note": args.note,
        }
        if args.action_id:
            record = next(
                (item for item in state["external_actions"] if item["id"] == args.action_id),
                None,
            )
            if record is None:
                raise WorkflowError(f"external action not found: {args.action_id}", EXIT_INPUT)
            if record["kind"] != args.kind:
                raise WorkflowError("external action kind does not match existing record", EXIT_INPUT)
            allowed = EXTERNAL_TRANSITIONS.get(record["state"], set())
            if args.state not in allowed:
                raise WorkflowError(
                    f"invalid external transition: {record['state']} -> {args.state}",
                    EXIT_TRANSITION,
                )
            previous_state = record["state"]
            record["state"] = args.state
            record["evidence_ref"] = args.evidence or record.get("evidence_ref")
            record["note"] = args.note
            record["updated_at"] = timestamp
            record["history"].append(history_item)
        else:
            if args.state not in {"prepared", "user_reported_performed", "not_applicable"}:
                raise WorkflowError(
                    f"new external action cannot start at {args.state}; create it at prepared, explicit post-hoc user_reported_performed, or not_applicable",
                    EXIT_TRANSITION,
                )
            previous_state = None
            record = {
                "id": "ext_" + uuid.uuid4().hex[:16],
                "kind": args.kind,
                "performer": "user_or_authorized_human",
                "state": args.state,
                "evidence_ref": args.evidence,
                "note": args.note,
                "recorded_at": timestamp,
                "updated_at": timestamp,
                "history": [history_item],
            }
            state["external_actions"].append(record)
        state["revision"] += 1
        commit(
            project,
            state,
            command="record-external",
            actor="user",
            stage=state.get("current_stage"),
            from_status=previous_state,
            to_status=args.state,
            request_id=args.request_id,
            details={"action_id": record["id"], **history_item},
        )
        output(
            response(
                state,
                changed=True,
                message=f"external action {record['id']} recorded as {args.state}; controller performed no external action",
            )
        )
    return EXIT_OK


def archive_cycle(project: Path, state: dict[str, Any]) -> None:
    archive = project / ".history" / f"cycle-{state['cycle']:02d}"
    archive.mkdir(parents=True, exist_ok=False)
    atomic_write_json(archive / STATUS_NAME, state)
    for name in (HANDOFF_NAME, EVENTS_NAME):
        source = project / name
        if source.is_file():
            shutil.copy2(source, archive / name)
    artifact_root = archive / "artifacts"
    for stage in state["stages"].values():
        for artifact in stage["artifacts"]:
            source = safe_artifact_path(project, artifact["path"])
            if source.is_file():
                target = artifact_root / artifact["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            elif source.is_dir():
                shutil.copytree(source, artifact_root / artifact["path"])


def command_new_cycle(args: argparse.Namespace) -> int:
    project = resolve_project(args.project)
    with project_lock(project):
        _, state, duplicate = mutate_preamble(args)
        if duplicate:
            output(duplicate)
            return EXIT_OK
        if state["overall_status"] not in {"completed", "stopped"}:
            raise WorkflowError("new-cycle requires a completed or stopped workflow", EXIT_TRANSITION)
        if args.from_stage not in state["stages"]:
            raise WorkflowError(f"unknown stage: {args.from_stage}", EXIT_INPUT)
        from_order = state["stages"][args.from_stage]["order"]
        unaccepted_dependencies = [
            stage_id
            for stage_id, stage in state["stages"].items()
            if stage["order"] < from_order and stage["status"] != "accepted"
        ]
        if unaccepted_dependencies:
            raise WorkflowError(
                "new-cycle cannot skip unaccepted upstream stages: "
                + ", ".join(sorted(unaccepted_dependencies)),
                EXIT_TRANSITION,
            )
        archive_cycle(project, state)
        timestamp = now_iso()
        for stage in state["stages"].values():
            if stage["order"] < from_order:
                continue
            stage["status"] = "pending"
            stage["acceptance"] = {"required": True, "accepted_by": None, "accepted_at": None, "note": None, "scope": "stage_artifacts_only"}
            stage["blocker"] = None
            stage["started_at"] = None
            stage["completed_at"] = None
            for artifact in stage["artifacts"]:
                artifact["status"] = "draft" if safe_artifact_path(project, artifact["path"]).exists() else "missing"
                artifact["sha256"] = None
                artifact["accepted_sha256"] = None
                artifact["updated_at"] = None
        first = state["stages"][args.from_stage]
        first["status"] = "in_progress"
        first["attempts"] += 1
        first["started_at"] = timestamp
        state["cycle"] += 1
        state["current_stage"] = args.from_stage
        state["overall_status"] = "active"
        state["blocked_stage"] = None
        state["stop_reason"] = None
        state["stopped_at"] = None
        state["product_branch"] = None if from_order <= state["stages"]["80_systemization_productization"]["order"] else state.get("product_branch")
        state["next_actions"] = [f"新周期从阶段 {args.from_stage} 继续：{args.reason}"]
        state["revision"] += 1
        commit(project, state, command="new-cycle", actor="user", stage=args.from_stage, from_status="completed_or_stopped", to_status="in_progress", request_id=args.request_id, details={"reason": args.reason, "cycle": state["cycle"]})
        output(response(state, changed=True, message=f"started cycle {state['cycle']} from {args.from_stage}"))
    return EXIT_OK


def command_validate(args: argparse.Namespace) -> int:
    project = resolve_project(args.project)
    state = read_state(project)
    errors, warnings = validate_state(
        project,
        state,
        check_hashes=args.check_hashes,
        check_active_artifacts=True,
    )
    payload = response(state, changed=False, message="validation passed" if not errors else "validation failed", warnings=warnings)
    payload["ok"] = not errors
    payload["errors"] = errors
    output(payload, json_mode=args.json)
    if errors:
        return EXIT_CORRUPT
    if args.strict and warnings:
        return EXIT_WARNING
    return EXIT_OK


def add_mutation_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--if-revision", type=int)
    parser.add_argument("--request-id")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init")
    init.add_argument("project")
    init.add_argument("--name", required=True)
    init.add_argument("--brief")
    init.add_argument("--goal")
    init.add_argument("--request-id")
    init.set_defaults(func=command_init)

    status = subparsers.add_parser("status")
    status.add_argument("project")
    status.add_argument("--json", action="store_true")
    status.add_argument("--verbose", action="store_true")
    status.set_defaults(func=command_status)

    next_parser = subparsers.add_parser("next")
    next_parser.add_argument("project")
    next_parser.add_argument("--dry-run", action="store_true")
    add_mutation_options(next_parser)
    next_parser.set_defaults(func=command_next)

    accept = subparsers.add_parser("accept")
    accept.add_argument("project")
    accept.add_argument("--stage")
    accept.add_argument("--by", choices=["user"], required=True)
    accept.add_argument("--note")
    add_mutation_options(accept)
    accept.set_defaults(func=command_accept)

    for name, func in (("block", command_block), ("pause", command_pause)):
        item = subparsers.add_parser(name)
        item.add_argument("project")
        item.add_argument("--reason", required=True)
        item.add_argument("--owner", choices=["user", "codex", "external_professional", "external_state"], required=True)
        item.add_argument("--unblock-condition", required=True)
        item.add_argument("--fallback")
        item.add_argument("--evidence")
        add_mutation_options(item)
        item.set_defaults(func=func)

    resume = subparsers.add_parser("resume")
    resume.add_argument("project")
    resume.add_argument("--resolution", required=True)
    resume.add_argument("--evidence")
    add_mutation_options(resume)
    resume.set_defaults(func=command_resume)

    stop = subparsers.add_parser("stop")
    stop.add_argument("project")
    stop.add_argument("--reason", required=True)
    add_mutation_options(stop)
    stop.set_defaults(func=command_stop)

    branch = subparsers.add_parser("set-branch")
    branch.add_argument("project")
    branch.add_argument("--primary", choices=sorted(BRANCHES), required=True)
    branch.add_argument("--defer", default="")
    branch.add_argument("--rationale", required=True)
    add_mutation_options(branch)
    branch.set_defaults(func=command_set_branch)

    external = subparsers.add_parser("record-external")
    external.add_argument("project")
    external.add_argument("--kind", choices=sorted(EXTERNAL_KINDS), required=True)
    external.add_argument("--state", choices=sorted(EXTERNAL_STATES), default="prepared")
    external.add_argument("--action-id")
    external.add_argument("--evidence")
    external.add_argument("--note")
    add_mutation_options(external)
    external.set_defaults(func=command_record_external)

    cycle = subparsers.add_parser("new-cycle")
    cycle.add_argument("project")
    cycle.add_argument("--from-stage", required=True)
    cycle.add_argument("--reason", required=True)
    add_mutation_options(cycle)
    cycle.set_defaults(func=command_new_cycle)

    validate = subparsers.add_parser("validate")
    validate.add_argument("project")
    validate.add_argument("--strict", action="store_true")
    validate.add_argument("--json", action="store_true")
    validate.add_argument("--check-hashes", action="store_true")
    validate.set_defaults(func=command_validate)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return int(args.func(args))
    except WorkflowError as exc:
        print(json.dumps({"ok": False, "changed": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return exc.code
    except OSError as exc:
        print(json.dumps({"ok": False, "changed": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return EXIT_IO


if __name__ == "__main__":
    sys.exit(main())
