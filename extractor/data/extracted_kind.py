"""Schema classification of already-extracted JSON (not admission)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

KIND_ANNUAL_FILING = "annual_filing"
KIND_MANAGEMENT_KPI = "management_kpi"

_MANAGEMENT_KEYS = (
    "company",
    "report",
    "kpi_definitions",
    "reported_kpis",
    "store_counts_by_market",
    "management_targets",
)
_MANAGEMENT_SIGNAL_KEYS = (
    "report",
    "kpi_definitions",
    "reported_kpis",
    "store_counts_by_market",
    "management_targets",
)
_ANNUAL_SIGNAL_KEYS = ("filing", "statements")


def document_label(path: Path | str | None) -> str:
    if path is None:
        return "extracted document"
    return Path(path).name


def classify_extracted_payload(
    payload: object,
    *,
    path: Path | str | None = None,
) -> str:
    """Classify one extracted JSON object by structure, not filename."""
    label = document_label(path)
    if not isinstance(payload, dict):
        raise ValueError(f"{label}: extracted JSON must be an object")
    management_complete = _management_schema_complete(payload)
    annual_complete = _annual_schema_complete(payload)
    management_signals = [key for key in _MANAGEMENT_SIGNAL_KEYS if key in payload]
    annual_signals = [key for key in _ANNUAL_SIGNAL_KEYS if key in payload]
    if management_complete and (annual_complete or annual_signals):
        raise ValueError(f"{label}: ambiguous extracted schema")
    if annual_complete and management_signals:
        raise ValueError(f"{label}: ambiguous extracted schema")
    if isinstance(payload.get("company"), dict) and management_signals:
        raise ValueError(f"{label}: ambiguous extracted schema")
    if isinstance(payload.get("company"), str) and annual_signals:
        raise ValueError(f"{label}: ambiguous extracted schema")
    if management_complete:
        return KIND_MANAGEMENT_KPI
    if annual_complete:
        return KIND_ANNUAL_FILING
    if isinstance(payload.get("company"), str) or management_signals:
        raise ValueError(f"{label}: malformed management-KPI schema")
    if isinstance(payload.get("company"), dict) or annual_signals:
        return KIND_ANNUAL_FILING
    raise ValueError(f"{label}: unknown extracted schema")


def _management_schema_complete(payload: Mapping[str, Any]) -> bool:
    return (
        isinstance(payload.get("company"), str)
        and isinstance(payload.get("report"), dict)
        and isinstance(payload.get("kpi_definitions"), list)
        and isinstance(payload.get("reported_kpis"), list)
        and isinstance(payload.get("store_counts_by_market"), dict)
        and isinstance(payload.get("management_targets"), list)
        and all(key in payload for key in _MANAGEMENT_KEYS)
    )


def _annual_schema_complete(payload: Mapping[str, Any]) -> bool:
    return (
        isinstance(payload.get("company"), dict)
        and isinstance(payload.get("filing"), dict)
        and isinstance(payload.get("statements"), dict)
    )
