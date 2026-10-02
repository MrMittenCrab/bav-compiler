"""Historical-strategy judgments: featured evidence, verdict groups, and limits."""

from __future__ import annotations

from dataclasses import dataclass

from extractor.data.historical_strategy import (
    ROLE_OBJECTIVE,
    ROLE_OPERATING_USE,
    ROLE_STRATEGY,
    THEME_COMPARABLE_SALES,
    THEME_GEOGRAPHIC_GROWTH,
    THEME_PRODUCTIVITY,
    THEME_STORE_EXPANSION,
    HistoricalStrategyDisclosure,
)
from interpreter.revenue_driver import (
    VERDICT_CONTRADICTED,
    VERDICT_INSUFFICIENT,
    VERDICT_MIXED,
    VERDICT_SUPPORTED,
)
from modeler.revenue_driver import RevenueDriverHypothesisTest

_ROLE_PRIORITY = (ROLE_STRATEGY, ROLE_OPERATING_USE, ROLE_OBJECTIVE)
LIMIT_UNTESTED = "limit_untested"
LIMIT_HISTORY = "limit_history"
LIMIT_DEFERRED_SPSF = "limit_deferred_spsf"
INFERENCE_SUPPORTED = "supported"
INFERENCE_MIXED = "mixed"
INFERENCE_CONTRADICTED = "contradicted"
INFERENCE_INSUFFICIENT = "insufficient"
GAP_INSUFFICIENT = "insufficient"
GAP_OTHER = "other"


@dataclass(frozen=True)
class StrategyThemeJudgment:
    theme: str
    inference: str
    qualification_codes: tuple[str, ...]
    counterexample_ids: tuple[int, ...]
    featured_disclosures: tuple[HistoricalStrategyDisclosure, ...]
    objective_disclosures: tuple[HistoricalStrategyDisclosure, ...]


@dataclass(frozen=True)
class HistoricalStrategyJudgment:
    themes: tuple[StrategyThemeJudgment, ...]
    verdict_groups: dict[str, tuple[str, ...]]
    has_counterexamples: bool
    productivity_gap_kind: str
    has_deferred_spsf: bool
    limit_codes: tuple[str, ...]


def _featured_disclosure(
    disclosures: tuple[HistoricalStrategyDisclosure, ...],
) -> HistoricalStrategyDisclosure:
    for role in _ROLE_PRIORITY:
        for item in disclosures:
            if item.role == role:
                return item
    return disclosures[0]


def select_featured_disclosures(
    disclosures: tuple[HistoricalStrategyDisclosure, ...],
) -> tuple[tuple[HistoricalStrategyDisclosure, ...], tuple[HistoricalStrategyDisclosure, ...]]:
    featured = [
        item for item in disclosures if item.role in (ROLE_STRATEGY, ROLE_OPERATING_USE)
    ]
    if not featured:
        featured = [_featured_disclosure(disclosures)]
    objectives = tuple(
        item
        for item in disclosures
        if item.role == ROLE_OBJECTIVE and item not in featured
    )
    return tuple(featured), objectives


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


def selected_counterexample_ids(test: RevenueDriverHypothesisTest) -> tuple[int, ...]:
    return tuple(
        index
        for index, item in enumerate(test.observations)
        if item.counterexample
    )


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


def interpret_historical_strategy(
    tests: tuple[RevenueDriverHypothesisTest, ...],
) -> HistoricalStrategyJudgment:
    themes = []
    groups: dict[str, list[str]] = {
        VERDICT_SUPPORTED: [],
        VERDICT_MIXED: [],
        VERDICT_CONTRADICTED: [],
        VERDICT_INSUFFICIENT: [],
    }
    any_counter = False
    for test in tests:
        featured, objectives = select_featured_disclosures(test.disclosures)
        themes.append(
            StrategyThemeJudgment(
                theme=test.theme,
                inference=select_verdict_inference(test),
                qualification_codes=qualification_codes(test),
                counterexample_ids=selected_counterexample_ids(test),
                featured_disclosures=featured,
                objective_disclosures=objectives,
            )
        )
        groups.setdefault(test.verdict, []).append(test.theme)
        if selected_counterexample_ids(test):
            any_counter = True
    deferred = any(
        has_deferred_spsf(test) for test in tests if test.theme == THEME_PRODUCTIVITY
    )
    limits = [LIMIT_HISTORY, LIMIT_UNTESTED]
    if deferred:
        limits.append(LIMIT_DEFERRED_SPSF)
    return HistoricalStrategyJudgment(
        themes=tuple(themes),
        verdict_groups={key: tuple(value) for key, value in groups.items()},
        has_counterexamples=any_counter,
        productivity_gap_kind=productivity_gap_kind(tests),
        has_deferred_spsf=deferred,
        limit_codes=tuple(limits),
    )
