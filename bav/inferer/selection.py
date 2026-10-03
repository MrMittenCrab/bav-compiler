"""Neutral driver claim typology and economic gates."""

from __future__ import annotations

from dataclasses import dataclass

from bav.modeler.research.eligibility import margin_is_eligible
from bav.modeler.research.geo_conditions import (
    GeographicClaimConditions,
    latest_index,
    present,
)
from bav.modeler.research.records import ResearchQuestion


CLAIM_IDENTITY = "accounting_identity"
CLAIM_REPORTED = "reported_fact"
CLAIM_PROXY = "proxy"
CLAIM_LOCALIZATION = "geographic_localization"
CLAIM_ASSOCIATION = "historical_association"
CLAIM_ATTRIBUTION = "management_attribution"
CLAIM_INFERENCE = "system_inference"
CLAIM_INTERPRETATION = "supported_interpretation"
CLAIM_UNRESOLVED = "unresolved_material_question"

_NEUTRAL_GEO_RATIONALE = (
    "Geographic contributions localize where revenue and profit changed."
)


@dataclass(frozen=True)
class DriverInterpretation:
    questions: tuple[ResearchQuestion, ...]
    margin_material: bool
    geo_story: bool
    footprint_diverged: bool
    cash_visible: bool
    calendar_limited: bool


def geographic_materiality_rationale(conditions: GeographicClaimConditions) -> str:
    if conditions.revenue_offset is not None and conditions.consolidated_profit_weaker:
        return (
            "The location of dependence changed: international revenue offset "
            "did not prevent consolidated profit deterioration."
        )
    return _NEUTRAL_GEO_RATIONALE


def calendar_limitation_applies(view) -> bool:
    period = view.fifty_three_week_period
    return period is not None and period in view.periods


def geo_has_operating_story(conditions: GeographicClaimConditions | None) -> bool:
    if conditions is None:
        return False
    return bool(
        conditions.revenue_offset is not None
        or conditions.americas_profit_declined
        or conditions.consolidated_profit_weaker
    )


def footprint_diverged(view, latest: int) -> bool:
    rev_g = view.revenue_growth[latest] if latest < len(view.revenue_growth) else None
    store_g = view.store_growth[latest] if latest < len(view.store_growth) else None
    return present(rev_g) and present(store_g) and store_g > rev_g


def cash_visible(view, latest: int) -> bool:
    cfo = None if view.cfo is None or latest >= len(view.cfo) else view.cfo[latest]
    ni = None if view.net_income is None or latest >= len(view.net_income) else view.net_income[latest]
    if not present(cfo) or not present(ni):
        return False
    cfo_change = (
        None
        if view.cfo_change is None or latest >= len(view.cfo_change)
        else view.cfo_change[latest]
    )
    ni_change = (
        None
        if view.net_income_change is None or latest >= len(view.net_income_change)
        else view.net_income_change[latest]
    )
    weaker = present(cfo_change) and present(ni_change) and cfo_change < ni_change
    return weaker or present(cfo_change)


def interpret_driver_gates(view, questions: tuple[ResearchQuestion, ...]) -> DriverInterpretation:
    latest = latest_index(view)
    by_id = {item.identifier: item for item in questions}
    geo = by_id.get("geographic_localization")
    from bav.modeler.research.geo_conditions import geographic_claim_conditions
    conditions = geographic_claim_conditions(view, latest) if geo and latest is not None else None
    return DriverInterpretation(
        questions=questions,
        margin_material=bool(by_id.get("operating_margin_bridge"))
        and margin_is_eligible(view, latest),
        geo_story=geo_has_operating_story(conditions),
        footprint_diverged=bool(by_id.get("footprint_intensity"))
        and latest is not None
        and footprint_diverged(view, latest),
        cash_visible=bool(by_id.get("cash_conversion"))
        and latest is not None
        and cash_visible(view, latest),
        calendar_limited=calendar_limitation_applies(view),
    )
