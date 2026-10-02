"""Compatibility façade. BAV construction is Modeler; Trainer overlay is Legacy."""

from composer.workbook_opening import BAV_OPENING_SHEET, _add_bav_opening
from modeler.build_bav import (
    BASE_FONT,
    CLEAR_BORDER,
    FONT_NAME,
    JUDGMENT_FIRST_DATA_ROW,
    JUDGMENT_RESPONSE_COLS,
    NOTE_AUTHOR,
    WHITE_FILL,
    _judgment_case_rows,
    build_bav_workbook,
    finalize_bav,
)
from modeler.engine.map_embed import COMPONENT_MAP_SHEET
from modeler.semantic_io import group_components_by_family
from legacy.trainer.derive import build_training_workbook, derive_trainer_workbook
from legacy.trainer.workbook import (
    PRACTICE_FILL,
    TRAINER_INDEX_INSTRUCTION,
    TrainingWorkbookGenerator,
    remove_trainer_sidecars,
)

__all__ = [
    "BAV_OPENING_SHEET",
    "BASE_FONT",
    "CLEAR_BORDER",
    "COMPONENT_MAP_SHEET",
    "FONT_NAME",
    "JUDGMENT_FIRST_DATA_ROW",
    "JUDGMENT_RESPONSE_COLS",
    "NOTE_AUTHOR",
    "PRACTICE_FILL",
    "TRAINER_INDEX_INSTRUCTION",
    "TrainingWorkbookGenerator",
    "WHITE_FILL",
    "_add_bav_opening",
    "_judgment_case_rows",
    "build_bav_workbook",
    "build_training_workbook",
    "derive_trainer_workbook",
    "finalize_bav",
    "group_components_by_family",
    "remove_trainer_sidecars",
]
