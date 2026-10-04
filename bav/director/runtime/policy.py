"""Native restrictions, path validation and Cursor command construction."""

from __future__ import annotations

import errno
import hashlib
import inspect
import json
import os
import re
import stat
import time
from collections import deque
from pathlib import Path
from typing import Any, Callable, Mapping

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
_CAPTURE_OPEN_FLAGS = (
    os.O_RDONLY
    | getattr(os, "O_CLOEXEC", 0)
    | getattr(os, "O_NOFOLLOW", 0)
    | getattr(os, "O_NONBLOCK", 0)
)
_DIR_OPEN_FLAGS = (
    os.O_RDONLY
    | getattr(os, "O_CLOEXEC", 0)
    | getattr(os, "O_DIRECTORY", 0)
    | getattr(os, "O_NOFOLLOW", 0)
)
_MAX_CAPTURE_DIAGNOSTICS = 32
_MAX_PATH_COMPONENTS = 64
_MAX_SYSTEM_PREFIX_FOLLOWS = 8
_REPLACEMENT_ERRNOS = {
    errno.ELOOP,
    errno.ENOTDIR,
    getattr(errno, "EFTYPE", -1),
}


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


def _kind_from_mode(mode: int) -> str:
    if stat.S_ISLNK(mode):
        return "symlink"
    if stat.S_ISREG(mode):
        return "file"
    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISFIFO(mode) or stat.S_ISCHR(mode) or stat.S_ISBLK(mode) or stat.S_ISSOCK(mode):
        return "special"
    return "other"


def _entry_kind(path: Path) -> str:
    try:
        info = os.lstat(path)
    except OSError:
        return "unreadable"
    return _kind_from_mode(info.st_mode)


def _kind_from_direntry(entry: os.DirEntry[str]) -> str:
    try:
        if entry.is_symlink():
            return "symlink"
        info = entry.stat(follow_symlinks=False)
    except OSError:
        return "unreadable"
    return _kind_from_mode(info.st_mode)


def _safe_relative(path: Path, root: Path) -> str | None:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return None


def _read_owned_chunk(fd: int, size: int, observer: Callable[[Mapping[str, Any]], None] | None) -> bytes:
    data = os.read(fd, size)
    if observer is not None:
        observer({"kind": "read", "requested": size, "returned": len(data)})
    return data


def _descriptor_traversal_supported() -> bool:
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        return False
    try:
        parameters = inspect.signature(os.open).parameters
    except (TypeError, ValueError):
        return False
    return "dir_fd" in parameters


def _is_replacement_error(exc: OSError) -> bool:
    return exc.errno in _REPLACEMENT_ERRNOS


def _capture_diagnostic(root_name: str, relative: str) -> str:
    return f"{root_name}/{relative or '.'}"


def _unreadable_note(root_name: str, relative: str) -> str:
    return f"unreadable:{_capture_diagnostic(root_name, relative)}"


def _replaced_note(root_name: str, relative: str) -> str:
    return f"replaced:{_capture_diagnostic(root_name, relative)}"


def _fd_identity(fd: int) -> tuple[int, int] | None:
    try:
        info = os.fstat(fd)
    except OSError:
        return None
    if not stat.S_ISDIR(info.st_mode):
        return None
    return (info.st_dev, info.st_ino)


def _close_fd(fd: int | None) -> None:
    if fd is None:
        return
    try:
        os.close(fd)
    except OSError:
        pass


def _single_component(name: str) -> bool:
    return bool(name) and name not in {".", ".."} and os.sep not in name and "\0" not in name


def _absolute_names(path: Path) -> tuple[str, ...] | None:
    raw = os.path.abspath(os.fsdecode(os.fspath(path)))
    if not os.path.isabs(raw):
        return None
    parts = Path(raw).parts
    if not parts or parts[0] != os.sep:
        return None
    names: list[str] = []
    for part in parts[1:]:
        if not part or part == ".":
            continue
        if part == ".." or not _single_component(part):
            return None
        names.append(part)
    return tuple(names)


def _walk_error_kind(exc: OSError | None) -> str:
    if exc is None:
        return "unreadable"
    if exc.errno == errno.ENOENT:
        return "missing"
    if _is_replacement_error(exc):
        return "replaced"
    return "unreadable"


def _open_trust_anchor() -> tuple[int | None, tuple[int, int] | None, OSError | None]:
    try:
        fd = os.open(os.sep, _DIR_OPEN_FLAGS)
    except OSError as exc:
        return None, None, exc
    identity = _fd_identity(fd)
    if identity is None:
        _close_fd(fd)
        return None, None, OSError(errno.ENOTDIR, "trust anchor identity lost")
    return fd, identity, None


def _system_prefix_names(anchor_fd: int, name: str) -> tuple[str, ...] | None:
    try:
        target = os.readlink(name, dir_fd=anchor_fd)
    except OSError:
        return None
    if not isinstance(target, str):
        target = os.fsdecode(target)
    if not target or "\0" in target:
        return None
    if os.path.isabs(target):
        return _absolute_names(Path(target))
    names: list[str] = []
    for part in Path(target).parts:
        if not part or part in {os.sep, "."}:
            continue
        if part == ".." or not _single_component(part):
            return None
        names.append(part)
    return tuple(names) or None


def _open_owned_directory(
    *,
    dir_fd: int,
    name: str | None = None,
) -> tuple[int | None, OSError | None]:
    if name is not None and not _single_component(name) and name != ".":
        return None, OSError(errno.EINVAL, "unsafe path component")
    try:
        fd = os.open(name if name is not None else ".", _DIR_OPEN_FLAGS, dir_fd=dir_fd)
    except OSError as exc:
        return None, exc
    identity = _fd_identity(fd)
    if identity is None:
        _close_fd(fd)
        return None, OSError(errno.ENOTDIR, "owned directory identity lost")
    return fd, None


def _child_relative(parent_relative: str, name: str) -> str:
    if not parent_relative or parent_relative == ".":
        return name
    return f"{parent_relative}/{name}"


class _RootAcquisition:
    __slots__ = (
        "fd",
        "parent_fd",
        "identity",
        "parent_identity",
        "name",
        "walk_names",
        "walk_identities",
    )

    def __init__(
        self,
        fd: int,
        parent_fd: int | None,
        identity: tuple[int, int],
        parent_identity: tuple[int, int] | None,
        name: str,
        walk_names: tuple[str, ...],
        walk_identities: tuple[tuple[int, int], ...],
    ) -> None:
        self.fd = fd
        self.parent_fd = parent_fd
        self.identity = identity
        self.parent_identity = parent_identity
        self.name = name
        self.walk_names = walk_names
        self.walk_identities = walk_identities


class _QueuedDirectory:
    __slots__ = (
        "root_name",
        "relative",
        "name",
        "dir_fd",
        "parent_fd",
        "identity",
        "depth",
        "walk_names",
        "walk_identities",
        "root_identity",
    )

    def __init__(
        self,
        root_name: str,
        relative: str,
        name: str,
        dir_fd: int,
        parent_fd: int | None,
        identity: tuple[int, int],
        depth: int,
        walk_names: tuple[str, ...] = (),
        walk_identities: tuple[tuple[int, int], ...] = (),
        root_identity: tuple[int, int] | None = None,
    ) -> None:
        self.root_name = root_name
        self.relative = relative
        self.name = name
        self.dir_fd = dir_fd
        self.parent_fd = parent_fd
        self.identity = identity
        self.depth = depth
        self.walk_names = walk_names
        self.walk_identities = walk_identities
        self.root_identity = root_identity


class _CaptureSession:
    def __init__(
        self,
        limits: CaptureLimits,
        clock: Callable[[], float],
        observer: Callable[[Mapping[str, Any]], None] | None,
    ) -> None:
        self.limits = limits
        self.clock = clock
        self.observer = observer
        self.started = clock()
        self.records: list[dict[str, Any]] = []
        self.limitations: list[str] = []
        self._seen_limitations: set[str] = set()
        self.entries_seen = 0
        self.files_seen = 0
        self.bytes_read = 0
        self.bytes_hashed = 0
        self.read_operations = 0
        self.complete = True
        self.unstable = False
        self.stop = False
        self._owned_fds: list[int] = []
        self._scanners: list[Any] = []

    def elapsed_exceeded(self) -> bool:
        return (self.clock() - self.started) >= self.limits.max_elapsed_seconds

    def note(self, limitation: str) -> None:
        self.complete = False
        if not limitation or limitation in self._seen_limitations:
            return
        if len(self.limitations) >= _MAX_CAPTURE_DIAGNOSTICS:
            return
        self._seen_limitations.add(limitation)
        self.limitations.append(limitation)
        generic = limitation.split(":", 1)[0]
        if generic != limitation and generic not in self._seen_limitations:
            if len(self.limitations) < _MAX_CAPTURE_DIAGNOSTICS:
                self._seen_limitations.add(generic)
                self.limitations.append(generic)

    def retain(self, record: dict[str, Any]) -> bool:
        if len(self.records) >= self.limits.max_records:
            self.note("truncated")
            self.stop = True
            return False
        self.records.append(record)
        return True

    def consume_entry(self) -> bool:
        if self.stop or self.elapsed_exceeded():
            self.note("elapsed" if self.elapsed_exceeded() else "truncated")
            self.stop = True
            return False
        if self.entries_seen >= self.limits.max_entries:
            self.note("truncated")
            self.stop = True
            return False
        self.entries_seen += 1
        return True

    def retain_fd(self, fd: int) -> bool:
        if len(self._owned_fds) >= self.limits.max_entries:
            self.note("truncated")
            self.stop = True
            return False
        self._owned_fds.append(fd)
        return True

    def retain_scanner(self, scanner: Any) -> None:
        self._scanners.append(scanner)

    def release_scanner(self, scanner: Any) -> None:
        try:
            scanner.close()
        except OSError:
            pass
        try:
            self._scanners.remove(scanner)
        except ValueError:
            pass

    def close_resources(self) -> None:
        while self._scanners:
            scanner = self._scanners.pop()
            try:
                scanner.close()
            except OSError:
                pass
        while self._owned_fds:
            fd = self._owned_fds.pop()
            try:
                os.close(fd)
            except OSError:
                pass


def _walk_budget(state: _CaptureSession, owned: list[int]) -> str | None:
    if state.elapsed_exceeded():
        state.note("elapsed")
        state.stop = True
        return "elapsed"
    if len(owned) > _MAX_PATH_COMPONENTS:
        state.note("truncated")
        state.stop = True
        return "truncated"
    return None


def _walk_names_from_anchor(
    names: tuple[str, ...],
    state: _CaptureSession,
    *,
    retain_parent: bool,
) -> tuple[_RootAcquisition | None, str | None]:
    if not names:
        return None, "unreadable"
    if len(names) > _MAX_PATH_COMPONENTS:
        return None, "truncated"
    if not _descriptor_traversal_supported():
        return None, "unavailable"

    owned: list[int] = []
    success = False
    final_fd: int | None = None
    parent_out: int | None = None
    try:
        anchor, anchor_id, exc = _open_trust_anchor()
        if anchor is None:
            return None, "unavailable"
        owned.append(anchor)
        current = anchor
        identities: list[tuple[int, int]] = []
        follows = 0
        for index, name in enumerate(names):
            budget = _walk_budget(state, owned)
            if budget:
                return None, budget
            child, child_exc = _open_owned_directory(dir_fd=current, name=name)
            if child is None and child_exc is not None and _is_replacement_error(child_exc):
                current_id = _fd_identity(current)
                if (
                    current_id == anchor_id
                    and follows < _MAX_SYSTEM_PREFIX_FOLLOWS
                ):
                    prefix = _system_prefix_names(current, name)
                    if prefix:
                        follows += 1
                        if len(prefix) + len(names) - index - 1 > _MAX_PATH_COMPONENTS:
                            return None, "truncated"
                        for prefix_name in prefix:
                            budget = _walk_budget(state, owned)
                            if budget:
                                return None, budget
                            prefix_fd, prefix_exc = _open_owned_directory(
                                dir_fd=current, name=prefix_name
                            )
                            if prefix_fd is None:
                                return None, _walk_error_kind(prefix_exc)
                            prefix_identity = _fd_identity(prefix_fd)
                            if prefix_identity is None:
                                _close_fd(prefix_fd)
                                return None, "replaced"
                            owned.append(prefix_fd)
                            identities.append(prefix_identity)
                            current = prefix_fd
                        continue
                return None, "replaced"
            if child is None:
                return None, _walk_error_kind(child_exc)
            identity = _fd_identity(child)
            if identity is None:
                _close_fd(child)
                return None, "replaced"
            owned.append(child)
            identities.append(identity)
            current = child
        if not identities:
            return None, "unreadable"
        final_fd = owned[-1]
        parent_fd = owned[-2] if len(owned) >= 2 else None
        keep = {final_fd}
        if retain_parent and parent_fd is not None:
            keep.add(parent_fd)
            parent_out = parent_fd
        for fd in owned:
            if fd not in keep:
                _close_fd(fd)
        owned = [fd for fd in owned if fd in keep]
        success = True
        return (
            _RootAcquisition(
                final_fd,
                parent_out,
                identities[-1],
                identities[-2] if len(identities) >= 2 else None,
                names[-1],
                names,
                tuple(identities),
            ),
            None,
        )
    finally:
        if not success:
            for fd in owned:
                _close_fd(fd)


def _probe_identity_mismatch(
    expected: tuple[int, int],
    *,
    dir_fd: int,
    name: str,
) -> bool:
    probe, _exc = _open_owned_directory(dir_fd=dir_fd, name=name)
    if probe is None:
        return True
    try:
        return _fd_identity(probe) != expected
    finally:
        _close_fd(probe)


def _probe_walk_replaced(item: _QueuedDirectory, state: _CaptureSession) -> bool:
    if not item.walk_names or not item.walk_identities:
        return True
    acquired, _kind = _walk_names_from_anchor(item.walk_names, state, retain_parent=False)
    if acquired is None:
        return True
    try:
        return acquired.walk_identities != item.walk_identities or (
            item.root_identity is not None and acquired.identity != item.root_identity
        )
    finally:
        _close_fd(acquired.fd)
        _close_fd(acquired.parent_fd)


def _queued_directory_replaced(item: _QueuedDirectory, state: _CaptureSession) -> bool:
    held = _fd_identity(item.dir_fd)
    if held is None or held != item.identity:
        return True
    if item.parent_fd is not None and _probe_identity_mismatch(
        item.identity, dir_fd=item.parent_fd, name=item.name
    ):
        return True
    if item.walk_names:
        return _probe_walk_replaced(item, state)
    return False


def _observe_symlink(
    dir_fd: int,
    name: str,
    *,
    root_name: str,
    relative: str,
    state: _CaptureSession,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "root": root_name,
        "path": relative,
        "type": "symlink",
        "content_complete": False,
    }
    try:
        record["link"] = os.readlink(name, dir_fd=dir_fd)
    except OSError:
        record["limitation"] = "unreadable"
        state.note(_unreadable_note(root_name, relative))
    return record


def _observe_owned_file(
    dir_fd: int,
    name: str,
    *,
    root_name: str,
    relative: str,
    state: _CaptureSession,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "root": root_name,
        "path": relative,
        "type": "file",
        "content_complete": False,
    }
    state.files_seen += 1
    remaining = state.limits.max_bytes_hashed - state.bytes_read
    if remaining <= 0 or state.files_seen > state.limits.max_files:
        record["limitation"] = "truncated"
        state.note("truncated")
        return record
    fd: int | None = None
    try:
        fd = os.open(name, _CAPTURE_OPEN_FLAGS, dir_fd=dir_fd)
        info = os.fstat(fd)
        opened_kind = _kind_from_mode(info.st_mode)
        if opened_kind != "file":
            record["type"] = opened_kind
            record["limitation"] = "unstable"
            state.unstable = True
            state.note("unstable")
            if opened_kind == "special":
                record["limitation"] = "special_file_skipped"
                state.note("special_file_skipped")
            return record
        record["size"] = info.st_size
        digest = hashlib.sha256()
        total_read = 0
        chunk_size = state.limits.read_chunk_bytes
        chunk = b""
        request = 0
        while True:
            if state.elapsed_exceeded():
                record["limitation"] = "elapsed"
                record["bytes_read"] = total_read
                state.note("elapsed")
                state.stop = True
                return record
            budget = remaining - total_read
            if budget <= 0:
                record["limitation"] = "truncated"
                record["bytes_read"] = total_read
                state.note("truncated")
                return record
            request = min(chunk_size, budget)
            chunk = _read_owned_chunk(fd, request, state.observer)
            state.read_operations += 1
            state.bytes_read += len(chunk)
            state.bytes_hashed += len(chunk)
            total_read += len(chunk)
            if chunk:
                digest.update(chunk)
            if not chunk or len(chunk) < request:
                break
            if total_read >= remaining:
                break
        record["bytes_read"] = total_read
        try:
            after = os.fstat(fd)
        except OSError:
            record["limitation"] = "unreadable"
            state.note(_unreadable_note(root_name, relative))
            return record
        if (
            after.st_size != info.st_size
            or after.st_ino != info.st_ino
            or after.st_dev != info.st_dev
            or after.st_mtime_ns != info.st_mtime_ns
        ):
            record["limitation"] = "unstable"
            state.unstable = True
            state.note("unstable")
            return record
        reached_eof = bool(not chunk or len(chunk) < request) if total_read or remaining > 0 else True
        exact_known_size = total_read == info.st_size and total_read <= remaining
        if exact_known_size or (reached_eof and total_read < remaining):
            record["content_complete"] = True
            record["fingerprint"] = digest.hexdigest()
            return record
        record["limitation"] = "truncated"
        state.note("truncated")
        return record
    except OSError as exc:
        if _is_replacement_error(exc):
            record["type"] = "symlink"
            record["limitation"] = "unstable"
            state.unstable = True
            state.note("unstable")
            try:
                record["link"] = os.readlink(name, dir_fd=dir_fd)
            except OSError:
                pass
            return record
        record["limitation"] = "unreadable"
        state.note(_unreadable_note(root_name, relative))
        return record
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass


def _capture_result(state: _CaptureSession) -> dict[str, Any]:
    if state.unstable:
        state.note("unstable")
    return {
        "records": tuple(state.records),
        "complete": state.complete and not state.stop,
        "limitations": tuple(state.limitations),
        "files_seen": state.files_seen,
        "entries_seen": state.entries_seen,
        "bytes_hashed": state.bytes_hashed,
        "bytes_read": state.bytes_read,
        "read_operations": state.read_operations,
        "elapsed_ms": int((state.clock() - state.started) * 1000),
        "unchanged_not_established": (not state.complete) or state.stop,
    }


def _queue_child_directory(
    item: _QueuedDirectory,
    name: str,
    relative: str,
    pending: deque[_QueuedDirectory],
    state: _CaptureSession,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "root": item.root_name,
        "path": relative,
        "type": "directory",
        "content_complete": False,
    }
    if item.depth >= state.limits.max_depth:
        state.note("truncated")
        return record
    if len(pending) >= state.limits.max_entries:
        state.note("truncated")
        state.stop = True
        return record
    child_fd, exc = _open_owned_directory(dir_fd=item.dir_fd, name=name)
    if child_fd is None:
        if exc is not None and _is_replacement_error(exc):
            record["type"] = "symlink"
            record["limitation"] = "unstable"
            state.unstable = True
            state.note(_replaced_note(item.root_name, relative))
            try:
                record["link"] = os.readlink(name, dir_fd=item.dir_fd)
            except OSError:
                pass
            return record
        record["limitation"] = "unreadable"
        state.note(_unreadable_note(item.root_name, relative))
        return record
    identity = _fd_identity(child_fd)
    if identity is None or not state.retain_fd(child_fd):
        try:
            os.close(child_fd)
        except OSError:
            pass
        if identity is None:
            record["limitation"] = "unstable"
            state.note(_replaced_note(item.root_name, relative))
        return record
    pending.append(
        _QueuedDirectory(
            item.root_name,
            relative,
            name,
            child_fd,
            item.dir_fd,
            identity,
            item.depth + 1,
            walk_names=item.walk_names,
            walk_identities=item.walk_identities,
            root_identity=item.root_identity,
        )
    )
    return record


def capture_owned_paths(
    roots: Mapping[str, Path],
    limits: CaptureLimits | None = None,
    *,
    clock: Callable[[], float] | None = None,
    io_observer: Callable[[Mapping[str, Any]], None] | None = None,
) -> dict[str, Any]:
    limits = limits or CaptureLimits()
    state = _CaptureSession(limits, clock or time.monotonic, io_observer)
    try:
        return _capture_owned_paths_bound(roots, limits, state)
    finally:
        state.close_resources()


def _capture_owned_paths_bound(
    roots: Mapping[str, Path],
    limits: CaptureLimits,
    state: _CaptureSession,
) -> dict[str, Any]:
    if not _descriptor_traversal_supported():
        state.note("unsafe_traversal_unavailable")
        return _capture_result(state)

    pending: deque[_QueuedDirectory] = deque()

    for root_name in OWNED_ROOT_NAMES:
        if state.stop:
            break
        root = roots.get(root_name)
        if root is None:
            continue
        if state.elapsed_exceeded():
            state.note("elapsed")
            state.stop = True
            break
        names = _absolute_names(root)
        if names is None:
            state.note(f"unreadable:{root_name}")
            continue
        acquired, kind = _walk_names_from_anchor(names, state, retain_parent=True)
        if acquired is None:
            if kind == "missing":
                state.note(f"missing:{root_name}")
            elif kind == "replaced":
                state.note(f"replaced:{root_name}")
            elif kind == "elapsed":
                state.note("elapsed")
                state.stop = True
                break
            elif kind == "truncated":
                state.note("truncated")
                state.stop = True
                break
            elif kind == "unavailable":
                state.note("unsafe_traversal_unavailable")
                state.stop = True
                break
            else:
                state.note(f"unreadable:{root_name}")
            continue
        fd = acquired.fd
        if not state.consume_entry():
            _close_fd(fd)
            _close_fd(acquired.parent_fd)
            break
        if not state.retain_fd(fd):
            _close_fd(fd)
            _close_fd(acquired.parent_fd)
            break
        if acquired.parent_fd is not None and not state.retain_fd(acquired.parent_fd):
            _close_fd(acquired.parent_fd)
            break
        root_record = {
            "root": root_name,
            "path": ".",
            "type": "directory",
            "content_complete": False,
        }
        if not state.retain(root_record):
            break
        if len(pending) >= limits.max_entries:
            state.note("truncated")
            state.stop = True
            break
        pending.append(
            _QueuedDirectory(
                root_name,
                ".",
                acquired.name,
                fd,
                acquired.parent_fd,
                acquired.identity,
                0,
                walk_names=acquired.walk_names,
                walk_identities=acquired.walk_identities,
                root_identity=acquired.identity,
            )
        )

    while pending and not state.stop:
        if state.elapsed_exceeded():
            state.note("elapsed")
            state.stop = True
            break
        item = pending.popleft()
        if item.depth > limits.max_depth:
            state.note("truncated")
            continue
        diagnostic = _capture_diagnostic(item.root_name, item.relative)
        if _queued_directory_replaced(item, state):
            state.note(f"replaced:{diagnostic}")
            continue
        try:
            scanner = os.scandir(item.dir_fd)
        except TypeError:
            state.note("unsafe_traversal_unavailable")
            state.stop = True
            break
        except OSError:
            state.note(f"unreadable:{diagnostic}")
            continue
        state.retain_scanner(scanner)
        try:
            if _queued_directory_replaced(item, state):
                state.note(f"replaced:{diagnostic}")
                continue
            while True:
                if state.stop or state.elapsed_exceeded():
                    if state.elapsed_exceeded():
                        state.note("elapsed")
                        state.stop = True
                    break
                try:
                    entry = next(scanner)
                except StopIteration:
                    break
                except OSError:
                    state.note(f"unreadable:{diagnostic}")
                    break
                if not state.consume_entry():
                    break
                name = entry.name
                if name in {".", ".."}:
                    continue
                relative = _child_relative(item.relative, name)
                kind = _kind_from_direntry(entry)
                if kind in {"file", "directory"} and _queued_directory_replaced(item, state):
                    state.note(f"replaced:{diagnostic}")
                    break
                if kind == "symlink":
                    record = _observe_symlink(
                        item.dir_fd, name, root_name=item.root_name, relative=relative, state=state
                    )
                elif kind == "special":
                    record = {
                        "root": item.root_name,
                        "path": relative,
                        "type": "special",
                        "content_complete": False,
                        "limitation": "special_file_skipped",
                    }
                    state.note("special_file_skipped")
                elif kind == "directory":
                    record = _queue_child_directory(item, name, relative, pending, state)
                elif kind == "file":
                    record = _observe_owned_file(
                        item.dir_fd,
                        name,
                        root_name=item.root_name,
                        relative=relative,
                        state=state,
                    )
                    if _queued_directory_replaced(item, state):
                        state.note(f"replaced:{diagnostic}")
                else:
                    record = {
                        "root": item.root_name,
                        "path": relative,
                        "type": kind,
                        "content_complete": False,
                    }
                    if kind == "unreadable":
                        record["limitation"] = "unreadable"
                        state.note(_unreadable_note(item.root_name, relative))
                if not state.retain(record):
                    break
        finally:
            state.release_scanner(scanner)

    return _capture_result(state)


def mutation_records(
    before: tuple[Mapping[str, Any], ...],
    after: tuple[Mapping[str, Any], ...],
    *,
    before_complete: bool = True,
    after_complete: bool = True,
) -> tuple[dict[str, Any], ...]:
    before_map = {(item.get("root"), item.get("path")): item for item in before}
    after_map = {(item.get("root"), item.get("path")): item for item in after}
    changes: list[dict[str, Any]] = []
    for key in sorted(set(before_map) | set(after_map), key=lambda item: (str(item[0]), str(item[1]))):
        previous = before_map.get(key)
        current = after_map.get(key)
        root, relative = key
        if previous is None and current is not None:
            definitive = bool(before_complete)
            changes.append(
                {
                    "root": root,
                    "path": relative,
                    "change": "added",
                    "after_type": current.get("type"),
                    "after_fingerprint": current.get("fingerprint"),
                    "definitive": definitive,
                    "coverage": "observed" if definitive else "before_incomplete",
                }
            )
            continue
        if current is None and previous is not None:
            definitive = bool(after_complete)
            changes.append(
                {
                    "root": root,
                    "path": relative,
                    "change": "removed",
                    "before_type": previous.get("type"),
                    "before_fingerprint": previous.get("fingerprint"),
                    "definitive": definitive,
                    "coverage": "observed" if definitive else "after_incomplete",
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
                    "definitive": True,
                    "coverage": "observed",
                }
            )
            continue
        before_complete_content = bool(previous.get("content_complete"))
        after_complete_content = bool(current.get("content_complete"))
        before_token = (
            previous.get("fingerprint")
            if before_complete_content
            else previous.get("link")
        )
        after_token = (
            current.get("fingerprint")
            if after_complete_content
            else current.get("link")
        )
        if previous.get("type") == "symlink" and previous.get("link") != current.get("link"):
            changes.append(
                {
                    "root": root,
                    "path": relative,
                    "change": "overwritten",
                    "before_type": previous.get("type"),
                    "after_type": current.get("type"),
                    "before_fingerprint": previous.get("fingerprint"),
                    "after_fingerprint": current.get("fingerprint"),
                    "definitive": True,
                    "coverage": "observed",
                }
            )
            continue
        if before_complete_content and after_complete_content and before_token != after_token:
            changes.append(
                {
                    "root": root,
                    "path": relative,
                    "change": "overwritten",
                    "before_type": previous.get("type"),
                    "after_type": current.get("type"),
                    "before_fingerprint": previous.get("fingerprint"),
                    "after_fingerprint": current.get("fingerprint"),
                    "definitive": True,
                    "coverage": "observed",
                }
            )
            continue
        if (
            previous.get("type") == "file"
            and (not before_complete_content or not after_complete_content)
        ):
            continue
    return tuple(changes)


def merge_capture_coverage(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> dict[str, Any]:
    limitations = tuple(
        dict.fromkeys(list(before.get("limitations") or ()) + list(after.get("limitations") or ()))
    )[:_MAX_CAPTURE_DIAGNOSTICS]
    complete = bool(before.get("complete")) and bool(after.get("complete"))
    return {
        "complete": complete,
        "limitations": limitations,
        "files_seen": after.get("files_seen", 0),
        "entries_seen": after.get("entries_seen", 0),
        "bytes_hashed": after.get("bytes_hashed", 0),
        "bytes_read": after.get("bytes_read", 0),
        "read_operations": after.get("read_operations", 0),
        "elapsed_ms": int(before.get("elapsed_ms") or 0) + int(after.get("elapsed_ms") or 0),
        "unchanged_not_established": (not complete)
        or bool(before.get("unchanged_not_established"))
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
