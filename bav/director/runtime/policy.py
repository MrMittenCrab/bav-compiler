"""Native restrictions, path validation and Cursor command construction."""

from __future__ import annotations

import hashlib
import json
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


def validate_approved_path(
    raw_path: str,
    *,
    workspace: Path,
    approved_names: set[str],
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
    target = literal.resolve()
    if not is_within(target, workspace):
        return None, "symlink_or_traversal_escape"
    try:
        if target.exists() and target.is_symlink():
            return None, "symlink_escape"
    except OSError:
        return None, "path_stat_failure"
    relative = str(target.relative_to(workspace.resolve()))
    if relative not in approved_names and candidate.name not in approved_names:
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
