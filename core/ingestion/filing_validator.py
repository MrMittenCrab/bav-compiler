"""Director/Modeler orchestration: documentary validation plus operating-KPI admission."""

from __future__ import annotations

from pathlib import Path

from extractor.data.filing import ExtractedFiling
from extractor.data.filing_validator import (
    FilingValidationIssue,
    FilingValidationReport,
    bind_source_file,
    current_period_missing_issue,
    documentary_statement_issues,
    documentary_supplemental_page_issue,
    source_row_identity,
    validate_extracted_filing as validate_extracted_filing_documentary,
)
from extractor.data.operating_kpi_contract import is_operating_kpi_fact_type

from ..data.historical_operating_kpis import validate_operating_kpi_fact

__all__ = [
    "FilingValidationIssue",
    "FilingValidationReport",
    "bind_source_file",
    "operating_kpi_admission_issues",
    "source_row_identity",
    "validate_extracted_filing",
    "validate_extracted_filing_documentary",
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


def validate_extracted_filing(
    filing: ExtractedFiling,
    *,
    source_root: Path | None = None,
) -> FilingValidationReport:
    """Documentary validation plus operating-KPI admission in original order."""
    issues: list[FilingValidationIssue] = []
    computed: str | None = None

    if source_root is not None:
        bind_issues, computed = bind_source_file(
            filing.filing.source_file,
            source_root=source_root,
            declared_sha256=filing.filing.source_sha256,
        )
        issues.extend(bind_issues)

    statement_issues, saw_current = documentary_statement_issues(filing)
    issues.extend(statement_issues)
    kpi_seen: set[tuple[str, str]] = set()
    for fact in (*filing.note_facts, *filing.share_facts):
        page_issue = documentary_supplemental_page_issue(fact)
        if page_issue is not None:
            issues.append(page_issue)
        issues.extend(_operating_kpi_admission_for_fact(fact, kpi_seen))

    if not saw_current:
        issues.append(current_period_missing_issue())

    return FilingValidationReport(issues=tuple(issues), computed_source_sha256=computed)
