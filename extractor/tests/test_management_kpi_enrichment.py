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


def test_fy2024_printed_34_is_physical_40():
    inspection = inspect_source_pdf(FY2024_PDF)
    assert inspection.printed_to_physical[34] == 40
    assert inspection.physical_to_printed[40] == 34
    assert inspection.printed_to_physical[4] == 10
    text = " ".join(decode_filing_text(inspection.page_texts[40]).split())
    assert "Comparable company-operated stores have been open" in text
    assert "53rd week of net revenue is excluded from the calculation of comparable sales" in text
    assert "average ending square footage" in text
    assert inspection.fiscal_calendar_evidenced
    assert 2024 in inspection.fifty_three_week_years
    assert 2023 in inspection.fifty_two_week_years


def test_printed_reference_resolves_without_inventing_pages():
    inspection = inspect_source_pdf(FY2024_PDF)
    assert printed_pages_from_reference("Form 10-K p. 34") == (34,)
    assert printed_pages_from_reference("Form 10-K pp. 33–34") == (33, 34)
    assert resolve_physical_pages("Form 10-K p. 34", inspection) == (40,)
    assert resolve_physical_pages("Form 10-K p. 4", inspection) == (10,)


def _enriched_admission(tmp_path: Path) -> dict:
    dest = _copy_extracted(tmp_path / "doc")
    enrich_management_working_copies(dest, SOURCE)
    return reconciliation_management_admission_payload(
        reconcile_filings(
            load_and_validate_extracted_dir(dest, source_root=SOURCE),
            admit_periods=ADMIT_2022,
        )
    )


def test_extract_asserted_physical_pages_still_rejected(tmp_path: Path):
    dest = _copy_extracted(tmp_path / "extract")
    enrich_management_working_copies(dest, SOURCE)
    working = json.loads((dest / "LULU_FY2024_management_kpis.json").read_text())
    for item in working["reported_kpis"]:
        if item.get("metric_id") == "comparable_sales_growth":
            item["source"]["physical_page_mapping"] = "40"
            item["presentation"]["source"]["physical_page_mapping"] = "40"
    (dest / "LULU_FY2024_management_kpis.json").write_text(
        json.dumps(working, indent=2) + "\n"
    )
    with pytest.raises(ValueError, match="cannot certify a PDF page"):
        load_and_validate_extracted_dir(dest, source_root=SOURCE)


def test_cross_filing_fy2022_calendar_from_fy2023_page_33(tmp_path: Path):
    dest = _copy_extracted(tmp_path / "cal")
    sidecar = enrich_management_working_copies(dest, SOURCE)
    fy2022 = next(
        item
        for item in sidecar["documents"]
        if item["extraction_document"] == "LULU_FY2022_management_kpis.json"
    )
    store = next(
        item for item in fy2022["fields"] if item["metric_id"] == "comparable_store_sales_growth"
    )
    assert store["calendar_week_excluded"] is False
    assert store["fiscal_year_length_weeks"] == 52
    provenance = store["calendar_provenance"]
    assert provenance["cross_filing"] is True
    assert provenance["source_file"] == "LULU_FY2023_Annual_Report.pdf"
    assert provenance["physical_page"] == 33
    assert "2022" in provenance["passage"]
    assert "52-week" in provenance["passage"]
    payload = reconciliation_management_admission_payload(
        reconcile_filings(load_and_validate_extracted_dir(dest, source_root=SOURCE))
    )
    fy2022_items = [
        item
        for item in payload["assessments"]["items"]
        if item["status"] == "supported"
        and item["evidence"]["period"] == "2023-01-29"
        and item["family"] == FAMILY_COMPARABLE_SALES_GROWTH
    ]
    assert fy2022_items
    assert all(
        item["evidence"]["calendar_week_adjustment"] == "included"
        for item in fy2022_items
    )
    assert all(
        item["evidence"]["fiscal_year_length_weeks"] == "52" for item in fy2022_items
    )


def test_shifted_comparison_windows_are_not_inferred(tmp_path: Path):
    payload = _enriched_admission(tmp_path)
    later = [
        item
        for item in payload["assessments"]["items"]
        if item["family"] == FAMILY_COMPARABLE_SALES_GROWTH
        and item["status"] == "supported"
        and item["metric_identity_fields"].get("geography") == "global"
        and item["metric_identity_fields"].get("basis") == "reported"
        and item["metric_identity_fields"].get("population")
        == "company_operated_stores_and_ecommerce"
    ]
    by_period = {item["evidence"]["period"]: item for item in later}
    fy2024 = by_period["2025-02-02"]
    fy2025 = by_period["2026-02-01"]
    assert fy2024["evidence"]["calendar_week_adjustment"] == "excluded"
    assert fy2025["evidence"]["calendar_week_adjustment"] == "included"
    assert fy2025["evidence"]["comparison_window"]
    assert "February 1" in fy2025["evidence"]["comparison_window"]
    assert "2026" in fy2025["evidence"]["comparison_window"]
    assert "February 2" in fy2025["evidence"]["comparison_window"]
    assert "2025" in fy2025["evidence"]["comparison_window"]
    assert fy2024["evidence"]["comparison_window"] != fy2025["evidence"]["comparison_window"]
    assert "comparison_window_mismatch" in fy2024["unresolved_reasons"]
    assert "comparison_window_mismatch" in fy2025["unresolved_reasons"]


def test_spsf_value_passages_require_metric_and_value(tmp_path: Path):
    dest = _copy_extracted(tmp_path / "spsfval")
    sidecar = enrich_management_working_copies(dest, SOURCE)
    by_doc = {item["extraction_document"]: item for item in sidecar["documents"]}
    fy2024 = next(
        item
        for item in by_doc["LULU_FY2024_management_kpis.json"]["fields"]
        if item["metric_id"] == "sales_per_square_foot" and item["period"] == "2025-02-02"
    )
    fy2025 = next(
        item
        for item in by_doc["LULU_FY2025_management_kpis.json"]["fields"]
        if item["metric_id"] == "sales_per_square_foot" and item["period"] == "2026-02-01"
    )
    assert "1,574" in fy2024["supporting_passages"]["value"]
    assert "sales per square foot" in fy2024["supporting_passages"]["value"].lower()
    assert "2024" in fy2024["supporting_passages"]["value"]
    assert "1,426" in fy2025["supporting_passages"]["value"]
    assert "sales per square foot" in fy2025["supporting_passages"]["value"].lower()
    assert "2025" in fy2025["supporting_passages"]["value"]


def test_date_passages_reject_introductory_text(tmp_path: Path):
    dest = _copy_extracted(tmp_path / "dates")
    sidecar = enrich_management_working_copies(dest, SOURCE)
    for document in sidecar["documents"]:
        for field in document["fields"]:
            if field["metric_id"] not in {
                "comparable_sales_growth",
                "sales_per_square_foot",
                "comparable_store_sales_growth",
                "total_comparable_sales_growth",
            }:
                continue
            dates = (field.get("supporting_passages") or {}).get("dates", "")
            if not dates:
                continue
            lowered = dates.lower()
            assert "components of management" not in lowered
            assert "components of this md" not in lowered
            assert "social impact" not in lowered
            assert "we have contributed" not in lowered
            assert (
                "fiscal year ended" in lowered
                or "weeks ended" in lowered
                or "number of company-operated stores" in lowered
            )
            assert not (
                "sunday closest to january 31" in lowered
                and "weeks ended" not in lowered
                and "fiscal year ended" not in lowered
            )


def test_unrelated_numeric_matches_are_rejected(tmp_path: Path):
    dest = _copy_extracted(tmp_path / "needles")
    sidecar = enrich_management_working_copies(dest, SOURCE)
    fy2024 = next(
        item
        for item in sidecar["documents"]
        if item["extraction_document"] == "LULU_FY2024_management_kpis.json"
    )
    company = next(
        item
        for item in fy2024["fields"]
        if item["metric_id"] == "comparable_sales_growth"
        and item["period"] == "2025-02-02"
    )
    value = company["supporting_passages"]["value"]
    assert "comparable sales" in value.lower()
    assert "4%" in value or "increased 4" in value.lower()
    assert "september 2024" not in value.lower()
    assert "supply partner" not in value.lower()
    fy2025 = next(
        item
        for item in sidecar["documents"]
        if item["extraction_document"] == "LULU_FY2025_management_kpis.json"
    )
    company_2025 = next(
        item
        for item in fy2025["fields"]
        if item["metric_id"] == "comparable_sales_growth"
        and item["period"] == "2026-02-01"
    )
    value_2025 = (company_2025.get("supporting_passages") or {}).get("value", "")
    assert "repurchase" not in value_2025.lower()
    assert "1.2 billion" not in value_2025.lower()


def test_prior_period_spsf_become_occurrences(tmp_path: Path):
    payload = _enriched_admission(tmp_path)
    fy2023_priors = [
        item
        for item in payload["observations"]
        if item["metric_id"] == "sales_per_square_foot"
        and item["extraction_document"] == "LULU_FY2023_management_kpis.json"
        and item["presentation_role"] == "prior"
    ]
    assert fy2023_priors
    assert any(item["value"] == 1580 and item["period"] == "2023-01-29" for item in fy2023_priors)
    assert all(item.get("revision") in (None, {}) for item in fy2023_priors)
    assert all(item["assurance"] == "unknown" for item in fy2023_priors)
    fy2024_priors = [
        item
        for item in payload["observations"]
        if item["metric_id"] == "sales_per_square_foot"
        and item["extraction_document"] == "LULU_FY2024_management_kpis.json"
        and item["presentation_role"] == "prior"
    ]
    assert any(item["value"] == 1609 and item["period"] == "2024-01-28" for item in fy2024_priors)


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


def test_metric_exclusion_is_not_inferred_from_53_week_year_alone():
    from core.ingestion.management_kpi_enrichment import (
        CalendarYearEvidence,
        _metric_excludes_53rd_week,
    )

    calendar = CalendarYearEvidence(
        fiscal_year=2024,
        fifty_three_week=True,
        source_file="LULU_FY2024_Annual_Report.pdf",
        physical_page=32,
        passage="Fiscal 2024 was a 53-week year.",
        cross_filing=False,
    )
    assert _metric_excludes_53rd_week(
        "sales_per_square_foot", calendar, [calendar.passage]
    ) is None
    assert _metric_excludes_53rd_week(
        "comparable_sales_growth", calendar, [calendar.passage]
    ) is None
    assert (
        _metric_excludes_53rd_week(
            "sales_per_square_foot",
            calendar,
            [
                "In fiscal years with 53 weeks the 53rd week of net revenue is "
                "excluded from the calculation of sales per square foot."
            ],
        )
        is True
    )
    fifty_two = CalendarYearEvidence(
        fiscal_year=2023,
        fifty_three_week=False,
        source_file="LULU_FY2023_Annual_Report.pdf",
        physical_page=33,
        passage="Fiscal 2023, 2022, and 2021 were each 52-week years.",
        cross_filing=False,
    )
    assert _metric_excludes_53rd_week(
        "sales_per_square_foot",
        fifty_two,
        [
            "In fiscal years with 53 weeks, the 53rd week of net revenue is "
            "excluded from the calculation of sales per square foot."
        ],
    ) is False


def test_comparison_window_is_not_copied_onto_priors_or_spsf(tmp_path: Path):
    dest = _copy_extracted(tmp_path / "win")
    sidecar = enrich_management_working_copies(dest, SOURCE)
    fields = _spsf_fields(sidecar)
    assert all(item.get("comparison_window") in (None, {}) for item in fields)
    by_doc = {item["extraction_document"]: item for item in sidecar["documents"]}
    fy2024_comp = next(
        item
        for item in by_doc["LULU_FY2024_management_kpis.json"]["fields"]
        if item["metric_id"] == "comparable_sales_growth"
        and item["period"] == "2025-02-02"
    )
    fy2025_comp = next(
        item
        for item in by_doc["LULU_FY2025_management_kpis.json"]["fields"]
        if item["metric_id"] == "comparable_sales_growth"
        and item["period"] == "2026-02-01"
    )
    fy2024_prior_spsf = next(
        item
        for item in by_doc["LULU_FY2025_management_kpis.json"]["fields"]
        if item["metric_id"] == "sales_per_square_foot"
        and item["period"] == "2025-02-02"
    )
    assert fy2024_comp["comparison_window"] in (None, {})
    assert fy2025_comp["comparison_window"]
    assert "February 1" in fy2025_comp["comparison_window"]["label"]
    assert fy2024_prior_spsf["comparison_window"] in (None, {})
    assert fy2024_prior_spsf["comparison_window"] != fy2025_comp["comparison_window"]
    window_pages = fy2025_comp["comparison_window"]["physical_pages"]
    assert window_pages
    assert len(window_pages) <= 2
    assert 33 in window_pages or 41 in window_pages


def test_complete_multiline_passages_and_individual_bindings(tmp_path: Path):
    dest = _copy_extracted(tmp_path / "pass")
    sidecar = enrich_management_working_copies(dest, SOURCE)
    for field in _spsf_fields(sidecar):
        presentation = (field.get("supporting_passages") or {}).get("presentation", "")
        if presentation:
            assert presentation.endswith("footage.") or "footage" in presentation.lower()
            assert not presentation.endswith("their square")
            assert presentation.lower().startswith("we use") or presentation.lower().startswith(
                "sales per square foot we use"
            )
        definition = (field.get("supporting_passages") or {}).get("definition", "")
        if definition:
            assert not definition.endswith("for each")
            assert "square footage" in definition.lower()
            assert "significantly" not in definition.lower() or definition.lower().endswith(
                ("expanded.", "year.", "footage.")
            )
        dates = (field.get("supporting_passages") or {}).get("dates", "")
        if dates:
            lowered = dates.lower()
            assert (
                lowered.startswith("for the fiscal year ended")
                or lowered.startswith("we refer to the fiscal year ended")
                or lowered.startswith("the fiscal year ended")
                or "weeks ended" in lowered
            )
            assert "united kingdom" not in lowered
            assert "number of company-operated stores by market" not in lowered
            assert "these core values attract" not in lowered
            assert "together with its subsidiaries" not in lowered
        bindings = field.get("passage_bindings") or {}
        for name, passage in (field.get("supporting_passages") or {}).items():
            binding = bindings[name]
            assert binding["source_file"]
            assert binding["physical_pages"]
            assert isinstance(binding["physical_pages"], list)
            if name in {"dates", "comparison_window", "calendar", "presentation"}:
                assert len(binding["physical_pages"]) <= 2
    fy2022 = next(
        item
        for item in sidecar["documents"]
        if item["extraction_document"] == "LULU_FY2022_management_kpis.json"
    )
    store = next(
        item
        for item in fy2022["fields"]
        if item["metric_id"] == "comparable_store_sales_growth"
    )
    calendar_binding = store["passage_bindings"]["calendar"]
    assert calendar_binding["source_file"] == "LULU_FY2023_Annual_Report.pdf"
    assert calendar_binding["physical_pages"] == [33]
    assert calendar_binding.get("cross_filing") is True


def _spsf_assessments(payload: dict) -> list[dict]:
    return [
        item
        for item in payload["assessments"]["items"]
        if item["family"] == FAMILY_SALES_PER_SQUARE_FOOT and item["status"] == "supported"
    ]


def _pair_key(locators: list[str]) -> tuple[str, ...]:
    return tuple(sorted(locators))


def test_fy2024_exclusion_flags_have_individually_bound_passages(tmp_path: Path):
    dest = _copy_extracted(tmp_path / "excl")
    sidecar = enrich_management_working_copies(dest, SOURCE)
    fy2024 = json.loads((dest / "LULU_FY2024_management_kpis.json").read_text())
    fy2025 = json.loads((dest / "LULU_FY2025_management_kpis.json").read_text())
    current = next(
        item
        for item in fy2024["reported_kpis"]
        if item["metric_id"] == "sales_per_square_foot" and item["period"] == "2025-02-02"
    )
    traced = next(
        item
        for item in fy2025["reported_kpis"]
        if item["metric_id"] == "sales_per_square_foot"
        and item["period"] == "2025-02-02"
        and item.get("traced_prior_period")
    )
    for item in (current, traced):
        exclusion = item["supporting_evidence"]["metric_exclusion"]
        assert item["qualifiers"]["excludes_53rd_week"] is True
        assert exclusion["passage"]
        assert exclusion["passage"].endswith(".")
        assert "sales per square foot" in exclusion["passage"].lower()
        assert "excluded" in exclusion["passage"].lower()
        assert "53" in exclusion["passage"]
        assert "Fiscal 2024 was a 53-week year" not in exclusion["passage"]
        assert exclusion["source_file"] == "LULU_FY2024_Annual_Report.pdf"
        assert 40 in exclusion["physical_pages"]
        assert exclusion["metric_id"] == "sales_per_square_foot"
        assert exclusion["period"] == "2025-02-02"
        binding = item["supporting_evidence"]["passage_bindings"]["metric_exclusion"]
        assert binding["source_file"] == "LULU_FY2024_Annual_Report.pdf"
        assert 40 in binding["physical_pages"]
        assert 34 in binding["printed_pages"]
    assert current["supporting_evidence"]["metric_exclusion"]["cross_filing"] is False
    assert traced["supporting_evidence"]["metric_exclusion"]["cross_filing"] is True
    fy2024_field = next(
        item
        for record in sidecar["documents"]
        if record["extraction_document"] == "LULU_FY2024_management_kpis.json"
        for item in record["fields"]
        if item["metric_id"] == "sales_per_square_foot" and item["period"] == "2025-02-02"
    )
    fy2025_traced_field = next(
        item
        for record in sidecar["documents"]
        if record["extraction_document"] == "LULU_FY2025_management_kpis.json"
        for item in record["fields"]
        if item["metric_id"] == "sales_per_square_foot" and item["period"] == "2025-02-02"
    )
    assert fy2024_field["metric_exclusion"]["physical_pages"] == fy2025_traced_field[
        "metric_exclusion"
    ]["physical_pages"]
    assert 40 in fy2024_field["metric_exclusion"]["physical_pages"]


def test_calendar_text_does_not_satisfy_exclusion_evidence():
    from core.ingestion.management_kpi_enrichment import (
        CalendarYearEvidence,
        _metric_exclusion_evidence,
        _metric_excludes_53rd_week,
    )

    calendar = CalendarYearEvidence(
        fiscal_year=2024,
        fifty_three_week=True,
        source_file="LULU_FY2024_Annual_Report.pdf",
        physical_page=32,
        passage="Fiscal 2024 was a 53-week year.",
        cross_filing=False,
    )
    assert _metric_exclusion_evidence(
        "sales_per_square_foot", calendar, [calendar.passage]
    ) is None
    assert _metric_excludes_53rd_week(
        "sales_per_square_foot", calendar, [calendar.passage]
    ) is None


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


def test_fy2022_management_use_and_current_period_table_are_identity_bound(
    tmp_path: Path,
):
    dest = _copy_extracted(tmp_path / "fy22-pres")
    sidecar = enrich_management_working_copies(dest, SOURCE)
    working = json.loads((dest / "LULU_FY2022_management_kpis.json").read_text())
    by_metric = {item["metric_id"]: item for item in _fy2022_fields(sidecar)}
    assert set(by_metric) == {row[0] for row in _FY2022_FOCUS}
    for metric_id, basis, phrase in _FY2022_FOCUS:
        field = by_metric[metric_id]
        passages = field["supporting_passages"]
        bindings = field["passage_bindings"]
        presentation = passages["presentation"]
        management_use = passages["management_use"]
        assert phrase in presentation.lower()
        assert "below changes" in presentation.lower()
        assert "e-commerce" not in presentation.lower()
        assert "e-commerce" not in management_use.lower()
        assert bindings["presentation"]["source_file"] == "LULU_FY2022_Annual_Report.pdf"
        assert 37 in bindings["presentation"]["physical_pages"]
        assert 33 in bindings["presentation"]["printed_pages"]
        assert bindings["management_use"]["source_file"] == "LULU_FY2022_Annual_Report.pdf"
        if basis == "constant_dollar":
            assert "management uses" in management_use.lower()
            assert "constant currency" in management_use.lower()
            assert 36 in bindings["management_use"]["physical_pages"]
            assert 32 in bindings["management_use"]["printed_pages"]
        elif metric_id == "total_comparable_sales_growth":
            assert (
                "we use total comparable sales" in management_use.lower()
                or "just one way of assessing" in management_use.lower()
            )
            assert set(bindings["management_use"]["physical_pages"]) <= {35, 36}
        else:
            assert "we use comparable store sales" in management_use.lower()
            assert "we use total comparable sales" not in management_use.lower()
            assert 35 in bindings["management_use"]["physical_pages"]
            assert 31 in bindings["management_use"]["printed_pages"]
        reported = next(
            item
            for item in working["reported_kpis"]
            if item["metric_id"] == metric_id
        )
        assert reported["presentation"]["role"] == "current"
        assert "assurance" not in reported
        assert "revision" not in reported
        definition = passages.get("definition", "")
        if "store_sales" in metric_id:
            assert "direct to consumer" not in definition.lower()
            assert "e-commerce" not in definition.lower()
        else:
            assert "direct to consumer" in definition.lower()
            assert "e-commerce" not in definition.lower()


def test_unrelated_strategy_language_cannot_satisfy_presentation_assurance_or_revision():
    strategy = (
        "Opening new stores and expanding existing stores is an important part "
        "of our growth strategy."
    )
    inspection = SourceInspection(
        source_file="LULU_FY2022_Annual_Report.pdf",
        physical_to_printed={36: 32},
        printed_to_physical={32: 36},
        fifty_three_week_years=(),
        fifty_two_week_years=(2022,),
        fiscal_calendar_evidenced=True,
        page_texts={36: strategy},
    )
    for metric_id, basis, _phrase in _FY2022_FOCUS:
        item = {"metric_id": metric_id, "value": 16.0, "basis": basis}
        passages = field_supporting_passages(
            inspection=inspection,
            physical_pages=(36,),
            item=item,
            comparison_window=None,
            calendar=None,
        )
        assert "presentation" not in passages
        assert "management_use" not in passages
        assert "assurance" not in passages
        assert "revision" not in passages


def test_definition_features_store_only_excludes_dtc_mention():
    store_only = (
        "Net revenue from company-operated stores open, or open after significant "
        "expansion, for at least 12 full fiscal months. Excludes new stores, stores "
        "not in expanded space for at least 12 full fiscal months, temporarily "
        "relocated/closed stores, direct-to-consumer and other operations, and "
        "closed company-operated stores."
    )
    total = "Comparable store sales plus direct-to-consumer net revenue."
    ecommerce = (
        "Comparable company-operated store and all e-commerce net revenue. "
        "Excludes new/expanded stores under 12 months, temporarily relocated/closed "
        "stores, closed stores, and channels other than company-operated stores and "
        "e-commerce."
    )
    strategy = (
        "Opening new stores and expanding existing stores is an important part "
        "of our growth strategy."
    )
    dtc_neighbor = (
        "Direct to consumer net revenue increased 33.2% compared to fiscal 2021."
    )
    assert definition_features(store_only)["channel_population"] == (
        "company_operated_stores"
    )
    assert definition_features(total)["channel_population"] == (
        "company_operated_stores_and_direct_to_consumer"
    )
    assert definition_features(ecommerce)["channel_population"] == (
        "company_operated_stores_and_ecommerce"
    )
    assert "channel_population" not in definition_features(strategy)
    assert definition_features(dtc_neighbor).get("channel_population") != (
        "company_operated_stores"
    )


def test_fy2022_presentation_source_agrees_with_table_passage_bindings(
    tmp_path: Path,
):
    dest = _copy_extracted(tmp_path / "fy22-src")
    sidecar = enrich_management_working_copies(dest, SOURCE)
    working = json.loads((dest / "LULU_FY2022_management_kpis.json").read_text())
    by_metric = {item["metric_id"]: item for item in _fy2022_fields(sidecar)}
    payload = reconciliation_management_admission_payload(
        reconcile_filings(
            load_and_validate_extracted_dir(dest, source_root=SOURCE),
            admit_periods=ADMIT_2022,
        )
    )
    admitted = {
        item["metric_id"]: item
        for item in payload["observations"]
        if item["kind"] == "reported_kpi"
        and item["extraction_document"] == "LULU_FY2022_management_kpis.json"
        and item["metric_id"] in {row[0] for row in _FY2022_FOCUS}
    }
    assert set(admitted) == {row[0] for row in _FY2022_FOCUS}
    table_ref = page_reference_from_printed((33,))
    for metric_id, basis, _phrase in _FY2022_FOCUS:
        field = by_metric[metric_id]
        bindings = field["passage_bindings"]
        presentation = bindings["presentation"]
        management_use = bindings["management_use"]
        definition = bindings["definition"]
        assert presentation["source_file"] == "LULU_FY2022_Annual_Report.pdf"
        assert presentation["physical_pages"] == [37]
        assert presentation["printed_pages"] == [33]
        assert 37 not in management_use["physical_pages"]
        assert 33 not in management_use["printed_pages"]
        assert set(management_use["physical_pages"]) <= {35, 36}
        if "total_comparable" in metric_id:
            assert 37 not in definition["physical_pages"]
        reported = next(
            item
            for item in working["reported_kpis"]
            if item["metric_id"] == metric_id
        )
        assert reported["source"]["page_reference"] == "Form 10-K p. 27"
        assert reported["presentation"]["source"]["page_reference"] == table_ref
        assert "physical_page_mapping" not in reported["presentation"]["source"]
        observation = admitted[metric_id]
        source = observation["presentation_evidence"]["source"]
        assert printed_pages_from_reference(source["page_reference"]) == (33,)
        assert source["physical_page_mapping"] == "33→37"
        assert observation["source"]["page_reference"] == "Form 10-K p. 27"
        assert observation["physical_page_mapping"] == "27→31"
        features = observation["supporting_evidence"]["definition_features"]
        if "store_sales" in metric_id:
            assert features["channel_population"] == "company_operated_stores"
            assert observation["scope"] == {"channel": "company_operated_stores"}
        else:
            assert features["channel_population"] == (
                "company_operated_stores_and_direct_to_consumer"
            )
            assert observation["scope"] == {"geography": "global"}
        assert observation["basis"] == basis


def test_neighboring_dtc_cannot_satisfy_store_only_identity_requirements():
    dtc = (
        "We use total comparable sales to evaluate the performance of our business "
        "from an omni-channel perspective. Total comparable sales combines comparable "
        "store sales and direct to consumer net revenue. Direct to consumer net "
        "revenue increased 33.2%."
    )
    inspection = SourceInspection(
        source_file="LULU_FY2022_Annual_Report.pdf",
        physical_to_printed={35: 31, 37: 33},
        printed_to_physical={31: 35, 33: 37},
        fifty_three_week_years=(),
        fifty_two_week_years=(2022,),
        fiscal_calendar_evidenced=True,
        page_texts={35: dtc, 37: dtc},
    )
    for metric_id, basis, _phrase in _FY2022_FOCUS:
        if "store_sales" not in metric_id:
            continue
        item = {"metric_id": metric_id, "value": 16.0, "basis": basis}
        passages = field_supporting_passages(
            inspection=inspection,
            physical_pages=(35, 37),
            item=item,
            comparison_window=None,
            calendar=None,
        )
        assert "presentation" not in passages
        assert "management_use" not in passages
        definition = passages.get("definition", "")
        assert "comparable store sales reflects" not in definition.lower()
        assert definition_features(dtc).get("channel_population") != (
            "company_operated_stores"
        )
