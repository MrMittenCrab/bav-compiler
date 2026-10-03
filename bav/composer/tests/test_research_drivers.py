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

from bav.director.current_build import prepare_company_input, resolve_company
from bav.extractor.ingestion.management_kpi_enrichment import inspect_source_pdf
from bav.composer.research.drivers import (
    APPENDIX_HEADING,
    OBSOLETE_SECTIONS,
    WORKPAPER_FIELDS,
    expected_sections,
    render_drivers_markdown,
    selected_figure_names,
)
from bav.director.research import (
    complete_driver_selection as select_driver_argument,
    complete_drivers_view as assemble_drivers_view,
    publish_drivers,
)
from bav.inferer.selection import geographic_materiality_rationale
from bav.debater.selection import geographic_strongest_conclusion
from bav.modeler.research.cfo import is_cfo_component, selected_cfo_concepts
from bav.modeler.research.drivers_view import (
    label_for as _label_for,
    margin_reconstruction_complete,
)
from bav.modeler.research.geo_conditions import (
    OFFSET_EXACT,
    OFFSET_GREATER,
    OFFSET_PARTIAL,
    geographic_claim_conditions,
    revenue_offset_kind as _revenue_offset_kind,
)
from bav.composer.research.selection import geographic_figure_question
from bav.composer.research.publish import publish_company_research, verify_research_artifacts
from bav.composer.research.style import (
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
from bav.modeler.tests.test_lululemon_benchmark import REVENUE_ANCHORS
from bav.modeler.tests.test_management_kpi_admission import EXTRACTED, SOURCE
from bav.modeler.tests.test_operating_kpi_facts import INDEPENDENT_STORE_TOTALS

ROOT = Path(__file__).resolve().parents[3]
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
    text = (ROOT / "bav" / "director" / "docs" / "STYLE.md").read_text(encoding="utf-8")
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


