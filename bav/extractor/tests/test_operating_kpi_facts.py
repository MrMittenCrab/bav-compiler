"""Company-operated store KPI source-to-model handoff."""

from __future__ import annotations

import copy
import json
import math
import subprocess
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from bav.extractor.data.filing import PresentationRole, SourceRef, SupplementalFact
from bav.modeler.data.historical_operating_kpis import (
    METRIC_STORE_COUNT,
    POPULATION_COMPANY_OPERATED,
    STORE_COUNT_FACT_TYPE,
)
from bav.modeler.data.interface import (
    FinancialPeriod,
    HistoricalManagementKpiObservation,
    HistoricalOperatingKpiData,
    HistoricalOperatingKpiObservation,
    StandardizedFinancials,
)
from bav.modeler.data.standardized_io import standardized_from_payload, standardized_to_payload
from bav.extractor.data.filing_json import extracted_filing_to_payload, load_extracted_filing
from bav.modeler.ingestion.filing_reconciler import SupplementalObservation, reconcile_filings
from bav.modeler.ingestion.filing_standardizer import (
    reconciliation_conflicts_payload,
    reconciliation_provenance_payload,
    standardize_reconciled,
)
from bav.director.ingestion.filing_validator import validate_extracted_filing
from bav.modeler.ingestion.operating_kpi import select_operating_kpi_facts
from bav.modeler.tests.test_filing_reconciler import _filing, _validated

ROOT = Path(__file__).resolve().parents[3]
BENCH = ROOT / "build" / "input" / "lululemon"
EXTRACTED = BENCH / "extracted"
SOURCE = BENCH / "source"
FIXTURE = (
    ROOT
    / "bav"
    / "extractor"
    / "tests"
    / "fixtures"
    / "operating_kpis"
    / "lululemon_company_operated_stores.json"
)
PREPARE = ROOT / "bav" / "extractor" / "scripts" / "prepare_lululemon_operating_kpi_filings.py"

P2022 = date(2022, 1, 30)
P2023 = date(2023, 1, 29)
P2024 = date(2024, 1, 28)
P2025 = date(2025, 2, 2)
P2026 = date(2026, 2, 1)
ADMIT_2022 = (P2022,)

INDEPENDENT_STORE_TOTALS = {
    P2022: 574,
    P2023: 655,
    P2024: 711,
    P2025: 767,
    P2026: 811,
}
EXPECTED_SELECTION = {
    P2022: (2022, "comparative", "sole_source_observation", 7),
    P2023: (2023, "comparative", "later_audited_presentation", 11),
    P2024: (2024, "comparative", "later_audited_presentation", 11),
    P2025: (2025, "comparative", "later_audited_presentation", 11),
    P2026: (2025, "current_period", "sole_source_observation", 11),
}
EXPECTED_SOURCE_NOTES = {
    P2022: "Company-Operated Stores",
    P2023: "Number of company-operated stores by market",
    P2024: "Number of company-operated stores by market",
    P2025: "Number of company-operated stores by market",
    P2026: "Number of company-operated stores by market",
}
REPORTED_STORE_LABEL = "Total company-operated stores"
_OMIT = object()
LABEL_MUTATIONS = (
    pytest.param(_OMIT, id="omitted"),
    pytest.param(None, id="null"),
    pytest.param("", id="empty"),
    pytest.param(" \t ", id="whitespace"),
)
NOTE_CONTEXTS = (
    pytest.param("Company-Operated Stores", id="note-populated"),
    pytest.param(_OMIT, id="note-absent"),
)
NON_STRING_LABELS = (
    pytest.param(123, id="int-123"),
    pytest.param(1.5, id="float-1.5"),
    pytest.param(0, id="int-0"),
    pytest.param(True, id="true"),
    pytest.param(False, id="false"),
    pytest.param({"x": 1}, id="nonempty-object"),
    pytest.param({}, id="empty-object"),
    pytest.param([1], id="nonempty-array"),
    pytest.param([], id="empty-array"),
)


def _store(
    period: date,
    value: float,
    *,
    page: int = 7,
    role: PresentationRole = PresentationRole.CURRENT_PERIOD,
    unit: str = "stores",
    label: object = REPORTED_STORE_LABEL,
    note: str = "Company-Operated Stores",
) -> SupplementalFact:
    return SupplementalFact(
        fact_type=STORE_COUNT_FACT_TYPE,
        period=period,
        value=value,
        status="reported",
        source=SourceRef(
            page=page,
            note=note,
            label=label,  # type: ignore[arg-type]
        ),
        presentation_role=role.value,
        unit=unit,
    )


def _label_text(label: object) -> object:
    return "" if label is _OMIT else label


def _note_text(note: object) -> str:
    return "" if note is _OMIT else str(note)


def _mutate_serialized_source(source: dict, *, label: object, note: object) -> dict:
    mutated = dict(source)
    if label is _OMIT:
        mutated.pop("label", None)
    else:
        mutated["label"] = label
    if note is _OMIT:
        mutated.pop("note", None)
    else:
        mutated["note"] = note
    return mutated


def _prepare_augmented(tmp_path: Path) -> Path:
    dest = tmp_path / "augmented"
    completed = subprocess.run(
        [
            sys.executable,
            str(PREPARE),
            "--extracted",
            str(EXTRACTED),
            "--dest",
            str(dest),
            "--facts",
            str(FIXTURE),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return dest


def _validated_augmented(tmp_path: Path):
    dest = _prepare_augmented(tmp_path)
    validated = []
    for name in (
        "LULU_FY2022.json",
        "LULU_FY2023.json",
        "LULU_FY2024.json",
        "LULU_FY2025.json",
    ):
        filing = load_extracted_filing(dest / name)
        report = validate_extracted_filing(filing, source_root=SOURCE)
        assert report.ok
        validated.append((filing, report))
    return dest, validated


def _kpi_model_observation(
    period: date,
    value: float,
    *,
    unit: str = "stores",
    metric: str = METRIC_STORE_COUNT,
    population: str = POPULATION_COMPANY_OPERATED,
) -> HistoricalOperatingKpiObservation:
    return HistoricalOperatingKpiObservation(
        metric=metric,
        population=population,
        period=period,
        value=value,
        unit=unit,
    )


def _fin_with_operating_kpis(
    *observations: HistoricalOperatingKpiObservation,
    extra_periods: list[date] | None = None,
    units: str = "USD in Thousands",
    include_payload: bool = True,
    management: list[HistoricalManagementKpiObservation] | None = None,
) -> StandardizedFinancials:
    if extra_periods is not None:
        dates = extra_periods
    else:
        dates = []
        seen: set[date] = set()
        for item in (*observations, *(management or ())):
            if item.period not in seen:
                dates.append(item.period)
                seen.add(item.period)
    if not dates:
        dates = [date(2025, 12, 31)]
    payload = (
        HistoricalOperatingKpiData(
            observations=list(observations),
            management_observations=list(management or ()),
        )
        if include_payload
        else None
    )
    return StandardizedFinancials(
        ticker="T",
        company_name="Co",
        currency="USD",
        units=units,
        jurisdiction="US",
        periods=[
            FinancialPeriod(end_date=period, label=f"FY{period.year}")
            for period in dates
        ],
        historical_operating_kpis=payload,
    )


def _kpi_observation(fact: SupplementalFact) -> SupplementalObservation:
    return SupplementalObservation(
        kind="note",
        filing_year=2025,
        source_file="a2025.pdf",
        source_sha256="abc",
        fact=fact,
    )


@pytest.mark.parametrize("label", LABEL_MUTATIONS)
@pytest.mark.parametrize("note", NOTE_CONTEXTS)
def test_missing_blank_labels_fail_even_with_note_context(label, note):
    period = date(2025, 12, 31)
    good = _store(period, 811)
    original = copy.deepcopy(good)
    bad = _store(period, 811, label=_label_text(label), note=_note_text(note))
    with pytest.raises(ValueError, match="missing reported label"):
        select_operating_kpi_facts((_kpi_observation(bad),))
    assert good == original
    assert good.source.label == REPORTED_STORE_LABEL
    assert good.source.note == "Company-Operated Stores"


@pytest.mark.parametrize("label", LABEL_MUTATIONS)
@pytest.mark.parametrize("note", NOTE_CONTEXTS)
def test_serialized_label_mutations_fail_filing_validation_and_reconcile(
    tmp_path: Path, label, note
):
    dest = _prepare_augmented(tmp_path)
    target = dest / "LULU_FY2025.json"
    before = {path: path.read_bytes() for path in dest.glob("*.json")}
    payload = json.loads(target.read_text(encoding="utf-8"))
    original_payload = copy.deepcopy(payload)
    stores = [
        fact
        for fact in payload["note_facts"]
        if fact.get("fact_type") == STORE_COUNT_FACT_TYPE
    ]
    assert stores
    for fact in stores:
        fact["source"] = _mutate_serialized_source(
            fact["source"], label=label, note=note
        )
    mutated_path = tmp_path / "mutated-fy2025.json"
    mutated_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    filing = load_extracted_filing(mutated_path)
    report = validate_extracted_filing(filing, source_root=SOURCE)
    assert not report.ok
    assert any(
        issue.code == "invalid_operating_kpi"
        and "missing reported label" in issue.message
        for issue in report.errors
    )
    with pytest.raises(ValueError, match="cannot reconcile filings with validation errors"):
        reconcile_filings([(filing, report)])
    assert json.loads(target.read_text(encoding="utf-8")) == original_payload
    assert {path: path.read_bytes() for path in dest.glob("*.json")} == before
    out = tmp_path / "reconciled"
    assert not out.exists()


@pytest.mark.parametrize("label", NON_STRING_LABELS)
@pytest.mark.parametrize("note", NOTE_CONTEXTS)
def test_serialized_non_string_labels_rejected_before_parse_coercion(
    tmp_path: Path, label, note
):
    dest = _prepare_augmented(tmp_path)
    target = dest / "LULU_FY2025.json"
    before = {path: path.read_bytes() for path in dest.glob("*.json")}
    payload = json.loads(target.read_text(encoding="utf-8"))
    original_payload = copy.deepcopy(payload)
    stores = [
        fact
        for fact in payload["note_facts"]
        if fact.get("fact_type") == STORE_COUNT_FACT_TYPE
    ]
    assert stores
    for fact in stores:
        fact["source"] = _mutate_serialized_source(
            fact["source"], label=label, note=note
        )
    mutated_path = tmp_path / "mutated-non-string-fy2025.json"
    mutated_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing reported label") as excinfo:
        load_extracted_filing(mutated_path)
    assert "invalid_operating_kpi" not in str(excinfo.value)
    assert json.loads(target.read_text(encoding="utf-8")) == original_payload
    assert {path: path.read_bytes() for path in dest.glob("*.json")} == before
    assert not (tmp_path / "reconciled").exists()


@pytest.mark.parametrize("label", NON_STRING_LABELS)
@pytest.mark.parametrize("note", NOTE_CONTEXTS)
def test_in_memory_non_string_labels_fail_even_with_note_context(label, note):
    period = date(2025, 12, 31)
    good = _store(period, 811)
    original = copy.deepcopy(good)
    bad = _store(period, 811, label=label, note=_note_text(note))
    with pytest.raises(ValueError, match="missing reported label"):
        select_operating_kpi_facts((_kpi_observation(bad),))
    assert good == original
    assert good.source.label == REPORTED_STORE_LABEL
    assert good.source.note == "Company-Operated Stores"


def test_review_reproduction_removes_label_and_note_from_serialized_store(
    tmp_path: Path,
):
    dest = _prepare_augmented(tmp_path)
    target = dest / "LULU_FY2025.json"
    before = target.read_bytes()
    payload = json.loads(before)
    observation = next(
        fact
        for fact in payload["note_facts"]
        if fact.get("fact_type") == STORE_COUNT_FACT_TYPE
    )
    assert observation["source"]["label"] == REPORTED_STORE_LABEL
    assert observation["source"]["note"]
    observation["source"].pop("label")
    observation["source"].pop("note")
    mutated_path = tmp_path / "review-repro.json"
    mutated_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    assert target.read_bytes() == before
    filing = load_extracted_filing(mutated_path)
    report = validate_extracted_filing(filing, source_root=SOURCE)
    assert not report.ok
    assert any(
        issue.code == "invalid_operating_kpi"
        and "missing reported label" in issue.message
        for issue in report.errors
    )
    with pytest.raises(ValueError, match="cannot reconcile filings with validation errors"):
        reconcile_filings([(filing, report)])
    assert target.read_bytes() == before


def test_valid_label_without_note_is_accepted(tmp_path: Path):
    period = date(2025, 12, 31)
    fact = _store(period, 811, note="")
    f2025 = _filing(
        year=2025,
        source_file="a2025.pdf",
        revenue_values={period: (110.0, PresentationRole.CURRENT_PERIOD)},
        note_facts=(fact,),
    )
    reconciled = reconcile_filings([_validated(tmp_path, f2025, b"2025")])
    selected = reconciled.selected_operating_kpi_facts[0]
    assert selected.value == 811
    assert selected.source_label == REPORTED_STORE_LABEL
    assert selected.source_note == ""
    provenance = reconciliation_provenance_payload(reconciled)
    assert provenance["selected_operating_kpi_facts"][0]["source_label"] == REPORTED_STORE_LABEL
    assert "source_note" not in provenance["selected_operating_kpi_facts"][0]


def test_augmented_lululemon_filings_round_trip_and_selected_totals(tmp_path: Path):
    originals = {
        name: json.loads((EXTRACTED / name).read_text(encoding="utf-8"))
        for name in (
            "LULU_FY2022.json",
            "LULU_FY2023.json",
            "LULU_FY2024.json",
            "LULU_FY2025.json",
        )
    }
    dest, validated = _validated_augmented(tmp_path)
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    for name, original in originals.items():
        reloaded = load_extracted_filing(dest / name)
        dumped = extracted_filing_to_payload(reloaded)
        round_path = tmp_path / f"round-{name}"
        round_path.write_text(json.dumps(dumped, indent=2) + "\n", encoding="utf-8")
        again = extracted_filing_to_payload(load_extracted_filing(round_path))
        assert again == dumped
        original_payload = extracted_filing_to_payload(
            load_extracted_filing(EXTRACTED / name)
        )
        assert dumped["statements"] == original_payload["statements"]
        assert dumped["share_facts"] == original_payload["share_facts"]
        assert dumped["filing"]["source_sha256"] == original["filing"]["source_sha256"]
        geo = [
            fact
            for fact in dumped["note_facts"]
            if str(fact["fact_type"]).startswith("segment.geo.")
        ]
        original_geo = [
            fact
            for fact in original_payload["note_facts"]
            if str(fact["fact_type"]).startswith("segment.geo.")
        ]
        assert geo == original_geo
        stores = [
            fact
            for fact in dumped["note_facts"]
            if fact["fact_type"] == STORE_COUNT_FACT_TYPE
        ]
        assert stores == fixture[name]
        assert all(fact["unit"] == "stores" for fact in stores)

    for order in (validated, list(reversed(validated))):
        reconciled = reconcile_filings(order, admit_periods=ADMIT_2022)
        selected = {
            item.period: item for item in reconciled.selected_operating_kpi_facts
        }
        assert set(selected) == set(INDEPENDENT_STORE_TOTALS)
        for period, value in INDEPENDENT_STORE_TOTALS.items():
            item = selected[period]
            year, role, reason, page = EXPECTED_SELECTION[period]
            assert item.value == value
            assert item.unit == "stores"
            assert item.metric == METRIC_STORE_COUNT
            assert item.population == POPULATION_COMPANY_OPERATED
            assert item.filing_year == year
            assert item.presentation_basis == role
            assert item.selection_reason == reason
            assert item.pdf_page == page
            assert item.source_label == REPORTED_STORE_LABEL
            assert item.source_note == EXPECTED_SOURCE_NOTES[period]
            assert item.source_label != item.fact_type

        assert len(reconciled.selected_geographic_facts) == 56
        americas = [
            item
            for item in reconciled.selected_geographic_facts
            if item.period == P2025 and item.fact_type.endswith("net_revenue.americas")
        ]
        assert americas == [
            next(
                item
                for item in reconciled.selected_geographic_facts
                if item.period == P2025
                and item.fact_type.endswith("net_revenue.americas")
            )
        ]
        assert americas[0].value == 7928156

        fin = standardize_reconciled(reconciled)
        restored = standardized_from_payload(standardized_to_payload(fin))
        assert restored.historical_operating_kpis == fin.historical_operating_kpis
        model = {
            item.period: item for item in restored.historical_operating_kpis.observations
        }
        assert set(model) == set(INDEPENDENT_STORE_TOTALS)
        for period, value in INDEPENDENT_STORE_TOTALS.items():
            assert model[period].value == value
            assert model[period].unit == "stores"
        payload = standardized_to_payload(fin)
        kpi_json = json.dumps(payload["historical_operating_kpis"])
        assert "source_sha256" not in kpi_json
        assert "pdf_page" not in kpi_json
        assert "source_label" not in kpi_json
        assert "source_note" not in kpi_json
        assert restored.historical_segment == fin.historical_segment
        assert sum(len(snap.values) for snap in restored.historical_segment.periods) == 56
        provenance = reconciliation_provenance_payload(reconciled)
        assert len(provenance["selected_operating_kpi_facts"]) == 5
        assert all(
            row["unit"] == "stores"
            and row["value"] == INDEPENDENT_STORE_TOTALS[date.fromisoformat(row["period"])]
            and row["source_label"] == REPORTED_STORE_LABEL
            and row["source_note"] == EXPECTED_SOURCE_NOTES[date.fromisoformat(row["period"])]
            for row in provenance["selected_operating_kpi_facts"]
        )

    for name, original in originals.items():
        assert json.loads((EXTRACTED / name).read_text(encoding="utf-8")) == original


