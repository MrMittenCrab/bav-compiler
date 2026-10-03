"""Compatibility façade. Implementation lives in modeler.judgment and interpreter.classification_judgment."""

from interpreter.classification_judgment import (
    CLASSIFICATION_JUDGMENT_TEMPLATES,
    CONSEQUENCE_PROMPT,
    ClassificationJudgmentTemplate,
)
from modeler.judgment import JudgmentCase, classification_judgment_cases
from modeler.judgment import _line_has_nonzero_value
