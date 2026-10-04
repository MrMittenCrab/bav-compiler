"""Extractor research-source preparation, inventory and contextual retrieval."""

from bav.extractor.research.adapter import (
    ConverterCapabilityGap,
    build_conversion_command,
    convert_pdf,
    inspect_installed_converter,
)
from bav.extractor.research.contracts import (
    CorpusQuery,
    PreparationRequest,
    PreparedBundle,
    RetrievalResult,
    SnapshotInventory,
)
from bav.extractor.research.prepare import prepare_source
from bav.extractor.research.retrieve import query_snapshot, result_key
from bav.extractor.research.snapshot import load_snapshot_inventory

__all__ = [
    "ConverterCapabilityGap",
    "CorpusQuery",
    "PreparationRequest",
    "PreparedBundle",
    "RetrievalResult",
    "SnapshotInventory",
    "build_conversion_command",
    "convert_pdf",
    "inspect_installed_converter",
    "load_snapshot_inventory",
    "prepare_source",
    "query_snapshot",
    "result_key",
]
