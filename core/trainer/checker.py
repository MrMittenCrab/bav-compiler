"""Compatibility façade. Delegates Trainer scoring to Legacy."""

from legacy.trainer.checker import (
    BLANK_RGB,
    CORRECT_RGB,
    CheckSummary,
    INCORRECT_RGB,
    check_workbook,
)

__all__ = [
    "BLANK_RGB",
    "CORRECT_RGB",
    "CheckSummary",
    "INCORRECT_RGB",
    "check_workbook",
]
