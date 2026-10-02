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

from core.current_build import prepare_company_input, resolve_company
from core.ingestion.management_kpi_enrichment import inspect_source_pdf
from core.research.drivers import (
    APPENDIX_HEADING,
    OBSOLETE_SECTIONS,
    WORKPAPER_FIELDS,
    _label_for,
    assemble_drivers_view,
    expected_sections,
    is_cfo_component,
    margin_reconstruction_complete,
    publish_drivers,
    render_drivers_markdown,
    selected_cfo_concepts,
    selected_figure_names,
)
from core.research.selection import (
    OFFSET_EXACT,
    OFFSET_GREATER,
    OFFSET_PARTIAL,
    _revenue_offset_kind,
    geographic_claim_conditions,
    geographic_figure_question,
    geographic_materiality_rationale,
    geographic_strongest_conclusion,
    select_driver_argument,
)
from core.research.publish import publish_company_research, verify_research_artifacts
from core.research.style import (
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
from core.tests.test_lululemon_benchmark import REVENUE_ANCHORS
from core.tests.test_management_kpi_admission import EXTRACTED, SOURCE
from core.tests.test_operating_kpi_facts import INDEPENDENT_STORE_TOTALS

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


def test_style_specification_and_fonts():
    text = (ROOT / "STYLE.md").read_text(encoding="utf-8")
    assert "Aptos Regular" in text
    assert "DengXian Regular" in text
    assert "14" in text and "10" in text
    assert "11" in text and "9" in text
    assert "8 pt" in text or "8pt" in text
    assert "16 pt" in text or "16pt" in text
    assert "1.25" in text
    fonts = resolve_required_fonts()
    assert fonts.latin_name
    assert fonts.cjk_name
    assert fonts.latin_path.is_file()
    assert fonts.cjk_path.is_file()
    style = apply_research_style(accent=None)
    assert style.accent is None
    assert style.series_color(0, highlight=True) == style.series_color(0)


def test_readme_documents_architecture_without_copying_style():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "build/output/lululemon/Lululemon_BAV.xlsx" in text
    assert "build/output/lululemon/research/*.md" in text
    assert "build/output/lululemon/figures/" in text
    assert "Drivers → Forecast → Valuation → Overview" in text
    assert "STYLE.md" in text
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


def test_accent_disabled_and_enabled_remain_complete(tmp_path):
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    publish_drivers(fin, tmp_path / "plain", display_name=company.name, accent=None)
    publish_drivers(fin, tmp_path / "accent", display_name=company.name, accent="#1F4E79")
    verify_research_artifacts(tmp_path / "plain", company.name)
    verify_research_artifacts(tmp_path / "accent", company.name)
    plain = {
        name: hashlib.sha256(
            (tmp_path / "plain" / "figures" / "drivers" / name).read_bytes()
        ).hexdigest()
        for name in selected_figure_names(assemble_drivers_view(fin, company.name))
    }
    styled = {
        name: hashlib.sha256(
            (tmp_path / "accent" / "figures" / "drivers" / name).read_bytes()
        ).hexdigest()
        for name in selected_figure_names(assemble_drivers_view(fin, company.name))
    }
    assert plain == styled


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


def test_figure_word_spacing_uses_required_fonts_and_visible_gaps(tmp_path):
    fonts = resolve_required_fonts()
    assert fonts.latin_name == LATIN_FACE
    assert fonts.cjk_name == CJK_FACE
    assert fonts.latin_path.name == "Aptos.ttf"
    assert fonts.cjk_path.name == "Deng.ttf"
    assert _font_has(fonts.latin_path, 0x20)
    assert _font_has(fonts.cjk_path, 0x20)
    assert not _font_has(fonts.latin_path, 0x2002)
    assert not _font_has(fonts.cjk_path, 0x2002)

    style = apply_research_style(accent=None)
    assert style.fonts.latin_path == fonts.latin_path
    assert style.fonts.cjk_path == fonts.cjk_path
    assert set(style.word_space) == {" "}
    assert "\u2002" not in style.word_space
    assert len(style.word_space) > 1
    assert spaced("Revenue growth") == f"Revenue{style.word_space}growth"
    assert "\u2002" not in spaced("Revenue growth")

    min_title = TITLE_PT * FIGURE_DPI * PT * MIN_WORD_GAP_EM
    min_note = LABEL_PT * FIGURE_DPI * PT * MIN_WORD_GAP_EM
    assert _ink_gap_px("Revenue growth", pt=TITLE_PT) < min_title
    assert _ink_gap_px(spaced("Revenue growth"), pt=TITLE_PT) >= min_title
    assert _ink_gap_px(spaced("store-count growth"), pt=LABEL_PT) >= min_note

    title = "Revenue growth, store-count growth, and reported comparable sales"
    source = (
        "Source: Lululemon BAV income statement and company-operated store counts.\n"
        "Comparable sales use the reported global definition of each year."
    )
    fig, ax = new_figure(style)
    ax.bar([0, 1], [10, 20], color=style.series_color(0), label="Consolidated revenue growth")
    ax.set_xticks([0, 1], ["FY2025\n2 Feb 2025", "FY2024\n28 Jan 2024"])
    ax.set_ylabel("Percentage-point contribution")
    ax.legend(loc="upper right")
    path = tmp_path / "spacing.png"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        finish_figure(fig, ax, style, title, source, path)
    missing = [
        str(item.message)
        for item in caught
        if "missing from font" in str(item.message) or "Glyph" in str(item.message)
    ]
    assert missing == []
    assert path.is_file() and path.stat().st_size > 0

    image = Image.open(path)
    assert image.size == (
        int(FIGURE_SIZE[0] * FIGURE_DPI),
        int(FIGURE_SIZE[1] * FIGURE_DPI),
    )
    title_gaps = _interior_ink_gaps(path, 90, 125)
    image_l = Image.open(path).convert("L")
    note_bands: list[tuple[int, int]] = []
    start = None
    for y in range(image_l.size[1]):
        ink = any(image_l.getpixel((x, y)) < 200 for x in range(image_l.size[0]))
        if ink and start is None:
            start = y
        elif not ink and start is not None:
            note_bands.append((start, y))
            start = None
    if start is not None:
        note_bands.append((start, image_l.size[1]))
    assert len(note_bands) >= 2, note_bands
    note_line_one = _interior_ink_gaps(path, note_bands[-2][0], note_bands[-2][1])
    note_line_two = _interior_ink_gaps(path, note_bands[-1][0], note_bands[-1][1])
    assert max(title_gaps) >= min_title, (title_gaps, min_title)
    assert max(note_line_one) >= min_note, (note_line_one, min_note)
    assert max(note_line_two) >= min_note, (note_line_two, min_note)
    assert sum(gap >= min_title for gap in title_gaps) >= 3
    assert sum(gap >= min_note for gap in note_line_one) >= 3


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

    from core.model.line_resolver import resolve_line
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


def test_roles_follow_evidence_not_company_label(tmp_path):
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    base = assemble_drivers_view(fin, company.name)
    assert base.selection.principal_ids == (
        "operating_margin_bridge",
        "geographic_localization",
    )
    assert base.selection.secondary_ids == ("cash_conversion",)
    assert "footprint_intensity" in base.selection.appendix_ids

    no_geo = replace(
        base,
        geo_identities=(),
        geo_contributions=tuple({} for _ in base.geo_contributions),
        geo_revenue_amount_changes=tuple({} for _ in (base.geo_revenue_amount_changes or ())),
        geo_profit_changes=tuple({} for _ in (base.geo_profit_changes or ())),
        geo_reconciling_profit_change=tuple(
            None for _ in (base.geo_reconciling_profit_change or ())
        ),
        geo_consolidated_profit_change=tuple(
            None for _ in (base.geo_consolidated_profit_change or ())
        ),
    )
    no_geo = replace(no_geo, selection=select_driver_argument(no_geo))
    assert "geographic_localization" not in no_geo.selection.main_body_ids
    assert "footprint_intensity" in no_geo.selection.principal_ids
    assert "cash_conversion" in no_geo.selection.secondary_ids

    no_margin = replace(
        base,
        reported_operating_margin_change=tuple(
            0.0 if value is not None else None
            for value in (base.reported_operating_margin_change or ())
        ),
    )
    no_margin = replace(no_margin, selection=select_driver_argument(no_margin))
    assert "operating_margin_bridge" not in no_margin.selection.principal_ids
    assert "cash_conversion" in no_margin.selection.secondary_ids
    assert "geographic_localization" in no_margin.selection.principal_ids

    only_cash = replace(
        no_geo,
        reported_operating_margin_change=tuple(
            0.0 if value is not None else None
            for value in (no_geo.reported_operating_margin_change or ())
        ),
        store_growth=tuple(None for _ in no_geo.store_growth),
    )
    only_cash = replace(only_cash, selection=select_driver_argument(only_cash))
    assert only_cash.selection.principal_ids == ("cash_conversion",)
    cash_text = render_drivers_markdown(only_cash)
    assert "## 1. Cash conversion" in cash_text
    assert "cash.png" in cash_text


def test_zero_figures_and_positive_margin_are_publishable(tmp_path):
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    base = assemble_drivers_view(fin, company.name)
    positive = replace(
        base,
        reported_operating_margin_change=_replace_latest(
            base.reported_operating_margin_change, 0.01
        ),
        geo_consolidated_profit_change=_replace_latest(
            base.geo_consolidated_profit_change, 100000.0
        ),
        geo_profit_changes=_replace_latest_geo(base.geo_profit_changes, americas=80000.0),
        geo_reconciling_profit_change=_replace_latest(
            base.geo_reconciling_profit_change, 20000.0
        ),
        geo_revenue_amount_changes=_replace_latest_geo(
            base.geo_revenue_amount_changes, americas=81000.0
        ),
    )
    positive = replace(positive, selection=select_driver_argument(positive))
    assert "operating_margin_bridge" in positive.selection.principal_ids
    text = render_drivers_markdown(positive)
    assert "Operating-margin expansion" in text
    assert "growth did not preserve the prior profit level" not in text

    zero_fig = replace(positive, selection=replace(positive.selection, figure_ids=()))
    zero_text = render_drivers_markdown(zero_fig)
    assert "../figures/drivers/" not in zero_text
    publish_drivers(fin, tmp_path / "out", display_name=company.name)
    drivers = tmp_path / "out" / "research" / "Lululemon_Drivers.md"
    drivers.write_text(zero_text, encoding="utf-8")
    for path in (tmp_path / "out" / "figures" / "drivers").glob("*.png"):
        path.unlink()
    verify_research_artifacts(tmp_path / "out", company.name)


def test_driver_md_states_company_agnostic_hierarchy():
    text = (ROOT / "DRIVER.md").read_text(encoding="utf-8")
    assert "Headline conclusion → Principal drivers → Secondary signals → Appendix" in text
    assert "labeled regression fixtures" in text
    assert "Portability" in text
    assert "Zero figures is acceptable" in text or "zero figures" in text.casefold()


def test_cfo_selection_fast_retailing_reviewed_set_and_exclusions(tmp_path):
    from core.data.standardized_io import standardized_from_payload

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

    incomplete = replace(
        base,
        contribution_residual=_replace_latest(base.contribution_residual, 0.02),
        operating_margin_residual=_replace_latest(base.operating_margin_residual, 0.02),
        operating_margin_change_residual=_replace_latest(
            base.operating_margin_change_residual, 0.02
        ),
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

    contradictory = replace(
        base,
        reported_operating_margin_change=_replace_latest(
            base.reported_operating_margin_change, 0.01
        ),
        gross_margin_contribution=_replace_latest(base.gross_margin_contribution, -0.02),
        sga_ratio_contribution=_replace_latest(base.sga_ratio_contribution, 0.005),
        contribution_residual=_replace_latest(base.contribution_residual, 0.025),
    )
    contradictory = replace(contradictory, selection=select_driver_argument(contradictory))
    contra_text = render_drivers_markdown(contradictory)
    contra_main = contra_text.split("## Appendix", 1)[0]
    assert "gross-margin contraction" in contra_main.casefold()
    assert "lower sg&a ratio" in contra_main.casefold()
    assert "Gross-margin contraction and a higher SG&A ratio account for" not in contra_main
    assert "residual remains" in contra_main

    missing = replace(base, sga_ratio=tuple(None for _ in base.sga_ratio))
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
