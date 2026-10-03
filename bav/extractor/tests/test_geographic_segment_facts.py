"""Geographic Q4-2023 segment fact extraction and supplemental selection."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from bav.extractor.data.filing import (
    ExtractedStatementRow,
    FilingValue,
    PresentationRole,
    SourceRef,
    SupplementalFact,
)
from bav.extractor.data.filing_json import extracted_filing_to_payload, load_extracted_filing
from bav.modeler.ingestion.filing_reconciler import SupplementalObservation, reconcile_filings
from bav.modeler.ingestion.filing_standardizer import (
    reconciliation_conflicts_payload,
    reconciliation_provenance_payload,
    standardize_reconciled,
)
from bav.director.ingestion.filing_validator import validate_extracted_filing
from bav.modeler.ingestion.geographic_segment import (
    GEO_BRIDGE_TOLERANCE,
    GEO_NAMESPACE,
    select_geographic_segment_facts,
)
from bav.modeler.data.historical_segments import (
    GEOGRAPHIC_SEGMENT_NAMESPACE,
    SEGMENT_BRIDGE_TOLERANCE,
)
from bav.modeler.data.standardized_io import standardized_from_payload, standardized_to_payload
from bav.modeler.tests.test_filing_reconciler import _filing, _validated

ROOT = Path(__file__).resolve().parents[3]
BENCH = ROOT / "build" / "input" / "lululemon"
EXTRACTED = BENCH / "extracted"
SOURCE = BENCH / "source"
RECONCILED = ROOT / "bav" / "modeler" / "tests" / "fixtures" / "ordinary_reconcile" / "lululemon"
NS = GEO_NAMESPACE

P2024 = date(2024, 12, 31)
P2025 = date(2025, 12, 31)


def _geo(
    identity: str,
    period: date,
    value: float,
    *,
    page: int = 80,
    role: PresentationRole = PresentationRole.CURRENT_PERIOD,
    label: str = "",
) -> SupplementalFact:
    return SupplementalFact(
        fact_type=f"{NS}.{identity}",
        period=period,
        value=value,
        status="reported",
        source=SourceRef(
            page=page,
            note="23 Segmented Information",
            label=label or identity,
        ),
        presentation_role=role.value,
    )


def _opinc(values: dict[date, tuple[float, PresentationRole]]) -> ExtractedStatementRow:
    return ExtractedStatementRow(
        label="Income from operations",
        section="",
        suggested_concept="operating_income",
        values={
            period: FilingValue(value=value, presentation_role=role)
            for period, (value, role) in values.items()
        },
        source=SourceRef(page=1, statement="Income Statement"),
    )


def _column_facts(
    period: date,
    *,
    page: int,
    role: PresentationRole,
    rev: tuple[int, int, int],
    ifop: tuple[int, int, int],
    corporate: int,
) -> tuple[SupplementalFact, ...]:
    a, cm, row = rev
    ia, icm, irow = ifop
    return (
        _geo("net_revenue.americas", period, a, page=page, role=role),
        _geo("net_revenue.china_mainland", period, cm, page=page, role=role),
        _geo("net_revenue.rest_of_world", period, row, page=page, role=role),
        _geo("net_revenue.segment_total", period, a + cm + row, page=page, role=role),
        _geo("net_revenue.consolidated", period, a + cm + row, page=page, role=role),
        _geo("income_from_operations.americas", period, ia, page=page, role=role),
        _geo("income_from_operations.china_mainland", period, icm, page=page, role=role),
        _geo("income_from_operations.rest_of_world", period, irow, page=page, role=role),
        _geo(
            "income_from_operations.segment_total",
            period,
            ia + icm + irow,
            page=page,
            role=role,
        ),
        _geo(
            "income_from_operations.corporate_unallocated",
            period,
            corporate,
            page=page,
            role=role,
        ),
        _geo(
            "income_from_operations.consolidated",
            period,
            ia + icm + irow + corporate,
            page=page,
            role=role,
        ),
    )


def _itemized_facts(period: date, *, page: int, role: PresentationRole) -> tuple[SupplementalFact, ...]:
    return (
        _geo("net_revenue.americas", period, 50, page=page, role=role),
        _geo("net_revenue.china_mainland", period, 30, page=page, role=role),
        _geo("net_revenue.rest_of_world", period, 20, page=page, role=role),
        _geo("net_revenue.consolidated", period, 100, page=page, role=role),
        _geo("income_from_operations.americas", period, 40, page=page, role=role),
        _geo("income_from_operations.china_mainland", period, 20, page=page, role=role),
        _geo("income_from_operations.rest_of_world", period, 10, page=page, role=role),
        _geo("income_from_operations.segment_total", period, 70, page=page, role=role),
        _geo("income_from_operations.consolidated", period, 55, page=page, role=role),
        _geo("ifop_reconciling.general_corporate_expenses", period, 12, page=page, role=role),
        _geo("ifop_reconciling.amortization_of_intangible_assets", period, 3, page=page, role=role),
    )


def test_invalid_provenance_and_nonfinite_fail_closed():
    complete = _column_facts(
        P2025,
        page=80,
        role=PresentationRole.CURRENT_PERIOD,
        rev=(80, 25, 15),
        ifop=(50, 18, 7),
        corporate=-25,
    )

    def _obs(fact: SupplementalFact) -> SupplementalObservation:
        return SupplementalObservation(
            kind="note",
            filing_year=2025,
            source_file="a2025.pdf",
            source_sha256="a" * 64,
            fact=fact,
        )

    missing_page = tuple(
        _obs(replace(fact, source=replace(fact.source, page=0)))
        if fact.fact_type.endswith("net_revenue.americas")
        else _obs(fact)
        for fact in complete
    )
    with pytest.raises(ValueError, match="positive source page"):
        select_geographic_segment_facts(
            missing_page,
            reconciled_values=(),
            model_periods=(P2025,),
        )

    nonfinite = tuple(
        _obs(replace(fact, value=math.inf))
        if fact.fact_type.endswith("net_revenue.americas")
        else _obs(fact)
        for fact in complete
    )
    with pytest.raises(ValueError, match="non-finite"):
        select_geographic_segment_facts(
            nonfinite,
            reconciled_values=(),
            model_periods=(P2025,),
        )


def _mutate_fy2025_prior_2025(filing):
    updated = []
    for fact in filing.note_facts:
        if fact.period != date(2025, 2, 2):
            updated.append(fact)
            continue
        value = fact.value
        if fact.fact_type.endswith("net_revenue.americas"):
            value = float(value) + 100
        elif fact.fact_type.endswith("net_revenue.rest_of_world"):
            value = float(value) - 100
        updated.append(
            replace(
                fact,
                value=value,
                presentation_role=PresentationRole.PRIOR_PRESENTATION.value,
            )
        )
    return replace(filing, note_facts=tuple(updated))


def test_lululemon_extracted_filings_round_trip_and_five_period_bridges():
    fy2022 = load_extracted_filing(EXTRACTED / "LULU_FY2022.json")
    fy2023 = load_extracted_filing(EXTRACTED / "LULU_FY2023.json")
    fy2024 = load_extracted_filing(EXTRACTED / "LULU_FY2024.json")
    fy2025 = load_extracted_filing(EXTRACTED / "LULU_FY2025.json")
    assert fy2022.note_facts == ()
    assert extracted_filing_to_payload(fy2023)["note_facts"]
    assert extracted_filing_to_payload(fy2024)["note_facts"]
    assert extracted_filing_to_payload(fy2025)["note_facts"]

    validated = []
    for filing in (fy2022, fy2023, fy2024, fy2025):
        report = validate_extracted_filing(filing, source_root=SOURCE)
        assert report.ok
        validated.append((filing, report))
    reconciled = reconcile_filings(
        validated,
        admit_periods=(date(2022, 1, 30),),
    )
    assert GEO_BRIDGE_TOLERANCE == 0.0
    selected = reconciled.selected_geographic_facts
    by_period = {}
    for item in selected:
        by_period.setdefault(item.period, []).append(item)

    expected_sources = {
        date(2022, 1, 30): (
            2023,
            "itemized_reconciling",
            "restated_comparative",
            "sole_source_observation",
        ),
        date(2023, 1, 29): (
            2024,
            "corporate_column",
            "restated_comparative",
            "later_audited_presentation",
        ),
        date(2024, 1, 28): (
            2025,
            "corporate_column",
            "restated_comparative",
            "restated_comparative_precedence",
        ),
        date(2025, 2, 2): (
            2025,
            "corporate_column",
            "restated_comparative",
            "restated_comparative_precedence",
        ),
        date(2026, 2, 1): (
            2025,
            "corporate_column",
            "current_period",
            "sole_source_observation",
        ),
    }
    assert set(by_period) == set(expected_sources)
    for period, (year, family, role, reason) in expected_sources.items():
        sample = by_period[period][0]
        assert sample.filing_year == year
        assert sample.presentation_family == family
        assert sample.presentation_basis == role
        assert sample.selection_reason == reason
        assert {item.presentation_basis for item in by_period[period]} == {role}
        assert {item.selection_reason for item in by_period[period]} == {reason}

    current = {
        item.fact_type.replace(f"{NS}.", ""): item.value
        for item in by_period[date(2026, 2, 1)]
    }
    assert current["income_from_operations.americas"] == 2560658
    assert current["income_from_operations.china_mainland"] == 701123
    assert current["income_from_operations.rest_of_world"] == 345901
    assert current["income_from_operations.segment_total"] == 3607682
    assert current["income_from_operations.corporate_unallocated"] == -1397067
    assert current["income_from_operations.consolidated"] == 2210615
    assert (
        current["income_from_operations.segment_total"]
        + current["income_from_operations.corporate_unallocated"]
        == current["income_from_operations.consolidated"]
    )

    fy2023_2022 = [
        obs
        for obs in reconciled.note_facts
        if obs.filing_year == 2023 and obs.fact.period == date(2024, 1, 28)
    ]
    fy2025_2022 = [
        obs
        for obs in reconciled.note_facts
        if obs.filing_year == 2025 and obs.fact.period == date(2024, 1, 28)
    ]
    assert fy2023_2022 and fy2025_2022

    fin = standardize_reconciled(reconciled)
    assert all(
        "segment.geo" not in (item.concept or "")
        for item in (*fin.income_statement, *fin.balance_sheet, *fin.cash_flow)
    )
    assert fin.historical_segment is not None
    assert fin.historical_segment.namespace == GEOGRAPHIC_SEGMENT_NAMESPACE
    assert GEOGRAPHIC_SEGMENT_NAMESPACE == NS
    assert SEGMENT_BRIDGE_TOLERANCE == 0.0
    model_values = {
        (snap.period, identity): value
        for snap in fin.historical_segment.periods
        for identity, value in snap.values.items()
    }
    selected_on_axis = {
        (item.period, item.fact_type[len(f"{NS}.") :]): item.value
        for item in selected
        if item.period in set(reconciled.periods)
    }
    assert model_values == selected_on_axis
    assert len(model_values) == 56
    assert [snap.period for snap in fin.historical_segment.periods] == [
        date(2022, 1, 30),
        date(2023, 1, 29),
        date(2024, 1, 28),
        date(2025, 2, 2),
        date(2026, 2, 1),
    ]
    fy2026 = next(
        snap
        for snap in fin.historical_segment.periods
        if snap.period == date(2026, 2, 1)
    )
    assert fy2026.presentation_family == "corporate_column"
    assert fy2026.values["income_from_operations.segment_total"] == 3607682
    assert fy2026.values["income_from_operations.corporate_unallocated"] == -1397067
    assert fy2026.values["income_from_operations.consolidated"] == 2210615
    assert (
        fy2026.values["income_from_operations.segment_total"]
        + fy2026.values["income_from_operations.corporate_unallocated"]
        == fy2026.values["income_from_operations.consolidated"]
    )
    assert fy2026.bridge_operations == {
        "income_from_operations.corporate_unallocated": "add"
    }
    for snap in fin.historical_segment.periods:
        revenue_sum = (
            snap.values["net_revenue.americas"]
            + snap.values["net_revenue.china_mainland"]
            + snap.values["net_revenue.rest_of_world"]
        )
        assert revenue_sum == snap.values["net_revenue.consolidated"]
        ifop_sum = (
            snap.values["income_from_operations.americas"]
            + snap.values["income_from_operations.china_mainland"]
            + snap.values["income_from_operations.rest_of_world"]
        )
        bridged = ifop_sum
        for identity, operation in snap.bridge_operations.items():
            if operation == "add":
                bridged += snap.values[identity]
            else:
                bridged -= snap.values[identity]
        assert bridged == snap.values["income_from_operations.consolidated"]
    itemized_2022 = next(
        snap
        for snap in fin.historical_segment.periods
        if snap.period == date(2022, 1, 30)
    )
    assert itemized_2022.presentation_family == "itemized_reconciling"
    assert "net_revenue.segment_total" not in itemized_2022.values
    assert "net_revenue.china_mainland" in itemized_2022.values
    restored = standardized_from_payload(standardized_to_payload(fin))
    assert restored.historical_segment == fin.historical_segment
    live = standardized_to_payload(fin)
    committed_std = json.loads((RECONCILED / "standardized.json").read_text())
    live_without_segment = dict(live)
    live_without_segment.pop("historical_segment")
    from bav.modeler.tests.test_lululemon_benchmark import _comparable_standardized
    assert _comparable_standardized(live_without_segment) == _comparable_standardized(
        committed_std
    )
    assert live["historical_segment"]["namespace"] == NS
    committed_conflicts = json.loads((RECONCILED / "conflicts.json").read_text())
    live_conflicts = reconciliation_conflicts_payload(reconciled)
    assert live_conflicts == committed_conflicts
    provenance = reconciliation_provenance_payload(reconciled)
    assert provenance["selected_geographic_segment_facts"]
    assert provenance["note_facts"]
    assert fy2022.filing.source_sha256 == hashlib.sha256(
        (SOURCE / fy2022.filing.source_file).read_bytes()
    ).hexdigest()


def _lululemon_validated():
    filings = [
        load_extracted_filing(EXTRACTED / name)
        for name in (
            "LULU_FY2022.json",
            "LULU_FY2023.json",
            "LULU_FY2024.json",
            "LULU_FY2025.json",
        )
    ]
    validated = []
    for filing in filings:
        report = validate_extracted_filing(filing, source_root=SOURCE)
        assert report.ok
        validated.append((filing, report))
    return validated


