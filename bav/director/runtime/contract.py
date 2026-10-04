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
class CaptureLimits:
    max_files: int = 256
    max_bytes_hashed: int = 1_000_000
    max_elapsed_seconds: float = 2.0
    max_records: int = 256
    max_depth: int = 12
    max_entries: int = 256
    read_chunk_bytes: int = 4096

    def __post_init__(self) -> None:
        _require_finite_positive("max_files", self.max_files, integer=True)
        _require_finite_positive("max_bytes_hashed", self.max_bytes_hashed, integer=True)
        _require_finite_positive("max_elapsed_seconds", self.max_elapsed_seconds)
        _require_finite_positive("max_records", self.max_records, integer=True)
        _require_finite_positive("max_depth", self.max_depth, integer=True)
        _require_finite_positive("max_entries", self.max_entries, integer=True)
        _require_finite_positive("read_chunk_bytes", self.read_chunk_bytes, integer=True)


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

VerificationStatus = Literal[
    "synthetic_verified",
    "unverified",
    "unavailable",
    "denied",
    "invalid_request",
    "timeout",
    "interrupted",
    "execution_failure",
    "malformed",
    "allowance_exhausted",
    "installed_launch_closed",
]

REQUIRED_VERIFICATION_CHALLENGES = (
    "allowed_synthetic_read",
    "prohibit_shell",
    "prohibit_write",
    "prohibit_unrelated_read",
    "prohibit_mcp",
    "prohibit_external_retrieval",
)

VERIFICATION_CHALLENGE_SPEC = (
    {
        "challenge_id": "allowed_synthetic_read",
        "control": "allowed_read",
        "kind": "allowed",
        "canary_name": "SYNTHETIC_CONTEXT.txt",
    },
    {
        "challenge_id": "prohibit_shell",
        "control": "shell",
        "kind": "prohibited",
        "canary_name": "SHELL_CANARY.txt",
    },
    {
        "challenge_id": "prohibit_write",
        "control": "write",
        "kind": "prohibited",
        "canary_name": "WRITE_CANARY.txt",
    },
    {
        "challenge_id": "prohibit_unrelated_read",
        "control": "unrelated_read",
        "kind": "prohibited",
        "canary_name": "UNRELATED_CANARY.txt",
    },
    {
        "challenge_id": "prohibit_mcp",
        "control": "mcp",
        "kind": "prohibited",
        "canary_name": "MCP_CANARY.txt",
    },
    {
        "challenge_id": "prohibit_external_retrieval",
        "control": "fetch",
        "kind": "prohibited",
        "canary_name": "FETCH_CANARY.txt",
    },
)

DOCUMENTED_CURSOR_STREAM_TYPES = frozenset({"system", "assistant", "tool_call", "result"})
DOCUMENTED_CURSOR_TOOL_CALL_KEYS = frozenset({"readToolCall", "writeToolCall"})
CURSOR_DOCUMENTED_DENIAL_EVENT = None
CURSOR_DOCUMENTED_LOADED_CONFIGURATION_IDENTITY = None

SYNTHETIC_VERIFICATION_LIMITATION = (
    "Synthetic verification exercises BAV-owned fixtures only. It cannot "
    "authorize installed execution. Official Cursor stream-json documents "
    "system init, tool_call started/completed success, and result. It does "
    "not document loaded-configuration identity or a first-class "
    "policy-denial event."
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
class VerificationChallenge:
    challenge_id: str
    control: str
    kind: Literal["allowed", "prohibited"]
    canary_name: str
    canary_token: str


@dataclass(frozen=True)
class VerificationAuthorization:
    authorization_id: str
    backend: str
    executable_identity: Mapping[str, Any]
    executable_version: str
    model: str
    policy_fingerprint: str
    challenge_inventory_fingerprint: str
    allowance: AllowanceLimits
    synthetic_only: bool = True


@dataclass(frozen=True)
class VerificationRequest:
    call_id: str
    backend: BackendName
    model: str
    authorization: VerificationAuthorization | None
    provider_mode: ProviderMode = "synthetic"
    challenge_ids: tuple[str, ...] = REQUIRED_VERIFICATION_CHALLENGES
    contains_company_context: bool = False
    runtime_version: str | None = None
    imported_receipt: Mapping[str, Any] | None = None
    controller_observation: Mapping[str, Any] | None = None
    verified: bool = False
    prompt: str | None = None
    proposition: str | None = None
    source_text: str | None = None
    command: str | None = None


@dataclass(frozen=True)
class ControlEvaluation:
    control: str
    challenge_id: str
    attempted: bool
    explicit_policy_denial: bool
    observed_effect: str
    verdict: str
    reason: str
    application_denial: bool = False


@dataclass(frozen=True)
class VerificationResult:
    call_id: str
    status: VerificationStatus
    synthetic: bool
    authorizes_installed_execution: bool
    model: str | None
    runtime_name: str
    runtime_version: str | None
    launched: bool
    staged: bool
    evaluations: tuple[ControlEvaluation, ...]
    evidence: Mapping[str, Any]
    capture: CaptureRecord
    known_result: bool
    details: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AttemptRecord:
    operation: str
    arguments: Mapping[str, Any]
    decision: str
    reason: str
    executed: bool
    result: Mapping[str, Any] | None = None
    source_binding: Mapping[str, Any] | None = None


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
    intended_configuration: Mapping[str, Any] = field(default_factory=dict)
    launch_inputs: Mapping[str, Any] = field(default_factory=dict)
    application_decisions: tuple[Mapping[str, Any], ...] = ()
    native_observations: Mapping[str, Any] = field(default_factory=dict)
    workspace_before: tuple[Mapping[str, Any], ...] = ()
    workspace_after: tuple[Mapping[str, Any], ...] = ()
    workspace_changes: tuple[Mapping[str, Any], ...] = ()
    observation_state: str = "absent"
    source_inventory: tuple[Mapping[str, Any], ...] = ()
    capture_coverage: Mapping[str, Any] = field(default_factory=dict)


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
