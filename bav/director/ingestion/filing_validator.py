"""Director orchestration: documentary validation plus operating-KPI admission."""

from __future__ import annotations

from pathlib import Path

from bav.extractor.data.filing import ExtractedFiling
from bav.extractor.data.filing_validator import (
    FilingValidationIssue,
    FilingValidationReport,
    bind_source_file,
    current_period_missing_issue,
    documentary_statement_issues,
    documentary_supplemental_page_issue,
)
from bav.modeler.ingestion.filing_validator import _operating_kpi_admission_for_fact


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
