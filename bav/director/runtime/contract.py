"""Compact Planner/Reviewer backend request and result contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping

Role = Literal["planner", "reviewer"]
BackendName = Literal["cursor"]
ResultStatus = Literal[
    "ok",
    "execution_failure",
    "malformed",
    "timeout",
    "allowance_exhausted",
    "interrupted",
    "denied",
    "native_restriction_unverified",
    "invalid_request",
]

ALLOWED_OPERATIONS = frozenset({"inspect_approved_source"})
PROHIBITED_OPERATIONS = frozenset(
    {
        "shell",
        "write",
        "mcp",
        "fetch",
        "search",
        "webfetch",
        "websearch",
        "apply_source_policy",
        "execute",
    }
)

CURSOR_DOCUMENTED_FLAGS = (
    "--print",
    "--output-format",
    "--sandbox",
    "--trust",
    "--workspace",
    "--model",
)
CURSOR_FORBIDDEN_FLAGS = frozenset(
    {
        "--force",
        "-f",
        "--yolo",
        "--approve-mcps",
        "--add-dir",
        "--continue",
        "--resume",
        "--worktree",
        "--disable-project-configs",
        "--plugin-dir",
    }
)


@dataclass(frozen=True)
class AllowanceLimits:
    max_backend_calls: int = 12
    max_tool_dispatches: int = 20
    max_elapsed_seconds: int = 1200
    max_output_bytes: int = 1_000_000


@dataclass(frozen=True)
class ApprovedSource:
    source_id: str
    origin: Literal["synthetic", "company_corpus", "user_import"]
    label: str
    text: str
    fingerprint: str
    relative_name: str


@dataclass(frozen=True)
class ApprovedSnapshot:
    role: Role
    proposition: str
    scope: Mapping[str, Any]
    sources: tuple[ApprovedSource, ...]
    current_evidence: tuple[Mapping[str, Any], ...]
    permissions: Mapping[str, Any]
    user_notes: tuple[str, ...]
    prior_review: str | None
    candidate_argument: Mapping[str, Any] | None
    selected_excerpts: tuple[Mapping[str, Any], ...]
    modeler_results: tuple[Mapping[str, Any], ...]
    counterevidence: tuple[Mapping[str, Any], ...]
    search_coverage: tuple[Mapping[str, Any], ...]
    contains_company_context: bool
    content_hash: str


@dataclass(frozen=True)
class NativeRestrictionState:
    backend: str
    verified: bool
    reason: str
    documented_controls: tuple[str, ...]
    missing_controls: tuple[str, ...]


def cursor_unverified_restrictions() -> NativeRestrictionState:
    return NativeRestrictionState(
        backend="cursor",
        verified=False,
        reason=(
            "Installed Cursor has no documented loaded-configuration identity "
            "or first-class policy-denial event; historical enforcement is unknown."
        ),
        documented_controls=(
            "sandbox enabled override",
            "deny-precedes-allow permission tokens",
            "workspace/cwd alignment",
        ),
        missing_controls=(
            "loaded-configuration identity",
            "policy-denial event",
        ),
    )


def synthetic_controlled_restrictions() -> NativeRestrictionState:
    return NativeRestrictionState(
        backend="synthetic",
        verified=True,
        reason=(
            "Synthetic provider exposes no provider-native tools; "
            "Director owns launch and typed dispatch. This is not installed-provider enforcement."
        ),
        documented_controls=("application dispatcher only",),
        missing_controls=(),
    )


@dataclass(frozen=True)
class ResearchRequest:
    role: Role
    model: str
    backend: BackendName
    snapshot: ApprovedSnapshot
    call_id: str
    provider_mode: Literal["installed", "synthetic"] = "synthetic"
    runtime_version: str | None = None


@dataclass(frozen=True)
class AttemptRecord:
    operation: str
    arguments: Mapping[str, Any]
    decision: str
    reason: str
    executed: bool
    result: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class CaptureRecord:
    call_id: str
    role: Role
    request_fingerprint: str
    context_fingerprint: str
    policy_fingerprint: str
    runtime_name: str
    runtime_version: str | None
    model: str | None
    attempted_operations: tuple[AttemptRecord, ...]
    decisions: tuple[Mapping[str, str], ...]
    tool_results: tuple[Mapping[str, Any], ...]
    exit_code: int | None
    error: str | None
    timed_out: bool
    interrupted: bool
    elapsed_ms: int
    output_bytes: int
    cwd: str | None
    workspace: str | None
    env_names: tuple[str, ...]
    observed: Mapping[str, Any]
    backend_calls_attempted: int
    backend_failures: int
    launched: bool


@dataclass(frozen=True)
class BackendResult:
    call_id: str
    role: Role
    status: ResultStatus
    model: str | None
    runtime_name: str
    runtime_version: str | None
    structured_output: Mapping[str, Any] | None
    attempts: tuple[AttemptRecord, ...]
    capture: CaptureRecord
    known_result: bool
    retried: bool = False
    details: Mapping[str, Any] = field(default_factory=dict)
