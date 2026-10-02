"""Compatibility façade. Sequences revenue-driver compute, interpret, and wording."""

from __future__ import annotations

from datetime import date

from modeler.data.interface import StandardizedFinancials
from composer.revenue_driver import (
    ADDITIONAL_COMPSALES_HISTORY,
    ADDITIONAL_SPSF,
    FAILED_COMPSALES,
    FAILED_GEOGRAPHIC,
    FAILED_SPSF_GROWTH,
    FAILED_STORE_GROWTH,
    FOOTPRINT_IDENTITY_CONVENTION,
    SCOPE_NOTE,
)
from director.driver_assessment import complete_revenue_driver_analysis
from extractor.data.historical_strategy import (
    THEME_COMPARABLE_SALES,
    THEME_GEOGRAPHIC_GROWTH,
    THEME_PRODUCTIVITY,
    THEME_STORE_EXPANSION,
)
from interpreter.revenue_driver import (
    HYPOTHESIS_COMPARABLE_SALES,
    HYPOTHESIS_GEOGRAPHIC,
    HYPOTHESIS_PRODUCTIVITY,
    HYPOTHESIS_STORE_EXPANSION,
    MECHANISM_COMPARABLE_SALES,
    MECHANISM_GEOGRAPHIC,
    MECHANISM_PRODUCTIVITY,
    MECHANISM_STORE_EXPANSION,
    SUPPORTED_VERDICTS,
    VERDICT_CONTRADICTED,
    VERDICT_INSUFFICIENT,
    VERDICT_MIXED,
    VERDICT_SUPPORTED,
)
from modeler.revenue_driver import (
    CALCULATION_KIND,
    FOOTPRINT_IDENTITY_FORMULA,
    FootprintIntensityIdentity,
    GeographicRevenueReconstruction,
    RevenueDriverAnalysis,
    RevenueDriverHypothesisTest,
    RevenueDriverPeriodObservation,
    revenue_driver_applicable,
    strategy_synthesis_applicable,
)


def compute_revenue_driver_analysis(
    financials: StandardizedFinancials,
    periods: list[date] | None = None,
) -> RevenueDriverAnalysis:
    return complete_revenue_driver_analysis(financials, periods)
