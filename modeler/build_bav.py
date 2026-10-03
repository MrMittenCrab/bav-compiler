"""Professional BAV workbook construction. Does not derive a Trainer."""

from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import Border, Font, PatternFill

from composer.workbook_opening import _add_bav_opening
from modeler.data.line_identity import validate_financials_identities
from modeler.ingestion.reconciler import reconcile_financials
from modeler.engine.component_catalog import is_operating_kpi_source_identity
from modeler.engine.semantic_map import SemanticMap
from modeler.semantic_io import load_semantic_map, parse_cell_ref, resolve_pair_paths
from modeler.workbook import (
    JUDGMENT_SHEET,
    NORMALIZATION_JUDGMENT_SHEET,
    ReferenceModelBuilder,
)

NOTE_AUTHOR = "BAV"
JUDGMENT_FIRST_DATA_ROW = 5
JUDGMENT_RESPONSE_COLS = (6, 7, 8)
WHITE_FILL = PatternFill("solid", start_color="FFFFFF")
FONT_NAME = "Aptos Narrow"
BASE_FONT = Font(
    name=FONT_NAME,
    size=11,
    bold=False,
    italic=False,
    color="000000",
)
CLEAR_BORDER = Border()
_HIDDEN_PREFIX = "_"


def _judgment_case_rows(ws):
    """Yield data rows that look like judgment cases (not the zero-case message)."""
    for row in range(JUDGMENT_FIRST_DATA_ROW, (ws.max_row or 0) + 1):
        order = ws.cell(row=row, column=1).value
        label = ws.cell(row=row, column=2).value
        if isinstance(order, int) and order >= 1 and label not in (None, ""):
            yield row


def _visible_sheets(wb):
    return [
        ws
        for ws in wb.worksheets
        if not ws.title.startswith(_HIDDEN_PREFIX) and ws.sheet_state == "visible"
    ]


def _apply_minimal_style(wb) -> None:
    """Normalize visible sheets to Aptos Narrow 11 with white fill and no borders."""
    for ws in _visible_sheets(wb):
        ws.sheet_view.showGridLines = False
        max_row = ws.max_row or 1
        max_col = ws.max_column or 1
        for row in ws.iter_rows(min_row=1, max_row=max_row, min_col=1, max_col=max_col):
            for cell in row:
                if (
                    cell.value is None
                    and cell.comment is None
                    and not cell.has_style
                ):
                    continue
                cell.font = BASE_FONT
                cell.fill = WHITE_FILL
                cell.border = CLEAR_BORDER


def _decorate_answer_key_practice_cells(wb, semantic_map: SemanticMap) -> None:
    for comp in semantic_map.all_ordered():
        if is_operating_kpi_source_identity(comp):
            continue
        if comp.tab not in wb.sheetnames:
            continue
        ws = wb[comp.tab]
        row, col = parse_cell_ref(comp.cell)
        cell = ws.cell(row=row, column=col)
        cell.fill = WHITE_FILL
        hint = (comp.short_hint or "").strip()
        if not hint and comp.hints:
            hint = str(comp.hints[0]).strip()
        if not hint:
            hint = comp.title
        cell.comment = Comment(hint, NOTE_AUTHOR)


def _decorate_answer_key_judgment_cells(wb) -> None:
    if JUDGMENT_SHEET not in wb.sheetnames:
        return
    ws = wb[JUDGMENT_SHEET]
    for row in _judgment_case_rows(ws):
        for col in JUDGMENT_RESPONSE_COLS:
            cell = ws.cell(row=row, column=col)
            cell.fill = WHITE_FILL


def _decorate_answer_key_normalization_judgment_cells(wb) -> None:
    if NORMALIZATION_JUDGMENT_SHEET not in wb.sheetnames:
        return
    ws = wb[NORMALIZATION_JUDGMENT_SHEET]
    for row in _judgment_case_rows(ws):
        for col in JUDGMENT_RESPONSE_COLS:
            cell = ws.cell(row=row, column=col)
            cell.fill = WHITE_FILL


def _financials_for_opening(bav_path: Path, financials=None):
    if financials is not None:
        return financials
    from modeler.data.standardized_io import standardized_from_payload
    from modeler.check_context import load_check_context

    return standardized_from_payload(load_check_context(bav_path).source_payload)


def finalize_bav(
    bav_path: Path,
    semantic_map: SemanticMap | None = None,
    financials=None,
) -> Path:
    """Write formulas, Notes, opening and metadata into the BAV only."""
    bav_path = Path(bav_path)
    semantic_map = semantic_map or load_semantic_map(bav_path)
    financials = _financials_for_opening(bav_path, financials)
    wb = load_workbook(bav_path)
    _add_bav_opening(wb, financials)
    from modeler.build_status import add_build_status
    add_build_status(wb, semantic_map)
    _apply_minimal_style(wb)
    _decorate_answer_key_practice_cells(wb, semantic_map)
    _decorate_answer_key_judgment_cells(wb)
    _decorate_answer_key_normalization_judgment_cells(wb)
    wb.save(bav_path)
    wb.close()
    return bav_path


def build_bav_workbook(
    financials,
    output_path: Path,
    assumptions: dict | None = None,
    *,
    current_snapshot: bool = False,
) -> Path:
    """End-to-end: standardized data → professional BAV. Does not derive a Trainer."""
    validate_financials_identities(financials)

    report = reconcile_financials(financials)
    failed = [name for name, ok in report.checksums.items() if ok is False]
    if failed:
        details = "; ".join(failed)
        warnings = "; ".join(report.warnings) if report.warnings else details
        raise ValueError(
            f"Source statement checksum failed ({details}). "
            f"Refuse BAV build. {warnings}"
        )

    _, bav_path = resolve_pair_paths(output_path)
    builder = ReferenceModelBuilder(financials, assumptions, current_snapshot=current_snapshot)
    semantic_map = builder.build(bav_path)
    return finalize_bav(bav_path, semantic_map, financials=financials)
