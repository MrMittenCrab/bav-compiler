"""Base ingestion adapter with shared reconciliation hooks."""

from __future__ import annotations

from bav.extractor.data.interface import DataSourceAdapter, DocumentManifest
from bav.modeler.data.interface import ReconciliationReport, StandardizedFinancials
from .reconciler import reconcile_financials


class BaseIngestionAdapter(DataSourceAdapter):
    """Shared reconcile implementation for manual adapters."""

    def reconcile(self, data: StandardizedFinancials) -> ReconciliationReport:
        return reconcile_financials(data)
