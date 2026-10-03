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


