"""Compatibility façade. Sequences historical-strategy interpretation and wording."""

from __future__ import annotations

from composer.overview import (
    DEFERRED_SPSF_LINK,
    PROFESSIONAL_FALLBACK,
    THEME_LABELS,
    THEME_SCHEDULES,
    UNTESTED_INITIATIVES,
    WHAT_HISTORY_ESTABLISHES,
    HistoricalStrategySynthesis,
    StrategyFindingInterpretation,
)
from director.driver_assessment import complete_historical_strategy_synthesis
from modeler.revenue_driver import (
    RevenueDriverAnalysis,
    strategy_synthesis_applicable,
)


def compute_historical_strategy_synthesis(
    financials,
    analysis: RevenueDriverAnalysis | None = None,
) -> HistoricalStrategySynthesis:
    return complete_historical_strategy_synthesis(financials, analysis)
