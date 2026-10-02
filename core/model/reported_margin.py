"""Compatibility façade. Sequences reported-margin compute, interpret, and wording."""

from __future__ import annotations

from datetime import date

from core.data.interface import StandardizedFinancials
from composer.reported_margin import AMOUNT_BRIDGE_CONVENTION
from director.driver_assessment import complete_reported_margin_series
from modeler.reported_margin import (
    ACQUISITION_EXPENSE_CONCEPT,
    AMORTIZATION_CONCEPT,
    AMOUNT_BRIDGE_FORMULA,
    AMOUNT_RECONSTRUCTION_TOLERANCE,
    EXPENSE_PRESENTATION_POSITIVE,
    EXPENSE_PRESENTATION_SIGNED,
    GAIN_ON_DISPOSAL_CONCEPT,
    GROSS_PROFIT_CONCEPT,
    IMPAIRMENT_CONCEPT,
    KIND_ATTRIBUTED_EXPLANATION,
    KIND_CAUSAL,
    KIND_IDENTITY,
    KIND_OBSERVED,
    KIND_REPORTED_FACT,
    KIND_UNESTABLISHED,
    OPERATING_PROFIT_CONCEPT,
    OTHER_OPERATING_CONCEPTS,
    PUBLICATION_AMOUNT_TOLERANCE,
    PUBLICATION_RATIO_TOLERANCE,
    RATIO_RECONSTRUCTION_TOLERANCE,
    REVENUE_CONCEPT,
    SGA_CONCEPT,
    MarginRelationshipAssessment,
    ReportedMarginAvailability,
    ReportedMarginSeries,
    ReportedMarginSources,
    analytical_expense,
    expense_presentation_factor,
    expense_presentation_factor_for_sources,
    gross_margin_applicable,
    gross_margin_change_applicable,
    net_operating_expense_burden_applicable,
    net_operating_expense_burden_change_applicable,
    publication_reconstruction_allowed,
    reconstructed_operating_margin_change_applicable,
    reported_margin_applicable,
    reported_margin_availability,
    reported_operating_margin_applicable,
    residual_blocks_reconstruction_claim,
    resolve_reported_margin_sources,
)


def compute_reported_margin_series(
    financials: StandardizedFinancials,
    periods: list[date],
) -> ReportedMarginSeries:
    return complete_reported_margin_series(financials, periods)


__all__ = (
    "ACQUISITION_EXPENSE_CONCEPT",
    "AMORTIZATION_CONCEPT",
    "AMOUNT_BRIDGE_CONVENTION",
    "AMOUNT_BRIDGE_FORMULA",
    "AMOUNT_RECONSTRUCTION_TOLERANCE",
    "EXPENSE_PRESENTATION_POSITIVE",
    "EXPENSE_PRESENTATION_SIGNED",
    "GAIN_ON_DISPOSAL_CONCEPT",
    "GROSS_PROFIT_CONCEPT",
    "IMPAIRMENT_CONCEPT",
    "KIND_ATTRIBUTED_EXPLANATION",
    "KIND_CAUSAL",
    "KIND_IDENTITY",
    "KIND_OBSERVED",
    "KIND_REPORTED_FACT",
    "KIND_UNESTABLISHED",
    "OPERATING_PROFIT_CONCEPT",
    "OTHER_OPERATING_CONCEPTS",
    "PUBLICATION_AMOUNT_TOLERANCE",
    "PUBLICATION_RATIO_TOLERANCE",
    "RATIO_RECONSTRUCTION_TOLERANCE",
    "REVENUE_CONCEPT",
    "SGA_CONCEPT",
    "MarginRelationshipAssessment",
    "ReportedMarginAvailability",
    "ReportedMarginSeries",
    "ReportedMarginSources",
    "analytical_expense",
    "compute_reported_margin_series",
    "expense_presentation_factor",
    "expense_presentation_factor_for_sources",
    "gross_margin_applicable",
    "gross_margin_change_applicable",
    "net_operating_expense_burden_applicable",
    "net_operating_expense_burden_change_applicable",
    "publication_reconstruction_allowed",
    "reconstructed_operating_margin_change_applicable",
    "reported_margin_applicable",
    "reported_margin_availability",
    "reported_operating_margin_applicable",
    "residual_blocks_reconstruction_claim",
    "resolve_reported_margin_sources",
)
