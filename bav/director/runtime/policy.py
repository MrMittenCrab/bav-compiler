"""Native restrictions, path validation and Cursor command construction."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import time
from pathlib import Path
from typing import Any, Mapping

from bav.director.runtime.contract import (
    ALLOWED_OPERATIONS,
    CURSOR_DOCUMENTED_FLAGS,
    CURSOR_FORBIDDEN_FLAGS,
    PROHIBITED_OPERATIONS,
    ApprovedSnapshot,
    CaptureLimits,
)

_ERROR_INDICATOR_KEYS = ("error", "errors", "isError", "is_error", "failed", "failure")
_PROVIDER_ERROR_TYPES = frozenset({"error"})
_PROVIDER_ERROR_SUBTYPES = frozenset({"error"})

_SECRET_KEY = re.compile(r"(api[_-]?key|token|password|authorization|secret|credential)", re.I)
_INSTRUCTION_MARKERS = (
    "allow shell",
    "allow write",
    "allow mcp",
    "run this",
    "execute this",
    "grant permission",
    "system prompt",
    "ignore previous",
)
INSTRUCTION_FILENAMES = frozenset(
    {
        "TARGET.md",
        "SESSION.md",
        "IMPLEMENTATION.md",
        "AGENTS.md",
        "RESULT.md",
    }
)
PROTECTED_ENV_KEYS = frozenset(
    {
        "HOME",
        "CURSOR_CONFIG_DIR",
        "CURSOR_DATA_DIR",
        "BAV_RUNTIME_WORKSPACE",
        "BAV_RUNTIME_ROLE",
        "BAV_RUNTIME_MODEL",
        "PATH",
        "LANG",
        "LC_ALL",
    }
)
PROVIDER_CONFIG_KEYS = frozenset(
    {
        "CURSOR_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "CODEX_API_KEY",
    }
)
PROVIDER_CONFIG_PREFIXES = ("CURSOR_", "OPENAI_", "ANTHROPIC_", "CODEX_")
UNRELATED_TOOL_ENV = frozenset(
    {
        "PATH",
        "PYTHONPATH",
        "NODE_OPTIONS",
        "NODE_PATH",
        "LD_PRELOAD",
        "DYLD_INSERT_LIBRARIES",
        "DYLD_LIBRARY_PATH",
    }
)
ALLOWED_EXTRA_ENV_PREFIX = "BAV_FAKE_"
NATIVE_OBSERVATION_LIMITATION = (
    "Detecting an already executed action is not prevention. "
    "No event, missing artifact or DNS failure establishes policy denial."
)
SNAPSHOT_CONTENT_FIELDS = (
    "role",
    "proposition",
    "scope",
    "sources",
    "current_evidence",
    "permissions",
    "user_notes",
    "prior_review",
    "candidate_argument",
    "selected_excerpts",
    "modeler_results",
    "counterevidence",
    "search_coverage",
    "contains_company_context",
)
OWNED_ROOT_NAMES = ("workspace", "home", "config", "data")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sanitize(value: Any) -> Any:
    if isinstance(value, Mapping):
        cleaned = {}
        for key, item in value.items():
            if _SECRET_KEY.search(str(key)) and not isinstance(item, bool):
                cleaned[str(key)] = "[redacted]"
            else:
                cleaned[str(key)] = sanitize(item)
        return cleaned
    if isinstance(value, (list, tuple)):
        return [sanitize(item) for item in value]
    return value


def source_contains_instructions(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _INSTRUCTION_MARKERS)


def _jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def snapshot_dict(snapshot: ApprovedSnapshot) -> dict[str, Any]:
    return {
        "role": snapshot.role,
        "proposition": snapshot.proposition,
        "scope": dict(snapshot.scope),
        "sources": [
            {
                "source_id": source.source_id,
                "origin": source.origin,
                "label": source.label,
                "text": source.text,
                "fingerprint": source.fingerprint,
                "relative_name": source.relative_name,
            }
            for source in snapshot.sources
        ],
        "current_evidence": [dict(item) for item in snapshot.current_evidence],
        "permissions": dict(snapshot.permissions),
        "user_notes": list(snapshot.user_notes),
        "prior_review": snapshot.prior_review,
        "candidate_argument": (
            dict(snapshot.candidate_argument) if snapshot.candidate_argument else None
        ),
        "selected_excerpts": [dict(item) for item in snapshot.selected_excerpts],
        "modeler_results": [dict(item) for item in snapshot.modeler_results],
        "counterevidence": [dict(item) for item in snapshot.counterevidence],
        "search_coverage": [dict(item) for item in snapshot.search_coverage],
        "contains_company_context": snapshot.contains_company_context,
        "content_hash": snapshot.content_hash,
    }


def snapshot_content_payload(data: Any) -> dict[str, Any] | str:
    if not isinstance(data, Mapping):
        return "snapshot_content_malformed"
    unexpected = set(data) - set(SNAPSHOT_CONTENT_FIELDS) - {"content_hash"}
    if unexpected:
        return "snapshot_unexpected_content"
    missing = [key for key in SNAPSHOT_CONTENT_FIELDS if key not in data]
    if missing:
        return "snapshot_missing_content"
    payload = {key: _jsonable(data[key]) for key in SNAPSHOT_CONTENT_FIELDS}
    sources = payload.get("sources")
    if not isinstance(sources, list):
        return "snapshot_content_malformed"
    for item in sources:
        if not isinstance(item, Mapping):
            return "snapshot_content_malformed"
        required = ("source_id", "origin", "label", "text", "fingerprint", "relative_name")
        if any(field not in item for field in required):
            return "snapshot_missing_content"
    return payload


def recompute_snapshot_content_hash(data: Any) -> tuple[str | None, str | None]:
    payload = snapshot_content_payload(data)
    if isinstance(payload, str):
        return None, payload
    return fingerprint(payload), None


def approved_source_inventory(snapshot: ApprovedSnapshot) -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    for source in snapshot.sources:
        inventory.append(
            {
                "source_id": source.source_id,
                "managed_name": managed_source_name(source.source_id),
                "original_name": Path(source.relative_name).as_posix(),
                "fingerprint": source.fingerprint,
                "instruction_named": instruction_named(source.relative_name),
            }
        )
    return inventory


def validate_staged_snapshot(stored: Any, snapshot: ApprovedSnapshot) -> str | None:
    payload = snapshot_content_payload(stored)
    if isinstance(payload, str):
        return payload
    approved = snapshot_content_payload(snapshot_dict(snapshot))
    if isinstance(approved, str):
        return approved
    recomputed, error = recompute_snapshot_content_hash(stored)
    approved_hash, approved_error = recompute_snapshot_content_hash(snapshot_dict(snapshot))
    if error or approved_error:
        return error or approved_error
    if payload != approved or recomputed != approved_hash:
        return "snapshot_content_mismatch"
    declared = stored.get("content_hash") if isinstance(stored, Mapping) else None
    if declared != snapshot.content_hash:
        return "snapshot_binding_mismatch"
    return None


def validate_on_disk_source_inventory(
    isolated: Any,
    snapshot: ApprovedSnapshot,
) -> tuple[tuple[dict[str, Any], ...], str | None]:
    path = isolated.workspace / "source_inventory.json"
    try:
        if not path.exists() or path.is_symlink() or not path.is_file():
            return (), "source_inventory_binding_mismatch"
        stored = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return (), "source_inventory_malformed"
    items = stored.get("sources") if isinstance(stored, Mapping) else None
    if not isinstance(items, list):
        return (), "source_inventory_malformed"
    approved = approved_source_inventory(snapshot)
    approved_by_id = {item["source_id"]: item for item in approved}
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, Mapping):
            return (), "source_inventory_malformed"
        source_id = item.get("source_id")
        managed = item.get("managed_name")
        original = item.get("original_name")
        declared = item.get("fingerprint")
        if not isinstance(source_id, str) or source_id in seen:
            return (), "source_inventory_binding_mismatch"
        if not isinstance(managed, str) or not isinstance(original, str):
            return (), "source_inventory_binding_mismatch"
        if not isinstance(declared, str):
            return (), "source_inventory_binding_mismatch"
        escape = validate_source_relative_name(managed)
        if escape:
            return (), escape
        expected = approved_by_id.get(source_id)
        if expected is None:
            return (), "source_inventory_binding_mismatch"
        if (
            managed != expected["managed_name"]
            or original != expected["original_name"]
            or declared != expected["fingerprint"]
            or bool(item.get("instruction_named")) != bool(expected["instruction_named"])
        ):
            return (), "source_inventory_binding_mismatch"
        staged = isolated.workspace / managed
        try:
            if staged.is_symlink() or not staged.is_file():
                return (), "source_inventory_binding_mismatch"
            if not is_within(staged, isolated.workspace):
                return (), "source_path_escape"
            observed = text_fingerprint(staged.read_text(encoding="utf-8"))
        except OSError:
            return (), "source_inventory_binding_mismatch"
        source = next(item for item in snapshot.sources if item.source_id == source_id)
        if observed != source.fingerprint or observed != expected["fingerprint"]:
            return (), "source_inventory_binding_mismatch"
        seen.add(source_id)
        normalized.append(dict(expected))
    if seen != {item["source_id"] for item in approved}:
        return (), "source_inventory_binding_mismatch"
    sources_dir = isolated.workspace / "sources"
    if sources_dir.exists():
        expected_names = {Path(item["managed_name"]).name for item in approved}
        try:
            for child in sources_dir.iterdir():
                if child.name not in expected_names:
                    return (), "source_inventory_binding_mismatch"
        except OSError:
            return (), "source_inventory_binding_mismatch"
    return tuple(normalized), None


def has_error_indicator(value: Mapping[str, Any]) -> bool:
    if value.get("success") is False or value.get("ok") is False:
        return True
    for key in _ERROR_INDICATOR_KEYS:
        item = value.get(key)
        if item in (None, False, "", (), [], {}):
            continue
        return True
    return False


def validate_provider_event(event: Mapping[str, Any]) -> str | None:
    for field in ("type", "subtype"):
        if field not in event:
            continue
        value = event[field]
        if not isinstance(value, str):
            return "invalid_provider_discriminator"
        if field == "type" and value in _PROVIDER_ERROR_TYPES:
            return "provider_error_event"
        if field == "subtype" and value in _PROVIDER_ERROR_SUBTYPES:
            return "provider_error_event"
    return None


def provider_event_error(event: Mapping[str, Any]) -> str | None:
    control = validate_provider_event(event)
    if control:
        return control
    if has_error_indicator(event):
        return "provider_error_indicator"
    output = event.get("output")
    if isinstance(output, Mapping) and has_error_indicator(output):
        return "provider_error_indicator"
    return None


def validate_provider_envelope(
    payload: Mapping[str, Any] | None,
    *,
    exit_code: int | None,
    expected_role: str,
) -> str | None:
    if payload is None:
        return "missing_result"
    control = validate_provider_event(payload)
    if control:
        return control
    unsuccessful = exit_code not in (0, None)
    output = payload.get("output")
    has_success_shape = isinstance(output, Mapping) and "kind" in output
    error_indicated = unsuccessful or has_error_indicator(payload)
    if isinstance(output, Mapping) and has_error_indicator(output):
        error_indicated = True
    if has_success_shape and error_indicated:
        return "conflicting_success_error_signals"
    if unsuccessful:
        return "unsuccessful_provider_exit"
    if error_indicated:
        return "provider_error_indicator"
    if output is None:
        return "missing_result"
    if not isinstance(output, Mapping) or "kind" not in output:
        return "malformed"
    if payload.get("role") not in (None, expected_role):
        return "malformed"
    return None


def validate_request_collection(raw: Any) -> tuple[list[Mapping[str, Any]] | None, str | None]:
    if raw is None:
        return [], None
    if not isinstance(raw, list):
        return None, "invalid_request_collection"
    items: list[Mapping[str, Any]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            return None, "invalid_request_item"
        items.append(item)
    return items, None


def validate_operation_request(item: Mapping[str, Any]) -> tuple[str, dict[str, Any]] | str:
    operation = item.get("operation")
    if not isinstance(operation, str) or not operation.strip():
        return "invalid_operation_name"
    if "arguments" not in item:
        arguments: Any = {}
    else:
        arguments = item.get("arguments")
    if not isinstance(arguments, Mapping):
        return "invalid_arguments"
    if operation == "inspect_approved_source":
        if "source_id" in arguments and not isinstance(arguments["source_id"], str):
            return "invalid_argument_field"
        if "path" in arguments and not isinstance(arguments["path"], str):
            return "invalid_argument_field"
    sanitized = {str(key): value for key, value in arguments.items()}
    return operation, sanitized


def classify_operation(name: str) -> str:
    key = name.strip().lower()
    if key in ALLOWED_OPERATIONS:
        return "allowed"
    if key in PROHIBITED_OPERATIONS:
        return "prohibited"
    return "unknown"


def intended_research_policy() -> dict[str, Any]:
    return {
        "permissions": {
            "allow": [],
            "deny": [
                "Shell(*)",
                "Write(*)",
                "Mcp(*)",
                "WebFetch(*)",
                "WebSearch(*)",
            ],
        },
        "sandbox": {"mode": "enabled", "networkAccess": "untrusted"},
    }


def policy_fingerprint(policy: Mapping[str, Any], restriction_reason: str) -> str:
    return fingerprint({"policy": policy, "restriction": restriction_reason})


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def text_fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def managed_source_name(source_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", source_id).strip("._") or "source"
    if safe in INSTRUCTION_FILENAMES or safe.lower() in {name.lower() for name in INSTRUCTION_FILENAMES}:
        safe = f"evidence-{safe}"
    return f"sources/{safe}"


def validate_source_relative_name(relative_name: str) -> str | None:
    if not relative_name or relative_name.startswith("~"):
        return "source_path_escape"
    candidate = Path(relative_name)
    if candidate.is_absolute() or ".." in candidate.parts:
        return "source_path_escape"
    return None


def instruction_named(relative_name: str) -> bool:
    return Path(relative_name).name in INSTRUCTION_FILENAMES


def validate_extra_env(extra: Mapping[str, str] | None) -> str | None:
    if not extra:
        return None
    for key in extra:
        if key in PROTECTED_ENV_KEYS:
            return "environment_override"
        if key in PROVIDER_CONFIG_KEYS or key in UNRELATED_TOOL_ENV:
            return "environment_override"
        if any(key.startswith(prefix) for prefix in PROVIDER_CONFIG_PREFIXES):
            return "provider_configuration_injection"
        if _SECRET_KEY.search(key):
            return "provider_configuration_injection"
        if not key.startswith(ALLOWED_EXTRA_ENV_PREFIX):
            return "unrelated_environment"
    return None


def build_launch_environment(
    isolated: Any,
    *,
    role: str,
    model: str,
    extra: Mapping[str, str] | None = None,
) -> tuple[dict[str, str], str | None]:
    error = validate_extra_env(extra)
    if error:
        return {}, error
    path_entries = [item for item in (os.environ.get("PATH") or "").split(os.pathsep) if item]
    env = {
        "PATH": os.pathsep.join(path_entries) or "/usr/bin:/bin",
        "HOME": str(isolated.home),
        "CURSOR_CONFIG_DIR": str(isolated.config_dir),
        "CURSOR_DATA_DIR": str(isolated.data_dir),
        "LANG": "C",
        "LC_ALL": "C",
        "BAV_RUNTIME_WORKSPACE": str(isolated.workspace),
        "BAV_RUNTIME_ROLE": role,
        "BAV_RUNTIME_MODEL": model,
    }
    for key, value in dict(extra or {}).items():
        if key.startswith(ALLOWED_EXTRA_ENV_PREFIX):
            env[key] = value
    return env, None


def owned_file_inventory(root: Path) -> list[str]:
    names: list[str] = []
    if not root.exists():
        return names
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(dirpath)
        kept: list[str] = []
        for dirname in dirnames:
            child = current / dirname
            if child.is_symlink():
                continue
            kept.append(dirname)
        dirnames[:] = kept
        for filename in filenames:
            path = current / filename
            try:
                relative = str(path.relative_to(root))
            except ValueError:
                continue
            if path.is_symlink():
                names.append(f"{relative}#symlink")
                continue
            if path.is_file():
                names.append(relative)
    return sorted(names)


def workspace_changes(before: tuple[str, ...], after: tuple[str, ...]) -> tuple[dict[str, str], ...]:
    before_set = set(before)
    after_set = set(after)
    changes: list[dict[str, str]] = []
    for name in sorted(after_set - before_set):
        changes.append({"path": name, "change": "added"})
    for name in sorted(before_set - after_set):
        changes.append({"path": name, "change": "removed"})
    return tuple(changes)


def file_content_fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def bind_path_identity(path: str | Path) -> dict[str, Any]:
    raw = Path(path)
    record: dict[str, Any] = {
        "declared": str(raw),
        "resolved": None,
        "content_hash": None,
        "symlink": False,
        "symlink_target": None,
        "present": False,
    }
    try:
        record["symlink"] = raw.is_symlink()
        if record["symlink"]:
            record["symlink_target"] = os.readlink(raw)
        if not raw.exists() and not record["symlink"]:
            return record
        resolved = raw.resolve()
        record["resolved"] = str(resolved)
        if resolved.is_file() and not resolved.is_symlink():
            record["content_hash"] = file_content_fingerprint(resolved)
            record["present"] = True
    except OSError:
        return record
    return record


def bind_approved_invocation(
    *,
    provider_mode: str,
    provider_argv: list[str],
    agent_bin: str,
) -> dict[str, Any]:
    if provider_mode == "synthetic":
        argv = list(provider_argv)
        interpreter = bind_path_identity(argv[0]) if argv else None
        script = bind_path_identity(argv[1]) if len(argv) > 1 else None
        return {
            "kind": "synthetic",
            "argv": argv,
            "interpreter": interpreter,
            "script": script,
        }
    return {
        "kind": "installed",
        "argv": [agent_bin],
        "executable": bind_path_identity(agent_bin),
    }


def validate_invocation_binding(
    approved: Mapping[str, Any] | None,
    argv: list[str],
) -> str | None:
    if not approved or not argv:
        return "executable_binding_mismatch"
    if list(argv) != list(approved.get("argv") or []):
        return "executable_binding_mismatch"
    kind = approved.get("kind")
    if kind == "synthetic":
        current_interpreter = bind_path_identity(argv[0])
        expected_interpreter = approved.get("interpreter") or {}
        if _identity_changed(expected_interpreter, current_interpreter):
            return "executable_binding_mismatch"
        if len(argv) > 1:
            current_script = bind_path_identity(argv[1])
            expected_script = approved.get("script") or {}
            if _identity_changed(expected_script, current_script):
                return "executable_binding_mismatch"
        return None
    if kind == "installed":
        current = bind_path_identity(argv[0])
        expected = approved.get("executable") or {}
        if _identity_changed(expected, current):
            return "executable_binding_mismatch"
        return None
    return "executable_binding_mismatch"


def _identity_changed(expected: Mapping[str, Any], observed: Mapping[str, Any]) -> bool:
    if not expected.get("present") or not observed.get("present"):
        return True
    for key in ("resolved", "content_hash", "symlink", "symlink_target"):
        if expected.get(key) != observed.get(key):
            return True
    return False


def _entry_kind(path: Path) -> str:
    try:
        if path.is_symlink():
            return "symlink"
        info = path.lstat()
    except OSError:
        return "unreadable"
    mode = info.st_mode
    if stat.S_ISREG(mode):
        return "file"
    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISFIFO(mode) or stat.S_ISCHR(mode) or stat.S_ISBLK(mode) or stat.S_ISSOCK(mode):
        return "special"
    return "other"


def _safe_relative(path: Path, root: Path) -> str | None:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return None


def _observe_owned_entry(
    path: Path,
    *,
    root_name: str,
    relative: str,
    limits: CaptureLimits,
    bytes_hashed: int,
) -> tuple[dict[str, Any], int, str | None]:
    record: dict[str, Any] = {
        "root": root_name,
        "path": relative,
        "type": _entry_kind(path),
    }
    kind = record["type"]
    if kind == "symlink":
        try:
            record["link"] = os.readlink(path)
        except OSError:
            record["limitation"] = "unreadable"
        return record, bytes_hashed, record.get("limitation")
    if kind == "special":
        record["limitation"] = "special_file_skipped"
        return record, bytes_hashed, "special_file_skipped"
    if kind != "file":
        return record, bytes_hashed, None
    remaining = limits.max_bytes_hashed - bytes_hashed
    if remaining <= 0:
        record["limitation"] = "truncated"
        return record, bytes_hashed, "truncated"
    try:
        data = path.read_bytes()
    except OSError:
        record["limitation"] = "unreadable"
        return record, bytes_hashed, "unreadable"
    used = min(len(data), remaining)
    record["size"] = len(data)
    if len(data) > remaining:
        record["limitation"] = "truncated"
        record["fingerprint"] = hashlib.sha256(data[:remaining]).hexdigest()
        return record, bytes_hashed + used, "truncated"
    record["fingerprint"] = hashlib.sha256(data).hexdigest()
    return record, bytes_hashed + used, None


def capture_owned_paths(
    roots: Mapping[str, Path],
    limits: CaptureLimits | None = None,
) -> dict[str, Any]:
    limits = limits or CaptureLimits()
    started = time.monotonic()
    records: list[dict[str, Any]] = []
    limitations: list[str] = []
    files_seen = 0
    bytes_hashed = 0
    complete = True
    unstable = False

    def _time_exceeded() -> bool:
        return (time.monotonic() - started) >= limits.max_elapsed_seconds

    for root_name in OWNED_ROOT_NAMES:
        root = roots.get(root_name)
        if root is None:
            continue
        if _time_exceeded():
            complete = False
            limitations.append("elapsed")
            break
        if not root.exists():
            complete = False
            limitations.append(f"missing:{root_name}")
            continue
        try:
            walker = os.walk(root, followlinks=False)
        except OSError:
            complete = False
            limitations.append(f"unreadable:{root_name}")
            continue
        for dirpath, dirnames, filenames in walker:
            current = Path(dirpath)
            depth = len(Path(dirpath).relative_to(root).parts) if Path(dirpath) != root else 0
            if depth > limits.max_depth or _time_exceeded():
                complete = False
                limitations.append("truncated" if depth > limits.max_depth else "elapsed")
                dirnames[:] = []
                continue
            kept: list[str] = []
            for dirname in dirnames:
                child = current / dirname
                relative = _safe_relative(child, root)
                if relative is None:
                    complete = False
                    limitations.append("omitted")
                    continue
                kind = _entry_kind(child)
                if kind == "symlink":
                    files_seen += 1
                    record, bytes_hashed, limitation = _observe_owned_entry(
                        child,
                        root_name=root_name,
                        relative=relative,
                        limits=limits,
                        bytes_hashed=bytes_hashed,
                    )
                    if limitation:
                        complete = False
                        limitations.append(limitation)
                    if len(records) < limits.max_records:
                        records.append(record)
                    else:
                        complete = False
                        limitations.append("truncated")
                    continue
                kept.append(dirname)
            dirnames[:] = kept
            for filename in filenames:
                if _time_exceeded() or files_seen >= limits.max_files or len(records) >= limits.max_records:
                    complete = False
                    limitations.append("truncated" if files_seen >= limits.max_files or len(records) >= limits.max_records else "elapsed")
                    dirnames[:] = []
                    filenames = []
                    break
                path = current / filename
                relative = _safe_relative(path, root)
                if relative is None:
                    complete = False
                    limitations.append("omitted")
                    continue
                files_seen += 1
                before_hash = bytes_hashed
                record, bytes_hashed, limitation = _observe_owned_entry(
                    path,
                    root_name=root_name,
                    relative=relative,
                    limits=limits,
                    bytes_hashed=bytes_hashed,
                )
                if limitation:
                    complete = False
                    limitations.append(limitation)
                if bytes_hashed == before_hash and record.get("type") == "file" and record.get("limitation") == "unreadable":
                    unstable = True
                if len(records) < limits.max_records:
                    records.append(record)
                else:
                    complete = False
                    limitations.append("truncated")
    unique_limitations = tuple(dict.fromkeys(limitations))
    if unstable and "unstable" not in unique_limitations:
        unique_limitations = unique_limitations + ("unstable",)
        complete = False
    return {
        "records": tuple(records),
        "complete": complete,
        "limitations": unique_limitations,
        "files_seen": files_seen,
        "bytes_hashed": bytes_hashed,
        "elapsed_ms": int((time.monotonic() - started) * 1000),
        "unchanged_not_established": not complete,
    }


def mutation_records(
    before: tuple[Mapping[str, Any], ...],
    after: tuple[Mapping[str, Any], ...],
) -> tuple[dict[str, Any], ...]:
    before_map = {(item.get("root"), item.get("path")): item for item in before}
    after_map = {(item.get("root"), item.get("path")): item for item in after}
    changes: list[dict[str, Any]] = []
    for key in sorted(set(before_map) | set(after_map), key=lambda item: (str(item[0]), str(item[1]))):
        previous = before_map.get(key)
        current = after_map.get(key)
        root, relative = key
        if previous is None and current is not None:
            changes.append(
                {
                    "root": root,
                    "path": relative,
                    "change": "added",
                    "after_type": current.get("type"),
                    "after_fingerprint": current.get("fingerprint"),
                }
            )
            continue
        if current is None and previous is not None:
            changes.append(
                {
                    "root": root,
                    "path": relative,
                    "change": "removed",
                    "before_type": previous.get("type"),
                    "before_fingerprint": previous.get("fingerprint"),
                }
            )
            continue
        if previous is None or current is None:
            continue
        if previous.get("type") != current.get("type"):
            changes.append(
                {
                    "root": root,
                    "path": relative,
                    "change": "type_changed",
                    "before_type": previous.get("type"),
                    "after_type": current.get("type"),
                    "before_fingerprint": previous.get("fingerprint"),
                    "after_fingerprint": current.get("fingerprint"),
                }
            )
            continue
        before_token = previous.get("fingerprint") or previous.get("link")
        after_token = current.get("fingerprint") or current.get("link")
        if before_token != after_token:
            changes.append(
                {
                    "root": root,
                    "path": relative,
                    "change": "overwritten",
                    "before_type": previous.get("type"),
                    "after_type": current.get("type"),
                    "before_fingerprint": previous.get("fingerprint"),
                    "after_fingerprint": current.get("fingerprint"),
                }
            )
    return tuple(changes)


def merge_capture_coverage(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> dict[str, Any]:
    limitations = tuple(
        dict.fromkeys(list(before.get("limitations") or ()) + list(after.get("limitations") or ()))
    )
    complete = bool(before.get("complete")) and bool(after.get("complete"))
    return {
        "complete": complete,
        "limitations": limitations,
        "files_seen": after.get("files_seen", 0),
        "bytes_hashed": after.get("bytes_hashed", 0),
        "elapsed_ms": int(before.get("elapsed_ms") or 0) + int(after.get("elapsed_ms") or 0),
        "unchanged_not_established": (not complete) or bool(before.get("unchanged_not_established"))
        or bool(after.get("unchanged_not_established")),
    }


def validate_path_safety(
    raw_path: str,
    *,
    workspace: Path,
) -> tuple[Path | None, str | None]:
    if not raw_path or raw_path.startswith("~"):
        return None, "unapproved_path"
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return None, "outside_root_read"
    if ".." in candidate.parts:
        return None, "traversal_escape"
    literal = workspace / candidate
    try:
        if literal.is_symlink() or any(
            parent.is_symlink() for parent in literal.parents if is_within(parent, workspace)
        ):
            return None, "symlink_escape"
    except OSError:
        return None, "path_stat_failure"
    try:
        target = literal.resolve()
    except OSError:
        return None, "path_stat_failure"
    if not is_within(target, workspace):
        return None, "symlink_or_traversal_escape"
    try:
        if target.exists() and target.is_symlink():
            return None, "symlink_escape"
    except OSError:
        return None, "path_stat_failure"
    return target, None


def validate_approved_path(
    raw_path: str,
    *,
    workspace: Path,
    approved_names: set[str] | None = None,
    expected_relative: str | None = None,
) -> tuple[Path | None, str | None]:
    target, error = validate_path_safety(raw_path, workspace=workspace)
    if error or target is None:
        return None, error
    relative = str(target.relative_to(workspace.resolve()))
    if expected_relative is not None:
        if relative != expected_relative and Path(raw_path).as_posix() != expected_relative:
            return None, "source_path_mismatch"
        return target, None
    names = approved_names or set()
    if relative not in names:
        return None, "unapproved_source"
    return target, None


def build_cursor_command(
    *,
    agent_bin: str,
    workspace: Path,
    model: str,
) -> list[str]:
    if not model.strip():
        raise ValueError("explicit model is required; no silent selection")
    if not Path(workspace).is_absolute():
        raise ValueError("workspace must be an absolute dedicated directory")
    command = [
        agent_bin,
        "--print",
        "--output-format", "stream-json",
        "--sandbox", "enabled",
        "--trust",
        "--workspace", str(workspace),
        "--model", model,
    ]
    forbidden = [flag for flag in command if flag in CURSOR_FORBIDDEN_FLAGS]
    if forbidden:
        raise ValueError(f"forbidden Cursor flag: {forbidden}")
    documented = set(CURSOR_DOCUMENTED_FLAGS)
    flags = {item for item in command if item.startswith("--")}
    if not documented <= flags:
        raise ValueError("Cursor command is missing a documented control flag")
    return command
