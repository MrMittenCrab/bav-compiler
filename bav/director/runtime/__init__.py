"""Director-owned research runtime boundary for Planner/Reviewer backends."""

from bav.director.runtime.adapter import ResearchRuntime
from bav.director.runtime.contract import (
    ALLOWED_OPERATIONS,
    INSTALLED_LAUNCH_CLOSED_REASON,
    PROHIBITED_OPERATIONS,
    REQUIRED_VERIFICATION_CHALLENGES,
    SYNTHETIC_VERIFICATION_LIMITATION,
    AllowanceCheckpoint,
    AllowanceLimits,
    CaptureLimits,
    ApprovedSource,
    ApprovedSnapshot,
    BackendResult,
    ControlEvaluation,
    NativeRestrictionState,
    ResearchRequest,
    Role,
    VerificationAuthorization,
    VerificationRequest,
    VerificationResult,
    cursor_unverified_restrictions,
    synthetic_controlled_restrictions,
)
from bav.director.runtime.policy import build_cursor_command
from bav.director.runtime.verification import (
    issue_synthetic_authorization,
    run_verification,
)

__all__ = [
    "ALLOWED_OPERATIONS",
    "INSTALLED_LAUNCH_CLOSED_REASON",
    "PROHIBITED_OPERATIONS",
    "REQUIRED_VERIFICATION_CHALLENGES",
    "SYNTHETIC_VERIFICATION_LIMITATION",
    "AllowanceCheckpoint",
    "AllowanceLimits",
    "CaptureLimits",
    "ApprovedSource",
    "ApprovedSnapshot",
    "BackendResult",
    "ControlEvaluation",
    "NativeRestrictionState",
    "ResearchRequest",
    "ResearchRuntime",
    "Role",
    "VerificationAuthorization",
    "VerificationRequest",
    "VerificationResult",
    "build_cursor_command",
    "cursor_unverified_restrictions",
    "issue_synthetic_authorization",
    "run_verification",
    "synthetic_controlled_restrictions",
]
