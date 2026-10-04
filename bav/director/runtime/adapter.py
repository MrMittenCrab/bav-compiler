"""Cursor-first research runtime adapter with fail-closed native restrictions."""

from __future__ import annotations

import fcntl
import json
import math
import os
import select
import signal
import subprocess
import time
from pathlib import Path
from typing import Any, Mapping

from bav.director.repository import repository_root
from bav.director.runtime.contract import (
    INSTALLED_LAUNCH_CLOSED_REASON,
    SUPPORTED_PROVIDER_MODES,
    AllowanceCheckpoint,
    AllowanceLimits,
    AttemptRecord,
    BackendResult,
    CaptureRecord,
    NativeRestrictionState,
    ResearchRequest,
    cursor_unverified_restrictions,
    synthetic_controlled_restrictions,
)
from bav.director.runtime.dispatch import ApplicationDispatcher
from bav.director.runtime.policy import (
    build_cursor_command,
    fingerprint,
    intended_research_policy,
    provider_event_error,
    sanitize,
    snapshot_dict,
    validate_operation_request,
    validate_provider_envelope,
    validate_request_collection,
)
from bav.director.runtime.workspace import (
    IsolatedWorkspace,
    assert_no_repo_instructions,
    cleanup_workspace,
    create_isolated_workspace,
    isolated_environment,
)


_READ_CHUNK = 4096
_REAP_TIMEOUT_SECONDS = 2.0
_DRAIN_AFTER_KILL_BYTES = 4096


class ResearchRuntime:
    def __init__(
        self,
        *,
        model: str,
        backend: str = "cursor",
        provider_mode: str = "synthetic",
        provider_argv: list[str] | None = None,
        agent_bin: str | None = None,
        native_restriction: NativeRestrictionState | None = None,
        allowance: AllowanceLimits | None = None,
        timeout_seconds: float | None = None,
        retain_workspace: bool = False,
        checkout: Path | None = None,
        extra_env: Mapping[str, str] | None = None,
        checkpoint: AllowanceCheckpoint | None = None,
    ) -> None:
        if backend != "cursor":
            raise ValueError("only the Cursor backend is implemented; Codex is not selected")
        if not model or not str(model).strip():
            raise ValueError("explicit model is required; no silent selection")
        if provider_mode not in SUPPORTED_PROVIDER_MODES:
            raise ValueError(f"unknown provider mode: {provider_mode}")
        self.model = model
        self.backend = backend
        self.provider_mode = provider_mode
        self.provider_argv = list(provider_argv or [])
        self.agent_bin = agent_bin or "/Users/lizhiguo/.local/bin/agent"
        self.allowance = allowance or AllowanceLimits()
        if timeout_seconds is None:
            self.timeout_seconds = float(self.allowance.max_elapsed_seconds)
        else:
            _require_finite_positive_timeout(timeout_seconds)
            self.timeout_seconds = float(timeout_seconds)
        self.retain_workspace = retain_workspace
        self.checkout = (checkout or repository_root()).resolve()
        self.extra_env = {
            key: value
            for key, value in dict(extra_env or {}).items()
            if key not in {"CURSOR_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"}
        }
        self.backend_calls_attempted = 0
        self.backend_failures = 0
        self.tool_dispatches = 0
        self.elapsed_active_seconds = 0.0
        self.last_known_result_call_id: str | None = None
        self.last_status: str | None = None
        self.interrupted_uncertain = False
        self.known_result_call_ids: list[str] = []
        self.uncertain_attempt_call_ids: list[str] = []
        self._child: subprocess.Popen[bytes] | None = None
        self._interrupted = False
        self._active_started: float | None = None
        self.native = self._bound_restriction(native_restriction)
        if checkpoint is not None:
            self.restore(checkpoint)

    def _bound_restriction(
        self, supplied: NativeRestrictionState | None
    ) -> NativeRestrictionState:
        if self.provider_mode == "synthetic":
            return synthetic_controlled_restrictions()
        recorded = supplied or cursor_unverified_restrictions()
        if recorded.backend not in {self.backend, "cursor"}:
            return NativeRestrictionState(
                backend=self.backend,
                verified=False,
                reason=INSTALLED_LAUNCH_CLOSED_REASON,
                documented_controls=recorded.documented_controls,
                missing_controls=recorded.missing_controls
                + ("backend_identity",),
            )
        return NativeRestrictionState(
            backend=self.backend,
            verified=False,
            reason=INSTALLED_LAUNCH_CLOSED_REASON,
            documented_controls=recorded.documented_controls,
            missing_controls=recorded.missing_controls
            or cursor_unverified_restrictions().missing_controls,
        )

    def checkpoint(self) -> AllowanceCheckpoint:
        return AllowanceCheckpoint(
            backend_calls_attempted=self.backend_calls_attempted,
            backend_failures=self.backend_failures,
            tool_dispatches=self.tool_dispatches,
            elapsed_active_seconds=self.elapsed_active_seconds,
            last_known_result_call_id=self.last_known_result_call_id,
            last_status=self.last_status,
            interrupted_uncertain=self.interrupted_uncertain,
            known_result_call_ids=tuple(self.known_result_call_ids),
            uncertain_attempt_call_ids=tuple(self.uncertain_attempt_call_ids),
        )

    def restore(self, checkpoint: AllowanceCheckpoint) -> None:
        if not isinstance(checkpoint, AllowanceCheckpoint):
            raise ValueError("BAV-owned AllowanceCheckpoint is required")
        self.backend_calls_attempted = checkpoint.backend_calls_attempted
        self.backend_failures = checkpoint.backend_failures
        self.tool_dispatches = checkpoint.tool_dispatches
        self.elapsed_active_seconds = float(checkpoint.elapsed_active_seconds)
        self.last_known_result_call_id = checkpoint.last_known_result_call_id
        self.last_status = checkpoint.last_status
        self.interrupted_uncertain = checkpoint.interrupted_uncertain
        self.known_result_call_ids = list(checkpoint.known_result_call_ids)
        self.uncertain_attempt_call_ids = list(checkpoint.uncertain_attempt_call_ids)

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint: AllowanceCheckpoint,
        **kwargs: Any,
    ) -> ResearchRuntime:
        return cls(checkpoint=checkpoint, **kwargs)

    def remaining_elapsed_seconds(self) -> float:
        current = 0.0
        if self._active_started is not None:
            current = max(0.0, time.monotonic() - self._active_started)
        return max(
            0.0,
            float(self.allowance.max_elapsed_seconds) - self.elapsed_active_seconds - current,
        )

    def _recorded_elapsed_seconds(self) -> float:
        current = 0.0
        if self._active_started is not None:
            current = max(0.0, time.monotonic() - self._active_started)
        return self.elapsed_active_seconds + current

    def _calls_or_time_exhausted(self) -> bool:
        return (
            self.backend_calls_attempted >= self.allowance.max_backend_calls
            or self.tool_dispatches >= self.allowance.max_tool_dispatches
            or self.remaining_elapsed_seconds() <= 0
        )

    def _dispatch_blocked(self) -> bool:
        return (
            self.tool_dispatches >= self.allowance.max_tool_dispatches
            or self.remaining_elapsed_seconds() <= 0
        )

    def invoke(self, request: ResearchRequest) -> BackendResult:
        self._interrupted = False
        self._active_started = time.monotonic()
        try:
            return self._invoke(request)
        finally:
            started = self._active_started
            self._active_started = None
            if started is not None:
                self.elapsed_active_seconds += max(0.0, time.monotonic() - started)

    def _invoke(self, request: ResearchRequest) -> BackendResult:
        if self._calls_or_time_exhausted():
            return self._fail_closed(
                request,
                status="allowance_exhausted",
                error="elapsed, call or dispatch allowance exhausted",
            )
        self.backend_calls_attempted += 1
        invalid = self._validate_request(request)
        if invalid:
            return self._fail_closed(request, status="invalid_request", error=invalid)
        if self.provider_mode == "installed":
            return self._fail_closed(
                request,
                status="installed_launch_closed",
                error=INSTALLED_LAUNCH_CLOSED_REASON,
                details={
                    "missing_controls": list(self.native.missing_controls),
                    "caller_verified_ignored": True,
                    "company_context": request.snapshot.contains_company_context,
                    "bound_backend": self.backend,
                    "bound_executable": self.agent_bin,
                    "bound_model": self.model,
                    "policy_fingerprint": fingerprint(intended_research_policy()),
                },
            )
        remaining = self.remaining_elapsed_seconds()
        if remaining <= 0:
            return self._fail_closed(
                request,
                status="allowance_exhausted",
                error="elapsed allowance exhausted",
            )
        isolated = create_isolated_workspace(request.snapshot, checkout=self.checkout)
        try:
            assert_no_repo_instructions(isolated, self.checkout)
            return self._launch(request, isolated, remaining)
        finally:
            if not self.retain_workspace:
                cleanup_workspace(isolated)

    def interrupt(self) -> None:
        self._interrupted = True
        self._terminate_owned("interrupted")

    def _validate_request(self, request: ResearchRequest) -> str | None:
        if request.backend != "cursor" or request.backend != self.backend:
            return "inconsistent backend identity"
        if request.role not in {"planner", "reviewer"}:
            return "role must be planner or reviewer"
        if not request.model.strip() or request.model != self.model:
            return "inconsistent model identity"
        if request.provider_mode not in SUPPORTED_PROVIDER_MODES:
            return "unknown provider mode"
        if request.provider_mode != self.provider_mode:
            return "synthetic/installed mode confusion"
        if request.snapshot.role != request.role:
            return "snapshot role does not match request role"
        if request.runtime_version and self.provider_mode == "installed":
            return None
        return None

    def _launch(
        self,
        request: ResearchRequest,
        isolated: IsolatedWorkspace,
        remaining: float,
    ) -> BackendResult:
        argv = self._command(request, isolated)
        extra_env = dict(self.extra_env)
        extra_env["BAV_RUNTIME_WORKSPACE"] = str(isolated.workspace)
        extra_env["BAV_RUNTIME_ROLE"] = request.role
        extra_env["BAV_RUNTIME_MODEL"] = request.model
        env = isolated_environment(isolated, extra_env)
        call_timeout = min(self.timeout_seconds, remaining)
        timed_out = False
        interrupted = False
        overflowed = False
        exit_code: int | None = None
        stdout = b""
        stderr = b""
        try:
            self._child = subprocess.Popen(
                argv,
                cwd=str(isolated.workspace),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
            _set_nonblocking(self._child.stdout)
            _set_nonblocking(self._child.stderr)
            stdout, stderr, overflowed, timed_out, interrupted = self._consume_streams(
                self._child,
                timeout_seconds=call_timeout,
                max_bytes=self.allowance.max_output_bytes,
            )
            exit_code = self._child.returncode
        except OSError as exc:
            return self._finish(
                request,
                isolated,
                status="execution_failure",
                structured=None,
                attempts=(),
                exit_code=None,
                error=f"provider_spawn_failure:{exc}",
                timed_out=False,
                interrupted=False,
                output_bytes=0,
                env_names=tuple(sorted(env)),
                observed={},
                launched=False,
            )
        finally:
            self._child = None
        output_bytes = len(stdout) + len(stderr)
        if overflowed:
            return self._finish(
                request,
                isolated,
                status="malformed",
                structured=None,
                attempts=(),
                exit_code=exit_code,
                error="output_size_exceeded",
                timed_out=timed_out,
                interrupted=interrupted,
                output_bytes=output_bytes,
                env_names=tuple(sorted(env)),
                observed={},
                launched=True,
            )
        if self._interrupted or interrupted:
            return self._finish(
                request,
                isolated,
                status="interrupted",
                structured=None,
                attempts=(),
                exit_code=exit_code,
                error="provider_interrupted",
                timed_out=False,
                interrupted=True,
                output_bytes=output_bytes,
                env_names=tuple(sorted(env)),
                observed={},
                launched=True,
            )
        if timed_out:
            return self._finish(
                request,
                isolated,
                status="timeout",
                structured=None,
                attempts=(),
                exit_code=exit_code,
                error="provider_timeout",
                timed_out=True,
                interrupted=False,
                output_bytes=output_bytes,
                env_names=tuple(sorted(env)),
                observed=_safe_observed(stdout),
                launched=True,
            )
        parsed, parse_error = _parse_provider_output(stdout)
        if parse_error or parsed is None:
            return self._finish(
                request,
                isolated,
                status=_status_for_validation_error(parse_error),
                structured=None,
                attempts=(),
                exit_code=exit_code,
                error=parse_error or "malformed_provider_output",
                timed_out=False,
                interrupted=False,
                output_bytes=output_bytes,
                env_names=tuple(sorted(env)),
                observed=_safe_observed(stdout),
                launched=True,
            )
        envelope_error = validate_provider_envelope(
            parsed, exit_code=exit_code, expected_role=request.role
        )
        if envelope_error:
            return self._finish(
                request,
                isolated,
                status=_status_for_validation_error(envelope_error),
                structured=None,
                attempts=(),
                exit_code=exit_code,
                error=envelope_error,
                timed_out=False,
                interrupted=False,
                output_bytes=output_bytes,
                env_names=tuple(sorted(env)),
                observed=parsed.get("observed") if isinstance(parsed, dict) else {},
                launched=True,
            )
        if self._dispatch_blocked():
            return self._finish(
                request,
                isolated,
                status="allowance_exhausted",
                structured=None,
                attempts=(),
                exit_code=exit_code,
                error="dispatch_allowance_exhausted",
                timed_out=False,
                interrupted=False,
                output_bytes=output_bytes,
                env_names=tuple(sorted(env)),
                observed=parsed.get("observed") if isinstance(parsed, dict) else {},
                launched=True,
            )
        attempts, structured, reject = self._dispatch_requests(request, isolated, parsed)
        if reject:
            return self._finish(
                request,
                isolated,
                status=reject,
                structured=None,
                attempts=attempts,
                exit_code=exit_code,
                error="structured_output_rejected",
                timed_out=False,
                interrupted=False,
                output_bytes=output_bytes,
                env_names=tuple(sorted(env)),
                observed=parsed.get("observed") if isinstance(parsed, dict) else {},
                launched=True,
            )
        return self._finish(
            request,
            isolated,
            status="ok",
            structured=structured,
            attempts=attempts,
            exit_code=exit_code,
            error=None,
            timed_out=False,
            interrupted=False,
            output_bytes=output_bytes,
            env_names=tuple(sorted(env)),
            observed=parsed.get("observed") if isinstance(parsed, dict) else {},
            launched=True,
        )

    def _dispatch_requests(
        self,
        request: ResearchRequest,
        isolated: IsolatedWorkspace,
        payload: Mapping[str, Any],
    ) -> tuple[tuple[AttemptRecord, ...], Mapping[str, Any] | None, str | None]:
        items, collection_error = validate_request_collection(payload.get("requests"))
        if collection_error or items is None:
            return (
                (
                    AttemptRecord(
                        "unknown",
                        {},
                        "denied",
                        collection_error or "invalid_request_collection",
                        False,
                    ),
                ),
                None,
                "malformed",
            )
        dispatcher = ApplicationDispatcher(request.snapshot, isolated.workspace)
        attempts: list[AttemptRecord] = []
        rejected = False
        for item in items:
            validated = validate_operation_request(item)
            if isinstance(validated, str):
                attempts.append(
                    AttemptRecord(
                        str(item.get("operation") or "unknown"),
                        {},
                        "denied",
                        validated,
                        False,
                    )
                )
                rejected = True
                continue
            operation, arguments = validated
            if self._dispatch_blocked():
                attempts.append(
                    AttemptRecord(
                        operation,
                        arguments,
                        "denied",
                        "tool_dispatch_allowance_exhausted",
                        False,
                    )
                )
                rejected = True
                continue
            self.tool_dispatches += 1
            attempts.append(dispatcher.handle(operation, arguments))
        if rejected:
            return tuple(attempts), None, "malformed"
        output = payload.get("output")
        if not isinstance(output, Mapping) or "kind" not in output:
            return tuple(attempts), None, "malformed"
        return tuple(attempts), dict(output), None

    def _command(self, request: ResearchRequest, isolated: IsolatedWorkspace) -> list[str]:
        if self.provider_mode == "synthetic":
            if not self.provider_argv:
                raise ValueError("synthetic provider argv is required")
            return list(self.provider_argv)
        return build_cursor_command(
            agent_bin=self.agent_bin,
            workspace=isolated.workspace,
            model=request.model,
        )

    def _consume_streams(
        self,
        child: subprocess.Popen[bytes],
        *,
        timeout_seconds: float,
        max_bytes: int,
    ) -> tuple[bytes, bytes, bool, bool, bool]:
        stdout_buf = bytearray()
        stderr_buf = bytearray()
        deadline = time.monotonic() + max(0.0, timeout_seconds)
        overflowed = False
        timed_out = False
        interrupted = False
        stdout = child.stdout
        stderr = child.stderr
        streams = {
            stdout: stdout_buf,
            stderr: stderr_buf,
        }
        open_streams = {stream for stream in streams if stream is not None}
        try:
            while open_streams:
                if self._interrupted:
                    interrupted = True
                    self._terminate_owned("interrupted")
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    timed_out = True
                    self._terminate_owned("timeout")
                    break
                readable, _, _ = select.select(list(open_streams), [], [], min(0.1, remaining))
                if not readable:
                    if child.poll() is not None:
                        leftover, extra_overflow = self._drain_remaining(
                            open_streams, streams, max_bytes
                        )
                        overflowed = overflowed or extra_overflow
                        open_streams -= leftover
                        break
                    continue
                for stream in readable:
                    chunk = _read_available(stream, _READ_CHUNK)
                    if chunk is None:
                        continue
                    if not chunk:
                        open_streams.discard(stream)
                        continue
                    budget = max_bytes - (len(stdout_buf) + len(stderr_buf))
                    if budget <= 0:
                        overflowed = True
                        self._terminate_owned("output_size_exceeded")
                        open_streams.clear()
                        break
                    if len(chunk) > budget:
                        streams[stream].extend(chunk[:budget])
                        overflowed = True
                        self._terminate_owned("output_size_exceeded")
                        open_streams.clear()
                        break
                    streams[stream].extend(chunk)
                if overflowed:
                    break
            if overflowed or timed_out or interrupted:
                self._bounded_reap(child)
            elif child.poll() is None:
                try:
                    child.wait(timeout=max(0.0, deadline - time.monotonic()))
                except subprocess.TimeoutExpired:
                    timed_out = True
                    self._terminate_owned("timeout")
                    self._bounded_reap(child)
        finally:
            for stream in (stdout, stderr):
                if stream is not None:
                    try:
                        stream.close()
                    except OSError:
                        pass
        return bytes(stdout_buf), bytes(stderr_buf), overflowed, timed_out, interrupted

    def _drain_remaining(
        self,
        open_streams: set[Any],
        streams: dict[Any, bytearray],
        max_bytes: int,
    ) -> tuple[set[Any], bool]:
        closed: set[Any] = set()
        overflowed = False
        for stream in list(open_streams):
            try:
                chunk = _read_available(stream, _DRAIN_AFTER_KILL_BYTES) or b""
            except OSError:
                closed.add(stream)
                continue
            if not chunk:
                closed.add(stream)
                continue
            used = sum(len(buf) for buf in streams.values())
            budget = max_bytes - used
            if budget <= 0:
                overflowed = True
                closed.add(stream)
                continue
            streams[stream].extend(chunk[:budget])
            if len(chunk) > budget:
                overflowed = True
            closed.add(stream)
        return closed, overflowed

    def _bounded_reap(self, child: subprocess.Popen[bytes]) -> None:
        try:
            child.wait(timeout=_REAP_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                try:
                    child.kill()
                except OSError:
                    return
            try:
                child.wait(timeout=_REAP_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                return

    def _terminate_owned(self, reason: str) -> None:
        child = self._child
        if child is None or child.poll() is not None:
            return
        try:
            os.killpg(child.pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError, OSError):
            try:
                child.terminate()
            except OSError:
                return
        try:
            child.wait(timeout=_REAP_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                try:
                    child.kill()
                except OSError:
                    return

    def _fail_closed(
        self,
        request: ResearchRequest,
        *,
        status: str,
        error: str | None,
        details: Mapping[str, Any] | None = None,
    ) -> BackendResult:
        self.backend_failures += 1
        return self._result(
            request,
            status=status,
            error=error,
            launched=False,
            details=details,
        )

    def _result(
        self,
        request: ResearchRequest,
        *,
        status: str,
        error: str | None,
        launched: bool,
        details: Mapping[str, Any] | None = None,
    ) -> BackendResult:
        self.last_status = status
        if status == "interrupted":
            self.interrupted_uncertain = True
            self.uncertain_attempt_call_ids.append(request.call_id)
        capture = self._capture(
            request,
            attempts=(),
            exit_code=None,
            error=error,
            timed_out=status == "timeout",
            interrupted=status == "interrupted",
            output_bytes=0,
            cwd=None,
            workspace=None,
            env_names=(),
            observed={},
            launched=launched,
        )
        return BackendResult(
            call_id=request.call_id,
            role=request.role,
            status=status,  # type: ignore[arg-type]
            model=request.model,
            runtime_name=self.backend,
            runtime_version=request.runtime_version,
            structured_output=None,
            attempts=(),
            capture=capture,
            known_result=False,
            retried=False,
            details=dict(details or {}),
        )

    def _finish(
        self,
        request: ResearchRequest,
        isolated: IsolatedWorkspace,
        *,
        status: str,
        structured: Mapping[str, Any] | None,
        attempts: tuple[AttemptRecord, ...],
        exit_code: int | None,
        error: str | None,
        timed_out: bool,
        interrupted: bool,
        output_bytes: int,
        env_names: tuple[str, ...],
        observed: Mapping[str, Any] | None,
        launched: bool,
    ) -> BackendResult:
        if status != "ok":
            self.backend_failures += 1
        self.last_status = status
        known = structured is not None and status == "ok"
        if known:
            self.last_known_result_call_id = request.call_id
            self.known_result_call_ids.append(request.call_id)
        if interrupted or status == "interrupted":
            self.interrupted_uncertain = True
            self.uncertain_attempt_call_ids.append(request.call_id)
        capture = self._capture(
            request,
            attempts=attempts,
            exit_code=exit_code,
            error=error,
            timed_out=timed_out,
            interrupted=interrupted,
            output_bytes=output_bytes,
            cwd=str(isolated.workspace),
            workspace=str(isolated.workspace),
            env_names=env_names,
            observed=dict(observed or {}),
            launched=launched,
        )
        return BackendResult(
            call_id=request.call_id,
            role=request.role,
            status=status,  # type: ignore[arg-type]
            model=request.model,
            runtime_name=self.backend,
            runtime_version=(
                None
                if structured is None
                else str((observed or {}).get("runtime_version") or request.runtime_version or "")
                or request.runtime_version
            ),
            structured_output=structured,
            attempts=attempts,
            capture=capture,
            known_result=known,
            retried=False,
        )

    def _capture(
        self,
        request: ResearchRequest,
        *,
        attempts: tuple[AttemptRecord, ...],
        exit_code: int | None,
        error: str | None,
        timed_out: bool,
        interrupted: bool,
        output_bytes: int,
        cwd: str | None,
        workspace: str | None,
        env_names: tuple[str, ...],
        observed: Mapping[str, Any],
        launched: bool,
    ) -> CaptureRecord:
        request_payload = sanitize(
            {
                "call_id": request.call_id,
                "role": request.role,
                "model": request.model,
                "backend": request.backend,
                "provider_mode": request.provider_mode,
                "snapshot_hash": request.snapshot.content_hash,
            }
        )
        context_payload = sanitize(snapshot_dict(request.snapshot))
        decisions = tuple(
            {"operation": item.operation, "decision": item.decision, "reason": item.reason}
            for item in attempts
        )
        tool_results = tuple(
            {"operation": item.operation, "executed": item.executed, "result": item.result}
            for item in attempts
        )
        return CaptureRecord(
            call_id=request.call_id,
            role=request.role,
            request_fingerprint=fingerprint(request_payload),
            context_fingerprint=fingerprint(context_payload),
            policy_fingerprint=fingerprint(
                {
                    "policy": intended_research_policy(),
                    "restriction": self.native.reason,
                    "verified": False,
                    "bound_backend": self.backend,
                    "bound_executable": self.agent_bin,
                    "bound_model": self.model,
                    "provider_mode": self.provider_mode,
                }
            ),
            runtime_name=self.backend,
            runtime_version=request.runtime_version,
            model=request.model,
            attempted_operations=attempts,
            decisions=decisions,
            tool_results=tool_results,
            exit_code=exit_code,
            error=error,
            timed_out=timed_out,
            interrupted=interrupted,
            elapsed_ms=int(self._recorded_elapsed_seconds() * 1000),
            output_bytes=output_bytes,
            cwd=cwd,
            workspace=workspace,
            env_names=env_names,
            observed=sanitize(observed),
            backend_calls_attempted=self.backend_calls_attempted,
            backend_failures=self.backend_failures,
            launched=launched,
            elapsed_active_ms=int(self._recorded_elapsed_seconds() * 1000),
            remaining_elapsed_seconds=self.remaining_elapsed_seconds(),
            tool_dispatches=self.tool_dispatches,
        )


def _set_nonblocking(stream) -> None:
    if stream is None:
        return
    flags = fcntl.fcntl(stream.fileno(), fcntl.F_GETFL)
    fcntl.fcntl(stream.fileno(), fcntl.F_SETFL, flags | os.O_NONBLOCK)


def _read_available(stream, size: int) -> bytes | None:
    try:
        return os.read(stream.fileno(), size)
    except BlockingIOError:
        return None


def _require_finite_positive_timeout(value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("timeout_seconds must be a finite positive limit")
    if not math.isfinite(value) or value <= 0:
        raise ValueError("timeout_seconds must be a finite positive limit")


def _status_for_validation_error(code: str | None) -> str:
    if code in {
        "unsuccessful_provider_exit",
        "provider_error_indicator",
        "provider_error_event",
    }:
        return "execution_failure"
    return "malformed"


def _parse_provider_output(stdout: bytes) -> tuple[dict[str, Any] | None, str | None]:
    if not stdout:
        return None, "missing_provider_output"
    text = stdout.decode("utf-8", errors="replace").strip()
    if not text:
        return None, "missing_provider_output"
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        events, parse_error = _parse_provider_stream(text)
        if parse_error or events is None:
            return None, parse_error or "truncated_or_malformed_output"
        return _select_validated_stream_result(events)
    if not isinstance(payload, dict):
        return None, "provider_output_not_object"
    return payload, None


def _parse_provider_stream(
    text: str,
) -> tuple[list[dict[str, Any]] | None, str | None]:
    events: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            return None, "truncated_or_malformed_output"
        if not isinstance(item, dict):
            return None, "provider_output_not_object"
        events.append(item)
    if not events:
        return None, "truncated_or_malformed_output"
    return events, None


def _select_validated_stream_result(
    events: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, str | None]:
    for event in events:
        error = provider_event_error(event)
        if error:
            return None, error
    final = next((item for item in reversed(events) if item.get("type") == "result"), None)
    if final is None:
        return None, "missing_result"
    return _combine_stream_result(events, final), None


def _combine_stream_result(
    events: list[dict[str, Any]],
    final: Mapping[str, Any],
) -> dict[str, Any]:
    combined = dict(final)
    collected: list[Any] = []
    for event in events:
        if event.get("type") == "request":
            collected.append(event.get("request") or event)
        elif event.get("type") != "result" and "operation" in event:
            collected.append(event.get("request") or event)
    if collected:
        combined["requests"] = collected
    return combined


def _safe_observed(stdout: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(stdout.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {}
    if isinstance(payload, dict) and isinstance(payload.get("observed"), dict):
        return dict(payload["observed"])
    return {}
