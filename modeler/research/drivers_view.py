"""Numerical Driver assembly. No selection, interpretation, or wording."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
import re

from core.data.historical_operating_kpis import FAMILY_COMPARABLE_SALES_GROWTH
from core.data.interface import StandardizedFinancials
from modeler.geographic_segment import (
    compute_geographic_segment_series,
    geographic_segment_applicable,
)
from modeler.inventory_analysis import (
    compute_inventory_analysis_series,
    inventory_analysis_applicable,
)
from modeler.line_resolver import MissingLineError, resolve_line
from modeler.management_kpi import compute_management_kpi_series, management_kpi_applicable
from modeler.operating_kpi import compute_operating_kpi_series, operating_kpi_applicable
from modeler.operating_kpi_relationships import (
    compute_operating_kpi_revenue_store_relationship,
)
from modeler.period_axis import PeriodAxisError, canonical_fiscal_periods
from modeler.ratio_values import is_source_unavailable
from modeler.revenue_per_store import compute_revenue_per_store_series
from extractor.data.historical_strategy import (
    ROLE_ATTRIBUTION,
    THEME_COMPARABLE_SALES,
)
from modeler.reported_margin import (
    MarginRelationshipAssessment,
    compute_reported_margin_series as compute_reported_margin_numeric,
    publication_reconstruction_allowed,
    reported_operating_margin_applicable,
)
from modeler.research.cfo import _is_cfo_component
from modeler.research.records import ResearchSelection
from modeler.revenue_driver import (
    compute_revenue_driver_analysis as compute_revenue_driver_numeric,
    revenue_driver_applicable,
)


def financial_drivers_applicable(financials: StandardizedFinancials) -> bool:
    """Financial Drivers publish from verified income-statement history."""
    try:
        axis = canonical_fiscal_periods(financials)
        if not axis:
            return False
        resolve_line(financials.income_statement, "revenue", required=True)
        resolve_line(financials.income_statement, "operating_profit", required=True)
    except (MissingLineError, PeriodAxisError, ValueError):
        return False
    return True


def numeric(value) -> float | None:
    if value is None or is_source_unavailable(value) or isinstance(value, str):
        return None
    return float(value)


def attribution_amount(text: str) -> str | None:
    match = re.search(
        r"approximately\s+\$[0-9]+(?:\.[0-9]+)?\s+million",
        text,
        flags=re.IGNORECASE,
    )
    return match.group(0) if match else None


def attributions_from_financials(
    financials: StandardizedFinancials,
) -> tuple["ManagementAttribution", ...]:
    data = financials.historical_strategy
    if data is None:
        return ()
    items: list[ManagementAttribution] = []
    for disclosure in data.disclosures:
        if disclosure.role != ROLE_ATTRIBUTION:
            continue
        items.append(
            ManagementAttribution(
                period=disclosure.period,
                theme=disclosure.theme,
                text=disclosure.text,
                source_file=disclosure.source_file,
                page_reference=disclosure.page_reference,
                section=disclosure.section,
                approximate_amount=attribution_amount(disclosure.text),
            )
        )
    return tuple(items)


def geo_amount_changes(
    levels: dict,
    axis: tuple[date, ...],
    identities: tuple[str, ...],
) -> tuple[dict[str, float | None], ...]:
    rows: list[dict[str, float | None]] = []
    for index, period in enumerate(axis):
        current = levels.get(period) or {}
        prior = levels.get(axis[index - 1]) if index else None
        row: dict[str, float | None] = {}
        for identity in identities:
            now = numeric(current.get(identity))
            was = None if prior is None else numeric(prior.get(identity))
            row[identity] = None if now is None or was is None else now - was
        rows.append(row)
    return tuple(rows)


def mapped_numeric(mapping: dict, axis: tuple[date, ...]) -> tuple[float | None, ...]:
    return tuple(numeric(mapping.get(period)) for period in axis)


def cash_series(
    financials: StandardizedFinancials, axis: tuple[date, ...]
) -> tuple[
    tuple[float | None, ...],
    tuple[float | None, ...],
    tuple[float | None, ...],
    tuple[float | None, ...],
    tuple[float | None, ...],
]:
    cfo_item = resolve_line(
        financials.cash_flow, "operating_cash_flow", required=False
    ).item
    ni_item = resolve_line(financials.income_statement, "net_income", required=False).item
    cfo = tuple(
        None if cfo_item is None else numeric(cfo_item.values.get(period))
        for period in axis
    )
    ni = tuple(
        None if ni_item is None else numeric(ni_item.values.get(period))
        for period in axis
    )
    component_sum: list[float | None] = [None]
    for index in range(1, len(axis)):
        total = 0.0
        known = False
        for item in financials.cash_flow:
            if not _is_cfo_component(item.concept):
                continue
            current = numeric(item.values.get(axis[index]))
            prior = numeric(item.values.get(axis[index - 1]))
            if current is None or prior is None:
                continue
            total += current - prior
            known = True
        component_sum.append(total if known else None)
    change = adjacent_numeric_changes(cfo)
    remainder = tuple(
        None if item is None or summed is None else item - summed
        for item, summed in zip(change or (), tuple(component_sum))
    )
    return ni, cfo, change or tuple(None for _ in axis), tuple(component_sum), remainder


def adjacent_numeric_changes(
    values: tuple[float | str | None, ...] | None,
) -> tuple[float | None, ...] | None:
    if values is None:
        return None
    changes: list[float | None] = [None]
    for index in range(1, len(values)):
        current = numeric(values[index])
        prior = numeric(values[index - 1])
        if current is None or prior is None:
            changes.append(None)
        else:
            changes.append(current - prior)
    return tuple(changes)


_JAN31_FOLLOWING_YEAR = "Sunday closest to January 31 of the following year"
_EXCLUDED_EXTRA_WEEK = "excluded"


def label_for(financials: StandardizedFinancials, period: date) -> str:
    for item in financials.periods:
        if item.end_date == period:
            return item.label
    return period.isoformat()


def fifty_three_week_period(
    financials: StandardizedFinancials, axis: tuple[date, ...]
) -> date | None:
    data = financials.historical_operating_kpis
    if data is None:
        return None
    found = {
        item.period
        for item in data.management_observations
        if item.period in axis and item.calendar_week_adjustment == _EXCLUDED_EXTRA_WEEK
    }
    if len(found) != 1:
        return None
    return next(iter(found))


def issuer_fiscal_name(
    financials: StandardizedFinancials, period: date
) -> str | None:
    data = financials.historical_operating_kpis
    if data is None:
        return None
    for item in data.management_observations:
        if item.period != period:
            continue
        if _JAN31_FOLLOWING_YEAR not in item.calendar_reporting_basis:
            continue
        token = fiscal_year_token(label_for(financials, period))
        if not token.isdigit():
            return None
        return f"fiscal {token}"
    return None


def fiscal_year_token(label: str) -> str:
    text = label.casefold().replace("fiscal ", "").replace("fy", "").strip()
    return text


def date_text(period: date) -> str:
    return period.strftime("%-d %B %Y")


@dataclass(frozen=True)
class ComparableSalesPoint:
    period: date
    percent: float
    population: str
    basis: str


@dataclass(frozen=True)
class ManagementAttribution:
    period: date
    theme: str
    text: str
    source_file: str
    page_reference: str
    section: str
    approximate_amount: str | None = None


@dataclass(frozen=True)
class DriversView:
    """Numbers for Markdown and figures; all from the same BAV compute path."""

    company_name: str
    display_name: str
    currency: str
    units: str
    periods: tuple[date, ...]
    labels: tuple[str, ...]
    revenue: tuple[float, ...]
    operating_profit: tuple[float, ...]
    operating_margin: tuple[float, ...]
    gross_margin: tuple[float, ...]
    net_operating_expense_burden: tuple[float, ...]
    gross_margin_change: tuple[float | None, ...]
    net_operating_expense_burden_change: tuple[float | None, ...]
    operating_margin_change: tuple[float | None, ...]
    stores: tuple[float, ...]
    revenue_growth: tuple[float | None, ...]
    store_growth: tuple[float | None, ...]
    revenue_per_store: tuple[float, ...]
    comparable_sales: tuple[ComparableSalesPoint, ...]
    store_only_comparable_sales: ComparableSalesPoint | None
    geo_identities: tuple[str, ...]
    geo_contributions: tuple[dict[str, float | None], ...]
    consolidated_revenue_growth: tuple[float | None, ...]
    fifty_three_week_period: date | None = None
    revenue_per_store_growth: tuple[float | None, ...] | None = None
    issuer_fiscal_name: str | None = None
    sga: tuple[float | None, ...] | None = None
    impairment: tuple[float | None, ...] | None = None
    other_operating_items: tuple[float | None, ...] | None = None
    sga_ratio: tuple[float | None, ...] | None = None
    impairment_ratio: tuple[float | None, ...] | None = None
    other_operating_ratio: tuple[float | None, ...] | None = None
    operating_margin_residual: tuple[float | None, ...] | None = None
    operating_profit_residual: tuple[float | None, ...] | None = None
    gross_profit_change: tuple[float | None, ...] | None = None
    gross_profit_revenue_effect: tuple[float | None, ...] | None = None
    gross_profit_margin_effect: tuple[float | None, ...] | None = None
    gross_profit_interaction: tuple[float | None, ...] | None = None
    operating_profit_change: tuple[float | None, ...] | None = None
    reconstructed_operating_profit_change: tuple[float | None, ...] | None = None
    operating_profit_change_residual: tuple[float | None, ...] | None = None
    sga_change: tuple[float | None, ...] | None = None
    impairment_change: tuple[float | None, ...] | None = None
    other_operating_change: tuple[float | None, ...] | None = None
    reported_operating_margin_change: tuple[float | None, ...] | None = None
    reconstructed_component_operating_margin_change: tuple[float | None, ...] | None = None
    operating_margin_change_residual: tuple[float | None, ...] | None = None
    gross_margin_contribution: tuple[float | None, ...] | None = None
    sga_ratio_contribution: tuple[float | None, ...] | None = None
    impairment_ratio_contribution: tuple[float | None, ...] | None = None
    other_operating_ratio_contribution: tuple[float | None, ...] | None = None
    reconstructed_contribution_sum: tuple[float | None, ...] | None = None
    contribution_residual: tuple[float | None, ...] | None = None
    reconstruction_complete: tuple[bool | None, ...] | None = None
    amount_bridge_convention: str = ""
    geo_component_revenue: tuple[dict[str, float | None], ...] | None = None
    geo_reconstructed_revenue: tuple[float | None, ...] | None = None
    geo_reported_revenue: tuple[float | None, ...] | None = None
    geo_residual: tuple[float | None, ...] | None = None
    geo_contribution_amounts: tuple[dict[str, float | None], ...] | None = None
    geo_contribution_residual: tuple[float | None, ...] | None = None
    footprint_store_effect: tuple[float | None, ...] | None = None
    footprint_intensity_effect: tuple[float | None, ...] | None = None
    footprint_interaction: tuple[float | None, ...] | None = None
    footprint_residual: tuple[float | None, ...] | None = None
    footprint_reconstructed_change: tuple[float | None, ...] | None = None
    relationship_findings: tuple[str, ...] = ()
    assessments: tuple[MarginRelationshipAssessment, ...] = ()
    margin_explanation: str = ""
    geo_profit_changes: tuple[dict[str, float | None], ...] | None = None
    geo_reconciling_profit_change: tuple[float | None, ...] | None = None
    geo_consolidated_profit_change: tuple[float | None, ...] | None = None
    geo_profit_change_residual: tuple[float | None, ...] | None = None
    geo_revenue_amount_changes: tuple[dict[str, float | None], ...] | None = None
    net_income: tuple[float | None, ...] | None = None
    net_income_change: tuple[float | None, ...] | None = None
    cfo: tuple[float | None, ...] | None = None
    cfo_change: tuple[float | None, ...] | None = None
    cfo_component_sum: tuple[float | None, ...] | None = None
    cfo_unexplained: tuple[float | None, ...] | None = None
    inventory: tuple[float | None, ...] | None = None
    inventory_change: tuple[float | None, ...] | None = None
    cf_inventory_adjustment: tuple[float | None, ...] | None = None
    attributions: tuple[ManagementAttribution, ...] = ()
    selection: ResearchSelection | None = None

    def period_ended(self, period: date) -> str:
        return date_text(period)


def revenue_growth_from_levels(
    revenue: tuple[float, ...],
) -> tuple[float | None, ...]:
    growth: list[float | None] = [None]
    for index in range(1, len(revenue)):
        prior = revenue[index - 1]
        current = revenue[index]
        growth.append(None if not prior else current / prior - 1.0)
    return tuple(growth)


def revenue_per_store_growth_from_levels(
    levels: tuple[float | str | None, ...],
) -> tuple[float | None, ...]:
    """Adjacent intensity growth. Missing or zero prior values stay missing."""
    if not levels:
        return ()
    growth: list[float | None] = [None]
    for index in range(1, len(levels)):
        prior = numeric(levels[index - 1])
        current = numeric(levels[index])
        if prior is None or current is None or not prior:
            growth.append(None)
        else:
            growth.append(current / prior - 1.0)
    return tuple(growth)


def unique_assessments(
    items: tuple[MarginRelationshipAssessment, ...],
) -> tuple[MarginRelationshipAssessment, ...]:
    seen: set[str] = set()
    unique: list[MarginRelationshipAssessment] = []
    for item in items:
        if not item.name or item.name in seen:
            continue
        seen.add(item.name)
        unique.append(item)
    return tuple(unique)


def latest_growth_index(view: DriversView) -> int:
    for index in range(len(view.periods) - 1, -1, -1):
        if index < len(view.revenue_growth) and view.revenue_growth[index] is not None:
            return index
    return max(len(view.periods) - 1, 0)


def operating_profit_change(view: DriversView, latest: int) -> float | None:
    if view.geo_consolidated_profit_change is not None:
        if latest < len(view.geo_consolidated_profit_change):
            return view.geo_consolidated_profit_change[latest]
        return None
    if view.operating_profit_change and latest < len(view.operating_profit_change):
        value = view.operating_profit_change[latest]
        if value is not None:
            return value
    if latest > 0 and latest < len(view.operating_profit):
        return view.operating_profit[latest] - view.operating_profit[latest - 1]
    return None


def series_at(values, latest: int):
    if values is None or latest >= len(values):
        return None
    return values[latest]


def margin_reconstruction_complete(view: DriversView, latest: int) -> bool:
    """Gate exact reconstruction claims on available components and residuals."""
    if series_at(view.sga_ratio, latest) is None:
        return False
    residuals = (
        series_at(view.contribution_residual, latest),
        series_at(view.operating_margin_residual, latest),
        series_at(view.operating_margin_change_residual, latest),
    )
    available = tuple(item for item in residuals if item is not None)
    if not available:
        return False
    return publication_reconstruction_allowed(*available, kind="ratio")


def completed_intensity_growth(view: DriversView, latest: int) -> float | None:
    growth = view.revenue_per_store_growth
    if growth is None:
        raise ValueError("completed intensity growth")
    if latest < 0 or latest >= len(growth):
        return None
    return growth[latest]


def completed_reconstruction(view: DriversView, latest: int) -> bool:
    results = view.reconstruction_complete
    if results is None:
        raise ValueError("completed reconstruction")
    if latest < 0 or latest >= len(results) or results[latest] is None:
        raise ValueError("completed reconstruction")
    return bool(results[latest])


def _compsales_observations(analysis) -> tuple:
    if analysis is None:
        return ()
    for item in getattr(analysis, "tests", ()) or ():
        if getattr(item, "theme", None) == THEME_COMPARABLE_SALES:
            return item.observations
    for item in getattr(analysis, "theme_observations", ()) or ():
        if getattr(item, "theme", None) == THEME_COMPARABLE_SALES:
            return item.observations
    return ()


def assemble_drivers_view(
    financials: StandardizedFinancials,
    display_name: str,
    *,
    assessments: tuple[MarginRelationshipAssessment, ...] = (),
    margins=None,
    analysis=None,
) -> DriversView:
    if not financial_drivers_applicable(financials):
        raise ValueError("Drivers requires verified revenue and operating-profit history")
    axis = canonical_fiscal_periods(financials)
    revenue_item = resolve_line(financials.income_statement, "revenue", required=True).item
    operating_item = resolve_line(
        financials.income_statement, "operating_profit", required=True
    ).item
    revenue = tuple(float(revenue_item.values[period]) for period in axis)
    operating_profit = tuple(float(operating_item.values[period]) for period in axis)
    stores_vals: tuple[float, ...] = ()
    store_growth: tuple[float | None, ...] = tuple(None for _ in axis)
    revenue_growth = revenue_growth_from_levels(revenue)
    revenue_per_store: tuple[float, ...] = ()
    if operating_kpi_applicable(financials):
        stores = compute_operating_kpi_series(financials, list(axis))
        relationship = compute_operating_kpi_revenue_store_relationship(
            financials, list(axis)
        )
        rps = compute_revenue_per_store_series(financials, list(axis))
        stores_vals = tuple(float(stores.period_end_count[period]) for period in axis)
        store_growth = tuple(
            numeric(relationship.store_count_growth[period]) for period in axis
        )
        revenue_growth = tuple(
            numeric(relationship.revenue_growth[period]) for period in axis
        )
        revenue_per_store = tuple(
            float(rps.period_end_revenue_per_store[period]) for period in axis
        )
    revenue_per_store_growth = (
        revenue_per_store_growth_from_levels(revenue_per_store)
        if revenue_per_store
        else tuple(None for _ in axis)
    )
    if margins is None and reported_operating_margin_applicable(financials):
        margins = compute_reported_margin_numeric(financials, list(axis))
    if analysis is None and revenue_driver_applicable(financials):
        analysis = compute_revenue_driver_numeric(financials)
    points: list[ComparableSalesPoint] = []
    seen: set[date] = set()
    for observation in _compsales_observations(analysis):
        percent = numeric(observation.inputs.get("comparable_sales_percent"))
        if percent is None or observation.period in seen:
            continue
        if observation.inputs.get("basis") != "reported":
            continue
        seen.add(observation.period)
        points.append(
            ComparableSalesPoint(
                observation.period,
                percent,
                str(observation.inputs.get("population") or ""),
                "reported",
            )
        )
    store_only = None
    if management_kpi_applicable(financials):
        series = compute_management_kpi_series(financials, list(axis))
        for identity in series.identities:
            item = series.series[identity]
            if item.family != FAMILY_COMPARABLE_SALES_GROWTH:
                continue
            if item.population != "company_operated_stores" or item.basis != "reported":
                continue
            for period in axis:
                value = numeric(item.reported_value.get(period))
                if value is None:
                    continue
                store_only = ComparableSalesPoint(
                    period, value, item.population, item.basis
                )
                break
    week_period = fifty_three_week_period(financials, tuple(axis))
    issuer_name = (
        issuer_fiscal_name(financials, week_period) if week_period is not None else None
    )
    geo = (
        compute_geographic_segment_series(financials)
        if geographic_segment_applicable(financials)
        else None
    )
    geo_recon = None if analysis is None else analysis.geographic_reconstruction
    footprint = None if analysis is None else analysis.footprint_identity
    empty_change = tuple(None for _ in axis)
    if margins is None:
        operating_margin = tuple(
            op / rev if rev else 0.0 for op, rev in zip(operating_profit, revenue)
        )
        gross_margin = ()
        burden = ()
        gm_change = empty_change
        burden_change = empty_change
        om_change_recon = empty_change
        reported_om_change = adjacent_numeric_changes(operating_margin)
        component_om_change = None
        om_change_residual = None
    else:
        operating_margin = tuple(float(value) for value in margins.reported_operating_margin)
        gross_margin = tuple(float(value) for value in (margins.gross_margin or ()))
        burden = tuple(float(value) for value in (margins.net_operating_expense_burden or ()))
        gm_change = tuple(numeric(value) for value in (margins.gross_margin_change or ()))
        burden_change = tuple(
            numeric(value) for value in (margins.net_operating_expense_burden_change or ())
        )
        om_change_recon = tuple(
            numeric(value)
            for value in (margins.reconstructed_operating_margin_change or ())
        )
        reported_om_change = adjacent_numeric_changes(margins.reported_operating_margin)
        component_om = margins.reconstructed_component_operating_margin
        component_om_change = (
            None if component_om is None else adjacent_numeric_changes(component_om)
        )
        om_change_residual = None
        if reported_om_change is not None and component_om_change is not None:
            om_change_residual = tuple(
                None
                if reported is None or rebuilt is None
                else reported - rebuilt
                for reported, rebuilt in zip(reported_om_change, component_om_change)
            )
    ni_series, cfo_values, cfo_change, cfo_sum, cfo_remainder = cash_series(
        financials, tuple(axis)
    )
    inv_series = (
        compute_inventory_analysis_series(financials, list(axis))
        if inventory_analysis_applicable(financials)
        else None
    )
    footprint_reconstructed_change = None
    if footprint is not None:
        footprint_reconstructed_change = tuple(
            None
            if store is None or intensity is None or interaction is None
            else store + intensity + interaction
            for store, intensity, interaction in zip(
                footprint.store_effect,
                footprint.intensity_effect,
                footprint.interaction,
            )
        )
    geo_identities = () if geo is None else geo.identities
    view = DriversView(
        company_name=financials.company_name,
        display_name=display_name,
        currency=financials.currency,
        units=financials.units,
        periods=tuple(axis),
        labels=tuple(label_for(financials, period) for period in axis),
        revenue=revenue,
        operating_profit=operating_profit,
        operating_margin=operating_margin,
        gross_margin=gross_margin,
        net_operating_expense_burden=burden,
        gross_margin_change=gm_change,
        net_operating_expense_burden_change=burden_change,
        operating_margin_change=om_change_recon,
        stores=stores_vals,
        revenue_growth=revenue_growth,
        store_growth=store_growth,
        revenue_per_store=revenue_per_store,
        comparable_sales=tuple(points),
        store_only_comparable_sales=store_only,
        geo_identities=geo_identities,
        geo_contributions=tuple(
            {
                identity: numeric(geo.revenue_growth_contribution[period][identity])
                for identity in geo_identities
            }
            for period in axis
        )
        if geo is not None
        else tuple({} for _ in axis),
        consolidated_revenue_growth=tuple(
            numeric(geo.consolidated_revenue_growth[period]) for period in axis
        )
        if geo is not None
        else empty_change,
        fifty_three_week_period=week_period,
        revenue_per_store_growth=revenue_per_store_growth,
        issuer_fiscal_name=issuer_name,
        sga=None if margins is None else margins.sga,
        impairment=None if margins is None else margins.impairment,
        other_operating_items=None if margins is None else margins.other_operating_items,
        sga_ratio=tuple(numeric(value) for value in ((None if margins is None else margins.sga_ratio) or ())),
        impairment_ratio=tuple(
            numeric(value)
            for value in ((None if margins is None else margins.impairment_ratio) or ())
        ),
        other_operating_ratio=tuple(
            numeric(value)
            for value in ((None if margins is None else margins.other_operating_ratio) or ())
        ),
        operating_margin_residual=tuple(
            numeric(value)
            for value in ((None if margins is None else margins.operating_margin_residual) or ())
        ),
        operating_profit_residual=None if margins is None else margins.operating_profit_residual,
        gross_profit_change=None if margins is None else margins.gross_profit_change,
        gross_profit_revenue_effect=None if margins is None else margins.gross_profit_revenue_effect,
        gross_profit_margin_effect=None if margins is None else margins.gross_profit_margin_effect,
        gross_profit_interaction=None if margins is None else margins.gross_profit_interaction,
        operating_profit_change=None if margins is None else margins.operating_profit_change,
        reconstructed_operating_profit_change=(
            None if margins is None else margins.reconstructed_operating_profit_change
        ),
        operating_profit_change_residual=(
            None if margins is None else margins.operating_profit_change_residual
        ),
        sga_change=None if margins is None else margins.sga_change,
        impairment_change=None if margins is None else margins.impairment_change,
        other_operating_change=None if margins is None else margins.other_operating_change,
        reported_operating_margin_change=reported_om_change,
        reconstructed_component_operating_margin_change=component_om_change,
        operating_margin_change_residual=om_change_residual,
        gross_margin_contribution=tuple(
            numeric(value)
            for value in ((None if margins is None else margins.gross_margin_contribution) or ())
        ),
        sga_ratio_contribution=tuple(
            numeric(value)
            for value in ((None if margins is None else margins.sga_ratio_contribution) or ())
        ),
        impairment_ratio_contribution=tuple(
            numeric(value)
            for value in (
                (None if margins is None else margins.impairment_ratio_contribution) or ()
            )
        ),
        other_operating_ratio_contribution=tuple(
            numeric(value)
            for value in (
                (None if margins is None else margins.other_operating_ratio_contribution)
                or ()
            )
        ),
        reconstructed_contribution_sum=tuple(
            numeric(value)
            for value in (
                (None if margins is None else margins.reconstructed_contribution_sum) or ()
            )
        ),
        contribution_residual=tuple(
            numeric(value)
            for value in ((None if margins is None else margins.contribution_residual) or ())
        ),
        amount_bridge_convention="" if margins is None else margins.amount_bridge_convention,
        geo_component_revenue=None if geo_recon is None else geo_recon.component_revenue,
        geo_reconstructed_revenue=(
            None if geo_recon is None else geo_recon.reconstructed_revenue
        ),
        geo_reported_revenue=None if geo_recon is None else geo_recon.reported_revenue,
        geo_residual=None if geo_recon is None else geo_recon.residual,
        geo_contribution_amounts=(
            None if geo_recon is None else geo_recon.contribution_amounts
        ),
        geo_contribution_residual=(
            None if geo_recon is None else geo_recon.contribution_residual
        ),
        footprint_store_effect=None if footprint is None else footprint.store_effect,
        footprint_intensity_effect=(
            None if footprint is None else footprint.intensity_effect
        ),
        footprint_interaction=None if footprint is None else footprint.interaction,
        footprint_residual=None if footprint is None else footprint.change_residual,
        footprint_reconstructed_change=footprint_reconstructed_change,
        relationship_findings=(),
        assessments=assessments,
        margin_explanation="",
        geo_profit_changes=tuple(
            {
                identity: numeric(geo.operating_profit_amount_change[period][identity])
                for identity in geo_identities
            }
            for period in axis
        )
        if geo is not None
        else None,
        geo_reconciling_profit_change=(
            None
            if geo is None
            else mapped_numeric(geo.reconciling_operating_profit_amount_change, tuple(axis))
        ),
        geo_consolidated_profit_change=(
            None
            if geo is None
            else mapped_numeric(
                geo.consolidated_operating_profit_amount_change, tuple(axis)
            )
        ),
        geo_profit_change_residual=(
            None
            if geo is None
            else mapped_numeric(geo.operating_profit_amount_change_residual, tuple(axis))
        ),
        geo_revenue_amount_changes=(
            None
            if geo is None
            else geo_amount_changes(geo.net_revenue, tuple(axis), geo.identities)
        ),
        net_income=ni_series,
        net_income_change=adjacent_numeric_changes(ni_series),
        cfo=cfo_values,
        cfo_change=cfo_change,
        cfo_component_sum=cfo_sum,
        cfo_unexplained=cfo_remainder,
        inventory=None if inv_series is None else tuple(numeric(value) for value in inv_series.inventories),
        inventory_change=None if inv_series is None else tuple(numeric(value) for value in inv_series.inventory_change),
        cf_inventory_adjustment=(
            None
            if inv_series is None
            else tuple(numeric(value) for value in inv_series.change_in_inventories)
        ),
        attributions=attributions_from_financials(financials),
    )
    return replace(
        view,
        reconstruction_complete=tuple(
            margin_reconstruction_complete(view, index)
            for index in range(len(view.periods))
        ),
    )
