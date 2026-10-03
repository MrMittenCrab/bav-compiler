"""Disclosure-led historical revenue-driver tests from admitted evidence.

Generic methods. Issuer statements remain in source-bound company inputs.
Management statements are never treated as achieved outcomes. Revenue-growth
minus comparable-sales and revenue-growth minus store-growth results are
descriptive differences, not new-store contribution, organic growth, or
causal attribution. Total revenue divided by stores is an identity and cannot
independently demonstrate store productivity.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from bav.modeler.data.historical_operating_kpis import (
    FAMILY_COMPARABLE_SALES_GROWTH,
    FAMILY_SALES_PER_SQUARE_FOOT,
)
from bav.modeler.data.interface import (
    HistoricalManagementKpiDeferredDisagreement,
    StandardizedFinancials,
)
from bav.extractor.data.historical_strategy import (
    THEME_COMPARABLE_SALES,
    THEME_GEOGRAPHIC_GROWTH,
    THEME_PRODUCTIVITY,
    THEME_STORE_EXPANSION,
    HistoricalStrategyData,
    HistoricalStrategyDisclosure,
)
from bav.modeler.geographic_segment import (
    compute_geographic_segment_series,
    geographic_segment_applicable,
)
from bav.modeler.line_resolver import MissingLineError
from bav.modeler.management_kpi import (
    compute_management_kpi_series,
    management_kpi_applicable,
)
from bav.modeler.operating_kpi import compute_operating_kpi_series, operating_kpi_applicable
from bav.modeler.operating_kpi_relationships import (
    compute_operating_kpi_revenue_comparable_sales_relationship,
    compute_operating_kpi_revenue_sales_per_square_foot_relationship,
    compute_operating_kpi_revenue_store_relationship,
    operating_kpi_revenue_comparable_sales_relationship_applicable,
    operating_kpi_revenue_sales_per_square_foot_relationship_applicable,
    operating_kpi_revenue_store_relationship_applicable,
)
from bav.modeler.period_axis import PeriodAxisError, canonical_fiscal_periods
from bav.modeler.ratio_values import SOURCE_UNAVAILABLE, is_source_unavailable
from bav.modeler.reported_margin import KIND_IDENTITY, MarginRelationshipAssessment
from bav.modeler.revenue_per_store import (
    compute_revenue_per_store_series,
    revenue_per_store_applicable,
)

FOOTPRINT_IDENTITY_FORMULA = (
    "Company-wide revenue equals store count times company-wide revenue per "
    "store. The adjacent change uses prior intensity on the store-count "
    "change, prior store count on the intensity change, and an explicit "
    "interaction equal to the store-count change times the intensity change."
)

CALCULATION_KIND = "analyst-derived"
_QUALIFIER_FIELD_NAMES = (
    "population",
    "unit",
    "basis",
    "calendar_week_adjustment",
    "calendar_reporting_basis",
)


@dataclass(frozen=True)
class RevenueDriverPeriodObservation:
    """One aligned-period observation used by a hypothesis test."""

    period: date
    inputs: dict[str, float | str | None]
    consistent: bool | None
    note: str
    counterexample: bool = False
    mix_conflict: bool = False


@dataclass(frozen=True)
class RevenueDriverHypothesisTest:
    """One disclosure-led hypothesis and its historical test result."""

    theme: str
    hypothesis: str
    mechanism: str
    disclosures: tuple[HistoricalStrategyDisclosure, ...]
    admitted_inputs: tuple[str, ...]
    periods_tested: tuple[date, ...]
    sample_size: int
    observations: tuple[RevenueDriverPeriodObservation, ...]
    verdict: str
    finding: str
    limitations: tuple[str, ...]
    failed_requirement: str
    additional_evidence: str
    identity_notes: tuple[str, ...]
    assessment: MarginRelationshipAssessment | None = None
    qualification_codes: tuple[str, ...] = ()
    failed_requirement_code: str = ""
    additional_evidence_code: str = ""
    has_deferred_spsf: bool = False
    rps_increases: int = 0
    rps_declines: int = 0
    spsf_growth_available: bool = False
    compsales_ineligible: bool = False
    distinct_populations: tuple[tuple[str, tuple[date, ...]], ...] = ()
    spsf_missing_periods: tuple[date, ...] = ()
    spsf_unavailable: tuple[tuple[date, tuple[str, ...]], ...] = ()
    deferred_disagreements: tuple[HistoricalManagementKpiDeferredDisagreement, ...] = ()
    geographic_identities: tuple[str, ...] = ()


@dataclass(frozen=True)
class GeographicRevenueReconstruction:
    """Admitted geographic components versus consolidated revenue."""

    identities: tuple[str, ...]
    component_revenue: tuple[dict[str, float | None], ...]
    reconstructed_revenue: tuple[float | None, ...]
    reported_revenue: tuple[float | None, ...]
    residual: tuple[float | None, ...]
    contribution_amounts: tuple[dict[str, float | None], ...]
    growth_contributions: tuple[dict[str, float | None], ...]
    contribution_residual: tuple[float | None, ...]


@dataclass(frozen=True)
class FootprintIntensityIdentity:
    """Exact store-count × intensity identity for company-wide revenue."""

    stores: tuple[float | None, ...]
    intensity: tuple[float | None, ...]
    reconstructed_revenue: tuple[float | None, ...]
    reconstruction_residual: tuple[float | None, ...]
    store_effect: tuple[float | None, ...]
    intensity_effect: tuple[float | None, ...]
    interaction: tuple[float | None, ...]
    change_residual: tuple[float | None, ...]
    convention: str
    scope_note: str


@dataclass(frozen=True)
class RevenueDriverAnalysis:
    """Disclosure-led revenue-driver tests keyed by generic themes."""

    periods: tuple[date, ...]
    calculation_kind: str
    scope_note: str
    tests: tuple[RevenueDriverHypothesisTest, ...]
    geographic_reconstruction: GeographicRevenueReconstruction | None = None
    footprint_identity: FootprintIntensityIdentity | None = None
    assessments: tuple[MarginRelationshipAssessment, ...] = ()
    theme_observations: tuple[RevenueDriverThemeObservations, ...] = ()


@dataclass(frozen=True)
class RevenueDriverThemeObservations:
    """Numeric observations for one disclosure theme. Notes stay empty."""

    theme: str
    disclosures: tuple[HistoricalStrategyDisclosure, ...]
    admitted_inputs: tuple[str, ...]
    periods_tested: tuple[date, ...]
    sample_size: int
    observations: tuple[RevenueDriverPeriodObservation, ...]
    applicable: bool
    rps_increases: int = 0
    rps_declines: int = 0
    spsf_growth_available: bool = False
    compsales_ineligible: bool = False
    distinct_populations: tuple[tuple[str, tuple[date, ...]], ...] = ()
    spsf_missing_periods: tuple[date, ...] = ()
    spsf_unavailable: tuple[tuple[date, tuple[str, ...]], ...] = ()
    deferred_disagreements: tuple[HistoricalManagementKpiDeferredDisagreement, ...] = ()
    geographic_identities: tuple[str, ...] = ()


@dataclass(frozen=True)
class RevenueIdentityValidity:
    name: str
    kind: str
    established: bool
    max_resid: float | None
    identity_count: int = 0
    period_count: int = 0


def revenue_driver_applicable(financials: StandardizedFinancials) -> bool:
    data = financials.historical_strategy
    return bool(data is not None and data.disclosures)


def strategy_synthesis_applicable(financials: StandardizedFinancials) -> bool:
    return revenue_driver_applicable(financials)


def _require_annual_axis(financials: StandardizedFinancials) -> None:
    if not any(not period.is_interim for period in financials.periods):
        raise PeriodAxisError("revenue-driver analysis requires annual fiscal periods")


def _numeric(value: float | str | None) -> float | None:
    if value is None or is_source_unavailable(value):
        return None
    if isinstance(value, str):
        return None
    return float(value)


def _disclosures_for(
    data: HistoricalStrategyData, theme: str
) -> tuple[HistoricalStrategyDisclosure, ...]:
    return tuple(item for item in data.disclosures if item.theme == theme)


def _compsales_adjacent_comparison_ineligible(
    financials: StandardizedFinancials, axis: list[date]
) -> bool:
    if not management_kpi_applicable(financials):
        return False
    series = compute_management_kpi_series(financials, axis)
    saw_identity = False
    for identity in series.identities:
        item = series.series[identity]
        if item.family != FAMILY_COMPARABLE_SALES_GROWTH:
            continue
        saw_identity = True
        for index, period in enumerate(axis):
            if index == 0:
                continue
            if _numeric(item.adjacent_change[period]) is not None:
                return False
    return saw_identity


def _compsales_population_groups(
    financials: StandardizedFinancials,
) -> tuple[tuple[str, tuple[date, ...]], ...]:
    data = financials.historical_operating_kpis
    if data is None:
        return ()
    by_population: dict[str, list[date]] = {}
    for item in data.management_observations:
        if item.family != FAMILY_COMPARABLE_SALES_GROWTH:
            continue
        if item.basis != "reported":
            continue
        periods = by_population.setdefault(item.population, [])
        if item.period not in periods:
            periods.append(item.period)
    if len(by_population) <= 1:
        return ()
    return tuple(
        (population, tuple(sorted(by_population[population])))
        for population in sorted(by_population)
    )


def _deferred_disagreements_for(
    financials: StandardizedFinancials,
    family: str,
) -> tuple[HistoricalManagementKpiDeferredDisagreement, ...]:
    data = financials.historical_operating_kpis
    if data is None:
        return ()
    return tuple(
        item for item in data.deferred_disagreements if item.family == family
    )


def _conflicting_qualifier_fields(
    item: HistoricalManagementKpiDeferredDisagreement,
) -> tuple[str, ...]:
    names: list[str] = []
    for field in _QUALIFIER_FIELD_NAMES:
        values = {getattr(member, field) for member in item.members}
        if len(values) > 1:
            names.append(field)
    return tuple(names)


def _spsf_evidence_gaps(
    financials: StandardizedFinancials, axis: list[date]
) -> tuple[tuple[date, ...], tuple[tuple[date, tuple[str, ...]], ...]]:
    data = financials.historical_operating_kpis
    observations = ()
    if data is not None:
        observations = tuple(
            item
            for item in data.management_observations
            if item.family == FAMILY_SALES_PER_SQUARE_FOOT
        )
    admitted_periods = {item.period for item in observations}
    missing = ()
    if observations:
        missing = tuple(period for period in axis if period not in admitted_periods)
    unavailable: list[tuple[date, tuple[str, ...]]] = []
    if management_kpi_applicable(financials):
        series = compute_management_kpi_series(financials, axis)
        for identity in series.identities:
            item = series.series[identity]
            if item.family != FAMILY_SALES_PER_SQUARE_FOOT:
                continue
            for index, period in enumerate(axis):
                if index == 0:
                    continue
                reasons = item.unavailable_reasons.get(period) or ()
                if reasons:
                    unavailable.append((period, tuple(reasons)))
    return missing, tuple(unavailable)


def _empty_note_observation(
    period: date,
    inputs: dict[str, float | str | None],
    consistent: bool | None,
    *,
    mix_conflict: bool = False,
) -> RevenueDriverPeriodObservation:
    return RevenueDriverPeriodObservation(
        period=period,
        inputs=inputs,
        consistent=consistent,
        note="",
        mix_conflict=mix_conflict,
    )


def _store_expansion_observations(
    financials: StandardizedFinancials,
    axis: list[date],
    disclosures: tuple[HistoricalStrategyDisclosure, ...],
) -> RevenueDriverThemeObservations:
    inputs = (
        "statement-derived consolidated revenue growth",
        "company-operated period-end store-count growth",
        "analyst-derived revenue-versus-store-count growth difference",
    )
    if not operating_kpi_revenue_store_relationship_applicable(financials):
        return RevenueDriverThemeObservations(
            theme=THEME_STORE_EXPANSION,
            disclosures=disclosures,
            admitted_inputs=inputs,
            periods_tested=(),
            sample_size=0,
            observations=(),
            applicable=False,
        )
    relationship = compute_operating_kpi_revenue_store_relationship(financials, axis)
    rps = (
        compute_revenue_per_store_series(financials, axis)
        if revenue_per_store_applicable(financials)
        else None
    )
    observations: list[RevenueDriverPeriodObservation] = []
    for index, period in enumerate(axis):
        if index == 0:
            continue
        rev = _numeric(relationship.revenue_growth[period])
        stores = _numeric(relationship.store_count_growth[period])
        difference = relationship.growth_difference_pp[period]
        rps_change = None if rps is None else rps.period_end_change[period]
        payload: dict[str, float | str | None] = {
            "revenue_growth": relationship.revenue_growth[period],
            "store_count_growth": relationship.store_count_growth[period],
            "growth_difference_pp": difference,
            "period_end_revenue_per_store_change": rps_change,
        }
        if rev is None or stores is None:
            observations.append(_empty_note_observation(period, payload, None))
            continue
        coincident = rev > 0 and stores > 0
        observations.append(_empty_note_observation(period, payload, coincident))
    tested = tuple(item.period for item in observations if item.consistent is not None)
    return RevenueDriverThemeObservations(
        theme=THEME_STORE_EXPANSION,
        disclosures=disclosures,
        admitted_inputs=inputs,
        periods_tested=tested,
        sample_size=len(tested),
        observations=tuple(observations),
        applicable=True,
    )


def _comparable_sales_observations(
    financials: StandardizedFinancials,
    axis: list[date],
    disclosures: tuple[HistoricalStrategyDisclosure, ...],
) -> RevenueDriverThemeObservations:
    inputs = (
        "statement-derived consolidated revenue growth",
        "admitted global reported comparable-sales percentages",
        "analyst-derived revenue-versus-comparable-sales descriptive difference",
    )
    if not operating_kpi_revenue_comparable_sales_relationship_applicable(financials):
        return RevenueDriverThemeObservations(
            theme=THEME_COMPARABLE_SALES,
            disclosures=disclosures,
            admitted_inputs=inputs,
            periods_tested=(),
            sample_size=0,
            observations=(),
            applicable=False,
            compsales_ineligible=_compsales_adjacent_comparison_ineligible(
                financials, axis
            ),
            distinct_populations=_compsales_population_groups(financials),
            deferred_disagreements=_deferred_disagreements_for(
                financials, FAMILY_COMPARABLE_SALES_GROWTH
            ),
        )
    relationship = compute_operating_kpi_revenue_comparable_sales_relationship(
        financials, axis
    )
    observations: list[RevenueDriverPeriodObservation] = []
    tested: list[date] = []
    flags: list[bool | None] = []
    for identity in relationship.identities:
        series = relationship.series[identity]
        for index, period in enumerate(axis):
            if index == 0:
                continue
            rev = _numeric(series.revenue_growth[period])
            compsales = _numeric(series.comparable_sales_growth[period])
            payload: dict[str, float | str | None] = {
                "identity": identity,
                "revenue_growth": series.revenue_growth[period],
                "comparable_sales_percent": series.comparable_sales_growth[period],
                "growth_difference_pp": series.growth_difference_pp[period],
                "population": series.population,
                "basis": series.basis,
            }
            if rev is None or compsales is None:
                observations.append(_empty_note_observation(period, payload, None))
                continue
            consistent = rev > 0 and compsales > 0
            observations.append(_empty_note_observation(period, payload, consistent))
            flags.append(consistent)
            tested.append(period)
    unique_tested = tuple(dict.fromkeys(tested))
    return RevenueDriverThemeObservations(
        theme=THEME_COMPARABLE_SALES,
        disclosures=disclosures,
        admitted_inputs=inputs,
        periods_tested=unique_tested,
        sample_size=len(flags),
        observations=tuple(observations),
        applicable=True,
        compsales_ineligible=_compsales_adjacent_comparison_ineligible(financials, axis),
        distinct_populations=_compsales_population_groups(financials),
        deferred_disagreements=_deferred_disagreements_for(
            financials, FAMILY_COMPARABLE_SALES_GROWTH
        ),
    )


def _productivity_observations(
    financials: StandardizedFinancials,
    axis: list[date],
    disclosures: tuple[HistoricalStrategyDisclosure, ...],
) -> RevenueDriverThemeObservations:
    inputs = (
        "admitted company-operated-store sales per square foot",
        "adjacent SPSF growth when semantically compatible",
        "period-end Revenue per Store identity diagnostic",
    )
    spsf_growth_available = False
    spsf_observations: list[RevenueDriverPeriodObservation] = []
    if operating_kpi_revenue_sales_per_square_foot_relationship_applicable(financials):
        relationship = compute_operating_kpi_revenue_sales_per_square_foot_relationship(
            financials, axis
        )
        for identity in relationship.identities:
            series = relationship.series[identity]
            for index, period in enumerate(axis):
                if index == 0:
                    continue
                growth = _numeric(series.spsf_growth[period])
                payload = {
                    "identity": identity,
                    "spsf_growth": series.spsf_growth[period],
                    "revenue_growth": series.revenue_growth[period],
                    "growth_difference_pp": series.growth_difference_pp[period],
                }
                if growth is None:
                    spsf_observations.append(
                        _empty_note_observation(period, payload, None)
                    )
                    continue
                spsf_growth_available = True
                rev = _numeric(series.revenue_growth[period])
                consistent = None if rev is None else (rev > 0 and growth > 0)
                spsf_observations.append(
                    _empty_note_observation(period, payload, consistent)
                )
    elif management_kpi_applicable(financials):
        management = compute_management_kpi_series(financials, axis)
        for identity in management.identities:
            series = management.series[identity]
            if series.family != FAMILY_SALES_PER_SQUARE_FOOT:
                continue
            for index, period in enumerate(axis):
                if index == 0:
                    continue
                growth = _numeric(series.growth[period])
                payload = {
                    "identity": identity,
                    "spsf_growth": series.growth[period],
                    "reported_value": series.reported_value[period],
                }
                spsf_observations.append(
                    _empty_note_observation(
                        period, payload, None if growth is None else growth > 0
                    )
                )
                if growth is not None:
                    spsf_growth_available = True
    rps_increases = 0
    rps_declines = 0
    if revenue_per_store_applicable(financials):
        rps = compute_revenue_per_store_series(financials, axis)
        for index, period in enumerate(axis):
            if index == 0:
                continue
            change = _numeric(rps.period_end_change[period])
            if change is None:
                continue
            if change < 0:
                rps_declines += 1
            elif change > 0:
                rps_increases += 1
    missing, unavailable = _spsf_evidence_gaps(financials, axis)
    tested = tuple(
        item.period for item in spsf_observations if item.consistent is not None
    )
    return RevenueDriverThemeObservations(
        theme=THEME_PRODUCTIVITY,
        disclosures=disclosures,
        admitted_inputs=inputs,
        periods_tested=() if not spsf_growth_available else tested,
        sample_size=0 if not spsf_growth_available else len(tested),
        observations=tuple(spsf_observations),
        applicable=spsf_growth_available,
        rps_increases=rps_increases,
        rps_declines=rps_declines,
        spsf_growth_available=spsf_growth_available,
        spsf_missing_periods=missing,
        spsf_unavailable=unavailable,
        deferred_disagreements=_deferred_disagreements_for(
            financials, FAMILY_SALES_PER_SQUARE_FOOT
        ),
    )


def _geographic_observations(
    financials: StandardizedFinancials,
    axis: list[date],
    disclosures: tuple[HistoricalStrategyDisclosure, ...],
) -> RevenueDriverThemeObservations:
    inputs = (
        "admitted geographic segment net revenue",
        "arithmetic contributions to consolidated revenue growth",
        "reported consolidated revenue growth",
    )
    if not geographic_segment_applicable(financials):
        return RevenueDriverThemeObservations(
            theme=THEME_GEOGRAPHIC_GROWTH,
            disclosures=disclosures,
            admitted_inputs=inputs,
            periods_tested=(),
            sample_size=0,
            observations=(),
            applicable=False,
        )
    series = compute_geographic_segment_series(financials, axis)
    observations: list[RevenueDriverPeriodObservation] = []
    tested: list[date] = []
    identities = series.identities
    for index, period in enumerate(axis):
        if index == 0:
            continue
        cons = _numeric(series.consolidated_revenue_growth[period])
        period_positive = False
        period_negative = False
        missing = False
        contribs: dict[str, float | str | None] = {
            "consolidated_revenue_growth": series.consolidated_revenue_growth[period]
        }
        for identity in identities:
            value = series.revenue_growth_contribution[period].get(
                identity, SOURCE_UNAVAILABLE
            )
            contribs[identity] = value
            number = _numeric(value)
            if number is None:
                missing = True
                continue
            if number > 0:
                period_positive = True
            elif number < 0:
                period_negative = True
        if cons is None or missing:
            observations.append(_empty_note_observation(period, contribs, None))
            continue
        consistent = cons > 0 and period_positive
        mix_conflict = bool(consistent and period_negative)
        observations.append(
            _empty_note_observation(
                period, contribs, consistent, mix_conflict=mix_conflict
            )
        )
        tested.append(period)
    unique_tested = tuple(dict.fromkeys(tested))
    return RevenueDriverThemeObservations(
        theme=THEME_GEOGRAPHIC_GROWTH,
        disclosures=disclosures,
        admitted_inputs=inputs,
        periods_tested=unique_tested,
        sample_size=len(unique_tested),
        observations=tuple(observations),
        applicable=True,
        geographic_identities=identities,
    )


_THEME_BUILDERS = {
    THEME_STORE_EXPANSION: _store_expansion_observations,
    THEME_COMPARABLE_SALES: _comparable_sales_observations,
    THEME_PRODUCTIVITY: _productivity_observations,
    THEME_GEOGRAPHIC_GROWTH: _geographic_observations,
}


def compute_revenue_driver_analysis(
    financials: StandardizedFinancials,
    periods: list[date] | None = None,
) -> RevenueDriverAnalysis:
    """Compute disclosure-led revenue-driver observations and identities."""
    if not revenue_driver_applicable(financials):
        raise MissingLineError("revenue-driver disclosures are not available")
    assert financials.historical_strategy is not None
    if operating_kpi_applicable(financials) or geographic_segment_applicable(financials):
        _require_annual_axis(financials)
    axis = canonical_fiscal_periods(financials)
    if periods is not None and list(periods) != axis:
        raise ValueError("revenue-driver analysis must use the canonical fiscal axis")
    observed: list[RevenueDriverThemeObservations] = []
    for theme, builder in _THEME_BUILDERS.items():
        disclosures = _disclosures_for(financials.historical_strategy, theme)
        if not disclosures:
            continue
        observed.append(builder(financials, axis, disclosures))
    if not observed:
        raise MissingLineError("revenue-driver disclosures are not available")
    geo_reconstruction = _geographic_reconstruction(financials, axis)
    footprint = _footprint_intensity_identity(financials, axis)
    return RevenueDriverAnalysis(
        periods=tuple(axis),
        calculation_kind=CALCULATION_KIND,
        scope_note="",
        tests=(),
        geographic_reconstruction=geo_reconstruction,
        footprint_identity=footprint,
        assessments=(),
        theme_observations=tuple(observed),
    )


def _identity_assessment(
    theme: str,
    geo: GeographicRevenueReconstruction | None,
    footprint: FootprintIntensityIdentity | None,
) -> RevenueIdentityValidity | None:
    if theme == THEME_GEOGRAPHIC_GROWTH and geo is not None:
        resid_vals = [abs(value) for value in geo.residual if value is not None]
        max_resid = max(resid_vals) if resid_vals else None
        return RevenueIdentityValidity(
            name="geographic revenue reconstruction",
            kind=KIND_IDENTITY,
            established=max_resid is not None and max_resid < 1e-4,
            max_resid=max_resid,
            identity_count=len(geo.identities),
            period_count=len(geo.reported_revenue),
        )
    if theme == THEME_STORE_EXPANSION and footprint is not None:
        resid_vals = [
            abs(value)
            for value in footprint.reconstruction_residual
            if value is not None
        ]
        max_resid = max(resid_vals) if resid_vals else None
        return RevenueIdentityValidity(
            name="footprint and intensity identity",
            kind=KIND_IDENTITY,
            established=max_resid is not None and max_resid < 1e-4,
            max_resid=max_resid,
        )
    return None


def _geographic_reconstruction(
    financials: StandardizedFinancials, axis: list[date]
) -> GeographicRevenueReconstruction | None:
    if not geographic_segment_applicable(financials):
        return None
    series = compute_geographic_segment_series(financials, axis)
    component_revenue: list[dict[str, float | None]] = []
    reconstructed: list[float | None] = []
    reported: list[float | None] = []
    residual: list[float | None] = []
    contribution_amounts: list[dict[str, float | None]] = []
    growth_contribs: list[dict[str, float | None]] = []
    contrib_residual: list[float | None] = []
    prior_components: dict[str, float] | None = None
    for period in axis:
        row: dict[str, float | None] = {}
        missing = False
        for identity in series.identities:
            value = _numeric(series.net_revenue[period].get(identity))
            row[identity] = value
            if value is None:
                missing = True
        component_revenue.append(row)
        reported_rev = _numeric(series.reported_consolidated_revenue[period])
        reported.append(reported_rev)
        if missing:
            reconstructed.append(None)
            residual.append(None)
        else:
            total = sum(row[identity] or 0.0 for identity in series.identities)
            reconstructed.append(total)
            residual.append(
                None if reported_rev is None else total - reported_rev
            )
        amount_row: dict[str, float | None] = {}
        if prior_components is None:
            for identity in series.identities:
                amount_row[identity] = None
        else:
            for identity in series.identities:
                current = row[identity]
                prior = prior_components.get(identity)
                amount_row[identity] = (
                    None
                    if current is None or prior is None
                    else current - prior
                )
        contribution_amounts.append(amount_row)
        growth_row = {
            identity: _numeric(
                series.revenue_growth_contribution[period].get(identity)
            )
            for identity in series.identities
        }
        growth_contribs.append(growth_row)
        contrib_residual.append(
            _numeric(series.revenue_growth_contribution_residual[period])
        )
        prior_components = {
            identity: value
            for identity, value in row.items()
            if value is not None
        } or None
    return GeographicRevenueReconstruction(
        identities=series.identities,
        component_revenue=tuple(component_revenue),
        reconstructed_revenue=tuple(reconstructed),
        reported_revenue=tuple(reported),
        residual=tuple(residual),
        contribution_amounts=tuple(contribution_amounts),
        growth_contributions=tuple(growth_contribs),
        contribution_residual=tuple(contrib_residual),
    )


def _footprint_intensity_identity(
    financials: StandardizedFinancials, axis: list[date]
) -> FootprintIntensityIdentity | None:
    if not (
        operating_kpi_applicable(financials) and revenue_per_store_applicable(financials)
    ):
        return None
    stores = compute_operating_kpi_series(financials, axis)
    rps = compute_revenue_per_store_series(financials, axis)
    store_levels: list[float | None] = []
    intensity: list[float | None] = []
    reconstructed: list[float | None] = []
    residual: list[float | None] = []
    store_effect: list[float | None] = [None] * len(axis)
    intensity_effect: list[float | None] = [None] * len(axis)
    interaction: list[float | None] = [None] * len(axis)
    change_residual: list[float | None] = [None] * len(axis)
    for index, period in enumerate(axis):
        store = _numeric(stores.period_end_count[period])
        intensity_value = _numeric(rps.period_end_revenue_per_store[period])
        revenue = _numeric(rps.revenue[period])
        store_levels.append(store)
        intensity.append(intensity_value)
        if store is None or intensity_value is None:
            reconstructed.append(None)
            residual.append(None)
            continue
        built = store * intensity_value
        reconstructed.append(built)
        residual.append(None if revenue is None else revenue - built)
        if index == 0:
            continue
        prior_store = store_levels[index - 1]
        prior_intensity = intensity[index - 1]
        prior_revenue = _numeric(rps.revenue[axis[index - 1]])
        if (
            prior_store is None
            or prior_intensity is None
            or revenue is None
            or prior_revenue is None
        ):
            continue
        d_store = store - prior_store
        d_intensity = intensity_value - prior_intensity
        store_effect[index] = d_store * prior_intensity
        intensity_effect[index] = prior_store * d_intensity
        interaction[index] = d_store * d_intensity
        change_residual[index] = (revenue - prior_revenue) - (
            store_effect[index] + intensity_effect[index] + interaction[index]
        )
    return FootprintIntensityIdentity(
        stores=tuple(store_levels),
        intensity=tuple(intensity),
        reconstructed_revenue=tuple(reconstructed),
        reconstruction_residual=tuple(residual),
        store_effect=tuple(store_effect),
        intensity_effect=tuple(intensity_effect),
        interaction=tuple(interaction),
        change_residual=tuple(change_residual),
        convention=FOOTPRINT_IDENTITY_FORMULA,
        scope_note="",
    )

