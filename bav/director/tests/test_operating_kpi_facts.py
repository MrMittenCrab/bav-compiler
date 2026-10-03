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


def test_missing_label_cli_leaves_inputs_and_output_unchanged(tmp_path: Path):
    dest = _prepare_augmented(tmp_path)
    target = dest / "LULU_FY2025.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    for fact in payload["note_facts"]:
        if fact.get("fact_type") == STORE_COUNT_FACT_TYPE:
            fact["source"].pop("label", None)
            fact["source"].pop("note", None)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    before = {path: path.read_bytes() for path in dest.glob("*.json")}
    out = tmp_path / "reconciled"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "bav",
            "reconcile",
            str(dest),
            "--source-root",
            str(SOURCE),
            "--admit-period",
            "2022-01-30",
            "-o",
            str(out),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    combined = completed.stdout + completed.stderr
    assert completed.returncode != 0
    assert "invalid_operating_kpi" in combined
    assert "missing reported label" in combined
    assert "wrote no artifacts" in combined
    assert {path: path.read_bytes() for path in dest.glob("*.json")} == before
    assert not out.exists() or not any(out.iterdir())


@pytest.mark.parametrize("label", [123, True, {"x": 1}, [1]])
def test_non_string_label_cli_leaves_inputs_and_output_unchanged(
    tmp_path: Path, label
):
    dest = _prepare_augmented(tmp_path)
    target = dest / "LULU_FY2025.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    for fact in payload["note_facts"]:
        if fact.get("fact_type") == STORE_COUNT_FACT_TYPE:
            fact["source"]["label"] = label
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    before = {path: path.read_bytes() for path in dest.glob("*.json")}
    out = tmp_path / "reconciled"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "bav",
            "reconcile",
            str(dest),
            "--source-root",
            str(SOURCE),
            "--admit-period",
            "2022-01-30",
            "-o",
            str(out),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    combined = completed.stdout + completed.stderr
    assert completed.returncode != 0
    assert "missing reported label" in combined
    assert "error:" in combined
    assert "invalid_operating_kpi" not in combined
    assert "wrote no artifacts" not in combined
    assert {path: path.read_bytes() for path in dest.glob("*.json")} == before
    assert not out.exists() or not any(out.iterdir())


def test_rejected_cli_leaves_inputs_and_output_unchanged(tmp_path: Path):
    dest = _prepare_augmented(tmp_path)
    target = dest / "LULU_FY2025.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    for fact in payload["note_facts"]:
        if fact.get("fact_type") == STORE_COUNT_FACT_TYPE:
            fact["presentation_role"] = PresentationRole.PRIOR_PRESENTATION.value
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    before = {path: path.read_bytes() for path in dest.glob("*.json")}
    out = tmp_path / "reconciled"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "bav",
            "reconcile",
            str(dest),
            "--source-root",
            str(SOURCE),
            "--admit-period",
            "2022-01-30",
            "-o",
            str(out),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "no eligible operating-KPI observation" in completed.stdout + completed.stderr
    assert {path: path.read_bytes() for path in dest.glob("*.json")} == before
    assert not out.exists() or not any(out.iterdir())


