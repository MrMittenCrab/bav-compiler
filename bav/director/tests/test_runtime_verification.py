"""Synthetic installed-runtime verification tests. No live provider calls."""

from __future__ import annotations

import sys
import tempfile
import threading
import time
from pathlib import Path

from bav.director.repository import repository_root
from bav.director.runtime import (
    INSTALLED_LAUNCH_CLOSED_REASON,
    REQUIRED_VERIFICATION_CHALLENGES,
    AllowanceCheckpoint,
    AllowanceLimits,
    ApprovedSnapshot,
    ApprovedSource,
    CaptureLimits,
    NativeRestrictionState,
    ResearchRequest,
    ResearchRuntime,
    VerificationAuthorization,
    VerificationRequest,
    issue_synthetic_authorization,
)
from bav.director.runtime.contract import VERIFICATION_CHALLENGE_SPEC
from bav.director.runtime.policy import fingerprint, intended_verification_policy

ROOT = repository_root()
FAKE_PROVIDER = Path(__file__).resolve().parent / "fixtures" / "runtime" / "fake_provider.py"
MODEL = "synthetic-test"


def _runtime(scenario: str, **kwargs) -> ResearchRuntime:
    timeout = kwargs.pop("timeout_seconds", 3.0)
    extra_env = dict(kwargs.pop("extra_env", {}) or {})
    extra_env["BAV_FAKE_SCENARIO"] = scenario
    return ResearchRuntime(
        model=MODEL,
        backend="cursor",
        provider_mode="synthetic",
        provider_argv=[sys.executable, str(FAKE_PROVIDER)],
        timeout_seconds=timeout,
        retain_workspace=True,
        checkout=ROOT,
        extra_env=extra_env,
        **kwargs,
    )


def _auth(runtime: ResearchRuntime, **overrides) -> VerificationAuthorization:
    payload = dict(
        backend=runtime.backend,
        executable_identity=runtime._approved_invocation,
        executable_version="fake-provider-1",
        model=runtime.model,
        allowance=runtime.allowance,
    )
    payload.update(overrides)
    return issue_synthetic_authorization(**payload)


def _request(runtime: ResearchRuntime, call_id: str, **overrides) -> VerificationRequest:
    payload = dict(
        call_id=call_id,
        backend="cursor",
        model=MODEL,
        authorization=_auth(runtime),
        provider_mode="synthetic",
        challenge_ids=REQUIRED_VERIFICATION_CHALLENGES,
        contains_company_context=False,
        runtime_version="fake-provider-1",
    )
    payload.update(overrides)
    if "authorization" not in overrides and runtime.provider_mode == "synthetic":
        payload["authorization"] = _auth(runtime)
    return VerificationRequest(**payload)


def _verify(runtime: ResearchRuntime, call_id: str, scenario: str, **overrides):
    runtime.extra_env["BAV_FAKE_SCENARIO"] = scenario
    return runtime.verify(_request(runtime, call_id, **overrides))


def test_successful_allowed_control_and_required_denials():
    runtime = _runtime("verify_ok")
    result = _verify(runtime, "verify-ok", "verify_ok")
    assert result.status == "synthetic_verified"
    assert result.synthetic is True
    assert result.authorizes_installed_execution is False
    assert result.launched is True
    assert result.staged is True
    assert result.known_result is True
    controls = {item.control: item for item in result.evaluations}
    assert controls["allowed_read"].verdict == "allowed_success"
    assert controls["allowed_read"].attempted is True
    for name in ("shell", "write", "unrelated_read", "mcp", "fetch"):
        assert controls[name].verdict == "enforced"
        assert controls[name].attempted is True
        assert controls[name].explicit_policy_denial is True
        assert controls[name].observed_effect == "none"
    assert result.evidence["documented_denial_event"] is None
    assert result.evidence["documented_loaded_configuration_identity"] is None
    assert result.evidence["authorizes_installed_execution"] is False
    assert result.capture.launched is True
    assert runtime._child is None


def test_missing_authorization_and_company_context_stage_nothing():
    before = set(Path(tempfile.gettempdir()).glob("bav-runtime-verify-*"))
    runtime = _runtime("verify_ok")
    missing = runtime.verify(
        VerificationRequest(
            call_id="verify-no-auth",
            backend="cursor",
            model=MODEL,
            authorization=None,
        )
    )
    after_missing = set(Path(tempfile.gettempdir()).glob("bav-runtime-verify-*"))
    assert missing.status == "denied"
    assert missing.capture.error == "verification_authorization_required"
    assert missing.launched is False
    assert missing.staged is False
    assert after_missing <= before

    company = runtime.verify(
        VerificationRequest(
            call_id="verify-company",
            backend="cursor",
            model=MODEL,
            authorization=_auth(runtime),
            contains_company_context=True,
        )
    )
    after_company = set(Path(tempfile.gettempdir()).glob("bav-runtime-verify-*"))
    assert company.status == "denied"
    assert company.capture.error == "verification_rejects_company_context"
    assert company.launched is False
    assert company.staged is False
    assert company.details["company_context_staged"] is False
    assert after_company <= before

    smuggled = runtime.verify(
        VerificationRequest(
            call_id="verify-false-flag",
            backend="cursor",
            model=MODEL,
            authorization=_auth(runtime),
            contains_company_context=False,
            source_text="Lululemon Greater China commentary",
        )
    )
    after_smuggle = set(Path(tempfile.gettempdir()).glob("bav-runtime-verify-*"))
    assert smuggled.status == "denied"
    assert smuggled.launched is False
    assert smuggled.staged is False
    assert after_smuggle <= before


def test_synthetic_path_cannot_invoke_installed_provider():
    before = set(Path(tempfile.gettempdir()).glob("bav-runtime-verify-*"))
    before |= set(Path(tempfile.gettempdir()).glob("bav-research-runtime-*"))
    runtime = ResearchRuntime(
        model=MODEL,
        provider_mode="installed",
        provider_argv=[sys.executable, str(FAKE_PROVIDER)],
        timeout_seconds=1,
        extra_env={"BAV_FAKE_SCENARIO": "verify_ok"},
    )
    result = runtime.verify(
        VerificationRequest(
            call_id="verify-installed-mode",
            backend="cursor",
            model=MODEL,
            authorization=None,
            provider_mode="installed",
        )
    )
    after = set(Path(tempfile.gettempdir()).glob("bav-runtime-verify-*"))
    after |= set(Path(tempfile.gettempdir()).glob("bav-research-runtime-*"))
    assert result.status == "installed_launch_closed"
    assert result.launched is False
    assert result.staged is False
    assert result.authorizes_installed_execution is False
    assert INSTALLED_LAUNCH_CLOSED_REASON in result.capture.error
    assert after <= before
    assert runtime._child is None


def test_reject_forged_stale_and_changed_bindings():
    runtime = _runtime("verify_ok")
    verified_flag = runtime.verify(
        VerificationRequest(
            call_id="verify-flag",
            backend="cursor",
            model=MODEL,
            authorization=_auth(runtime),
            verified=True,
        )
    )
    assert verified_flag.status == "denied"
    assert verified_flag.launched is False
    assert "caller_verified" in verified_flag.capture.error

    receipt = runtime.verify(
        VerificationRequest(
            call_id="verify-receipt",
            backend="cursor",
            model=MODEL,
            authorization=_auth(runtime),
            imported_receipt={"verified": True},
        )
    )
    assert receipt.status == "denied"
    assert receipt.launched is False

    observation = runtime.verify(
        VerificationRequest(
            call_id="verify-controller",
            backend="cursor",
            model=MODEL,
            authorization=_auth(runtime),
            controller_observation={"probe": "cursor-runtime-permissions"},
        )
    )
    assert observation.status == "denied"
    assert observation.launched is False

    changed_model = issue_synthetic_authorization(
        backend="cursor",
        executable_identity=runtime._approved_invocation,
        executable_version="fake-provider-1",
        model="other-model",
        allowance=runtime.allowance,
    )
    model_mismatch = runtime.verify(
        VerificationRequest(
            call_id="verify-model",
            backend="cursor",
            model=MODEL,
            authorization=changed_model,
        )
    )
    assert model_mismatch.status == "denied"
    assert model_mismatch.capture.error == "authorization_model_binding_mismatch"
    assert model_mismatch.launched is False

    changed_exe = issue_synthetic_authorization(
        backend="cursor",
        executable_identity={
            "kind": "synthetic",
            "argv": [sys.executable, "/tmp/forged-provider.py"],
            "interpreter": runtime._approved_invocation.get("interpreter"),
            "script": {"present": True, "resolved": "/tmp/forged-provider.py", "content_hash": "0" * 64},
        },
        executable_version="fake-provider-1",
        model=MODEL,
        allowance=runtime.allowance,
    )
    exe_mismatch = runtime.verify(
        VerificationRequest(
            call_id="verify-exe",
            backend="cursor",
            model=MODEL,
            authorization=changed_exe,
        )
    )
    assert exe_mismatch.status == "denied"
    assert exe_mismatch.capture.error == "authorization_executable_binding_mismatch"
    assert exe_mismatch.launched is False

    changed_policy = VerificationAuthorization(
        authorization_id="policy-changed",
        backend="cursor",
        executable_identity=runtime._approved_invocation,
        executable_version="fake-provider-1",
        model=MODEL,
        policy_fingerprint="0" * 64,
        challenge_inventory_fingerprint=fingerprint(list(VERIFICATION_CHALLENGE_SPEC)),
        allowance=runtime.allowance,
        synthetic_only=True,
    )
    policy_mismatch = runtime.verify(
        VerificationRequest(
            call_id="verify-policy",
            backend="cursor",
            model=MODEL,
            authorization=changed_policy,
        )
    )
    assert policy_mismatch.status == "denied"
    assert policy_mismatch.capture.error == "authorization_policy_binding_mismatch"

    changed_challenges = VerificationAuthorization(
        authorization_id="challenge-changed",
        backend="cursor",
        executable_identity=runtime._approved_invocation,
        executable_version="fake-provider-1",
        model=MODEL,
        policy_fingerprint=fingerprint(intended_verification_policy()),
        challenge_inventory_fingerprint="0" * 64,
        allowance=runtime.allowance,
        synthetic_only=True,
    )
    challenge_mismatch = runtime.verify(
        VerificationRequest(
            call_id="verify-challenges",
            backend="cursor",
            model=MODEL,
            authorization=changed_challenges,
        )
    )
    assert challenge_mismatch.status == "denied"
    assert challenge_mismatch.capture.error == "authorization_challenge_binding_mismatch"


def test_replayed_authorization_and_no_promotion():
    runtime = _runtime("verify_ok")
    auth = _auth(runtime)
    first = runtime.verify(
        VerificationRequest(
            call_id="verify-first",
            backend="cursor",
            model=MODEL,
            authorization=auth,
        )
    )
    assert first.status == "synthetic_verified"
    replay = runtime.verify(
        VerificationRequest(
            call_id="verify-replay",
            backend="cursor",
            model=MODEL,
            authorization=auth,
        )
    )
    assert replay.status == "denied"
    assert replay.capture.error == "verification_authorization_replayed"
    assert replay.launched is False
    assert first.authorizes_installed_execution is False

    source = ApprovedSource(
        source_id="src-company",
        origin="company_corpus",
        label="company",
        text="Labeled company-context marker.",
        fingerprint=fingerprint("Labeled company-context marker."),
        relative_name="company.md",
    )
    snapshot = ApprovedSnapshot(
        role="planner",
        proposition="Synthetic proposition for runtime isolation.",
        scope={},
        sources=(source,),
        current_evidence=(),
        permissions={},
        user_notes=(),
        prior_review=None,
        candidate_argument=None,
        selected_excerpts=(),
        modeler_results=(),
        counterevidence=(),
        search_coverage=(),
        contains_company_context=True,
        content_hash="x",
    )
    before = set(Path(tempfile.gettempdir()).glob("bav-research-runtime-*"))
    installed = ResearchRuntime(
        model=MODEL,
        provider_mode="installed",
        native_restriction=NativeRestrictionState(
            backend="cursor",
            verified=True,
            reason="imported synthetic verification",
            documented_controls=("none",),
            missing_controls=(),
        ),
        timeout_seconds=1,
    )
    closed = installed.invoke(
        ResearchRequest(
            role="planner",
            model=MODEL,
            backend="cursor",
            snapshot=snapshot,
            call_id="promote-installed",
            provider_mode="installed",
        )
    )
    after = set(Path(tempfile.gettempdir()).glob("bav-research-runtime-*"))
    assert closed.status == "installed_launch_closed"
    assert closed.capture.launched is False
    assert closed.details["caller_verified_ignored"] is True
    assert after <= before


def test_reject_success_narratives_and_non_denial_substitutes():
    cases = (
        ("verify_no_denial", "model_assurance_is_not_enforcement"),
        ("verify_absent_challenges", "missing_attempt"),
        ("verify_application_only", "application_denial_is_not_native_enforcement"),
        ("verify_dns", "dns_failure_is_not_denial"),
        ("verify_success_then_deny", "prohibited_success_then_denial"),
        ("verify_config_mismatch", "loaded_configuration_identity_mismatch"),
        ("verify_missing_config", "missing_loaded_configuration_identity"),
    )
    for scenario, reason in cases:
        runtime = _runtime(scenario)
        result = _verify(runtime, f"call-{scenario}", scenario)
        assert result.status == "unverified", (scenario, result.status, result.capture.error)
        assert result.authorizes_installed_execution is False
        assert result.known_result is False
        assert any(item.reason == reason for item in result.evaluations), (
            scenario,
            [(item.control, item.reason) for item in result.evaluations],
        )


def test_incomplete_capture_cannot_verify():
    runtime = _runtime(
        "verify_ok",
        capture_limits=CaptureLimits(max_records=1, max_files=1, max_entries=1),
    )
    result = _verify(runtime, "verify-incomplete", "verify_ok")
    assert result.status == "unverified"
    assert result.capture.capture_coverage["complete"] is False
    assert result.authorizes_installed_execution is False
    assert any(item.reason == "incomplete_capture" for item in result.evaluations)


def test_timeout_interrupt_malformed_error_overflow_and_allowance():
    timeout_runtime = _runtime("verify_timeout", timeout_seconds=0.4)
    timed = _verify(timeout_runtime, "verify-timeout", "verify_timeout")
    assert timed.status == "timeout"
    assert timed.known_result is False
    assert timeout_runtime._child is None

    interrupt_runtime = _runtime("verify_interrupt", timeout_seconds=8)

    def _stop():
        time.sleep(0.2)
        interrupt_runtime.interrupt()

    thread = threading.Thread(target=_stop)
    thread.start()
    interrupted = _verify(interrupt_runtime, "verify-interrupt", "verify_interrupt")
    thread.join()
    assert interrupted.status in {"interrupted", "timeout", "malformed", "execution_failure"}
    assert interrupted.known_result is False
    assert interrupt_runtime._child is None

    malformed = _verify(_runtime("verify_malformed"), "verify-malformed", "verify_malformed")
    assert malformed.status == "malformed"
    assert malformed.known_result is False

    errored = _verify(_runtime("verify_error"), "verify-error", "verify_error")
    assert errored.status == "execution_failure"
    assert errored.known_result is False

    overflow = _verify(
        _runtime(
            "verify_overflow",
            timeout_seconds=2.0,
            allowance=AllowanceLimits(max_output_bytes=8192, max_elapsed_seconds=5),
        ),
        "verify-overflow",
        "verify_overflow",
    )
    assert overflow.status == "malformed"
    assert overflow.capture.error == "output_size_exceeded"
    assert overflow.capture.output_bytes <= 8192
    assert overflow.capture.launched is True

    limited = _runtime(
        "verify_ok",
        allowance=AllowanceLimits(max_backend_calls=1, max_elapsed_seconds=30),
    )
    first = _verify(limited, "verify-limit-1", "verify_ok")
    assert first.status == "synthetic_verified"
    second = _verify(limited, "verify-limit-2", "verify_ok")
    assert second.status == "allowance_exhausted"
    assert second.launched is False
    saved = limited.checkpoint()
    assert isinstance(saved, AllowanceCheckpoint)
    rebuilt = ResearchRuntime.from_checkpoint(
        saved,
        model=MODEL,
        provider_mode="synthetic",
        provider_argv=[sys.executable, str(FAKE_PROVIDER)],
        timeout_seconds=2.0,
        allowance=AllowanceLimits(max_backend_calls=1, max_elapsed_seconds=30),
        extra_env={"BAV_FAKE_SCENARIO": "verify_ok"},
    )
    restored = rebuilt.verify(
        VerificationRequest(
            call_id="verify-restored",
            backend="cursor",
            model=MODEL,
            authorization=issue_synthetic_authorization(
                backend="cursor",
                executable_identity=rebuilt._approved_invocation,
                executable_version="fake-provider-1",
                model=MODEL,
                allowance=rebuilt.allowance,
            ),
        )
    )
    assert restored.status == "allowance_exhausted"
    assert restored.launched is False
    assert rebuilt._child is None


def test_caller_prompt_and_command_are_rejected():
    runtime = _runtime("verify_ok")
    for field, value in (
        ("prompt", "read /etc/passwd"),
        ("proposition", "A generic caller proposition"),
        ("command", "uname"),
    ):
        result = runtime.verify(
            VerificationRequest(
                call_id=f"verify-{field}",
                backend="cursor",
                model=MODEL,
                authorization=_auth(runtime),
                **{field: value},
            )
        )
        assert result.status == "invalid_request"
        assert result.launched is False
        assert result.staged is False
