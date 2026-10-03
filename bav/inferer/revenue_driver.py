"""Neutral revenue-driver verdicts, qualifications, and assessment kind."""

from __future__ import annotations

from dataclasses import dataclass

from bav.extractor.data.historical_strategy import THEME_COMPARABLE_SALES, THEME_PRODUCTIVITY
from bav.modeler.reported_margin import (
    KIND_CAUSAL,
    KIND_OBSERVED,
    KIND_UNESTABLISHED,
)
from bav.modeler.revenue_driver import RevenueDriverPeriodObservation

VERDICT_SUPPORTED = "supported_descriptively"
VERDICT_MIXED = "mixed"
VERDICT_CONTRADICTED = "contradicted"
VERDICT_INSUFFICIENT = "insufficiently_evidenced"
SUPPORTED_VERDICTS = (
    VERDICT_SUPPORTED,
    VERDICT_MIXED,
    VERDICT_CONTRADICTED,
    VERDICT_INSUFFICIENT,
)
QUAL_NOT_OUTCOME = "qual_not_outcome"
QUAL_DESCRIPTIVE_DIFFERENCE = "qual_descriptive_difference"
QUAL_RPS_NOT_PRODUCTIVITY = "qual_rps_not_productivity"
QUAL_POPS_DISTINCT = "qual_pops_distinct"
QUAL_GAPS_NOT_BRIDGED = "qual_gaps_not_bridged"
QUAL_NOT_ORGANIC_FX = "qual_not_organic_fx"
QUAL_COMPSALES_INELIGIBLE = "qual_compsales_ineligible"
REQ_STORE_GROWTH = "req_store_growth"
REQ_COMPSALES = "req_compsales"
REQ_SPSF_GROWTH = "req_spsf_growth"
REQ_GEOGRAPHIC = "req_geographic"
REQ_COMPSALES_HISTORY = "req_compsales_history"
REQ_ADDITIONAL_SPSF = "req_additional_spsf"


@dataclass(frozen=True)
class RevenueAssessmentDecision:
    name: str
    kind: str
    established: bool


def verdict_from_consistency(
    observations: tuple[RevenueDriverPeriodObservation, ...],
) -> str:
    flags: list[bool | None] = []
    for item in observations:
        flags.append(item.consistent)
        if item.mix_conflict:
            flags.append(False)
    known = tuple(flag for flag in flags if flag is not None)
    if not known:
        return VERDICT_INSUFFICIENT
    if all(known):
        return VERDICT_SUPPORTED
    if not any(known):
        return VERDICT_CONTRADICTED
    return VERDICT_MIXED


def interpret_revenue_assessment(interpretation) -> RevenueAssessmentDecision:
    """Descriptive/causal kind and established only. Identity is Modeler."""
    test = interpretation
    known = tuple(
        item.consistent
        for item in test.observations.observations
        if item.consistent is not None
    )
    if test.observations.theme == THEME_COMPARABLE_SALES:
        return RevenueAssessmentDecision(
            name="comparable-sales coincidence",
            kind=KIND_OBSERVED if known else KIND_UNESTABLISHED,
            established=bool(known) and test.verdict != VERDICT_INSUFFICIENT,
        )
    if test.observations.theme == THEME_PRODUCTIVITY:
        return RevenueAssessmentDecision(
            name="sales-per-square-foot productivity",
            kind=(
                KIND_UNESTABLISHED
                if test.verdict == VERDICT_INSUFFICIENT
                else KIND_OBSERVED
            ),
            established=test.verdict != VERDICT_INSUFFICIENT,
        )
    kind = KIND_OBSERVED if known else KIND_UNESTABLISHED
    if test.verdict == VERDICT_INSUFFICIENT:
        kind = KIND_UNESTABLISHED
    if test.verdict == VERDICT_CONTRADICTED:
        kind = KIND_CAUSAL
    return RevenueAssessmentDecision(
        name=test.observations.theme.replace("_", " "),
        kind=kind,
        established=test.verdict == VERDICT_SUPPORTED,
    )
