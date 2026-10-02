"""Thin Director orchestration for Driver research."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from composer.research.drivers import finding_sentence, publish_completed_drivers
from composer.research.selection import select_driver_argument
from core.data.interface import StandardizedFinancials
from core.model.period_axis import canonical_fiscal_periods
from interpreter.selection import interpret_driver_selection
from modeler.reported_margin import reported_operating_margin_applicable
from modeler.research.drivers_view import (
    assemble_drivers_view as assemble_numeric_drivers_view,
    unique_assessments,
)
from modeler.revenue_driver import revenue_driver_applicable


def complete_drivers_view(
    financials: StandardizedFinancials, display_name: str
):
    """Obtain calculations and assessments, interpret, then attach selection."""
    from director.driver_assessment import (
        complete_reported_margin_series,
        complete_revenue_driver_analysis,
    )

    axis = list(canonical_fiscal_periods(financials))
    margins = (
        complete_reported_margin_series(financials, axis)
        if reported_operating_margin_applicable(financials)
        else None
    )
    analysis = (
        complete_revenue_driver_analysis(financials)
        if revenue_driver_applicable(financials)
        else None
    )
    assessments = unique_assessments(
        (() if analysis is None else analysis.assessments)
        + (() if margins is None else margins.assessments)
    )
    view = assemble_numeric_drivers_view(
        financials,
        display_name,
        assessments=assessments,
        margins=margins,
        analysis=analysis,
    )
    view = replace(
        view, relationship_findings=tuple(finding_sentence(item) for item in assessments)
    )
    interpretation = interpret_driver_selection(view)
    return replace(view, selection=select_driver_argument(view, interpretation))


def complete_driver_selection(view):
    return select_driver_argument(view, interpret_driver_selection(view))


def publish_drivers(
    financials: StandardizedFinancials,
    output: Path,
    *,
    display_name: str,
    accent: str | None = None,
):
    view = complete_drivers_view(financials, display_name)
    return publish_completed_drivers(view, output, accent=accent)
