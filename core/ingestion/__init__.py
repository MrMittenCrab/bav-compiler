"""Ingestion adapters for manual and exported financial data."""

from .base import BaseIngestionAdapter
from .reconciler import reconcile_financials

__all__ = [
    "BaseIngestionAdapter",
    "ExcelExportAdapter",
    "HKManualDocumentAdapter",
    "reconcile_financials",
]


def __getattr__(name):
    if name == "ExcelExportAdapter":
        from .excel_import import ExcelExportAdapter

        return ExcelExportAdapter
    if name == "HKManualDocumentAdapter":
        from .manual_hk import HKManualDocumentAdapter

        return HKManualDocumentAdapter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
