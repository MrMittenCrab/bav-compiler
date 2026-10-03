"""Working-copy enrichment orchestration and sidecar persistence.

Directory traversal, protected-path checks and sequencing live here.
Substantive inspection and enrichment are delegated.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from extractor.data.extracted_kind import KIND_MANAGEMENT_KPI, classify_extracted_payload
from extractor.ingestion.management_kpi_enrichment import (
    SourceInspection,
    collect_calendar_corpus,
    collect_exclusion_corpus,
    inspect_source_pdf,
)
from modeler.ingestion.management_kpi_enrichment import enrich_management_payload

PAGE_RESOLUTION_NAME = "management_kpi_page_resolution.json"


def enrich_management_working_copies(
    extracted_dir: Path,
    source_dir: Path,
    *,
    resolution_path: Path | None = None,
) -> dict[str, Any]:
    """Enrich management-KPI working copies in extracted_dir from source_dir PDFs."""
    extracted = Path(extracted_dir)
    source = Path(source_dir)
    resolved = extracted.resolve()
    if resolved == source.resolve():
        raise ValueError("refusing to enrich a source directory")
    protected_extracted = source.resolve().parent / "extracted"
    if resolved == protected_extracted:
        raise ValueError("refusing to enrich protected source extracts")
    records: list[dict[str, Any]] = []
    written: list[str] = []
    inspections: dict[str, SourceInspection] = {}
    for path in sorted(extracted.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if classify_extracted_payload(payload, path=path) != KIND_MANAGEMENT_KPI:
            continue
        source_file = str(payload.get("report", {}).get("source_file") or "")
        pdf = source / source_file
        if not pdf.is_file():
            raise ValueError(f"{path.name}: bound source PDF missing: {pdf}")
        if source_file not in inspections:
            inspections[source_file] = inspect_source_pdf(pdf)
    calendar_corpus = collect_calendar_corpus(inspections)
    exclusion_corpus = collect_exclusion_corpus(inspections, calendar_corpus)
    year_end_map: dict[int, str] = {}
    for path in sorted(extracted.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if classify_extracted_payload(payload, path=path) != KIND_MANAGEMENT_KPI:
            continue
        report = payload.get("report") or {}
        try:
            year_end_map[int(report["fiscal_year"])] = str(report["fiscal_year_end"])
        except (KeyError, TypeError, ValueError):
            continue
    for path in sorted(extracted.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if classify_extracted_payload(payload, path=path) != KIND_MANAGEMENT_KPI:
            continue
        source_file = str(payload.get("report", {}).get("source_file") or "")
        enriched, record = enrich_management_payload(
            payload,
            inspections[source_file],
            extraction_document=path.name,
            calendar_corpus=calendar_corpus,
            year_end_map=year_end_map,
            exclusion_corpus=exclusion_corpus,
        )
        path.write_text(json.dumps(enriched, indent=2) + "\n", encoding="utf-8")
        written.append(path.name)
        records.append(record)
    sidecar = {
        "documents": records,
        "written": written,
    }
    dest = Path(resolution_path) if resolution_path is not None else (
        extracted.parent / PAGE_RESOLUTION_NAME
    )
    dest.write_text(json.dumps(sidecar, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    sidecar["resolution_path"] = str(dest)
    return sidecar

