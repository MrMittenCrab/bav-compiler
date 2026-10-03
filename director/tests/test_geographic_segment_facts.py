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

from extractor.data.filing import (
    ExtractedStatementRow,
    FilingValue,
    PresentationRole,
    SourceRef,
    SupplementalFact,
)
from extractor.data.filing_json import extracted_filing_to_payload, load_extracted_filing
from modeler.ingestion.filing_reconciler import SupplementalObservation, reconcile_filings
from modeler.ingestion.filing_standardizer import (
    reconciliation_conflicts_payload,
    reconciliation_provenance_payload,
    standardize_reconciled,
)
from director.ingestion.filing_validator import validate_extracted_filing
from modeler.ingestion.geographic_segment import (
    GEO_BRIDGE_TOLERANCE,
    GEO_NAMESPACE,
    select_geographic_segment_facts,
)
from modeler.data.historical_segments import (
    GEOGRAPHIC_SEGMENT_NAMESPACE,
    SEGMENT_BRIDGE_TOLERANCE,
)
from modeler.data.standardized_io import standardized_from_payload, standardized_to_payload
from modeler.tests.test_filing_reconciler import _filing, _validated

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "build" / "input" / "lululemon"
EXTRACTED = BENCH / "extracted"
SOURCE = BENCH / "source"
RECONCILED = ROOT / "core" / "tests" / "fixtures" / "ordinary_reconcile" / "lululemon"
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


def test_rejected_cli_leaves_inputs_and_output_unchanged(tmp_path: Path):
    source_root = tmp_path / "source"
    extracted = tmp_path / "extracted"
    source_root.mkdir()
    extracted.mkdir()
    (source_root / "demo.pdf").write_bytes(b"%PDF-fixture")
    facts = [
        {
            "fact_type": fact.fact_type,
            "period": fact.period.isoformat(),
            "value": fact.value,
            "status": "reported",
            "source": {
                "page": fact.source.page,
                "note": fact.source.note,
                "label": fact.source.label,
            },
            "presentation_role": fact.presentation_role,
        }
        for fact in _column_facts(
            date(2025, 12, 31),
            page=80,
            role=PresentationRole.PRIOR_PRESENTATION,
            rev=(80, 25, 15),
            ifop=(50, 18, 7),
            corporate=-25,
        )
    ]
    payload = {
        "schema_version": "1.0",
        "company": {
            "name": "DEMO CO",
            "ticker": "DEMO",
            "stock_code": "DEMO",
            "jurisdiction": "HK",
        },
        "filing": {
            "document_type": "annual_report",
            "fiscal_year": 2025,
            "period_end": "2025-12-31",
            "currency": "HKD",
            "unit_scale": "millions",
            "source_file": "demo.pdf",
        },
        "statements": {
            "income_statement": [
                {
                    "label": "Revenue",
                    "section": "",
                    "suggested_concept": "revenue",
                    "values": {
                        "2025-12-31": {
                            "value": 120,
                            "presentation_role": "current_period",
                        }
                    },
                    "source": {"page": 1},
                }
            ],
            "balance_sheet": [],
            "cash_flow": [],
        },
        "note_facts": facts,
        "share_facts": [],
    }
    extracted_path = extracted / "FY2025.json"
    extracted_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    before = extracted_path.read_bytes()
    out = tmp_path / "reconciled"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "core",
            "reconcile",
            str(extracted),
            "--source-root",
            str(source_root),
            "-o",
            str(out),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "no eligible complete geographic presentation" in completed.stdout
    assert extracted_path.read_bytes() == before
    assert not out.exists() or not any(out.iterdir())


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


