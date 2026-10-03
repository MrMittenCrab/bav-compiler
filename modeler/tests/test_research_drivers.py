"""Lululemon Drivers research publication from validated BAV outputs."""
from __future__ import annotations

import hashlib
import json
import re
import warnings
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest
from matplotlib import ft2font
from PIL import Image

from director.current_build import prepare_company_input, resolve_company
from extractor.ingestion.management_kpi_enrichment import inspect_source_pdf
from composer.research.drivers import (
    APPENDIX_HEADING,
    OBSOLETE_SECTIONS,
    WORKPAPER_FIELDS,
    expected_sections,
    render_drivers_markdown,
    selected_figure_names,
)
from director.research import (
    complete_driver_selection as select_driver_argument,
    complete_drivers_view as assemble_drivers_view,
    publish_drivers,
)
from interpreter.selection import (
    geographic_materiality_rationale,
    geographic_strongest_conclusion,
)
from modeler.research.cfo import is_cfo_component, selected_cfo_concepts
from modeler.research.drivers_view import (
    label_for as _label_for,
    margin_reconstruction_complete,
)
from modeler.research.geo_conditions import (
    OFFSET_EXACT,
    OFFSET_GREATER,
    OFFSET_PARTIAL,
    geographic_claim_conditions,
    revenue_offset_kind as _revenue_offset_kind,
)
from composer.research.selection import geographic_figure_question
from composer.research.publish import publish_company_research, verify_research_artifacts
from composer.research.style import (
    CJK_FACE,
    FIGURE_DPI,
    FIGURE_SIZE,
    LABEL_PT,
    LATIN_FACE,
    MIN_WORD_GAP_EM,
    PT,
    TITLE_PT,
    _ink_gap_px,
    apply_research_style,
    finish_figure,
    new_figure,
    resolve_required_fonts,
    spaced,
)
from modeler.tests.test_lululemon_benchmark import REVENUE_ANCHORS
from modeler.tests.test_management_kpi_admission import EXTRACTED, SOURCE
from modeler.tests.test_operating_kpi_facts import INDEPENDENT_STORE_TOTALS

ROOT = Path(__file__).resolve().parents[2]
FIFTY_THREE_WEEK_END = date(2025, 2, 2)
DISPLAYED_FY2024_END = date(2024, 1, 28)
FORBIDDEN_PROSE = (
    "admitted",
    "fail-closed",
    "fail closed",
    "source unavailable",
    "standardizedfinancials",
    "hypothesis",
    "verdict",
    "audit-only",
    "audit only",
    "supported_descriptively",
    "segment_bridge",
    "provenance",
    "trainer",
    "answer key",
)


def test_drivers_calendar_limitation_reconciles_53_week_year(tmp_path):
    extract = json.loads(
        (EXTRACTED / "LULU_FY2024_management_kpis.json").read_text(encoding="utf-8")
    )
    assert extract["report"]["fiscal_year"] == 2024
    assert extract["report"]["fiscal_year_end"] == FIFTY_THREE_WEEK_END.isoformat()
    assert "53 weeks" in extract["report"]["reporting_basis"]
    fy2024_definition = next(
        item["definition"]
        for item in extract["kpi_definitions"]
        if item["metric_id"] == "comparable_sales_growth"
    )
    assert "53rd week is excluded from comparable sales" in fy2024_definition
    fy2025 = json.loads(
        (EXTRACTED / "LULU_FY2025_management_kpis.json").read_text(encoding="utf-8")
    )
    fy2025_definition = next(
        item["definition"]
        for item in fy2025["kpi_definitions"]
        if item["metric_id"] == "comparable_sales_growth"
    )
    assert "shifted by one week" in fy2025_definition
    inspection = inspect_source_pdf(SOURCE / "LULU_FY2024_Annual_Report.pdf")
    assert 2024 in inspection.fifty_three_week_years
    assert 2023 in inspection.fifty_two_week_years
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    assert _label_for(fin, FIFTY_THREE_WEEK_END) == "FY2024"
    assert _label_for(fin, DISPLAYED_FY2024_END) == "FY2023"
    adjustments = {
        (item.period, item.calendar_week_adjustment)
        for item in fin.historical_operating_kpis.management_observations
        if item.family == "comparable_sales_growth"
        and item.geography == "global"
        and item.basis == "reported"
        and item.population == "company_operated_stores_and_ecommerce"
    }
    assert (FIFTY_THREE_WEEK_END, "excluded") in adjustments
    assert (DISPLAYED_FY2024_END, "included") in adjustments
    view = assemble_drivers_view(fin, company.name)
    assert view.fifty_three_week_period == FIFTY_THREE_WEEK_END
    assert view.labels[view.periods.index(FIFTY_THREE_WEEK_END)] == "FY2024"
    assert view.labels[view.periods.index(DISPLAYED_FY2024_END)] == "FY2023"
    assert view.issuer_fiscal_name == "fiscal 2024"
    text = render_drivers_markdown(view)
    assert "| FY2023 | 28 January 2024 |" in text
    assert "| FY2024 | 2 February 2025 |" in text
    week_sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=\.)\s+", text)
        if "53-week" in sentence
    ]
    assert len(week_sentences) == 1
    assert week_sentences[0].startswith("FY2024, the year ended 2 February 2025, is a 53-week year")
    assert "FY2025 is a 53-week" not in text
    assert "FY2023 is a 53-week" not in text
    assert "exclude or realign that extra week" in text
    publish_drivers(fin, tmp_path / "out", display_name=company.name)
    published = (tmp_path / "out" / "research" / "Lululemon_Drivers.md").read_text(
        encoding="utf-8"
    )
    assert published == text


def _font_has(path: Path, codepoint: int) -> bool:
    return codepoint in ft2font.FT2Font(str(path)).get_charmap()


def _interior_ink_gaps(path: Path, y0: int, y1: int, *, min_gap: int = 2) -> list[int]:
    image = Image.open(path).convert("L")
    strip = image.crop((0, y0, image.size[0], y1))
    cols = [
        any(strip.getpixel((x, row)) < 200 for row in range(strip.size[1]))
        for x in range(strip.size[0])
    ]
    gaps: list[int] = []
    index = 0
    width = len(cols)
    while index < width:
        if cols[index]:
            index += 1
            continue
        end = index
        while end < width and not cols[end]:
            end += 1
        if index > 0 and end < width and end - index >= min_gap:
            gaps.append(end - index)
        index = end
    return gaps


def test_incompatible_compsales_are_not_trended(tmp_path):
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    view = assemble_drivers_view(fin, company.name)
    text = render_drivers_markdown(view)
    trend = next(
        claim
        for question in view.selection.questions
        if question.identifier == "comparable_sales"
        for claim in question.claims
        if claim.identifier == "compsales_trend"
    )
    assert trend.status == "blocked"
    assert "not one deceleration" in text.lower() or "cannot be joined" in text.lower()
    assert "new-store contribution" in text.lower()
    main = text.split("## Appendix", 1)[0]
    assert "25%, 13%, 4%" not in main
    assert "connected trend" not in main.lower() or "not" in main.lower()


def _replace_latest(series, value):
    values = list(series)
    values[-1] = value
    return tuple(values)


def _carry_reconstruction(view):
    return replace(
        view,
        reconstruction_complete=tuple(
            margin_reconstruction_complete(view, index)
            for index in range(len(view.periods))
        ),
    )


def _replace_latest_geo(rows, **updates):
    values = [dict(row) for row in rows]
    values[-1].update(updates)
    return tuple(values)


def _render_geo_view(view, **replacements):
    updated = replace(view, **replacements)
    return replace(updated, selection=select_driver_argument(updated))


def _assert_no_offset_or_growth_claim(text: str) -> None:
    lower = text.lower()
    assert "only partially offset" not in lower
    assert "exactly offset the americas" not in lower
    assert "more than offset" not in lower
    assert "international growth" not in lower
    assert "international revenue offset" not in lower
    assert "did international revenue growth offset" not in lower


def test_revenue_offset_kind_requires_positive_international_sum(tmp_path):
    assert _revenue_offset_kind(-100, -20) is None
    assert _revenue_offset_kind(-100, 0) is None
    assert _revenue_offset_kind(-100, 40) == OFFSET_PARTIAL
    assert _revenue_offset_kind(-100, 100) == OFFSET_EXACT
    assert _revenue_offset_kind(-100, 140) == OFFSET_GREATER
    assert _revenue_offset_kind(-100, None) is None
    assert _revenue_offset_kind(50, 40) is None
    assert _revenue_offset_kind(None, 40) is None

    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    base = assemble_drivers_view(fin, company.name)
    latest = len(base.periods) - 1

    def _offset_view(americas, china, rest):
        return _render_geo_view(
            base,
            geo_revenue_amount_changes=_replace_latest_geo(
                base.geo_revenue_amount_changes,
                americas=americas,
                china_mainland=china,
                rest_of_world=rest,
            ),
            geo_contribution_amounts=_replace_latest_geo(
                base.geo_contribution_amounts,
                americas=americas,
                china_mainland=china,
                rest_of_world=rest,
            ),
        )

    negative = _offset_view(-100.0, 10.0, -30.0)
    zero_total = _offset_view(-100.0, 20.0, -20.0)
    observed_zero = _offset_view(-100.0, 0.0, 0.0)
    mixed_negative = _offset_view(-100.0, 40.0, -60.0)
    partial = _offset_view(-100.0, 25.0, 15.0)
    exact = _offset_view(-100.0, 55.0, 45.0)
    greater = _offset_view(-100.0, 80.0, 40.0)
    missing = _offset_view(-100.0, None, 40.0)
    americas_growth = _offset_view(100.0, 25.0, 15.0)

    negative_conditions = geographic_claim_conditions(negative, latest)
    zero_conditions = geographic_claim_conditions(zero_total, latest)
    observed_zero_conditions = geographic_claim_conditions(observed_zero, latest)
    mixed_negative_conditions = geographic_claim_conditions(mixed_negative, latest)
    missing_conditions = geographic_claim_conditions(missing, latest)
    growth_conditions = geographic_claim_conditions(americas_growth, latest)
    partial_conditions = geographic_claim_conditions(partial, latest)
    exact_conditions = geographic_claim_conditions(exact, latest)
    greater_conditions = geographic_claim_conditions(greater, latest)

    assert negative_conditions.international_revenue == -20.0
    assert zero_conditions.international_revenue == 0.0
    assert observed_zero_conditions.international_revenue == 0.0
    assert mixed_negative_conditions.international_revenue == -20.0
    assert missing_conditions.international_revenue is None
    assert negative_conditions.revenue_offset is None
    assert zero_conditions.revenue_offset is None
    assert observed_zero_conditions.revenue_offset is None
    assert mixed_negative_conditions.revenue_offset is None
    assert missing_conditions.revenue_offset is None
    assert growth_conditions.revenue_offset is None
    assert partial_conditions.revenue_offset == OFFSET_PARTIAL
    assert exact_conditions.revenue_offset == OFFSET_EXACT
    assert greater_conditions.revenue_offset == OFFSET_GREATER

    for conditions in (
        negative_conditions,
        zero_conditions,
        observed_zero_conditions,
        mixed_negative_conditions,
        missing_conditions,
        growth_conditions,
    ):
        assert "offset" not in geographic_strongest_conclusion(conditions).lower()
        assert "international revenue offset" not in geographic_materiality_rationale(
            conditions
        ).lower()
        assert "international revenue growth" not in geographic_figure_question(
            conditions
        ).lower()

    negative_text = render_drivers_markdown(negative)
    zero_text = render_drivers_markdown(zero_total)
    observed_zero_text = render_drivers_markdown(observed_zero)
    mixed_negative_text = render_drivers_markdown(mixed_negative)
    missing_text = render_drivers_markdown(missing)
    growth_text = render_drivers_markdown(americas_growth)
    partial_text = render_drivers_markdown(partial)
    exact_text = render_drivers_markdown(exact)
    greater_text = render_drivers_markdown(greater)

    for text in (
        negative_text,
        zero_text,
        observed_zero_text,
        mixed_negative_text,
        missing_text,
        growth_text,
    ):
        _assert_no_offset_or_growth_claim(text)

    for view in (
        negative,
        zero_total,
        observed_zero,
        mixed_negative,
        missing,
        americas_growth,
    ):
        assert "geographic_localization" in view.selection.main_body_ids

    assert "n/a" in missing_text
    assert "only partially offset the Americas revenue decline" in partial_text
    assert "exactly offset the Americas revenue decline" in exact_text
    assert "more than offset the Americas revenue decline" in greater_text
    assert "Did international revenue growth offset Americas profit deterioration?" in greater_text
    assert "Did international revenue growth offset Americas profit deterioration?" not in zero_text

    empty_row = {identity: None for identity in base.geo_identities}
    only_consolidated = _render_geo_view(
        base,
        geo_contributions=tuple(dict(empty_row) for _ in base.geo_contributions),
        geo_revenue_amount_changes=tuple(
            dict(empty_row) for _ in base.geo_revenue_amount_changes
        ),
        geo_contribution_amounts=tuple(
            dict(empty_row) for _ in base.geo_contribution_amounts
        ),
        geo_profit_changes=tuple(dict(empty_row) for _ in base.geo_profit_changes),
        geo_reconciling_profit_change=tuple(
            None for _ in base.geo_reconciling_profit_change
        ),
    )
    assert "geographic_localization" in only_consolidated.selection.main_body_ids
    only_text = render_drivers_markdown(only_consolidated)
    _assert_no_offset_or_growth_claim(only_text)


def test_cfo_selection_fast_retailing_reviewed_set_and_exclusions(tmp_path):
    from modeler.data.standardized_io import standardized_from_payload

    fr = standardized_from_payload(
        json.loads(
            (
                ROOT / "build" / "input" / "fast_retailing" / "reconciled" / "standardized.json"
            ).read_text(encoding="utf-8")
        )
    )
    selected = set(selected_cfo_concepts(fr))
    assert "net_change_in_cash" not in selected
    assert "change_in_cash" not in selected
    assert "cash_beginning" not in selected
    assert "cash_ending" not in selected
    assert "cash_generated_from_operations" not in selected
    assert "operating_cash_flow" not in selected
    assert "investing_cash_flow" not in selected
    assert "financing_cash_flow" not in selected
    assert "payments_for_ppe" not in selected
    assert "dividends_paid_to_owners" not in selected
    assert "change_in_inventories" in selected
    assert "change_in_trade_and_other_receivables" in selected
    assert "change_in_trade_and_other_payables" in selected
    assert "change_in_other_assets" in selected
    assert "change_in_other_liabilities" in selected
    assert "depreciation_amortization" in selected
    assert is_cfo_component("change_in_short_term_debt") is False
    assert is_cfo_component("net_change_in_cash") is False
    assert is_cfo_component("change_in_inventories") is True
    company = resolve_company("FastRetailing")
    view = assemble_drivers_view(fr, company.name)
    latest = len(view.periods) - 1
    assert view.cfo[latest] - view.cfo[latest - 1] == pytest.approx(-70903.0)
    assert view.cfo_component_sum[latest] == pytest.approx(-65650.0)
    assert view.cfo_unexplained[latest] == pytest.approx(-5253.0)
    prior_selected = -656249.0
    excluded_cash_change = -590599.0
    assert prior_selected - excluded_cash_change == pytest.approx(-65650.0)
    assert (-70903.0) - (-65650.0) == pytest.approx(-5253.0)

    lulu = resolve_company("Lululemon")
    lulu_fin = prepare_company_input(lulu, tmp_path / "input")
    lulu_view = assemble_drivers_view(lulu_fin, lulu.name)
    assert lulu_view.cfo_unexplained[-1] == pytest.approx(-67381.0)
    assert "change_in_cash" not in selected_cfo_concepts(lulu_fin)


