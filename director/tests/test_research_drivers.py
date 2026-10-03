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


def test_readme_documents_architecture_without_copying_style():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "build/output/lululemon/Lululemon_BAV.xlsx" in text
    assert "build/output/lululemon/research/*.md" in text
    assert "build/output/lululemon/figures/" in text
    assert "Drivers → Forecast → Valuation → Overview" in text
    assert "director/docs/STYLE.md" in text
    assert "Aptos Regular" not in text
    assert "DengXian Regular" not in text


def test_lululemon_drivers_from_validated_outputs(tmp_path):
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    view = publish_drivers(fin, tmp_path / "out", display_name=company.name)
    verify_research_artifacts(tmp_path / "out", company.name)
    text = (tmp_path / "out" / "research" / "Lululemon_Drivers.md").read_text(
        encoding="utf-8"
    )
    headings = [line for line in text.splitlines() if line.startswith("#")]
    assert headings[0] == expected_sections(company.name)[0]
    assert APPENDIX_HEADING in headings
    assert headings[1] != APPENDIX_HEADING
    assert any(line.startswith("## 1. ") for line in headings)
    assert "## Secondary signals" in headings
    assert headings[headings.index(APPENDIX_HEADING) - 1] == "## Secondary signals"
    assert not set(OBSOLETE_SECTIONS).intersection(headings)
    main = text.split(APPENDIX_HEADING, 1)[0]
    appendix = text.split(APPENDIX_HEADING, 1)[1]
    opening = " ".join(main.split()[:250])
    assert "profit" in opening.lower()
    assert "margin" in opening.lower() or "compression" in opening.lower()
    lowered = text.lower()
    for term in FORBIDDEN_PROSE:
        assert term not in lowered, term
    assert "forecast" not in lowered
    assert "valuation" not in lowered
    assert "acquisition" not in lowered
    assert "synerg" not in lowered
    assert "price target" not in lowered
    assert "catalyst" not in lowered
    for field in WORKPAPER_FIELDS:
        assert f"## {field}" not in main
        assert f"### {field}" not in main
    assert "new-store revenue" not in lowered.replace("not measured new-store revenue", "")
    assert "not measured new-store revenue" in lowered
    assert "not store productivity" in lowered
    assert "not one deceleration" in lowered or "cannot be joined" in lowered
    assert "not a causal" in lowered
    assert "not inserted into the accounting bridge" in lowered or "not inserted into the accounting" in lowered
    assert "not a manipulation" in lowered or "not an earnings-quality" in lowered
    for period, revenue in REVENUE_ANCHORS.items():
        assert view.revenue[view.periods.index(period)] == revenue
    for period, stores in INDEPENDENT_STORE_TOTALS.items():
        assert view.stores[view.periods.index(period)] == stores
    latest = view.periods[-1]
    latest_i = view.periods.index(latest)
    assert abs(view.revenue_growth[latest_i] - 0.04858971266492295) < 1e-12
    assert abs(view.store_growth[latest_i] - 0.05736636245110821) < 1e-12
    assert abs(view.geo_contributions[latest_i]["americas"] + 0.7660656852780181) < 1e-12
    assert abs(view.geo_contributions[latest_i]["china_mainland"] - 3.716068358083385) < 1e-12
    assert abs(view.geo_contributions[latest_i]["rest_of_world"] - 1.9089685936869283) < 1e-12
    assert view.geo_consolidated_profit_change[latest_i] == pytest.approx(-295082.0)
    assert view.cfo_unexplained[latest_i] == pytest.approx(-67381.0)
    assert "−$295.082 million" in text or "-$295.082 million" in text
    assert "−$67.381 million" in text or "-$67.381 million" in text
    assert "−0.766 pp" in text or "-0.766 pp" in text
    assert "5.74%" in text and "4.86%" in text
    assert view.labels[latest_i] == "FY2025"
    assert view.labels[view.periods.index(FIFTY_THREE_WEEK_END)] == "FY2024"
    gm = view.gross_margin_change[latest_i]
    burden = view.net_operating_expense_burden_change[latest_i]
    om = view.operating_margin_change[latest_i]
    assert gm is not None and burden is not None and om is not None
    assert abs(om - (gm - burden)) < 1e-12
    assert view.gross_margin_contribution[-1] is not None
    assert view.contribution_residual[-1] == pytest.approx(0.0)
    assert "approximately $275 million" in text
    assert "Form 10-K pp. 28–29" in text or "Form 10-K pp. 28-29" in text
    assert "company-wide revenue per store" in text.lower()
    assert view.sga_ratio[-1] == pytest.approx(4066556.0 / 11102600.0)
    assert view.impairment[1] == 407913.0
    assert view.impairment_ratio_contribution[-1] == pytest.approx(0.0)
    assert view.operating_margin_residual[-1] == 0.0
    assert view.geo_residual is not None
    assert all(value == 0.0 for value in view.geo_residual)
    assert view.selection is not None
    assert "operating_margin_bridge" in view.selection.principal_ids
    assert "geographic_localization" in view.selection.principal_ids
    assert "cash_conversion" in view.selection.secondary_ids
    assert "footprint_intensity" in view.selection.appendix_ids
    assert "footprint_intensity" not in view.selection.principal_ids
    assert selected_figure_names(view) == (
        "margin.png",
        "geography.png",
    )
    assert "margin.png" in main and "geography.png" in main
    assert "growth.png" not in main
    assert "cash.png" not in text
    assert appendix.count("| Fiscal year |") >= 1
    assembled = assemble_drivers_view(fin, company.name)
    assert assembled.revenue == view.revenue
    assert assembled.operating_margin == view.operating_margin


def test_fast_retailing_publishes_from_own_evidence(tmp_path):
    company = resolve_company("FastRetailing")
    fin = prepare_company_input(company, tmp_path / "input")
    publish_company_research(company.name, fin, tmp_path / "out")
    verify_research_artifacts(tmp_path / "out", company.name)
    text = (tmp_path / "out" / "research" / "FastRetailing_Drivers.md").read_text(
        encoding="utf-8"
    )
    view = assemble_drivers_view(fin, company.name)
    assert view.currency == "JPY"
    assert "million" in view.units.casefold()
    assert "JPY" in text
    assert "Lululemon" not in text
    assert "Americas" not in text.split("## Appendix", 1)[0]
    assert "store" not in text.split("## Appendix", 1)[0].casefold()
    assert "approximately $275 million" not in text
    assert view.selection is not None
    assert "operating_margin_bridge" in view.selection.principal_ids
    assert "geographic_localization" not in view.selection.principal_ids
    assert "footprint_intensity" not in view.selection.main_body_ids
    assert len(view.selection.principal_ids) <= 2
    assert text.startswith("# FastRetailing — Drivers")
    assert "## 1. " in text
    assert "## Appendix" in text
    main = text.split("## Appendix", 1)[0]
    assert "Forecast" not in main
    placeholders = tmp_path / "out" / "research"
    assert (placeholders / "FastRetailing_Forecast.md").stat().st_size == 0
    assert (placeholders / "FastRetailing_Valuation.md").stat().st_size == 0
    assert (placeholders / "FastRetailing_Overview.md").stat().st_size == 0
    latest_i = len(view.periods) - 1
    assert view.cfo_component_sum[latest_i] == pytest.approx(-65650.0)
    assert view.cfo_unexplained[latest_i] == pytest.approx(-5253.0)
    assert not margin_reconstruction_complete(view, latest_i)
    assert "partial explanation" in main
    assert "residual remains" in main
    assert "Gross-margin contraction and a higher SG&A ratio account for" not in main
    assert "partly explain" in main or "partial" in main


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


def test_output_depends_on_evidence_and_not_company_name(tmp_path):
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    renamed = render_drivers_markdown(assemble_drivers_view(fin, "RenamedCo"))
    assert renamed.startswith("# RenamedCo — Drivers")
    assert "Lululemon — Drivers" not in renamed
    assert "if company" not in renamed.lower()
    assert "approximately $275 million" in renamed

    missing_attr = assemble_drivers_view(fin, company.name)
    from dataclasses import replace
    stripped = replace(missing_attr, attributions=())
    stripped = replace(stripped, selection=select_driver_argument(stripped))
    stripped_text = render_drivers_markdown(stripped)
    assert "approximately $275 million" not in stripped_text
    assert "operating-margin" in stripped_text.lower()
    assert "China Mainland" in stripped_text

    zeroed = replace(
        missing_attr,
        impairment_ratio_contribution=tuple(
            0.0 if value is not None else None
            for value in missing_attr.impairment_ratio_contribution
        ),
    )
    zeroed = replace(zeroed, selection=select_driver_argument(zeroed))
    zero_text = render_drivers_markdown(zeroed)
    assert "0.00 pp" in zero_text or "+0.00 pp" in zero_text or "0.00" in zero_text

    from modeler.line_resolver import resolve_line
    cfo = resolve_line(fin.cash_flow, "operating_cash_flow", required=True).item
    latest = fin.periods[-1].end_date
    del cfo.values[latest]
    missing_cash = assemble_drivers_view(fin, company.name)
    assert missing_cash.selection is not None
    assert "cash_conversion" not in missing_cash.selection.main_body_ids
    assert "operating_margin_bridge" in missing_cash.selection.principal_ids
    assert "geographic_localization" in missing_cash.selection.principal_ids
    assert "footprint_intensity" not in missing_cash.selection.principal_ids
    missing_text = render_drivers_markdown(missing_cash)
    assert "cash.png" not in missing_text
    assert "growth.png" not in missing_text
    assert "margin.png" in missing_text


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


def test_geographic_claim_conditions_and_supported_wording(tmp_path):
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    base = assemble_drivers_view(fin, company.name)
    latest = len(base.periods) - 1
    canonical = geographic_claim_conditions(base, latest)
    assert canonical.revenue_offset == OFFSET_GREATER
    assert canonical.americas_profit_declined
    assert canonical.corporate_burden_increased
    assert canonical.consolidated_profit_weaker
    canonical_text = render_drivers_markdown(base)
    assert "growth did not preserve the prior profit level" in canonical_text
    assert (
        "International revenue more than offset the Americas decline"
        in canonical_text
    )
    assert "International growth more than offset the Americas revenue decline." in canonical_text
    assert "left a weaker consolidated profit outcome" in canonical_text
    assert "Americas profit decline and higher corporate/unallocated burden" in canonical_text
    assert (
        "Did international revenue growth offset Americas profit deterioration?"
        in canonical_text
    )
    assert "geographic_localization" in base.selection.main_body_ids

    positive = _render_geo_view(
        base,
        geo_consolidated_profit_change=_replace_latest(
            base.geo_consolidated_profit_change, 100000.0
        ),
        geo_profit_changes=_replace_latest_geo(
            base.geo_profit_changes, americas=80000.0
        ),
        geo_reconciling_profit_change=_replace_latest(
            base.geo_reconciling_profit_change, 20000.0
        ),
    )
    positive_text = render_drivers_markdown(positive)
    assert "growth did not preserve the prior profit level" not in positive_text
    assert "deteriorat" not in positive_text.lower()
    assert "weaker consolidated profit" not in positive_text
    assert "Americas profit decline" not in positive_text
    assert "higher corporate/unallocated burden" not in positive_text
    assert "Operating profit changed by $100.0 million." in positive_text
    assert "geographic_localization" in positive.selection.main_body_ids

    zero = _render_geo_view(
        base,
        geo_consolidated_profit_change=_replace_latest(
            base.geo_consolidated_profit_change, 0.0
        ),
        geo_profit_changes=_replace_latest_geo(
            base.geo_profit_changes, americas=0.0
        ),
    )
    zero_text = render_drivers_markdown(zero)
    assert "growth did not preserve the prior profit level" not in zero_text
    assert "deteriorat" not in zero_text.lower()
    assert "weaker consolidated profit" not in zero_text
    assert "Operating profit changed by $0.0 million." in zero_text

    missing_profit = _render_geo_view(
        base,
        geo_consolidated_profit_change=_replace_latest(
            base.geo_consolidated_profit_change, None
        ),
        geo_profit_changes=_replace_latest_geo(
            base.geo_profit_changes, americas=None
        ),
        geo_reconciling_profit_change=_replace_latest(
            base.geo_reconciling_profit_change, None
        ),
    )
    missing_text = render_drivers_markdown(missing_profit)
    assert "growth did not preserve the prior profit level" not in missing_text
    assert "deteriorat" not in missing_text.lower()
    assert "weaker consolidated profit" not in missing_text
    assert "declined" not in missing_text.split("## Appendix", 1)[0]
    assert "geographic_localization" in missing_profit.selection.main_body_ids

    negative = _render_geo_view(
        base,
        geo_consolidated_profit_change=_replace_latest(
            base.geo_consolidated_profit_change, -50000.0
        ),
    )
    negative_text = render_drivers_markdown(negative)
    assert "growth did not preserve the prior profit level" in negative_text
    assert "left a weaker consolidated profit outcome" in negative_text

    americas_growth = _render_geo_view(
        base,
        geo_revenue_amount_changes=_replace_latest_geo(
            base.geo_revenue_amount_changes, americas=81000.0
        ),
        geo_contribution_amounts=_replace_latest_geo(
            base.geo_contribution_amounts, americas=81000.0
        ),
    )
    growth_text = render_drivers_markdown(americas_growth)
    assert geographic_claim_conditions(americas_growth, latest).revenue_offset is None
    assert "offset the Americas decline" not in growth_text
    assert "offset the Americas revenue decline" not in growth_text
    assert "geographic_localization" in americas_growth.selection.main_body_ids

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

    partial = _offset_view(-100000.0, 30000.0, 20000.0)
    exact = _offset_view(-100000.0, 60000.0, 40000.0)
    greater = _offset_view(-100000.0, 80000.0, 40000.0)
    assert geographic_claim_conditions(partial, latest).revenue_offset == OFFSET_PARTIAL
    assert geographic_claim_conditions(exact, latest).revenue_offset == OFFSET_EXACT
    assert geographic_claim_conditions(greater, latest).revenue_offset == OFFSET_GREATER
    partial_text = render_drivers_markdown(partial)
    exact_text = render_drivers_markdown(exact)
    greater_text = render_drivers_markdown(greater)
    assert "only partially offset the Americas revenue decline" in partial_text
    assert "exactly offset the Americas revenue decline" in exact_text
    assert "more than offset the Americas revenue decline" in greater_text
    assert "more than offset" not in partial_text.split("## Appendix", 1)[0]

    missing_region = _offset_view(-100000.0, None, 400000.0)
    missing_conditions = geographic_claim_conditions(missing_region, latest)
    assert missing_conditions.international_revenue is None
    assert missing_conditions.revenue_offset is None
    missing_region_text = render_drivers_markdown(missing_region)
    assert "offset the Americas" not in missing_region_text
    assert "n/a" in missing_region_text

    burden_up_profit_up = _render_geo_view(
        base,
        geo_consolidated_profit_change=_replace_latest(
            base.geo_consolidated_profit_change, 80000.0
        ),
        geo_reconciling_profit_change=_replace_latest(
            base.geo_reconciling_profit_change, -20000.0
        ),
        geo_profit_changes=_replace_latest_geo(
            base.geo_profit_changes, americas=100000.0
        ),
    )
    mixed_up = render_drivers_markdown(burden_up_profit_up)
    mixed_conditions = geographic_claim_conditions(burden_up_profit_up, latest)
    assert mixed_conditions.corporate_burden_increased
    assert not mixed_conditions.consolidated_profit_weaker
    assert not mixed_conditions.americas_profit_declined
    assert "deteriorat" not in mixed_up.lower()
    assert "weaker consolidated profit" not in mixed_up
    assert "Americas profit decline" not in mixed_up
    assert "higher corporate/unallocated burden" not in mixed_up

    burden_down_profit_down = _render_geo_view(
        base,
        geo_reconciling_profit_change=_replace_latest(
            base.geo_reconciling_profit_change, 20000.0
        ),
    )
    mixed_down = render_drivers_markdown(burden_down_profit_down)
    assert geographic_claim_conditions(burden_down_profit_down, latest).corporate_burden_increased is False
    assert "higher corporate/unallocated burden" not in mixed_down
    assert "left a weaker consolidated profit outcome" in mixed_down
    assert "Americas profit decline" in mixed_down

    empty_row = {
        identity: None for identity in base.geo_identities
    }
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
    assert "offset the Americas" not in only_text
    assert "higher corporate/unallocated burden" not in only_text
    assert "Geographic contributions localize where revenue and profit changed" in only_text
    assert "Geographic evidence localizes revenue and profit changes" in only_text


def _assert_no_offset_or_growth_claim(text: str) -> None:
    lower = text.lower()
    assert "only partially offset" not in lower
    assert "exactly offset the americas" not in lower
    assert "more than offset" not in lower
    assert "international growth" not in lower
    assert "international revenue offset" not in lower
    assert "did international revenue growth offset" not in lower


def test_driver_md_states_company_agnostic_hierarchy():
    text = (ROOT / "director" / "docs" / "DRIVER.md").read_text(encoding="utf-8")
    assert "Headline conclusion → Principal drivers → Secondary signals → Appendix" in text
    assert "labeled regression fixtures" in text
    assert "Portability" in text
    assert "Zero figures is acceptable" in text or "zero figures" in text.casefold()


def test_reconstruction_gates_incomplete_contradictory_and_zero_figures(tmp_path):
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    base = assemble_drivers_view(fin, company.name)
    latest = len(base.periods) - 1
    assert margin_reconstruction_complete(base, latest)
    complete_text = render_drivers_markdown(base)
    complete_main = complete_text.split("## Appendix", 1)[0]
    assert "account for the reported operating-margin change as an identity" in complete_main
    assert "Which accounting components reconstruct the latest operating-margin change?" in complete_main

    incomplete = _carry_reconstruction(
        replace(
            base,
            contribution_residual=_replace_latest(base.contribution_residual, 0.02),
            operating_margin_residual=_replace_latest(base.operating_margin_residual, 0.02),
            operating_margin_change_residual=_replace_latest(
                base.operating_margin_change_residual, 0.02
            ),
        )
    )
    incomplete = replace(incomplete, selection=select_driver_argument(incomplete))
    assert not margin_reconstruction_complete(incomplete, latest)
    incomplete_text = render_drivers_markdown(incomplete)
    incomplete_main = incomplete_text.split("## Appendix", 1)[0]
    assert "residual remains" in incomplete_main
    assert "partly explain" in incomplete_main
    assert "account for the reported operating-margin change as an identity" not in incomplete_main
    margin_q = incomplete.selection.question("operating_margin_bridge")
    assert margin_q is not None
    assert "partial" in margin_q.strongest_conclusion
    assert "reconstruct" not in margin_q.figure_question

    contradictory = _carry_reconstruction(
        replace(
            base,
            reported_operating_margin_change=_replace_latest(
                base.reported_operating_margin_change, 0.01
            ),
            gross_margin_contribution=_replace_latest(base.gross_margin_contribution, -0.02),
            sga_ratio_contribution=_replace_latest(base.sga_ratio_contribution, 0.005),
            contribution_residual=_replace_latest(base.contribution_residual, 0.025),
        )
    )
    contradictory = replace(contradictory, selection=select_driver_argument(contradictory))
    contra_text = render_drivers_markdown(contradictory)
    contra_main = contra_text.split("## Appendix", 1)[0]
    assert "gross-margin contraction" in contra_main.casefold()
    assert "lower sg&a ratio" in contra_main.casefold()
    assert "Gross-margin contraction and a higher SG&A ratio account for" not in contra_main
    assert "residual remains" in contra_main

    missing = _carry_reconstruction(
        replace(base, sga_ratio=tuple(None for _ in base.sga_ratio))
    )
    missing = replace(missing, selection=select_driver_argument(missing))
    assert not margin_reconstruction_complete(missing, latest)
    missing_text = render_drivers_markdown(missing)
    assert "residual remains" in missing_text or "partial" in missing_text

    zero_fig = replace(incomplete.selection, figure_ids=())
    zero_view = replace(incomplete, selection=zero_fig)
    zero_text = render_drivers_markdown(zero_view)
    assert "../figures/drivers/" not in zero_text
    publish_drivers(fin, tmp_path / "out", display_name=company.name)
    drivers = tmp_path / "out" / "research" / "Lululemon_Drivers.md"
    drivers.write_text(zero_text, encoding="utf-8")
    for path in (tmp_path / "out" / "figures" / "drivers").glob("*.png"):
        path.unlink()
    verify_research_artifacts(tmp_path / "out", company.name)
