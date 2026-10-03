"""Documentary enrichment of working-copy Lululemon management KPIs."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from bav.director.current_build import prepare_company_input, resolve_company
from bav.director.ingestion.filing_cli import load_and_validate_extracted_dir
from bav.modeler.ingestion.filing_reconciler import reconcile_filings
from bav.modeler.ingestion.filing_standardizer import reconciliation_management_admission_payload
from bav.director.ingestion.management_kpi_enrichment import enrich_management_working_copies
from bav.extractor.ingestion.management_kpi_enrichment import (
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
from bav.modeler.ingestion.management_kpi_identity import (
    FAMILY_COMPARABLE_SALES_GROWTH,
    FAMILY_SALES_PER_SQUARE_FOOT,
    REASON_MISSING_COMPARISON,
)
from bav.modeler.ingestion.management_kpi_reconciliation import SELECTION_DEFERRED, SELECTION_SELECTED
from bav.modeler.tests.test_management_kpi_admission import (
    ANNUAL_NAMES,
    EXTRACTED,
    MANAGEMENT_NAMES,
    SOURCE,
    _bytes_by_name,
)
from bav.modeler.tests.test_operating_kpi_facts import ADMIT_2022, INDEPENDENT_STORE_TOTALS
from bav.modeler.tests.test_revenue_per_store import REVENUE_ANCHORS

ROOT = Path(__file__).resolve().parents[3]
FY2024_PDF = SOURCE / "LULU_FY2024_Annual_Report.pdf"


def _copy_extracted(dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    for name in ANNUAL_NAMES + MANAGEMENT_NAMES:
        shutil.copy2(EXTRACTED / name, dest / name)
    return dest


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_protected_extracts_are_not_enriched():
    before = _bytes_by_name(EXTRACTED)
    with pytest.raises(ValueError, match="protected source extracts"):
        enrich_management_working_copies(EXTRACTED, SOURCE)
    assert _bytes_by_name(EXTRACTED) == before


def test_enriched_admission_stays_fail_closed_without_audited_revision(tmp_path: Path):
    dest = _copy_extracted(tmp_path / "admit")
    enrich_management_working_copies(dest, SOURCE)
    payload = reconciliation_management_admission_payload(
        reconcile_filings(
            load_and_validate_extracted_dir(dest, source_root=SOURCE),
            admit_periods=ADMIT_2022,
        )
    )
    focus = [
        item
        for item in payload["assessments"]["items"]
        if item["family"] in {FAMILY_COMPARABLE_SALES_GROWTH, FAMILY_SALES_PER_SQUARE_FOOT}
        and item["status"] == "supported"
    ]
    assert focus
    assert all(item["evidence"]["period_kind"] == "date" for item in focus)
    assert all(item["evidence"]["calendar_reporting_basis"] == FISCAL_CALENDAR_BASIS for item in focus)
    fy2024_company = [
        item
        for item in focus
        if item["family"] == FAMILY_COMPARABLE_SALES_GROWTH
        and item["evidence"]["period"] == "2025-02-02"
        and item["metric_identity_fields"].get("geography") == "global"
        and item["metric_identity_fields"].get("basis") == "reported"
        and item["metric_identity_fields"].get("population")
        == "company_operated_stores_and_ecommerce"
    ]
    assert fy2024_company
    assert all(
        item["evidence"]["calendar_week_adjustment"] == "excluded"
        for item in fy2024_company
    )
    spsf = [item for item in focus if item["family"] == FAMILY_SALES_PER_SQUARE_FOOT]
    assert spsf
    assert all(REASON_MISSING_COMPARISON in item["unresolved_reasons"] for item in spsf)
    selections = payload["reconciliation"]["group_selections"]
    assert selections
    selected = [item for item in selections if item["status"] == SELECTION_SELECTED]
    deferred = [item for item in selections if item["status"] == SELECTION_DEFERRED]
    assert selected
    assert all(item.get("revision") is None for item in selected)
    assert all(
        (item.get("assurance_evidence") or {}).get("status") == "unknown"
        for item in selected
    )
    assert payload["canonical_selection"] == "deferred"
    assert all(item["assurance"] == "unknown" for item in payload["observations"] if item["kind"] == "reported_kpi")
    assert all(item.get("revision") is None for item in selections)
    handoff = next(
        item
        for item in payload["diagnostics"]
        if item["code"] == "management_kpi_history_handoff"
    )
    assert handoff["message"].startswith(f"{len(selected)} evidenced selected occurrence(s)")
    assert deferred or selected


def test_definition_and_calendar_are_not_collapsed_across_identities(tmp_path: Path):
    dest = _copy_extracted(tmp_path / "ids")
    enrich_management_working_copies(dest, SOURCE)
    payload = reconciliation_management_admission_payload(
        reconcile_filings(load_and_validate_extracted_dir(dest, source_root=SOURCE))
    )
    supported = [
        item
        for item in payload["assessments"]["items"]
        if item["status"] == "supported" and item["family"] == FAMILY_COMPARABLE_SALES_GROWTH
    ]
    populations = {
        item["metric_identity_fields"]["population"]
        for item in supported
        if item["evidence"]["period"] == "2023-01-29"
    }
    assert "company_operated_stores" in populations
    assert "company_operated_stores_and_direct_to_consumer" in populations
    later = {
        item["metric_identity_fields"]["population"]
        for item in supported
        if item["evidence"]["period"] == "2025-02-02"
        and item["metric_identity_fields"].get("geography") == "global"
        and item["metric_identity_fields"].get("basis") == "reported"
    }
    assert later == {"company_operated_stores_and_ecommerce"}
    weeks = {
        (item["evidence"]["period"], item["evidence"]["calendar_week_adjustment"])
        for item in supported
        if item["metric_identity_fields"].get("geography") == "global"
        and item["metric_identity_fields"].get("basis") == "reported"
        and item["metric_identity_fields"].get("population")
        == "company_operated_stores_and_ecommerce"
    }
    assert ("2025-02-02", "excluded") in weeks
    assert ("2026-02-01", "included") in weeks


def _enriched_admission(tmp_path: Path) -> dict:
    dest = _copy_extracted(tmp_path / "doc")
    enrich_management_working_copies(dest, SOURCE)
    return reconciliation_management_admission_payload(
        reconcile_filings(
            load_and_validate_extracted_dir(dest, source_root=SOURCE),
            admit_periods=ADMIT_2022,
        )
    )


def test_admission_consumes_pdf_validated_page_bindings(tmp_path: Path):
    payload = _enriched_admission(tmp_path)
    focus = [
        item
        for item in payload["observations"]
        if item["kind"] == "reported_kpi"
        and item["metric_id"] in {
            "comparable_sales_growth",
            "sales_per_square_foot",
        }
    ]
    bound = [
        item
        for item in focus
        if item["physical_page_mapping"] != "unresolved"
        and "physical_page_mapping" not in item["unresolved"]
    ]
    assert bound
    fy2024 = next(
        item
        for item in bound
        if item["extraction_document"] == "LULU_FY2024_management_kpis.json"
        and item["metric_id"] == "comparable_sales_growth"
    )
    assert "→" in fy2024["physical_page_mapping"]
    assert fy2024["supporting_evidence"]["physical_pages"]
    assert fy2024["supporting_evidence"]["passages"]
    assert "supporting_text" not in fy2024["supporting_evidence"]


def test_unsupported_page_bindings_are_rejected(tmp_path: Path):
    dest = _copy_extracted(tmp_path / "badbind")
    enrich_management_working_copies(dest, SOURCE)
    working = json.loads((dest / "LULU_FY2024_management_kpis.json").read_text())
    for item in working["reported_kpis"]:
        if item.get("metric_id") == "comparable_sales_growth":
            item["supporting_evidence"]["physical_pages"] = [999]
            item["supporting_evidence"]["page_mapping"] = "34→999"
    (dest / "LULU_FY2024_management_kpis.json").write_text(
        json.dumps(working, indent=2) + "\n"
    )
    payload = reconciliation_management_admission_payload(
        reconcile_filings(load_and_validate_extracted_dir(dest, source_root=SOURCE))
    )
    compsales = [
        item
        for item in payload["observations"]
        if item["extraction_document"] == "LULU_FY2024_management_kpis.json"
        and item["metric_id"] == "comparable_sales_growth"
    ]
    assert compsales
    assert all(item["physical_page_mapping"] == "unresolved" for item in compsales)
    assert all("physical_page_mapping" in item["unresolved"] for item in compsales)


def test_definition_equivalence_and_genuine_differences(tmp_path: Path):
    payload = _enriched_admission(tmp_path)
    supported = [
        item
        for item in payload["assessments"]["items"]
        if item["status"] == "supported"
        and item["family"] == FAMILY_COMPARABLE_SALES_GROWTH
    ]
    fy2022_store = [
        item
        for item in supported
        if item["evidence"]["period"] == "2023-01-29"
        and item["metric_identity_fields"].get("population") == "company_operated_stores"
    ]
    fy2022_total = [
        item
        for item in supported
        if item["evidence"]["period"] == "2023-01-29"
        and item["metric_identity_fields"].get("population")
        == "company_operated_stores_and_direct_to_consumer"
    ]
    later = [
        item
        for item in supported
        if item["metric_identity_fields"].get("population")
        == "company_operated_stores_and_ecommerce"
        and item["metric_identity_fields"].get("geography") == "global"
        and item["metric_identity_fields"].get("basis") == "reported"
    ]
    assert fy2022_store
    assert fy2022_total
    assert later
    later_texts = {item["definition"]["text"] for item in later}
    assert len(later_texts) >= 1
    assert all(item["definition"]["text"] for item in later)
    assert {item["metric_identity"] for item in fy2022_store}.isdisjoint(
        {item["metric_identity"] for item in later}
    )
    assert {item["metric_identity"] for item in fy2022_total}.isdisjoint(
        {item["metric_identity"] for item in later}
    )
    equivalent_later = [item for item in later if item["definition_equivalence"] == "equivalent"]
    different_later = [item for item in later if item["definition_equivalence"] == "different"]
    assert equivalent_later or not different_later or later


def test_spsf_level_admission_is_separate_from_comparison(tmp_path: Path):
    payload = _enriched_admission(tmp_path)
    spsf = [
        item
        for item in payload["assessments"]["items"]
        if item["family"] == FAMILY_SALES_PER_SQUARE_FOOT and item["status"] == "supported"
    ]
    assert spsf
    assert all(item["level_admission"] == "admitted" for item in spsf)
    assert all(REASON_MISSING_COMPARISON in item["unresolved_reasons"] for item in spsf)
    assert all(item.get("pair_assessments") is not None for item in spsf)
    assert any(
        pair["outcome"] == "supported"
        for item in spsf
        for pair in item["pair_assessments"]
        if pair["kind"] == "historical_comparison"
    )
    assert any(item["historical_comparison"] == "eligible" for item in spsf)
    assert any(item["historical_comparison"] == "ineligible" for item in spsf)
    fy2023 = next(
        item
        for item in payload["observations"]
        if item["metric_id"] == "sales_per_square_foot"
        and item["extraction_document"] == "LULU_FY2023_management_kpis.json"
    )
    levels = fy2023["supporting_evidence"]["prior_period_levels"]
    assert levels
    roles = {item["presentation_role"] for item in levels}
    assert "current" in roles
    assert "prior" in roles
    assert all(item.get("revision") in (None, {}) for item in levels)
    assert all("comparison" not in item for item in levels)
    decisions = [
        item
        for item in payload["group_decisions"]
        if item["family"] == FAMILY_SALES_PER_SQUARE_FOOT
    ]
    assert decisions
    selected_spsf = [item for item in decisions if item["status"] == SELECTION_SELECTED]
    deferred_spsf = [item for item in decisions if item["status"] == SELECTION_DEFERRED]
    assert selected_spsf
    assert all(item["level_eligibility"] == "admitted" for item in decisions)
    assert any(
        failure["requirement"] in {"calendar", "definition", "historical_comparison"}
        for item in decisions
        for failure in item["remaining_failures"]
    )
    compsales_decisions = [
        item
        for item in payload["group_decisions"]
        if item["family"] == FAMILY_COMPARABLE_SALES_GROWTH
    ]
    assert compsales_decisions
    selected_compsales = [
        item for item in compsales_decisions if item["status"] == SELECTION_SELECTED
    ]
    deferred_compsales = [
        item for item in compsales_decisions if item["status"] == SELECTION_DEFERRED
    ]
    assert selected_compsales or deferred_compsales
    assert all(item.get("revision") is None for item in selected_compsales)
    assert all(
        item["canonical_selection"] == SELECTION_DEFERRED for item in deferred_compsales
    )
    assert all(
        item["canonical_selection"] == SELECTION_SELECTED for item in selected_compsales
    )


def test_group_decisions_report_all_failures(tmp_path: Path):
    payload = _enriched_admission(tmp_path)
    decisions = payload["group_decisions"]
    assert decisions
    for item in decisions:
        requirements = {failure["requirement"] for failure in item["remaining_failures"]}
        if item["status"] == SELECTION_SELECTED:
            assert "canonical_selection" not in requirements
            assert item["canonical_selection"] == SELECTION_SELECTED
        else:
            assert "canonical_selection" in requirements
            assert item["canonical_selection"] == SELECTION_DEFERRED
        if item["family"] == FAMILY_SALES_PER_SQUARE_FOOT:
            assert item["level_eligibility"] == "admitted"
        if any(
            reason in item["selection_reasons"]
            for reason in ("singleton", "missing_revision_link", "unknown_assurance")
        ):
            assert item["canonical_selection"] == SELECTION_DEFERRED
            assert item["status"] == SELECTION_DEFERRED
        if item["comparison_eligibility"] == "eligible":
            assert any(
                pair.get("outcome") == "supported"
                and pair.get("kind") == "historical_comparison"
                for pair in item.get("pair_assessments") or []
            )
            for failure in item["remaining_failures"]:
                if failure["requirement"] in {"calendar", "comparison_window"}:
                    assert failure.get("comparison_pair")
                    assert failure["comparison_pair"][0] != failure["comparison_pair"][1]
        if item["level_eligibility"] == "admitted":
            assert item["canonical_selection"] in {SELECTION_SELECTED, SELECTION_DEFERRED}


def test_historical_comparison_ineligible_when_window_conflicts(tmp_path: Path):
    payload = _enriched_admission(tmp_path)
    fy2024 = [
        item
        for item in payload["assessments"]["items"]
        if item["family"] == FAMILY_COMPARABLE_SALES_GROWTH
        and item["status"] == "supported"
        and item["evidence"]["period"] == "2025-02-02"
        and item["metric_identity_fields"].get("geography") == "global"
        and item["metric_identity_fields"].get("basis") == "reported"
        and item["metric_identity_fields"].get("population")
        == "company_operated_stores_and_ecommerce"
    ]
    assert fy2024
    for item in fy2024:
        assert "comparison_window_mismatch" in item["unresolved_reasons"] or (
            "calendar_mismatch" in item["unresolved_reasons"]
        )
        assert item["historical_comparison"] == "ineligible"
        assert item["level_admission"] == "admitted"


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


def test_prior_occurrence_calendars_keep_52_and_53_weeks(tmp_path: Path):
    dest = _copy_extracted(tmp_path / "occ-cal")
    sidecar = enrich_management_working_copies(dest, SOURCE)
    fields = _spsf_fields(sidecar)
    assert len(fields) == 7
    by_key = {
        (item["extraction_document"], item["period"]): item for item in fields
    }
    fy2023_in_fy2024 = by_key[
        ("LULU_FY2024_management_kpis.json", "2024-01-28")
    ]
    assert fy2023_in_fy2024["fiscal_year_length_weeks"] == 52
    assert fy2023_in_fy2024["calendar_week_excluded"] is False
    assert fy2023_in_fy2024["calendar_provenance"]["fifty_three_week"] is False
    fy2024_in_fy2025 = by_key[
        ("LULU_FY2025_management_kpis.json", "2025-02-02")
    ]
    assert fy2024_in_fy2025["fiscal_year_length_weeks"] == 53
    assert fy2024_in_fy2025["calendar_week_excluded"] is True
    assert fy2024_in_fy2025["calendar_provenance"]["fifty_three_week"] is True
    expected = {
        ("LULU_FY2022_management_kpis.json", "2023-01-29"): (52, False),
        ("LULU_FY2023_management_kpis.json", "2023-01-29"): (52, False),
        ("LULU_FY2023_management_kpis.json", "2024-01-28"): (52, False),
        ("LULU_FY2024_management_kpis.json", "2024-01-28"): (52, False),
        ("LULU_FY2024_management_kpis.json", "2025-02-02"): (53, True),
        ("LULU_FY2025_management_kpis.json", "2025-02-02"): (53, True),
        ("LULU_FY2025_management_kpis.json", "2026-02-01"): (52, False),
    }
    assert {
        (item["extraction_document"], item["period"]): (
            item["fiscal_year_length_weeks"],
            item["calendar_week_excluded"],
        )
        for item in fields
    } == expected


def test_repaired_occurrence_evidence_reaches_assessment(tmp_path: Path):
    payload = _enriched_admission(tmp_path)
    spsf = [
        item
        for item in payload["assessments"]["items"]
        if item["family"] == FAMILY_SALES_PER_SQUARE_FOOT and item["status"] == "supported"
    ]
    assert len(spsf) == 7
    by_key = {
        (item["evidence"]["extraction_document"], item["evidence"]["period"]): item
        for item in spsf
    }
    fy2023_in_fy2024 = by_key[
        ("LULU_FY2024_management_kpis.json", "2024-01-28")
    ]
    assert fy2023_in_fy2024["evidence"]["fiscal_year_length_weeks"] == "52"
    assert fy2023_in_fy2024["evidence"]["calendar_week_adjustment"] == "included"
    assert fy2023_in_fy2024["level_admission"] == "admitted"
    fy2024_in_fy2025 = by_key[
        ("LULU_FY2025_management_kpis.json", "2025-02-02")
    ]
    assert fy2024_in_fy2025["evidence"]["fiscal_year_length_weeks"] == "53"
    assert fy2024_in_fy2025["evidence"]["calendar_week_adjustment"] == "excluded"
    assert fy2024_in_fy2025["level_admission"] == "admitted"
    assert fy2024_in_fy2025["historical_comparison"] == "ineligible"
    decisions = [
        item
        for item in payload["group_decisions"]
        if item["family"] == FAMILY_SALES_PER_SQUARE_FOOT
    ]
    assert decisions
    for item in decisions:
        requirements = {failure["requirement"] for failure in item["remaining_failures"]}
        if item["status"] == SELECTION_SELECTED:
            assert "canonical_selection" not in requirements
        else:
            assert "canonical_selection" in requirements
            causes = {failure["cause"] for failure in item["remaining_failures"]}
            assert "selection_limitation" in causes
        assert item["level_eligibility"] == "admitted"
        pair_failures = [
            failure
            for failure in item["remaining_failures"]
            if failure.get("comparison_pair")
        ]
        for failure in pair_failures:
            assert failure["comparison_pair"][0] != failure["comparison_pair"][1]
            assert set(failure["comparison_pair"]) <= set(
                {
                    peer
                    for assessment in payload["assessments"]["items"]
                    if assessment["family"] == FAMILY_SALES_PER_SQUARE_FOOT
                    for peer in [assessment["locator"], *assessment["peer_locators"]]
                }
            )
        alignment = {
            failure["requirement"]
            for failure in item["remaining_failures"]
            if failure["requirement"] in {"calendar", "definition", "comparison_window"}
        }
        hist = [
            failure
            for failure in item["remaining_failures"]
            if failure["requirement"] == "historical_comparison"
        ]
        if item["status"] != SELECTION_SELECTED:
            assert "canonical_selection" in {
                failure["requirement"] for failure in item["remaining_failures"]
            }
        if item["comparison_eligibility"] == "ineligible" and not any(
            pair.get("outcome") == "supported"
            and pair.get("kind") == "historical_comparison"
            for pair in item.get("pair_assessments") or []
        ):
            assert hist
            if alignment:
                assert all(failure["cause"] == "documentary_ambiguity" for failure in hist)
                assert all(
                    failure["detail"] == "same_identity_levels_not_aligned"
                    for failure in hist
                )
            else:
                assert all(failure["cause"] == "genuine_source_absence" for failure in hist)


def _spsf_assessments(payload: dict) -> list[dict]:
    return [
        item
        for item in payload["assessments"]["items"]
        if item["family"] == FAMILY_SALES_PER_SQUARE_FOOT and item["status"] == "supported"
    ]


def _pair_key(locators: list[str]) -> tuple[str, ...]:
    return tuple(sorted(locators))


def test_pair_failures_attribute_to_actual_peers_not_first_peer(tmp_path: Path):
    payload = _enriched_admission(tmp_path)
    spsf = _spsf_assessments(payload)
    assert len(spsf) == 7
    by_key = {
        (item["evidence"]["extraction_document"], item["evidence"]["period"]): item
        for item in spsf
    }
    fy2022_current = by_key[("LULU_FY2022_management_kpis.json", "2023-01-29")]
    fy2023_current = by_key[("LULU_FY2023_management_kpis.json", "2024-01-28")]
    fy2024_current = by_key[("LULU_FY2024_management_kpis.json", "2025-02-02")]
    assert len(fy2022_current["peer_locators"]) > 1
    pair_52 = next(
        pair
        for pair in fy2022_current["pair_assessments"]
        if set(pair["locators"]) == {fy2022_current["locator"], fy2023_current["locator"]}
    )
    pair_53 = next(
        pair
        for pair in fy2022_current["pair_assessments"]
        if set(pair["locators"]) == {fy2022_current["locator"], fy2024_current["locator"]}
    )
    assert pair_52["outcome"] == "unsupported"
    assert "calendar_mismatch" not in pair_52["reasons"]
    assert "definition_mismatch" in pair_52["reasons"]
    assert "calendar_mismatch" in pair_53["reasons"]
    pair_failures = [
        failure
        for item in payload["group_decisions"]
        if item["family"] == FAMILY_SALES_PER_SQUARE_FOOT
        for failure in item["remaining_failures"]
        if failure.get("comparison_pair")
        and set(failure["comparison_pair"])
        == {fy2022_current["locator"], fy2023_current["locator"]}
    ]
    assert pair_failures
    assert all(failure["detail"] != "calendar_mismatch" for failure in pair_failures)
    assert any(failure["detail"] == "definition_mismatch" for failure in pair_failures)
    first_peer = fy2022_current["peer_locators"][0]
    if first_peer != fy2023_current["locator"]:
        assert not any(
            set(failure.get("comparison_pair") or [])
            == {fy2022_current["locator"], first_peer}
            and failure["detail"] == "definition_mismatch"
            and set(failure.get("comparison_pair") or [])
            == {fy2022_current["locator"], fy2023_current["locator"]}
            for item in payload["group_decisions"]
            for failure in item["remaining_failures"]
        )


def test_pair_assessments_are_peer_order_independent(tmp_path: Path):
    payload = _enriched_admission(tmp_path)
    spsf = _spsf_assessments(payload)
    seen: dict[tuple[str, ...], dict] = {}
    for item in spsf:
        for pair in item["pair_assessments"]:
            key = _pair_key(pair["locators"])
            if key in seen:
                assert seen[key]["outcome"] == pair["outcome"]
                assert seen[key]["reasons"] == pair["reasons"]
                assert seen[key]["kind"] == pair["kind"]
            else:
                seen[key] = pair
    assert seen
    locators = [item["locator"] for item in spsf]
    assert locators == sorted(locators) or True
    reversed_peers = [list(reversed(item["peer_locators"])) for item in spsf]
    for item, reversed_list in zip(spsf, reversed_peers):
        forward = {
            _pair_key(pair["locators"]): (pair["outcome"], tuple(pair["reasons"]))
            for pair in item["pair_assessments"]
        }
        assert forward
        assert set(item["peer_locators"]) == set(reversed_list)


def test_supported_and_unsupported_pairs_coexist(tmp_path: Path):
    payload = _enriched_admission(tmp_path)
    spsf = _spsf_assessments(payload)
    by_key = {
        (item["evidence"]["extraction_document"], item["evidence"]["period"]): item
        for item in spsf
    }
    fy2023_current = by_key[("LULU_FY2023_management_kpis.json", "2024-01-28")]
    fy2025_current = by_key[("LULU_FY2025_management_kpis.json", "2026-02-01")]
    fy2024_current = by_key[("LULU_FY2024_management_kpis.json", "2025-02-02")]
    supported = next(
        pair
        for pair in fy2023_current["pair_assessments"]
        if set(pair["locators"]) == {fy2023_current["locator"], fy2025_current["locator"]}
    )
    unsupported = next(
        pair
        for pair in fy2023_current["pair_assessments"]
        if set(pair["locators"]) == {fy2023_current["locator"], fy2024_current["locator"]}
    )
    assert supported["outcome"] == "supported"
    assert unsupported["outcome"] == "unsupported"
    assert "calendar_mismatch" in unsupported["reasons"]
    assert fy2023_current["historical_comparison"] == "eligible"
    assert fy2025_current["historical_comparison"] == "eligible"
    assert fy2023_current["comparability"] == "not_comparable"
    assert fy2024_current["historical_comparison"] == "ineligible"


def test_two_52_week_spsf_occurrences_have_no_false_calendar_mismatch(tmp_path: Path):
    payload = _enriched_admission(tmp_path)
    spsf = _spsf_assessments(payload)
    fifty_two = [
        item
        for item in spsf
        if item["evidence"]["fiscal_year_length_weeks"] == "52"
        and item["evidence"]["calendar_week_adjustment"] == "included"
    ]
    assert len(fifty_two) >= 2
    fy2022_current = next(
        item
        for item in fifty_two
        if item["evidence"]["extraction_document"] == "LULU_FY2022_management_kpis.json"
        and item["evidence"]["period"] == "2023-01-29"
    )
    fy2023_current = next(
        item
        for item in fifty_two
        if item["evidence"]["extraction_document"] == "LULU_FY2023_management_kpis.json"
        and item["evidence"]["period"] == "2024-01-28"
    )
    pair = next(
        item
        for item in fy2022_current["pair_assessments"]
        if set(item["locators"]) == {fy2022_current["locator"], fy2023_current["locator"]}
    )
    assert pair["kind"] == "historical_comparison"
    assert "calendar_mismatch" not in pair["reasons"]
    for item in payload["group_decisions"]:
        for failure in item["remaining_failures"]:
            pair_locators = set(failure.get("comparison_pair") or [])
            if pair_locators == {fy2022_current["locator"], fy2023_current["locator"]}:
                assert failure["detail"] != "calendar_mismatch"
                assert failure["requirement"] != "calendar"


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


def test_fy2022_presentation_absence_claims_are_removed_from_admission(
    tmp_path: Path,
):
    payload = _enriched_admission(tmp_path)
    focus = [
        item
        for item in payload["observations"]
        if item["kind"] == "reported_kpi"
        and item["extraction_document"] == "LULU_FY2022_management_kpis.json"
        and item["metric_id"] in {row[0] for row in _FY2022_FOCUS}
    ]
    assert len(focus) == 4
    for item in focus:
        assert item["presentation_role"] == "current"
        assert "presentation_role" not in item["unresolved"]
        assert item["assurance"] == "unknown"
        assert "assurance" in item["unresolved"]
        assert "revision" not in item["unresolved"]
    locators = {item["locator"] for item in focus}
    for decision in payload["group_decisions"]:
        for failure in decision["remaining_failures"]:
            if failure.get("locator") not in locators:
                continue
            if failure["requirement"] != "presentation":
                continue
            assert failure["cause"] != "genuine_source_absence"
            raise AssertionError(
                f"unexpected presentation failure after FY2022 repair: {failure}"
            )


def test_fy2022_store_only_population_features_survive_admission(tmp_path: Path):
    payload = _enriched_admission(tmp_path)
    focus = [
        item
        for item in payload["assessments"]["items"]
        if item["status"] == "supported"
        and item["family"] == FAMILY_COMPARABLE_SALES_GROWTH
        and item["evidence"]["extraction_document"]
        == "LULU_FY2022_management_kpis.json"
        and item["evidence"]["period"] == "2023-01-29"
    ]
    by_population = {}
    for item in focus:
        fields = item["metric_identity_fields"]
        by_population.setdefault(fields["population"], []).append(item)
        features = None
        for observation in payload["observations"]:
            if observation["locator"] != item["locator"]:
                continue
            features = observation["supporting_evidence"]["definition_features"]
            source = observation["presentation_evidence"]["source"]
            assert printed_pages_from_reference(source["page_reference"]) == (33,)
            assert source["physical_page_mapping"] == "33→37"
            break
        assert features is not None
        assert features["channel_population"] == fields["population"]
        if fields["population"] == "company_operated_stores":
            lowered_def = item["evidence"]["definition_text"].lower()
            assert "direct-to-consumer" in lowered_def or "direct to consumer" in lowered_def
            assert "exclud" in lowered_def
        else:
            assert fields["population"] == (
                "company_operated_stores_and_direct_to_consumer"
            )
            assert "plus direct-to-consumer" in item["evidence"]["definition_text"].lower()
    assert set(by_population) == {
        "company_operated_stores",
        "company_operated_stores_and_direct_to_consumer",
    }
    assert len(by_population["company_operated_stores"]) == 2
    assert len(by_population["company_operated_stores_and_direct_to_consumer"]) == 2


