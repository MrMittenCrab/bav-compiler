"""Revenue-driver hypotheses, verdicts, requirement codes, and qualifications."""

from __future__ import annotations

from dataclasses import dataclass, replace

from bav.extractor.data.historical_strategy import (
    ROLE_OBJECTIVE,
    THEME_COMPARABLE_SALES,
    THEME_GEOGRAPHIC_GROWTH,
    THEME_PRODUCTIVITY,
    THEME_STORE_EXPANSION,
)
from bav.modeler.reported_margin import (
    KIND_CAUSAL,
    KIND_OBSERVED,
    KIND_UNESTABLISHED,
)
from bav.modeler.revenue_driver import (
    RevenueDriverPeriodObservation,
    RevenueDriverThemeObservations,
    _numeric,
)

from bav.inferer.revenue_driver import (
    QUAL_COMPSALES_INELIGIBLE,
    QUAL_DESCRIPTIVE_DIFFERENCE,
    QUAL_GAPS_NOT_BRIDGED,
    QUAL_NOT_ORGANIC_FX,
    QUAL_NOT_OUTCOME,
    QUAL_POPS_DISTINCT,
    QUAL_RPS_NOT_PRODUCTIVITY,
    REQ_ADDITIONAL_SPSF,
    REQ_COMPSALES,
    REQ_COMPSALES_HISTORY,
    REQ_GEOGRAPHIC,
    REQ_SPSF_GROWTH,
    REQ_STORE_GROWTH,
    RevenueAssessmentDecision,
    VERDICT_CONTRADICTED,
    VERDICT_INSUFFICIENT,
    VERDICT_MIXED,
    VERDICT_SUPPORTED,
    SUPPORTED_VERDICTS,
    interpret_revenue_assessment,
    verdict_from_consistency,
)

HYPOTHESIS_STORE_EXPANSION = (
    "If disclosed store expansion was a material historical revenue driver, "
    "company-operated store counts and consolidated revenue should both "
    "increase over aligned periods."
)
HYPOTHESIS_COMPARABLE_SALES = (
    "If disclosed comparable sales were a material historical revenue driver, "
    "reported global comparable-sales percentages should be positive in "
    "periods when statement-derived consolidated revenue grew."
)
HYPOTHESIS_PRODUCTIVITY = (
    "If disclosed store productivity was a material historical revenue driver, "
    "adjacent sales-per-square-foot growth should be measurable on admitted "
    "company-operated-store observations."
)
HYPOTHESIS_GEOGRAPHIC = (
    "If disclosed geographic expansion was a material historical revenue "
    "driver, admitted geographic segments should show positive reported "
    "revenue-growth contributions to consolidated revenue over aligned periods."
)
MECHANISM_STORE_EXPANSION = (
    "Additional company-operated stores can add selling capacity. The test "
    "compares statement-derived consolidated revenue growth with company-"
    "operated period-end store-count growth."
)
MECHANISM_COMPARABLE_SALES = (
    "Continuing stores and disclosed comparable channels can grow revenue "
    "without a change in store count. The test compares statement-derived "
    "consolidated revenue growth with reported global comparable-sales "
    "percentages."
)
MECHANISM_PRODUCTIVITY = (
    "Higher sales per unit of store space can grow revenue independently of "
    "store count. The disclosed productivity metric is sales per square foot. "
    "Revenue per Store is retained only as an identity diagnostic."
)
MECHANISM_GEOGRAPHIC = (
    "Geographic mix can change consolidated revenue when some regions grow "
    "faster than others. The test uses admitted arithmetic revenue-growth "
    "contributions."
)


@dataclass(frozen=True)
class RevenueDriverThemeInterpretation:
    observations: RevenueDriverThemeObservations
    hypothesis: str
    mechanism: str
    verdict: str
    qualification_codes: tuple[str, ...]
    failed_requirement_code: str
    additional_evidence_code: str
    has_deferred_spsf: bool


def _has_objective_role(bundle: RevenueDriverThemeObservations) -> bool:
    return any(item.role == ROLE_OBJECTIVE for item in bundle.disclosures)


def _with_objective(codes: list[str], bundle: RevenueDriverThemeObservations) -> tuple[str, ...]:
    if _has_objective_role(bundle):
        codes.append(QUAL_NOT_OUTCOME)
    return tuple(codes)


def _mark_store_counterexamples(
    bundle: RevenueDriverThemeObservations,
) -> RevenueDriverThemeObservations:
    marked = []
    for item in bundle.observations:
        rev = _numeric(item.inputs.get("revenue_growth"))
        stores = _numeric(item.inputs.get("store_count_growth"))
        rps_change = _numeric(item.inputs.get("period_end_revenue_per_store_change"))
        counterexample = False
        if rev is not None and stores is not None:
            if stores > 0 and rev <= 0:
                counterexample = True
            if stores > rev:
                counterexample = True
        if rps_change is not None and rps_change < 0:
            counterexample = True
        marked.append(replace(item, counterexample=counterexample))
    return replace(bundle, observations=tuple(marked))


def _mark_compsales_counterexamples(
    bundle: RevenueDriverThemeObservations,
) -> RevenueDriverThemeObservations:
    marked = []
    for item in bundle.observations:
        rev = _numeric(item.inputs.get("revenue_growth"))
        compsales = _numeric(item.inputs.get("comparable_sales_percent"))
        counterexample = (
            rev is not None and compsales is not None and rev <= 0 and compsales > 0
        )
        marked.append(replace(item, counterexample=counterexample))
    return replace(bundle, observations=tuple(marked))


def _mark_geographic_counterexamples(
    bundle: RevenueDriverThemeObservations,
) -> RevenueDriverThemeObservations:
    marked = [
        replace(item, counterexample=item.mix_conflict or item.consistent is False)
        if item.consistent is not None
        else item
        for item in bundle.observations
    ]
    return replace(bundle, observations=tuple(marked))


def interpret_store_expansion(
    bundle: RevenueDriverThemeObservations,
) -> RevenueDriverThemeInterpretation:
    bundle = _mark_store_counterexamples(bundle)
    if not bundle.applicable:
        return RevenueDriverThemeInterpretation(
            observations=bundle,
            hypothesis=HYPOTHESIS_STORE_EXPANSION,
            mechanism=MECHANISM_STORE_EXPANSION,
            verdict=VERDICT_INSUFFICIENT,
            qualification_codes=_with_objective(
                [QUAL_DESCRIPTIVE_DIFFERENCE, QUAL_RPS_NOT_PRODUCTIVITY], bundle
            ),
            failed_requirement_code=REQ_STORE_GROWTH,
            additional_evidence_code=REQ_STORE_GROWTH,
            has_deferred_spsf=False,
        )
    verdict = verdict_from_consistency(bundle.observations)
    failed = REQ_STORE_GROWTH if verdict == VERDICT_INSUFFICIENT else ""
    return RevenueDriverThemeInterpretation(
        observations=bundle,
        hypothesis=HYPOTHESIS_STORE_EXPANSION,
        mechanism=MECHANISM_STORE_EXPANSION,
        verdict=verdict,
        qualification_codes=_with_objective(
            [QUAL_DESCRIPTIVE_DIFFERENCE, QUAL_RPS_NOT_PRODUCTIVITY], bundle
        ),
        failed_requirement_code=failed,
        additional_evidence_code=failed,
        has_deferred_spsf=False,
    )


def interpret_comparable_sales(
    bundle: RevenueDriverThemeObservations,
) -> RevenueDriverThemeInterpretation:
    bundle = _mark_compsales_counterexamples(bundle)
    codes = [QUAL_DESCRIPTIVE_DIFFERENCE, QUAL_NOT_ORGANIC_FX]
    if bundle.distinct_populations:
        codes.append(QUAL_POPS_DISTINCT)
    if bundle.compsales_ineligible:
        codes.append(QUAL_COMPSALES_INELIGIBLE)
    if not bundle.applicable:
        return RevenueDriverThemeInterpretation(
            observations=bundle,
            hypothesis=HYPOTHESIS_COMPARABLE_SALES,
            mechanism=MECHANISM_COMPARABLE_SALES,
            verdict=VERDICT_INSUFFICIENT,
            qualification_codes=_with_objective(codes, bundle),
            failed_requirement_code=REQ_COMPSALES,
            additional_evidence_code=REQ_COMPSALES_HISTORY,
            has_deferred_spsf=False,
        )
    verdict = verdict_from_consistency(bundle.observations)
    if verdict == VERDICT_INSUFFICIENT:
        failed, additional = REQ_COMPSALES, REQ_COMPSALES_HISTORY
    else:
        failed, additional = "", REQ_COMPSALES_HISTORY
    return RevenueDriverThemeInterpretation(
        observations=bundle,
        hypothesis=HYPOTHESIS_COMPARABLE_SALES,
        mechanism=MECHANISM_COMPARABLE_SALES,
        verdict=verdict,
        qualification_codes=_with_objective(codes, bundle),
        failed_requirement_code=failed,
        additional_evidence_code=additional,
        has_deferred_spsf=False,
    )


def interpret_productivity(
    bundle: RevenueDriverThemeObservations,
) -> RevenueDriverThemeInterpretation:
    codes = [QUAL_RPS_NOT_PRODUCTIVITY, QUAL_GAPS_NOT_BRIDGED]
    has_deferred = bool(bundle.deferred_disagreements)
    if not bundle.spsf_growth_available:
        return RevenueDriverThemeInterpretation(
            observations=bundle,
            hypothesis=HYPOTHESIS_PRODUCTIVITY,
            mechanism=MECHANISM_PRODUCTIVITY,
            verdict=VERDICT_INSUFFICIENT,
            qualification_codes=_with_objective(codes, bundle),
            failed_requirement_code=REQ_SPSF_GROWTH,
            additional_evidence_code=REQ_ADDITIONAL_SPSF,
            has_deferred_spsf=has_deferred,
        )
    verdict = verdict_from_consistency(bundle.observations)
    return RevenueDriverThemeInterpretation(
        observations=bundle,
        hypothesis=HYPOTHESIS_PRODUCTIVITY,
        mechanism=MECHANISM_PRODUCTIVITY,
        verdict=verdict,
        qualification_codes=_with_objective(codes, bundle),
        failed_requirement_code="",
        additional_evidence_code="",
        has_deferred_spsf=has_deferred,
    )


def interpret_geographic(
    bundle: RevenueDriverThemeObservations,
) -> RevenueDriverThemeInterpretation:
    bundle = _mark_geographic_counterexamples(bundle)
    if not bundle.applicable:
        return RevenueDriverThemeInterpretation(
            observations=bundle,
            hypothesis=HYPOTHESIS_GEOGRAPHIC,
            mechanism=MECHANISM_GEOGRAPHIC,
            verdict=VERDICT_INSUFFICIENT,
            qualification_codes=_with_objective([QUAL_NOT_ORGANIC_FX], bundle),
            failed_requirement_code=REQ_GEOGRAPHIC,
            additional_evidence_code=REQ_GEOGRAPHIC,
            has_deferred_spsf=False,
        )
    verdict = verdict_from_consistency(bundle.observations)
    failed = REQ_GEOGRAPHIC if verdict == VERDICT_INSUFFICIENT else ""
    return RevenueDriverThemeInterpretation(
        observations=bundle,
        hypothesis=HYPOTHESIS_GEOGRAPHIC,
        mechanism=MECHANISM_GEOGRAPHIC,
        verdict=verdict,
        qualification_codes=_with_objective([QUAL_NOT_ORGANIC_FX], bundle),
        failed_requirement_code=failed,
        additional_evidence_code=failed,
        has_deferred_spsf=False,
    )


_THEME_INTERPRETERS = {
    THEME_STORE_EXPANSION: interpret_store_expansion,
    THEME_COMPARABLE_SALES: interpret_comparable_sales,
    THEME_PRODUCTIVITY: interpret_productivity,
    THEME_GEOGRAPHIC_GROWTH: interpret_geographic,
}


def interpret_theme(
    bundle: RevenueDriverThemeObservations,
) -> RevenueDriverThemeInterpretation:
    return _THEME_INTERPRETERS[bundle.theme](bundle)


