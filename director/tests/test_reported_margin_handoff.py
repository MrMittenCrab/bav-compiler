"""Step 9M.2.4.1.1.1.26 — source-supported reported operating-margin bridge."""

from __future__ import annotations

import copy
import json
from datetime import date
from pathlib import Path

import pytest
from openpyxl import load_workbook

from director.current_build import prepare_company_input, resolve_company
from extractor.data.interface import (
    DocumentManifest,
    DocumentType,
)
from modeler.data.interface import (
    LineItem,
    StandardizedFinancials,
)
from modeler.data.standardized_io import standardized_from_payload, standardized_to_payload
from modeler.engine.component_catalog import (
    REPORTED_MARGIN_COMPONENT_CATALOG,
    expand_reported_margin_specs,
)
from modeler.workbook import ReferenceModelBuilder
from legacy.ingestion.manual_hk import HKManualDocumentAdapter
from modeler.historical_expected import reported_margin_expected_series
from modeler.line_resolver import AmbiguousLineError, MissingLineError, resolve_line
from modeler.period_axis import canonical_fiscal_periods
from modeler.ratio_values import UNDEFINED_RATIO
from composer.research.drivers import render_drivers_markdown
from director.driver_assessment import complete_reported_margin_series as compute_reported_margin_series
from director.research import complete_drivers_view as assemble_drivers_view
from modeler.reported_margin import (
    EXPENSE_PRESENTATION_POSITIVE,
    EXPENSE_PRESENTATION_SIGNED,
    GROSS_PROFIT_CONCEPT,
    OPERATING_PROFIT_CONCEPT,
    REVENUE_CONCEPT,
    analytical_expense,
    expense_presentation_factor,
    gross_margin_applicable,
    net_operating_expense_burden_applicable,
    publication_reconstruction_allowed,
    reported_margin_applicable,
    reported_margin_availability,
    reported_operating_margin_applicable,
    residual_blocks_reconstruction_claim,
    resolve_reported_margin_sources,
)
from modeler.source_values import MissingHistoricalValueError
from modeler.tests.test_capex import P1, P2, _dupont_row_by_label, _tiny
from modeler.tests.test_normalization import _inject_formula_and_cached_value
from legacy.trainer.checker import check_workbook
from modeler.semantic_io import load_semantic_map, parse_cell_ref
from modeler.semantic_io import group_components_by_family
from legacy.trainer.derive import build_training_workbook

ROOT = Path(__file__).resolve().parents[2]
FR_JSON = ROOT / "build" / "input" / "fast_retailing" / "reconciled" / "standardized.json"
DEMO_JSON = ROOT / "legacy" / "example" / "DEMO_HK_Standardized.json"


def _li(label, values, concept=""):
    return LineItem(label=label, values=values, concept=concept)


def _vals(a, b, *, missing_period=False, none_period=False):
    if missing_period:
        return {P1: a}
    if none_period:
        return {P1: a, P2: None}
    return {P1: a, P2: b}


def _add_margins(
    fin: StandardizedFinancials,
    *,
    revenue=(1000.0, 1100.0),
    gross=(560.0, 600.0),
    operating=(200.0, 180.0),
    revenue_concept=REVENUE_CONCEPT,
    gross_concept=GROSS_PROFIT_CONCEPT,
    operating_concept=OPERATING_PROFIT_CONCEPT,
    include_revenue=True,
    include_gross=True,
    include_operating=True,
    duplicate=None,
    missing_period=None,
    none_period=None,
    on_balance_sheet=None,
):
    rows = (
        ("revenue", include_revenue, "Revenue", revenue_concept, revenue),
        ("gross", include_gross, "Gross profit", gross_concept, gross),
        (
            "operating",
            include_operating,
            "Operating profit",
            operating_concept,
            operating,
        ),
    )
    stored = {}
    for key, include, label, concept, values in rows:
        if not include:
            continue
        item = _li(
            label,
            _vals(
                values[0],
                values[1],
                missing_period=missing_period == key,
                none_period=none_period == key,
            ),
            concept=concept,
        )
        if key == "revenue":
            existing = next(
                (
                    row
                    for row in fin.income_statement
                    if row.concept == "revenue" or row.label.lower() == "revenue"
                ),
                None,
            )
            if existing is not None:
                fin.income_statement.remove(existing)
        target = (
            fin.balance_sheet if on_balance_sheet == key else fin.income_statement
        )
        target.append(item)
        stored[key] = item
        if duplicate == key and on_balance_sheet != key:
            target.append(
                _li(
                    f"{label} duplicate",
                    _vals(values[0], values[1]),
                    concept=concept,
                )
            )
    return stored


LULU_RECONCILED = (
    ROOT / "build" / "input" / "lululemon" / "reconciled" / "standardized.json"
)


def _add_component_lines(
    fin: StandardizedFinancials,
    *,
    sga=(300.0, 300.0),
    impairment=(0.0, 50.0),
    other=(10.0, 0.0),
    omit_impairment=False,
    impairment_none_current=False,
):
    fin.income_statement.append(
        _li(
            "SG&A",
            _vals(sga[0], sga[1]),
            concept="selling_general_and_administrative_expenses",
        )
    )
    if not omit_impairment:
        fin.income_statement.append(
            _li(
                "Impairment",
                {P1: impairment[0], P2: None}
                if impairment_none_current
                else _vals(impairment[0], impairment[1]),
                concept="impairment_and_restructuring",
            )
        )
    fin.income_statement.append(
        _li(
            "Amortization",
            _vals(other[0], other[1]),
            concept="amortization_of_intangible_assets",
        )
    )


def test_margin_phase_boundaries_and_flags_copy_through_wording():
    import ast
    from pathlib import Path

    from composer.reported_margin import (
        word_latest_movement,
        word_margin_contributions,
        word_unsupported_mix,
    )
    from interpreter.reported_margin import (
        interpret_latest_movement,
        interpret_unsupported_mix,
    )
    from modeler.reported_margin import (
        compute_reported_margin_series as compute_numeric,
        _latest_adjacent_movement,
        _margin_contribution_validity,
    )

    root = Path(__file__).resolve().parents[2]
    modeler_modules = {
        node.module
        for node in ast.parse((root / "modeler" / "reported_margin.py").read_text()).body
        if isinstance(node, ast.ImportFrom) and node.module
    }
    interpreter_modules = {
        node.module
        for node in ast.parse((root / "interpreter" / "reported_margin.py").read_text()).body
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert not any(
        module.startswith("interpreter") or module.startswith("composer")
        for module in modeler_modules
    )
    assert not any(module.startswith("composer") for module in interpreter_modules)

    payload = json.loads(LULU_RECONCILED.read_text(encoding="utf-8"))
    fin = standardized_from_payload(payload)
    periods = canonical_fiscal_periods(fin)
    numeric = compute_numeric(fin, periods)
    assert numeric.assessments == ()
    contrib = _margin_contribution_validity(numeric)
    worded = word_margin_contributions(contrib)
    assert worded.kind == contrib.kind
    assert worded.established == contrib.established
    mix = word_unsupported_mix(interpret_unsupported_mix())
    assert mix.kind == "unestablished_inference"
    assert mix.established is False
    latest = _latest_adjacent_movement(numeric)
    movement = word_latest_movement(latest, interpret_latest_movement(latest))
    assert movement.kind == "observed_relationship"
    assert movement.established is True
    assert movement.established == latest.established

    checker_src = (root / "core" / "trainer" / "checker.py").read_text()
    expected_src = (root / "core" / "model" / "historical_expected.py").read_text()
    assert "composer.reported_margin" not in checker_src
    assert "interpreter.reported_margin" not in checker_src
    assert "word_margin" not in expected_src
    assert "interpret_latest_movement" not in expected_src
