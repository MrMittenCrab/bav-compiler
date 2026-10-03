"""Deterministic classification case selection (coordinate-free)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from bav.inferer.classification_judgment import CLASSIFICATION_JUDGMENT_TEMPLATES
from bav.modeler.data.interface import StandardizedFinancials
from bav.modeler.data.line_identity import line_identity
from bav.modeler.classification import BALANCE_SHEET_CATEGORIES, BalanceSheetReformulation


@dataclass(frozen=True)
class JudgmentCase:
    id: str
    order: int
    line_identity: str
    override_selector: str
    label: str
    topic: str
    supplied_treatment: str
    alternatives: tuple[str, ...]
    model_rationale: str
    consequence_prompt: str
    model_consequence: str


def _line_has_nonzero_value(item, periods: list[date]) -> bool:
    for period in periods:
        value = item.values.get(period)
        if value is None:
            continue
        if float(value) != 0.0:
            return True
    return False


def classification_judgment_cases(
    financials: StandardizedFinancials,
    periods: list[date],
    reformulation: BalanceSheetReformulation,
) -> tuple[JudgmentCase, ...]:
    """Derive guided classification cases from supported ambiguous supplied lines."""
    cases: list[JudgmentCase] = []
    order = 1
    for idx in reformulation.detail_indices:
        decision = reformulation.decisions[idx]
        if not decision.ambiguous:
            continue
        if decision.overridden:
            continue
        if decision.judgment_code is None:
            continue
        template = CLASSIFICATION_JUDGMENT_TEMPLATES.get(decision.judgment_code)
        if template is None:
            raise ValueError(
                f"Unsupported judgment_code {decision.judgment_code!r} on "
                f"{financials.balance_sheet[idx].label!r}; add a registry template "
                f"or clear the code"
            )
        if template.options[0] != decision.category:
            raise ValueError(
                f"judgment template for {decision.judgment_code!r} expects category "
                f"{template.options[0]!r} but classifier returned {decision.category!r}"
            )
        for option in template.options:
            if option not in BALANCE_SHEET_CATEGORIES:
                raise ValueError(
                    f"judgment template option {option!r} is not a balance-sheet category"
                )
        item = financials.balance_sheet[idx]
        if not _line_has_nonzero_value(item, periods):
            continue
        ident = line_identity(item)
        identity = ident.key()
        override_selector = f"identity:{identity}"
        cases.append(
            JudgmentCase(
                id=f"classification::{identity}",
                order=order,
                line_identity=identity,
                override_selector=override_selector,
                label=item.label,
                topic=template.topic,
                supplied_treatment=decision.category,
                alternatives=tuple(template.options[1:]),
                model_rationale=template.model_rationale,
                consequence_prompt=template.consequence_prompt,
                model_consequence=template.model_consequence,
            )
        )
        order += 1
    return tuple(cases)
