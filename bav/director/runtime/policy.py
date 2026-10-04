"""Native restrictions, path validation and Cursor command construction."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Mapping

from bav.director.runtime.contract import (
    ALLOWED_OPERATIONS,
    CURSOR_DOCUMENTED_FLAGS,
    CURSOR_FORBIDDEN_FLAGS,
    PROHIBITED_OPERATIONS,
    ApprovedSnapshot,
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
