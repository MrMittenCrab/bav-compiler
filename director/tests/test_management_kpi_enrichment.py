"""Documentary enrichment of working-copy Lululemon management KPIs."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from director.current_build import prepare_company_input, resolve_company
from director.ingestion.filing_cli import load_and_validate_extracted_dir
from modeler.ingestion.filing_reconciler import reconcile_filings
from modeler.ingestion.filing_standardizer import reconciliation_management_admission_payload
from director.ingestion.management_kpi_enrichment import enrich_management_working_copies
from extractor.ingestion.management_kpi_enrichment import (
    FISCAL_CALENDAR_BASIS,
    SourceInspection,
    decode_filing_text,
    definition_features,
    field_supporting_passages,
    inspect_source_pdf,
    page_reference_from_printed,
    printed_pages_from_reference,
    resolve_physical_pages,
)
from modeler.ingestion.management_kpi_identity import (
    FAMILY_COMPARABLE_SALES_GROWTH,
    FAMILY_SALES_PER_SQUARE_FOOT,
    REASON_MISSING_COMPARISON,
)
from modeler.ingestion.management_kpi_reconciliation import SELECTION_DEFERRED, SELECTION_SELECTED
from modeler.tests.test_management_kpi_admission import (
    ANNUAL_NAMES,
    EXTRACTED,
    MANAGEMENT_NAMES,
    SOURCE,
    _bytes_by_name,
)
from modeler.tests.test_operating_kpi_facts import ADMIT_2022, INDEPENDENT_STORE_TOTALS
from modeler.tests.test_revenue_per_store import REVENUE_ANCHORS

ROOT = Path(__file__).resolve().parents[2]
FY2024_PDF = SOURCE / "LULU_FY2024_Annual_Report.pdf"


def _copy_extracted(dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    for name in ANNUAL_NAMES + MANAGEMENT_NAMES:
        shutil.copy2(EXTRACTED / name, dest / name)
    return dest


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_working_copy_enrichment_maps_period_and_calendar(tmp_path: Path):
    dest = _copy_extracted(tmp_path / "work")
    protected = _bytes_by_name(EXTRACTED)
    sidecar = enrich_management_working_copies(dest, SOURCE)
    assert _bytes_by_name(EXTRACTED) == protected
    assert Path(sidecar["resolution_path"]).is_file()
    fy2024 = json.loads((dest / "LULU_FY2024_management_kpis.json").read_text())
    original = json.loads((EXTRACTED / "LULU_FY2024_management_kpis.json").read_text())
    assert fy2024["report"]["fiscal_year_end"] == "2025-02-02"
    assert fy2024["report"]["reporting_basis"] == FISCAL_CALENDAR_BASIS
    assert fy2024["report"]["original_reporting_basis"] == original["report"]["reporting_basis"]
    compsales = next(
        item
        for item in fy2024["reported_kpis"]
        if item["metric_id"] == "comparable_sales_growth"
    )
    original_comp = next(
        item
        for item in original["reported_kpis"]
        if item["metric_id"] == "comparable_sales_growth"
    )
    assert compsales["period"] == "2025-02-02"
    assert compsales["original_period_label"] == "FY2024"
    assert compsales["value"] == original_comp["value"]
    assert compsales["qualifiers"]["excludes_53rd_week"] is True
    assert compsales["presentation"]["role"] == "current"
    assert "assurance" not in compsales
    assert "revision" not in compsales
    assert "physical_page_mapping" not in compsales.get("source", {})
    spsf = next(
        item for item in fy2024["reported_kpis"] if item["metric_id"] == "sales_per_square_foot"
    )
    assert spsf["period"] == "2025-02-02"
    assert spsf["value"] == 1574
    assert spsf["qualifiers"]["excludes_53rd_week"] is True
    assert spsf.get("comparison") in (None, "")
    fy2025 = json.loads((dest / "LULU_FY2025_management_kpis.json").read_text())
    fy2025_comp = next(
        item
        for item in fy2025["reported_kpis"]
        if item["metric_id"] == "comparable_sales_growth"
    )
    assert fy2025_comp["period"] == "2026-02-01"
    assert fy2025_comp["qualifiers"]["excludes_53rd_week"] is False
    fy2022 = json.loads((dest / "LULU_FY2022_management_kpis.json").read_text())
    store = next(
        item
        for item in fy2022["reported_kpis"]
        if item["metric_id"] == "comparable_store_sales_growth"
    )
    total = next(
        item
        for item in fy2022["reported_kpis"]
        if item["metric_id"] == "total_comparable_sales_growth"
    )
    assert store["period"] == "2023-01-29"
    assert total["period"] == "2023-01-29"
    assert store["metric_id"] != "comparable_sales_growth"
    record = next(
        item
        for item in sidecar["documents"]
        if item["extraction_document"] == "LULU_FY2024_management_kpis.json"
    )
    company = next(
        item for item in record["fields"] if item["metric_id"] == "comparable_sales_growth"
    )
    assert 40 in company["physical_pages"] or company["physical_pages"] == [33]
    assert company.get("supporting_passages")
    assert "supporting_text" not in company
    spsf_field = next(
        item for item in record["fields"] if item["metric_id"] == "sales_per_square_foot"
    )
    assert spsf_field["physical_pages"] == [10]


def test_ordinary_prepare_writes_resolution_and_keeps_revenue_per_store(tmp_path: Path):
    company = resolve_company("Lululemon")
    staged = tmp_path / "staged"
    before = _bytes_by_name(EXTRACTED)
    fin = prepare_company_input(company, staged)
    assert _bytes_by_name(EXTRACTED) == before
    assert not (staged / "supporting" / "management_kpi_page_resolution.json").exists()
    assert not (staged / "supporting" / "extracted").exists()
    assert not (staged / "supporting" / "management_kpi_admission.json").exists()
    assert fin.historical_operating_kpis is not None
    assert fin.historical_operating_kpis.management_observations
    stores = {
        item.period: item.value
        for item in fin.historical_operating_kpis.observations
    }
    assert stores == INDEPENDENT_STORE_TOTALS
    from modeler.revenue_per_store import compute_revenue_per_store_series

    series = compute_revenue_per_store_series(fin)
    for period, revenue in REVENUE_ANCHORS.items():
        expected = revenue / INDEPENDENT_STORE_TOTALS[period]
        assert series.period_end_revenue_per_store[period] == pytest.approx(expected)


def test_director_working_copy_enrichment_writes_resolution_and_admits(tmp_path: Path):
    from director.ingestion.management_kpi_enrichment import (
        enrich_management_working_copies as director_enrich,
    )

    dest = _copy_extracted(tmp_path / "supporting" / "extracted")
    protected = EXTRACTED / "LULU_FY2024_management_kpis.json"
    sidecar = director_enrich(dest, SOURCE)
    resolution = Path(sidecar["resolution_path"])
    assert resolution.is_file()
    payload = json.loads(resolution.read_text())
    fy2024 = next(
        item
        for item in payload["documents"]
        if item["extraction_document"] == "LULU_FY2024_management_kpis.json"
    )
    assert fy2024["fiscal_year_end"] == "2025-02-02"
    assert fy2024["printed_to_physical"]["34"] == 40
    working = dest / "LULU_FY2024_management_kpis.json"
    assert _sha(protected) != _sha(working)
    original_comp = next(
        item
        for item in json.loads(protected.read_text())["reported_kpis"]
        if item["metric_id"] == "comparable_sales_growth"
    )
    assert original_comp["period"] == "FY2024"
    admission = reconciliation_management_admission_payload(
        reconcile_filings(
            load_and_validate_extracted_dir(dest, source_root=SOURCE),
            admit_periods=ADMIT_2022,
        )
    )
    assert admission["reconciliation"]["selected_count"] > 0


def test_repeated_working_copy_enrichment_is_stable(tmp_path: Path):
    dest = _copy_extracted(tmp_path / "repeat")
    first = enrich_management_working_copies(dest, SOURCE)
    second = enrich_management_working_copies(dest, SOURCE)
    assert second["written"] == first["written"]
    assert second["documents"] == first["documents"]
    assert Path(second["resolution_path"]) == Path(first["resolution_path"])


def _enriched_admission(tmp_path: Path) -> dict:
    dest = _copy_extracted(tmp_path / "doc")
    enrich_management_working_copies(dest, SOURCE)
    return reconciliation_management_admission_payload(
        reconcile_filings(
            load_and_validate_extracted_dir(dest, source_root=SOURCE),
            admit_periods=ADMIT_2022,
        )
    )


def _spsf_fields(sidecar: dict) -> list[dict]:
    fields: list[dict] = []
    for document in sidecar["documents"]:
        for field in document["fields"]:
            if field["metric_id"] != "sales_per_square_foot":
                continue
            item = dict(field)
            item["extraction_document"] = document["extraction_document"]
            fields.append(item)
    return fields


def _spsf_assessments(payload: dict) -> list[dict]:
    return [
        item
        for item in payload["assessments"]["items"]
        if item["family"] == FAMILY_SALES_PER_SQUARE_FOOT and item["status"] == "supported"
    ]


def _pair_key(locators: list[str]) -> tuple[str, ...]:
    return tuple(sorted(locators))


_FY2022_FOCUS = (
    ("comparable_store_sales_growth", "reported", "comparable store sales"),
    (
        "comparable_store_sales_growth_constant_dollar",
        "constant_dollar",
        "comparable store sales",
    ),
    ("total_comparable_sales_growth", "reported", "total comparable sales"),
    (
        "total_comparable_sales_growth_constant_dollar",
        "constant_dollar",
        "total comparable sales",
    ),
)


def _fy2022_fields(sidecar: dict) -> list[dict]:
    document = next(
        item
        for item in sidecar["documents"]
        if item["extraction_document"] == "LULU_FY2022_management_kpis.json"
    )
    return [
        item
        for item in document["fields"]
        if item["metric_id"] in {row[0] for row in _FY2022_FOCUS}
    ]


