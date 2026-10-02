"""Legacy Trainer practice overlay. Active BAV construction does not import this package."""

from .checker import CheckSummary, check_workbook
from .derive import build_training_workbook, derive_trainer_workbook
from .workbook import TrainingWorkbookGenerator, remove_trainer_sidecars

__all__ = [
    "CheckSummary",
    "TrainingWorkbookGenerator",
    "build_training_workbook",
    "check_workbook",
    "derive_trainer_workbook",
    "remove_trainer_sidecars",
]
