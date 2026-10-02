"""Compatibility package. BAV construction is Modeler; Trainer overlay is Legacy."""

from modeler.build_bav import build_bav_workbook
from modeler.semantic_io import (
    answer_key_path_for,
    bav_path_for,
    load_semantic_map,
    resolve_pair_paths,
)
from legacy.trainer.checker import CheckSummary, check_workbook
from legacy.trainer.derive import build_training_workbook, derive_trainer_workbook
from legacy.trainer.workbook import TrainingWorkbookGenerator

__all__ = [
    "CheckSummary",
    "TrainingWorkbookGenerator",
    "answer_key_path_for",
    "bav_path_for",
    "build_bav_workbook",
    "build_training_workbook",
    "check_workbook",
    "derive_trainer_workbook",
    "load_semantic_map",
    "resolve_pair_paths",
]
