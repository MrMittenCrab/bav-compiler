"""Cursor-first research runtime adapter with fail-closed native restrictions."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Any, Mapping

from bav.director.repository import repository_root
from bav.director.runtime.contract import (
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
    sanitize,
    snapshot_dict,
)
from bav.director.runtime.workspace import (
    IsolatedWorkspace,
    assert_no_repo_instructions,
    cleanup_workspace,
    create_isolated_workspace,
    isolated_environment,
    workspace_file_names,
)


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
    ) -> None:
        if backend != "cursor":
            raise ValueError("only the Cursor backend is implemented; Codex is not selected")
        if not model or not str(model).strip():
            raise ValueError("explicit model is required; no silent selection")
        self.model = model
        self.backend = backend
        self.provider_mode = provider_mode
        self.provider_argv = list(provider_argv or [])
        self.agent_bin = agent_bin or "/Users/lizhiguo/.local/bin/agent"
        if provider_mode == "installed":
            self.native = native_restriction or cursor_unverified_restrictions()
        else:
            self.native = native_restriction or synthetic_controlled_restrictions()
        self.allowance = allowance or AllowanceLimits()
        self.timeout_seconds = (
            self.allowance.max_elapsed_seconds if timeout_seconds is None else timeout_seconds
        )
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
        self._child: subprocess.Popen[bytes] | None = None
        self._interrupted = False

    def invoke(self, request: ResearchRequest) -> BackendResult:
        self._interrupted = False
        if self.backend_calls_attempted >= self.allowance.max_backend_calls:
            return self._result(
                request,
                status="allowance_exhausted",
                error="backend call allowance exhausted",
                launched=False,
            )
        self.backend_calls_attempted += 1
        invalid = self._validate_request(request)
        if invalid:
            self.backend_failures += 1
            return self._result(request, status="invalid_request", error=invalid, launched=False)
        if request.snapshot.contains_company_context and not self.native.verified:
            self.backend_failures += 1
            return self._result(
                request,
                status="native_restriction_unverified",
                error=self.native.reason,
                launched=False,
                details={"missing_controls": list(self.native.missing_controls)},
            )
        isolated = create_isolated_workspace(request.snapshot, checkout=self.checkout)
        try:
            assert_no_repo_instructions(isolated, self.checkout)
            return self._launch(request, isolated)
        finally:
            if not self.retain_workspace:
                cleanup_workspace(isolated)

    def interrupt(self) -> None:
        self._interrupted = True
        self._terminate_owned("interrupted")

    def _validate_request(self, request: ResearchRequest) -> str | None:
        if request.backend != "cursor":
            return "only the Cursor backend is implemented"
        if request.role not in {"planner", "reviewer"}:
            return "role must be planner or reviewer"
        if not request.model.strip():
            return "explicit model is required"
        if request.provider_mode != self.provider_mode:
            return "provider mode does not match runtime"
        if request.snapshot.role != request.role:
            return "snapshot role does not match request role"
        if request.snapshot.contains_company_context and any(
            source.origin == "synthetic" and request.provider_mode == "installed"
            for source in request.snapshot.sources
        ):
            return None
        return None

    def _launch(self, request: ResearchRequest, isolated: IsolatedWorkspace) -> BackendResult:
        argv = self._command(request, isolated)
        extra_env = dict(self.extra_env)
        if self.provider_mode == "synthetic":
            extra_env["BAV_RUNTIME_WORKSPACE"] = str(isolated.workspace)
            extra_env["BAV_RUNTIME_ROLE"] = request.role
            extra_env["BAV_RUNTIME_MODEL"] = request.model
        env = isolated_environment(isolated, extra_env)
        started = time.monotonic()
        timed_out = False
        interrupted = False
        exit_code: int | None = None
        stdout = b""
        stderr = b""
        error = None
        try:
            self._child = subprocess.Popen(
                argv,
                cwd=str(isolated.workspace),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
            try:
                stdout, stderr = self._child.communicate(timeout=self.timeout_seconds)
                exit_code = self._child.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
                self._terminate_owned("timeout")
                leftover = self._child.communicate(timeout=2)
                stdout, stderr = leftover
                exit_code = self._child.returncode
            except KeyboardInterrupt:
                interrupted = True
                self._interrupted = True
                self._terminate_owned("interrupted")
                exit_code = self._child.returncode if self._child else None
        except OSError as exc:
            error = f"provider_spawn_failure:{exc}"
            self.backend_failures += 1
            return self._finish(
                request,
                isolated,
                status="execution_failure",
                structured=None,
                attempts=(),
                exit_code=None,
                error=error,
                timed_out=False,
                interrupted=False,
                elapsed_ms=int((time.monotonic() - started) * 1000),
                output_bytes=0,
                env_names=tuple(sorted(env)),
                observed={},
                launched=False,
            )
        finally:
            self._child = None
        elapsed_ms = int((time.monotonic() - started) * 1000)
        output_bytes = len(stdout) + len(stderr)
        if output_bytes > self.allowance.max_output_bytes:
            self.backend_failures += 1
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
                elapsed_ms=elapsed_ms,
                output_bytes=output_bytes,
                env_names=tuple(sorted(env)),
                observed={},
                launched=True,
            )
        if self._interrupted or interrupted:
            self.backend_failures += 1
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
                elapsed_ms=elapsed_ms,
                output_bytes=output_bytes,
                env_names=tuple(sorted(env)),
                observed={},
                launched=True,
            )
        if timed_out:
            self.backend_failures += 1
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
                elapsed_ms=elapsed_ms,
                output_bytes=output_bytes,
                env_names=tuple(sorted(env)),
                observed=_safe_observed(stdout),
                launched=True,
            )
        parsed, parse_error = _parse_provider_output(stdout)
        if parse_error or parsed is None:
            self.backend_failures += 1
            return self._finish(
                request,
                isolated,
                status="malformed",
                structured=None,
                attempts=(),
                exit_code=exit_code,
                error=parse_error or "malformed_provider_output",
                timed_out=False,
                interrupted=False,
                elapsed_ms=elapsed_ms,
                output_bytes=output_bytes,
                env_names=tuple(sorted(env)),
                observed=_safe_observed(stdout),
                launched=True,
            )
        if exit_code not in (0, None) and exit_code != 0:
            self.backend_failures += 1
            return self._finish(
                request,
                isolated,
                status="execution_failure",
                structured=None,
                attempts=(),
                exit_code=exit_code,
                error="unsuccessful_provider_exit",
                timed_out=False,
                interrupted=False,
                elapsed_ms=elapsed_ms,
                output_bytes=output_bytes,
                env_names=tuple(sorted(env)),
                observed=parsed.get("observed") if isinstance(parsed, dict) else {},
                launched=True,
            )
        attempts, structured, reject = self._dispatch_requests(request, isolated, parsed)
        if reject:
            self.backend_failures += 1
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
                elapsed_ms=elapsed_ms,
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
            elapsed_ms=elapsed_ms,
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
        dispatcher = ApplicationDispatcher(request.snapshot, isolated.workspace)
        attempts: list[AttemptRecord] = []
        for item in payload.get("requests") or []:
            if not isinstance(item, Mapping):
                attempts.append(
                    AttemptRecord("unknown", {}, "denied", "malformed_request_item", False)
                )
                continue
            if self.tool_dispatches >= self.allowance.max_tool_dispatches:
                attempts.append(
                    AttemptRecord(
                        str(item.get("operation") or "unknown"),
                        dict(item.get("arguments") or {}),
                        "denied",
                        "tool_dispatch_allowance_exhausted",
                        False,
                    )
                )
                continue
            self.tool_dispatches += 1
            attempts.append(
                dispatcher.handle(
                    str(item.get("operation") or ""),
                    dict(item.get("arguments") or {}),
                )
            )
        output = payload.get("output")
        if output is None:
            return tuple(attempts), None, "malformed"
        if not isinstance(output, Mapping):
            return tuple(attempts), None, "malformed"
        if payload.get("role") not in (None, request.role):
            return tuple(attempts), None, "malformed"
        if "kind" not in output:
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
            child.wait(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                try:
                    child.kill()
                except OSError:
                    return

    def _result(
        self,
        request: ResearchRequest,
        *,
        status: str,
        error: str | None,
        launched: bool,
        details: Mapping[str, Any] | None = None,
    ) -> BackendResult:
        capture = self._capture(
            request,
            attempts=(),
            exit_code=None,
            error=error,
            timed_out=status == "timeout",
            interrupted=status == "interrupted",
            elapsed_ms=0,
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
        elapsed_ms: int,
        output_bytes: int,
        env_names: tuple[str, ...],
        observed: Mapping[str, Any] | None,
        launched: bool,
    ) -> BackendResult:
        capture = self._capture(
            request,
            attempts=attempts,
            exit_code=exit_code,
            error=error,
            timed_out=timed_out,
            interrupted=interrupted,
            elapsed_ms=elapsed_ms,
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
            known_result=structured is not None and status == "ok",
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
        elapsed_ms: int,
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
                    "verified": self.native.verified,
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
            elapsed_ms=elapsed_ms,
            output_bytes=output_bytes,
            cwd=cwd,
            workspace=workspace,
            env_names=env_names,
            observed=sanitize(observed),
            backend_calls_attempted=self.backend_calls_attempted,
            backend_failures=self.backend_failures,
            launched=launched,
        )


def _parse_provider_output(stdout: bytes) -> tuple[dict[str, Any] | None, str | None]:
    if not stdout:
        return None, "missing_provider_output"
    text = stdout.decode("utf-8", errors="replace").strip()
    if not text:
        return None, "missing_provider_output"
    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            return payload, None
        return None, "provider_output_not_object"
    except json.JSONDecodeError:
        events: list[dict[str, Any]] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                return None, "truncated_or_malformed_output"
            if isinstance(item, dict):
                events.append(item)
        if not events:
            return None, "truncated_or_malformed_output"
        final = next((item for item in reversed(events) if item.get("type") == "result"), None)
        if final is None:
            return None, "missing_result"
        combined = dict(final)
        combined["requests"] = [
            event.get("request") or event
            for event in events
            if event.get("type") == "request" or "operation" in event
        ]
        return combined, None


def _safe_observed(stdout: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(stdout.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {}
    if isinstance(payload, dict) and isinstance(payload.get("observed"), dict):
        return dict(payload["observed"])
    return {}
