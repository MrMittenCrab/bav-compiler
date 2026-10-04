"""Deterministic Case/Status/Next formatter for Debater terminal output."""

from __future__ import annotations

from bav.debater.contracts import DebateEnvelope
from bav.debater.intake import colon_safe

_LABELS = ("Case", "Status", "Next")


def format_terminal(envelope: DebateEnvelope) -> str:
    lines: list[str] = []
    if envelope.case_title:
        lines.append(f"Case: {colon_safe(envelope.case_title)}")
    if envelope.status:
        if envelope.status not in {"Draft", "Incomplete", "Unsupported"}:
            raise ValueError(f"unknown research status: {envelope.status}")
        lines.append(f"Status: {envelope.status}")
    if envelope.next_lines:
        first, *rest = envelope.next_lines
        lines.append(f"Next: {colon_safe(first)}")
        for item in rest:
            lines.append(f"      {colon_safe(item)}")
    text = "\n".join(lines)
    _assert_colon_contract(text)
    return text + ("\n" if text else "")


def _assert_colon_contract(text: str) -> None:
    for line in text.splitlines():
        if ":" not in line:
            continue
        if not any(line.startswith(f"{label}:") for label in _LABELS):
            raise ValueError(f"colon outside Case/Status/Next label: {line!r}")
