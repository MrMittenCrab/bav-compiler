"""Compact Planner/Reviewer backend request and result contract."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Literal, Mapping

Role = Literal["planner", "reviewer"]
BackendName = Literal["cursor"]
ProviderMode = Literal["installed", "synthetic"]
ResultStatus = Literal[
    "ok",
    "execution_failure",
    "malformed",
    "timeout",
    "allowance_exhausted",
    "interrupted",
    "denied",
    "native_restriction_unverified",
    "installed_launch_closed",
    "invalid_request",
]
SUPPORTED_PROVIDER_MODES = frozenset({"installed", "synthetic"})
ALLOWANCE_CHECKPOINT_VERSION = 1

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


def _require_finite_positive(name: str, value: Any, *, integer: bool = False) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite positive limit")
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive limit")
    if integer and (not isinstance(value, int) or isinstance(value, bool)):
        raise ValueError(f"{name} must be a finite positive integer")


@dataclass(frozen=True)
class AllowanceLimits:
    max_backend_calls: int = 12
    max_tool_dispatches: int = 20
    max_elapsed_seconds: float = 1200
    max_output_bytes: int = 1_000_000

    def __post_init__(self) -> None:
        _require_finite_positive("max_backend_calls", self.max_backend_calls, integer=True)
        _require_finite_positive("max_tool_dispatches", self.max_tool_dispatches, integer=True)
        _require_finite_positive("max_elapsed_seconds", self.max_elapsed_seconds)
        _require_finite_positive("max_output_bytes", self.max_output_bytes, integer=True)


@dataclass(frozen=True)
class AllowanceCheckpoint:
    schema_version: int = ALLOWANCE_CHECKPOINT_VERSION
    backend_calls_attempted: int = 0
    backend_failures: int = 0
    tool_dispatches: int = 0
    elapsed_active_seconds: float = 0.0
    last_known_result_call_id: str | None = None
    last_status: str | None = None
    interrupted_uncertain: bool = False
    known_result_call_ids: tuple[str, ...] = ()
    uncertain_attempt_call_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.schema_version != ALLOWANCE_CHECKPOINT_VERSION:
            raise ValueError("unsupported allowance checkpoint version")
        for name in (
            "backend_calls_attempted",
            "backend_failures",
            "tool_dispatches",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if (
            isinstance(self.elapsed_active_seconds, bool)
            or not isinstance(self.elapsed_active_seconds, (int, float))
            or not math.isfinite(self.elapsed_active_seconds)
            or self.elapsed_active_seconds < 0
        ):
            raise ValueError("elapsed_active_seconds must be a finite non-negative value")


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


INSTALLED_LAUNCH_CLOSED_REASON = (
    "Installed launch is closed: no supported BAV verification path binds the "
    "actual backend, executable, version, effective BAV policy/configuration "
    "and launch boundary. Caller-supplied verified flags and synthetic evidence "
    "are not launch authority."
)


@dataclass(frozen=True)
class ResearchRequest:
    role: Role
    model: str
    backend: BackendName
    snapshot: ApprovedSnapshot
    call_id: str
    provider_mode: ProviderMode = "synthetic"
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
    elapsed_active_ms: int = 0
    remaining_elapsed_seconds: float = 0.0
    tool_dispatches: int = 0


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
