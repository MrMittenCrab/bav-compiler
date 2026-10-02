"""Thin Director sequence: Modeler compute → Interpreter interpret → Composer word."""

from __future__ import annotations

from dataclasses import replace
from datetime import date

from core.data.interface import StandardizedFinancials
from composer.reported_margin import (
    AMOUNT_BRIDGE_CONVENTION,
    word_disclosed_charges,
    word_gross_profit_bridge,
    word_latest_movement,
    word_margin_contributions,
    word_margin_identity,
    word_unsupported_mix,
)
from composer.revenue_driver import (
    SCOPE_NOTE,
    word_footprint_identity,
    word_identity_assessment,
    word_revenue_assessment,
    word_theme,
)
from interpreter.historical_strategy import interpret_historical_strategy
from interpreter.reported_margin import (
    interpret_disclosed_charges,
    interpret_latest_movement,
    interpret_unsupported_mix,
)
from interpreter.revenue_driver import interpret_revenue_assessment, interpret_theme
from modeler.reported_margin import (
    ReportedMarginSeries,
    _gross_profit_bridge_validity,
    _impairment_charge_observations,
    _latest_adjacent_movement,
    _margin_contribution_validity,
    _margin_identity_validity,
    compute_reported_margin_series as compute_reported_margin_numeric,
    reported_margin_applicable,
)
from modeler.revenue_driver import (
    RevenueDriverAnalysis,
    _identity_assessment,
    compute_revenue_driver_analysis as compute_revenue_driver_numeric,
    strategy_synthesis_applicable,
)


def complete_reported_margin_series(
    financials: StandardizedFinancials,
    periods: list[date],
) -> ReportedMarginSeries:
    series = compute_reported_margin_numeric(financials, periods)
    assessments = []
    identity = _margin_identity_validity(series)
    if identity is not None:
        assessments.append(word_margin_identity(identity))
    contributions = _margin_contribution_validity(series)
    if contributions is not None:
        assessments.append(word_margin_contributions(contributions))
    gp_bridge = _gross_profit_bridge_validity(series)
    if gp_bridge is not None:
        assessments.append(word_gross_profit_bridge(gp_bridge))
    charges = _impairment_charge_observations(series, periods)
    if charges is not None:
        assessments.append(
            word_disclosed_charges(charges, interpret_disclosed_charges(charges))
        )
    assessments.append(word_unsupported_mix(interpret_unsupported_mix()))
    latest = _latest_adjacent_movement(series)
    if latest is not None:
        assessments.append(
            word_latest_movement(latest, interpret_latest_movement(latest))
        )
    return replace(
        series,
        assessments=tuple(assessments),
        amount_bridge_convention=AMOUNT_BRIDGE_CONVENTION,
    )


def complete_revenue_driver_analysis(
    financials: StandardizedFinancials,
    periods: list[date] | None = None,
) -> RevenueDriverAnalysis:
    numeric = compute_revenue_driver_numeric(financials, periods)
    tests = []
    assessments = []
    for bundle in numeric.theme_observations:
        interpretation = interpret_theme(bundle)
        test = word_theme(interpretation)
        identity = _identity_assessment(
            bundle.theme,
            numeric.geographic_reconstruction,
            numeric.footprint_identity,
        )
        if identity is not None:
            assessment = word_identity_assessment(
                identity, test, numeric.footprint_identity
            )
        else:
            decision = interpret_revenue_assessment(interpretation)
            assessment = word_revenue_assessment(decision, test)
        test = replace(test, assessment=assessment)
        tests.append(test)
        assessments.append(assessment)
    margins = None
    if reported_margin_applicable(financials):
        margins = complete_reported_margin_series(
            financials, list(numeric.periods)
        )
        assessments.extend(margins.assessments)
    return replace(
        numeric,
        tests=tuple(tests),
        assessments=tuple(assessments),
        scope_note=SCOPE_NOTE,
        footprint_identity=word_footprint_identity(numeric.footprint_identity),
        theme_observations=numeric.theme_observations,
    )


def word_historical_strategy(*args, **kwargs):
    from composer.overview import compute_historical_strategy_synthesis

    return compute_historical_strategy_synthesis(*args, **kwargs)


def complete_historical_strategy_synthesis(
    financials: StandardizedFinancials,
    analysis: RevenueDriverAnalysis | None = None,
):
    if not strategy_synthesis_applicable(financials):
        raise ValueError("strategy synthesis requires admitted strategy disclosures")
    if analysis is None:
        analysis = complete_revenue_driver_analysis(financials)
    tests = analysis.tests
    if not tests:
        raise ValueError("strategy synthesis requires at least one driver test")
    judgment = interpret_historical_strategy(tests)
    return word_historical_strategy(financials, analysis, judgment)
