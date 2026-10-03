"""Analytical operating-KPI admission checks (not documentary provenance)."""

from __future__ import annotations

from bav.extractor.data.filing import ExtractedFiling
from bav.extractor.data.filing_validator import FilingValidationIssue
from bav.extractor.data.operating_kpi_contract import is_operating_kpi_fact_type

from bav.modeler.data.historical_operating_kpis import validate_operating_kpi_fact

__all__ = [
    "operating_kpi_admission_issues",
]


def operating_kpi_admission_issues(
    filing: ExtractedFiling,
) -> list[FilingValidationIssue]:
    """Analytical operating-KPI admission checks (not documentary provenance)."""
    issues: list[FilingValidationIssue] = []
    kpi_seen: set[tuple[str, str]] = set()
    for fact in (*filing.note_facts, *filing.share_facts):
        issues.extend(_operating_kpi_admission_for_fact(fact, kpi_seen))
    return issues


def _operating_kpi_admission_for_fact(
    fact,
    kpi_seen: set[tuple[str, str]],
) -> list[FilingValidationIssue]:
    if not is_operating_kpi_fact_type(fact.fact_type):
        return []
    issues: list[FilingValidationIssue] = []
    try:
        validate_operating_kpi_fact(fact)
    except ValueError as exc:
        issues.append(
            FilingValidationIssue(
                "error",
                "invalid_operating_kpi",
                str(exc),
            )
        )
    key = (fact.fact_type, fact.period.isoformat())
    if key in kpi_seen:
        issues.append(
            FilingValidationIssue(
                "error",
                "duplicate_operating_kpi_identity",
                f"duplicate operating-KPI identity {fact.fact_type} "
                f"for {fact.period.isoformat()}",
            )
        )
    kpi_seen.add(key)
    return issues
