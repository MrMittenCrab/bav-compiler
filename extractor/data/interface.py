"""Source-document handoff contract (documentary types only)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modeler.data.interface import ReconciliationReport, StandardizedFinancials


class DocumentType(str, Enum):
    ANNUAL_REPORT = "annual_report"
    INTERIM_REPORT = "interim_report"
    RESULTS_ANNOUNCEMENT = "results_announcement"
    EXCEL_EXPORT = "excel_export"
    BLOOMBERG_EXPORT = "bloomberg_export"
    WIND_EXPORT = "wind_export"
    OTHER = "other"


@dataclass
class DocumentManifest:
    """A manually supplied source document registered for extraction."""

    path: str
    doc_type: DocumentType
    period_end: date | None = None
    language: str = "en"
    notes: str = ""
    page_refs: dict[str, str] = field(default_factory=dict)


class DataSourceAdapter(ABC):
    """Common adapter interface for all data sources."""

    jurisdiction: str = "HK"

    @abstractmethod
    def ingest(self, manifest: list[DocumentManifest]) -> StandardizedFinancials:
        """Extract and normalize financials from supplied documents."""

    @abstractmethod
    def reconcile(self, data: StandardizedFinancials) -> ReconciliationReport:
        """Validate checksums and resolve cross-document conflicts."""
