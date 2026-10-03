"""Qualifications for supplied normalization grouping and treatment decisions.

Supplied grouping and treatment decisions remain supplied judgments. Mechanical
validation does not choose them or establish them as source facts. Supplied
referenceRationale and consequenceNote pass through verbatim.
"""

from __future__ import annotations

from dataclasses import dataclass

GROUPING_IS_ACCEPTED_SOURCE_FACT = False

CONSEQUENCE_PROMPT = (
    "Explain why you would treat this item as recurring or non-recurring and how "
    "that treatment changes normalized earnings."
)


@dataclass(frozen=True)
class SuppliedNormalizationInterpretation:
    model_rationale: str
    consequence_prompt: str
    model_consequence: str


def supplied_normalization_interpretation(
    reference_rationale: str,
    consequence_note: str,
) -> SuppliedNormalizationInterpretation:
    """Attach supplied rationale and consequence without choosing a treatment."""
    return SuppliedNormalizationInterpretation(
        model_rationale=reference_rationale,
        consequence_prompt=CONSEQUENCE_PROMPT,
        model_consequence=consequence_note,
    )


def grouping_established_as_source_fact(
    authorization_kind: str | None = None,
) -> bool:
    """Independent authorization does not establish grouping as a source fact."""
    del authorization_kind
    return GROUPING_IS_ACCEPTED_SOURCE_FACT
