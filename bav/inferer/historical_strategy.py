"""Neutral historical-strategy inference, qualification, and limit codes."""

from __future__ import annotations

from bav.extractor.data.historical_strategy import (
    ROLE_OBJECTIVE,
    THEME_COMPARABLE_SALES,
    THEME_GEOGRAPHIC_GROWTH,
    THEME_PRODUCTIVITY,
    THEME_STORE_EXPANSION,
)
from bav.inferer.revenue_driver import (
    VERDICT_CONTRADICTED,
    VERDICT_INSUFFICIENT,
    VERDICT_MIXED,
    VERDICT_SUPPORTED,
)
from bav.modeler.revenue_driver import RevenueDriverHypothesisTest

LIMIT_UNTESTED = "limit_untested"
LIMIT_HISTORY = "limit_history"
LIMIT_DEFERRED_SPSF = "limit_deferred_spsf"
INFERENCE_SUPPORTED = "supported"
INFERENCE_MIXED = "mixed"
INFERENCE_CONTRADICTED = "contradicted"
INFERENCE_INSUFFICIENT = "insufficient"
GAP_INSUFFICIENT = "insufficient"
GAP_OTHER = "other"


def qualification_codes(test: RevenueDriverHypothesisTest) -> tuple[str, ...]:
    codes: list[str] = []
    if test.theme == THEME_STORE_EXPANSION:
        codes.append("descriptive_store")
    elif test.theme == THEME_COMPARABLE_SALES:
        codes.append("descriptive_compsales")
        if test.compsales_ineligible:
            codes.append("compsales_ineligible")
    elif test.theme == THEME_PRODUCTIVITY:
        codes.append("rps_not_productivity")
    elif test.theme == THEME_GEOGRAPHIC_GROWTH:
        codes.append("arithmetic_geo")
    if any(item.role == ROLE_OBJECTIVE for item in test.disclosures):
        codes.append("not_outcome")
    return tuple(codes)


def select_verdict_inference(test: RevenueDriverHypothesisTest) -> str:
    if test.verdict == VERDICT_SUPPORTED:
        return INFERENCE_SUPPORTED
    if test.verdict == VERDICT_MIXED:
        return INFERENCE_MIXED
    if test.verdict == VERDICT_CONTRADICTED:
        return INFERENCE_CONTRADICTED
    return INFERENCE_INSUFFICIENT


def has_deferred_spsf(test: RevenueDriverHypothesisTest) -> bool:
    return bool(test.has_deferred_spsf or test.deferred_disagreements)


def productivity_gap_kind(tests: tuple[RevenueDriverHypothesisTest, ...]) -> str:
    productivity = next(
        (test for test in tests if test.theme == THEME_PRODUCTIVITY),
        None,
    )
    if productivity is None:
        return ""
    if productivity.verdict == VERDICT_INSUFFICIENT:
        return GAP_INSUFFICIENT
    return GAP_OTHER
