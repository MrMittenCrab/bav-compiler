"""Allowlisted PDF-to-Markdown adapter around the installed marker_single command."""

from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path
from typing import Mapping

from bav.extractor.research.contracts import (
    DEFAULT_CONVERTER_TIMEOUT_SECONDS,
    OFFLINE_TEXT_LAYER_PROFILE,
    RECORDED_MARKER_EXECUTABLE,
    RECORDED_MARKER_PACKAGE,
    RECORDED_MARKER_VERSION,
    ConversionAttempt,
    ConverterProfile,
)

REQUIRED_HELP_FLAGS = (
    "--mode",
    "--disable_ocr",
    "--output_format",
    "--disable_tqdm",
)
FORBIDDEN_HELP_FLAGS_IN_COMMAND = (
    "--force_ocr",
    "--ocr",
    "--use_llm",
    "--llm",
    "--redo_inline_math",
    "--paginate",
)
OFFLINE_ENV = {
    "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
}
DEFAULT_ALLOWLIST = (RECORDED_MARKER_EXECUTABLE,)


class ConverterCapabilityGap(RuntimeError):
    def __init__(self, reason: str, attempt: ConversionAttempt | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.attempt = attempt


def inspect_installed_converter(
    executable: str | Path | None = None,
    *,
    allowlist: tuple[str, ...] = DEFAULT_ALLOWLIST,
    timeout_seconds: float = 15.0,
) -> ConverterProfile | ConversionAttempt:
    """Recheck local help/version. Missing capability is a gap, not company evidence."""
    candidate = str(executable or RECORDED_MARKER_EXECUTABLE)
    if candidate not in allowlist:
        return ConversionAttempt(
            command=(candidate,),
            env={},
            timeout_seconds=int(timeout_seconds),
            exit_code=None,
            elapsed_seconds=0.0,
            stdout="",
            stderr="",
            timed_out=False,
            capability_gap="executable_not_allowlisted",
        )
    path = Path(candidate)
    if not path.is_file() or path.is_symlink() and not path.exists():
        if not path.exists():
            return ConversionAttempt(
                command=(candidate, "--help"),
                env=dict(OFFLINE_ENV),
                timeout_seconds=int(timeout_seconds),
                exit_code=None,
                elapsed_seconds=0.0,
                stdout="",
                stderr="",
                timed_out=False,
                capability_gap="executable_missing",
            )
    started = time.monotonic()
    try:
        completed = subprocess.run(
            [candidate, "--help"],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=_offline_env(),
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return ConversionAttempt(
            command=(candidate, "--help"),
            env=dict(OFFLINE_ENV),
            timeout_seconds=int(timeout_seconds),
            exit_code=None,
            elapsed_seconds=time.monotonic() - started,
            stdout=_text(exc.stdout),
            stderr=_text(exc.stderr),
            timed_out=True,
            capability_gap="help_timeout",
        )
    except OSError:
        return ConversionAttempt(
            command=(candidate, "--help"),
            env=dict(OFFLINE_ENV),
            timeout_seconds=int(timeout_seconds),
            exit_code=None,
            elapsed_seconds=time.monotonic() - started,
            stdout="",
            stderr="",
            timed_out=False,
            capability_gap="executable_missing",
        )
    help_text = (completed.stdout or "") + "\n" + (completed.stderr or "")
    missing = [flag for flag in REQUIRED_HELP_FLAGS if flag not in help_text]
    if completed.returncode != 0 or missing:
        return ConversionAttempt(
            command=(candidate, "--help"),
            env=dict(OFFLINE_ENV),
            timeout_seconds=int(timeout_seconds),
            exit_code=completed.returncode,
            elapsed_seconds=time.monotonic() - started,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            timed_out=False,
            capability_gap="help_missing_required_flags" if missing else "help_failed",
        )
    version = _parse_version(help_text) or RECORDED_MARKER_VERSION
    return ConverterProfile(
        executable=candidate,
        package=RECORDED_MARKER_PACKAGE,
        package_version=version,
        profile=OFFLINE_TEXT_LAYER_PROFILE,
        timeout_seconds=DEFAULT_CONVERTER_TIMEOUT_SECONDS,
        ocr=False,
        llm_enrichment=False,
    )


def build_conversion_command(
    profile: ConverterProfile,
    input_pdf: Path,
    output_dir: Path,
) -> list[str]:
    if profile.ocr or profile.llm_enrichment:
        raise ConverterCapabilityGap("ocr_or_enrichment_forbidden")
    if profile.profile != OFFLINE_TEXT_LAYER_PROFILE:
        raise ConverterCapabilityGap("unapproved_converter_profile")
    command = [
        profile.executable,
        str(input_pdf),
        "--output_dir",
        str(output_dir),
        "--mode",
        "fast",
        "--disable_ocr",
        "--output_format",
        "markdown",
        "--disable_tqdm",
    ]
    forbidden = [flag for flag in command if flag in FORBIDDEN_HELP_FLAGS_IN_COMMAND]
    if forbidden:
        raise ConverterCapabilityGap("forbidden_converter_flag")
    return command


def convert_pdf(
    input_pdf: Path,
    output_dir: Path,
    *,
    profile: ConverterProfile,
    timeout_seconds: int | None = None,
) -> tuple[Path, ConversionAttempt]:
    """Run one conversion. No automatic retry."""
    timeout = timeout_seconds if timeout_seconds is not None else profile.timeout_seconds
    if timeout <= 0:
        raise ConverterCapabilityGap("invalid_timeout")
    output_dir.mkdir(parents=True, exist_ok=True)
    command = build_conversion_command(profile, input_pdf, output_dir)
    env = _offline_env()
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        attempt = ConversionAttempt(
            command=tuple(command),
            env=dict(OFFLINE_ENV),
            timeout_seconds=timeout,
            exit_code=None,
            elapsed_seconds=time.monotonic() - started,
            stdout=_text(exc.stdout),
            stderr=_text(exc.stderr),
            timed_out=True,
            capability_gap="conversion_timeout",
        )
        raise ConverterCapabilityGap("conversion_timeout", attempt) from exc
    except OSError as exc:
        attempt = ConversionAttempt(
            command=tuple(command),
            env=dict(OFFLINE_ENV),
            timeout_seconds=timeout,
            exit_code=None,
            elapsed_seconds=time.monotonic() - started,
            stdout="",
            stderr="",
            timed_out=False,
            capability_gap="executable_missing",
        )
        raise ConverterCapabilityGap("executable_missing", attempt) from exc
    attempt = ConversionAttempt(
        command=tuple(command),
        env=dict(OFFLINE_ENV),
        timeout_seconds=timeout,
        exit_code=completed.returncode,
        elapsed_seconds=time.monotonic() - started,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
        timed_out=False,
        capability_gap=None if completed.returncode == 0 else "conversion_failed",
    )
    if completed.returncode != 0:
        raise ConverterCapabilityGap("conversion_failed", attempt)
    markdown = _find_markdown_output(output_dir)
    if markdown is None:
        attempt = ConversionAttempt(
            command=attempt.command,
            env=attempt.env,
            timeout_seconds=attempt.timeout_seconds,
            exit_code=attempt.exit_code,
            elapsed_seconds=attempt.elapsed_seconds,
            stdout=attempt.stdout,
            stderr=attempt.stderr,
            timed_out=False,
            capability_gap="markdown_output_missing",
        )
        raise ConverterCapabilityGap("markdown_output_missing", attempt)
    return markdown, attempt


def _offline_env() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key not in {"CURSOR_API_KEY", "OPENAI_API_KEY"}}
    env.update(OFFLINE_ENV)
    return env


def _parse_version(help_text: str) -> str | None:
    match = re.search(r"marker-pdf(?:\s+|==|/)(\d+\.\d+\.\d+)", help_text)
    if match:
        return match.group(1)
    match = re.search(r"version\s+(\d+\.\d+\.\d+)", help_text, re.I)
    if match:
        return match.group(1)
    return None


def _find_markdown_output(output_dir: Path) -> Path | None:
    candidates = sorted(output_dir.rglob("*.md"))
    if not candidates:
        return None
    for path in candidates:
        if path.name == "original.md" or path.stem == "original":
            return path
    return candidates[0]


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)
