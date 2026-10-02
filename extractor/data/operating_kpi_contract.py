"""Parse-time operating-KPI fact-type and reported-label shape helpers."""

from __future__ import annotations

KPI_NAMESPACE = "kpi.operating"
KPI_PREFIX = KPI_NAMESPACE + "."


def is_operating_kpi_fact_type(fact_type: str) -> bool:
    return fact_type.startswith(KPI_PREFIX)


def require_reported_label(identity: str, label: object) -> str:
    """Require a reported source label; note text is not a substitute."""
    if not isinstance(label, str) or not label.strip():
        raise ValueError(f"operating-KPI {identity} missing reported label")
    return label


def reject_non_string_reported_label(identity: str, label: object) -> None:
    """Reject non-string serialized labels before source coercion.

    ``None`` (omitted/null) is left to object-level validation.
    """
    if label is None or isinstance(label, str):
        return
    require_reported_label(identity, label)
