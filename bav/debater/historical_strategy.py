"""Featured-disclosure and counterexample selection for historical strategy."""

from __future__ import annotations

from dataclasses import dataclass

from bav.extractor.data.historical_strategy import (
    ROLE_OBJECTIVE,
    ROLE_OPERATING_USE,
    ROLE_STRATEGY,
    THEME_PRODUCTIVITY,
    HistoricalStrategyDisclosure,
)
from bav.inferer.historical_strategy import (
    LIMIT_DEFERRED_SPSF,
    LIMIT_HISTORY,
    LIMIT_UNTESTED,
    has_deferred_spsf,
    productivity_gap_kind,
    qualification_codes,
    select_verdict_inference,
)
from bav.inferer.revenue_driver import (
    VERDICT_CONTRADICTED,
    VERDICT_INSUFFICIENT,
    VERDICT_MIXED,
    VERDICT_SUPPORTED,
)
from bav.modeler.revenue_driver import RevenueDriverHypothesisTest

_ROLE_PRIORITY = (ROLE_STRATEGY, ROLE_OPERATING_USE, ROLE_OBJECTIVE)


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


def selected_counterexample_ids(test: RevenueDriverHypothesisTest) -> tuple[int, ...]:
    return tuple(
        index
        for index, item in enumerate(test.observations)
        if item.counterexample
    )


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
