"""Revenue-driver publication wording. Copies kind and established unchanged."""

from __future__ import annotations

from bav.modeler.data.historical_operating_kpis import (
    FAMILY_COMPARABLE_SALES_GROWTH,
    FAMILY_SALES_PER_SQUARE_FOOT,
)
from bav.modeler.data.interface import HistoricalManagementKpiDeferredDisagreement
from bav.modeler.management_kpi import (
    REASON_CALENDAR_REPORTING_MISMATCH,
    REASON_CALENDAR_WEEK_MISMATCH,
    REASON_DEFINITION_MISMATCH,
    REASON_MISSING_OBSERVATION,
    REASON_MISSING_PRIOR_OBSERVATION,
    REASON_PERIOD_KIND_MISMATCH,
    REASON_QUALIFIER_MISMATCH,
)
from bav.modeler.revenue_per_store import SCOPE_NOTE as REVENUE_PER_STORE_SCOPE_NOTE
from bav.extractor.data.historical_strategy import (
    THEME_COMPARABLE_SALES,
    THEME_GEOGRAPHIC_GROWTH,
    THEME_PRODUCTIVITY,
    THEME_STORE_EXPANSION,
)
from bav.inferer.revenue_driver import QUAL_COMPSALES_INELIGIBLE, QUAL_DESCRIPTIVE_DIFFERENCE, QUAL_GAPS_NOT_BRIDGED, QUAL_NOT_ORGANIC_FX, QUAL_NOT_OUTCOME, QUAL_POPS_DISTINCT, QUAL_RPS_NOT_PRODUCTIVITY, REQ_ADDITIONAL_SPSF, REQ_COMPSALES, REQ_COMPSALES_HISTORY, REQ_GEOGRAPHIC, REQ_SPSF_GROWTH, REQ_STORE_GROWTH, VERDICT_INSUFFICIENT, RevenueAssessmentDecision
from bav.debater.revenue_driver import RevenueDriverThemeInterpretation
from bav.modeler.reported_margin import KIND_IDENTITY, MarginRelationshipAssessment
from bav.modeler.revenue_driver import (
    FOOTPRINT_IDENTITY_FORMULA,
    FootprintIntensityIdentity,
    RevenueDriverHypothesisTest,
    RevenueDriverPeriodObservation,
    RevenueIdentityValidity,
    _conflicting_qualifier_fields,
    _numeric,
)

FOOTPRINT_IDENTITY_CONVENTION = (
    FOOTPRINT_IDENTITY_FORMULA + " "
    "Company-wide revenue per store is an intensity proxy that includes "
    "non-store revenue; it is not store productivity."
)
SCOPE_NOTE = (
    "Management statements are source facts, not achieved outcomes. Analyst "
    "hypotheses are tested separately. Revenue-growth-minus-comparable-sales "
    "and revenue-growth-minus-store-growth results are descriptive differences, "
    "never new-store contribution, organic growth, or causal attribution. "
    "Total-company revenue divided by company-operated stores is an accounting "
    "identity and cannot independently demonstrate store productivity or "
    "explain store expansion's causal contribution. Reported and constant-"
    "currency metrics, geographic and channel populations, fiscal-year labels "
    "and actual period-end dates remain distinct."
)
FAILED_STORE_GROWTH = (
    "adjacent admitted consolidated revenue growth and company-operated "
    "period-end store-count growth"
)
FAILED_COMPSALES = (
    "admitted global reported comparable-sales percentages aligned to "
    "statement-derived consolidated revenue growth"
)
FAILED_SPSF_GROWTH = (
    "immediately adjacent semantically compatible reported sales-per-square-"
    "foot observations"
)
FAILED_GEOGRAPHIC = (
    "admitted geographic revenue-growth contributions on immediately adjacent "
    "canonical periods"
)
ADDITIONAL_COMPSALES_HISTORY = (
    "calendar-compatible comparable-sales comparison windows and a single "
    "continuing identity across adjacent periods"
)
ADDITIONAL_SPSF = (
    "admitted adjacent SPSF observations with equivalent definition, "
    "population, calendar, and comparison-window evidence"
)
_REQUIREMENT_PHRASES = {
    REQ_STORE_GROWTH: FAILED_STORE_GROWTH,
    REQ_COMPSALES: FAILED_COMPSALES,
    REQ_SPSF_GROWTH: FAILED_SPSF_GROWTH,
    REQ_GEOGRAPHIC: FAILED_GEOGRAPHIC,
    REQ_COMPSALES_HISTORY: ADDITIONAL_COMPSALES_HISTORY,
    REQ_ADDITIONAL_SPSF: ADDITIONAL_SPSF,
}
_SEGMENT_LABELS = {
    "americas": "Americas",
    "china_mainland": "China Mainland",
    "rest_of_world": "Rest of World",
}
_SPSF_REASON_LABELS = {
    REASON_DEFINITION_MISMATCH: "definition mismatch",
    REASON_PERIOD_KIND_MISMATCH: "period-kind mismatch",
    REASON_CALENDAR_WEEK_MISMATCH: "calendar week-adjustment mismatch",
    REASON_CALENDAR_REPORTING_MISMATCH: "calendar reporting-basis mismatch",
    REASON_QUALIFIER_MISMATCH: "qualifier mismatch",
    REASON_MISSING_OBSERVATION: "missing admitted observation",
    REASON_MISSING_PRIOR_OBSERVATION: "missing prior admitted observation",
}
_FAMILY_DISAGREEMENT_LABELS = {
    FAMILY_SALES_PER_SQUARE_FOOT: "sales-per-square-foot",
    FAMILY_COMPARABLE_SALES_GROWTH: "comparable-sales",
}
_QUALIFIER_FIELD_LABELS = (
    ("population", "population"),
    ("unit", "unit"),
    ("basis", "basis"),
    ("calendar_week_adjustment", "calendar week-adjustment"),
    ("calendar_reporting_basis", "calendar reporting-basis"),
)


def _format_ratio_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _format_pp(value: float) -> str:
    return f"{value:.3f} pp"


def _segment_label(identity: str) -> str:
    return _SEGMENT_LABELS.get(identity, identity.replace("_", " ").title())


def _requirement_phrase(code: str) -> str:
    if not code:
        return ""
    return _REQUIREMENT_PHRASES.get(code, code)


def _finding_with_counterexamples(
    base: str, observations: tuple[RevenueDriverPeriodObservation, ...]
) -> str:
    extras = tuple(
        item.note for item in observations if item.note and item.counterexample
    )
    if not extras:
        return base
    return base + " " + " ".join(extras)


def _deferred_member_locator(member) -> str:
    pages = []
    if member.page_reference:
        pages.append(member.page_reference)
    if member.physical_page_mapping:
        pages.append(f"physical {member.physical_page_mapping}")
    source = "; ".join(
        part for part in (member.extraction_document, *pages) if part
    )
    locator = member.locator
    if source:
        return f"{locator} [{source}]"
    return locator


def _conflicting_qualifier_labels(
    item: HistoricalManagementKpiDeferredDisagreement,
) -> tuple[str, ...]:
    label_by_field = dict(_QUALIFIER_FIELD_LABELS)
    labels = [
        label_by_field.get(field, field)
        for field in _conflicting_qualifier_fields(item)
    ]
    definitions = {member.definition_text for member in item.members}
    if len(definitions) > 1:
        labels.insert(0, "definition")
    return tuple(labels)


def _format_deferred_disagreement(
    item: HistoricalManagementKpiDeferredDisagreement,
) -> str:
    family_label = _FAMILY_DISAGREEMENT_LABELS.get(
        item.family, item.family.replace("_", "-")
    )
    conflict_labels = _conflicting_qualifier_labels(item)
    conflict_text = (
        ", ".join(conflict_labels) if conflict_labels else "definition or qualifier"
    )
    member_parts = []
    for member in item.members:
        role = member.presentation_role.replace("_", " ") or "unspecified role"
        member_parts.append(
            f'{role} occurrence {_deferred_member_locator(member)} '
            f'defines {family_label} as "{member.definition_text}"'
        )
    reasons = ", ".join(item.reasons)
    return (
        f"Deferred {family_label} disagreement at period-end "
        f"{item.period.isoformat()} is not admitted. Conflicting {conflict_text} "
        f"evidence: " + "; ".join(member_parts) + ". Deferral reasons: "
        f"{reasons}. The complete group remains audit-only; the disagreement is "
        "not bridged into the test and does not create an admitted observation."
    )


def word_compsales_population_limit(
    groups: tuple[tuple[str, tuple], ...],
) -> tuple[str, ...]:
    if not groups:
        return ()
    parts = []
    for population, periods in groups:
        dates = ", ".join(period.isoformat() for period in periods)
        parts.append(f"{population} at period-end {dates}")
    return (
        "Admitted comparable-sales identities remain distinct by population "
        "and are never merged: " + "; ".join(parts) + ".",
    )


def word_spsf_evidence_limits(
    missing_periods,
    unavailable,
    deferred_disagreements,
) -> tuple[str, ...]:
    limits: list[str] = []
    if missing_periods:
        dates = ", ".join(period.isoformat() for period in missing_periods)
        limits.append(
            "No admitted sales-per-square-foot observation exists for "
            f"period-end {dates}; those period(s) are not bridged."
        )
    reason_parts = []
    for period, reasons in unavailable:
        labels = tuple(
            _SPSF_REASON_LABELS.get(reason, reason.replace("_", " "))
            for reason in reasons
        )
        reason_parts.append(f"{period.isoformat()} ({', '.join(labels)})")
    if reason_parts:
        limits.append(
            "Adjacent SPSF growth is unavailable on admitted evidence at "
            + "; ".join(reason_parts)
            + ". Those gaps are not bridged."
        )
    limits.extend(
        _format_deferred_disagreement(item) for item in deferred_disagreements
    )
    return tuple(limits)


def _objective_sentence() -> str:
    return (
        "Strategic objectives and plans are recorded as management statements "
        "and are not treated as achieved historical outcomes."
    )


def _store_notes(item: RevenueDriverPeriodObservation) -> str:
    rev = _numeric(item.inputs.get("revenue_growth"))
    stores = _numeric(item.inputs.get("store_count_growth"))
    difference = item.inputs.get("growth_difference_pp")
    rps_change = item.inputs.get("period_end_revenue_per_store_change")
    if rev is None or stores is None:
        return "Missing adjacent revenue or store-count growth."
    notes: list[str] = []
    if rev > 0 and stores > 0:
        notes.append(
            "Both consolidated revenue and company-operated store counts grew."
        )
    elif stores > 0 and rev <= 0:
        notes.append(
            f"Period-end {item.period.isoformat()}: store count grew "
            f"{_format_ratio_pct(stores)} while consolidated revenue did not "
            f"({_format_ratio_pct(rev)}); this contradicts expansion as a "
            "coincident revenue driver in this period."
        )
    elif rev > 0 and stores <= 0:
        notes.append(
            f"Period-end {item.period.isoformat()}: consolidated revenue grew "
            f"{_format_ratio_pct(rev)} without store-count growth "
            f"({_format_ratio_pct(stores)})."
        )
    else:
        notes.append(
            f"Period-end {item.period.isoformat()}: neither revenue nor store "
            "count grew."
        )
    if stores > rev:
        difference_number = _numeric(difference)
        difference_text = (
            f" (descriptive difference {_format_pp(difference_number)})"
            if difference_number is not None
            else ""
        )
        notes.append(
            f"Period-end {item.period.isoformat()}: store-count growth "
            f"{_format_ratio_pct(stores)} exceeded revenue growth "
            f"{_format_ratio_pct(rev)}{difference_text}. This is a "
            "descriptive counterexample, not new-store contribution or "
            "proof that expansion reduced productivity."
        )
    rps_change_number = _numeric(rps_change)
    if rps_change_number is not None and rps_change_number < 0:
        notes.append(
            f"Period-end {item.period.isoformat()}: period-end Revenue per Store "
            "declined. That identity uses total-company revenue divided by "
            "company-operated stores and cannot independently demonstrate "
            "store productivity."
        )
    return " ".join(notes)


def _compsales_note(item: RevenueDriverPeriodObservation) -> str:
    rev = _numeric(item.inputs.get("revenue_growth"))
    compsales = _numeric(item.inputs.get("comparable_sales_percent"))
    if rev is None or compsales is None:
        return "Missing aligned revenue growth or comparable-sales percent."
    if rev > 0 and compsales > 0:
        return (
            f"Period-end {item.period.isoformat()}: consolidated revenue grew "
            f"{_format_ratio_pct(rev)} and reported global comparable "
            f"sales were {compsales:.2f}%. The difference is descriptive only."
        )
    if rev > 0 and compsales <= 0:
        return (
            f"Period-end {item.period.isoformat()}: consolidated revenue grew "
            f"{_format_ratio_pct(rev)} while reported comparable sales "
            f"were {compsales:.2f}%."
        )
    if rev <= 0 and compsales > 0:
        return (
            f"Period-end {item.period.isoformat()}: reported comparable sales "
            f"were {compsales:.2f}% while consolidated revenue did not "
            f"grow ({_format_ratio_pct(rev)})."
        )
    return (
        f"Period-end {item.period.isoformat()}: neither consolidated "
        "revenue growth nor reported comparable sales were positive."
    )


def _productivity_note(item: RevenueDriverPeriodObservation) -> str:
    growth = _numeric(item.inputs.get("spsf_growth"))
    if "revenue_growth" in item.inputs:
        if growth is None:
            return (
                "Adjacent SPSF growth is unavailable. Failed "
                f"requirement: {FAILED_SPSF_GROWTH}."
            )
        return (
            "SPSF growth is an admitted adjacent comparison and "
            "is not store-only productivity from total-company "
            "revenue divided by stores."
        )
    if growth is None:
        return "Adjacent SPSF growth is unavailable."
    return "Admitted adjacent SPSF growth."


def _geographic_note(item: RevenueDriverPeriodObservation) -> str:
    cons = _numeric(item.inputs.get("consolidated_revenue_growth"))
    if cons is None or item.consistent is None:
        return "Missing adjacent geographic contribution or consolidated growth."
    identities = [key for key in item.inputs if key != "consolidated_revenue_growth"]
    negative_parts = []
    positive_parts = []
    for identity in identities:
        number = _numeric(item.inputs.get(identity))
        if number is None:
            continue
        label = _segment_label(identity)
        if number < 0:
            negative_parts.append(f"{label} {_format_pp(number)}")
        elif number > 0:
            positive_parts.append(f"{label} {_format_pp(number)}")
    if item.consistent and item.mix_conflict:
        return (
            f"Period-end {item.period.isoformat()}: consolidated revenue grew "
            f"{_format_ratio_pct(cons)} while {', '.join(negative_parts)} "
            "contributed negatively"
            + (
                f" and {', '.join(positive_parts)} contributed positively"
                if positive_parts
                else ""
            )
            + ". Mix is mixed, not a causal explanation."
        )
    if item.consistent:
        return (
            f"Period-end {item.period.isoformat()}: consolidated revenue "
            f"grew {_format_ratio_pct(cons)} and admitted geographic "
            "contributions were non-negative."
        )
    return (
        f"Period-end {item.period.isoformat()}: consolidated revenue "
        f"did not grow with a positive admitted geographic "
        f"contribution ({_format_ratio_pct(cons)})."
    )


def _worded_observations(
    interpretation: RevenueDriverThemeInterpretation,
    note_fn,
) -> tuple[RevenueDriverPeriodObservation, ...]:
    return tuple(
        RevenueDriverPeriodObservation(
            period=item.period,
            inputs=item.inputs,
            consistent=item.consistent,
            note=note_fn(item),
            counterexample=item.counterexample,
            mix_conflict=item.mix_conflict,
        )
        for item in interpretation.observations.observations
    )


def _base_test(
    interpretation: RevenueDriverThemeInterpretation,
    *,
    observations: tuple[RevenueDriverPeriodObservation, ...],
    finding: str,
    limitations: tuple[str, ...],
    identity_notes: tuple[str, ...],
) -> RevenueDriverHypothesisTest:
    bundle = interpretation.observations
    return RevenueDriverHypothesisTest(
        theme=bundle.theme,
        hypothesis=interpretation.hypothesis,
        mechanism=interpretation.mechanism,
        disclosures=bundle.disclosures,
        admitted_inputs=bundle.admitted_inputs,
        periods_tested=bundle.periods_tested,
        sample_size=bundle.sample_size,
        observations=observations,
        verdict=interpretation.verdict,
        finding=finding,
        limitations=limitations,
        failed_requirement=_requirement_phrase(interpretation.failed_requirement_code),
        additional_evidence=_requirement_phrase(
            interpretation.additional_evidence_code
        ),
        identity_notes=identity_notes,
        qualification_codes=interpretation.qualification_codes,
        failed_requirement_code=interpretation.failed_requirement_code,
        additional_evidence_code=interpretation.additional_evidence_code,
        has_deferred_spsf=interpretation.has_deferred_spsf,
        rps_increases=bundle.rps_increases,
        rps_declines=bundle.rps_declines,
        spsf_growth_available=bundle.spsf_growth_available,
        compsales_ineligible=bundle.compsales_ineligible,
        distinct_populations=bundle.distinct_populations,
        spsf_missing_periods=bundle.spsf_missing_periods,
        spsf_unavailable=bundle.spsf_unavailable,
        deferred_disagreements=bundle.deferred_disagreements,
        geographic_identities=bundle.geographic_identities,
    )


def word_store_expansion(
    interpretation: RevenueDriverThemeInterpretation,
) -> RevenueDriverHypothesisTest:
    codes = interpretation.qualification_codes
    limitations = [
        "The growth difference is a descriptive comparison of distinct scopes: "
        "consolidated revenue versus company-operated period-end store counts.",
        "The difference is not new-store contribution, organic growth, store "
        "productivity, or causal evidence.",
        REVENUE_PER_STORE_SCOPE_NOTE,
    ]
    if QUAL_NOT_OUTCOME in codes:
        limitations.append(_objective_sentence())
    observations = _worded_observations(interpretation, _store_notes)
    if interpretation.verdict == VERDICT_INSUFFICIENT:
        if not interpretation.observations.applicable:
            finding = (
                "Store-expansion cannot be tested: company-operated store-count "
                "history is not admitted."
            )
        else:
            finding = (
                "Store-expansion cannot be tested from the admitted series: no "
                "aligned adjacent revenue and store-count growth values exist."
            )
    else:
        finding = _finding_with_counterexamples(
            f"{len(interpretation.observations.periods_tested)} aligned period(s) "
            "compare statement-derived consolidated revenue growth with "
            "company-operated store-count "
            f"growth. Verdict: {interpretation.verdict.replace('_', ' ')}.",
            observations,
        )
    return _base_test(
        interpretation,
        observations=observations,
        finding=finding,
        limitations=tuple(limitations),
        identity_notes=(REVENUE_PER_STORE_SCOPE_NOTE,),
    )


def word_comparable_sales(
    interpretation: RevenueDriverThemeInterpretation,
) -> RevenueDriverHypothesisTest:
    codes = interpretation.qualification_codes
    limitations = [
        "The revenue-versus-comparable-sales difference is not new-store "
        "contribution, organic growth, productivity, or causal evidence.",
        "Reported and constant-currency comparable-sales series remain separate.",
        *word_compsales_population_limit(
            interpretation.observations.distinct_populations
        ),
    ]
    if QUAL_COMPSALES_INELIGIBLE in codes:
        limitations.append(
            "Historical comparable-sales-to-comparable-sales comparison remains "
            "ineligible on the admitted identities, periods, and calendar/"
            "comparison-window evidence."
        )
    limitations.extend(
        _format_deferred_disagreement(item)
        for item in interpretation.observations.deferred_disagreements
    )
    if QUAL_NOT_OUTCOME in codes:
        limitations.append(_objective_sentence())
    observations = _worded_observations(interpretation, _compsales_note)
    if interpretation.verdict == VERDICT_INSUFFICIENT:
        if not interpretation.observations.applicable:
            finding = (
                "Comparable-sales cannot be tested: no admitted global reported "
                "comparable-sales observations are available."
            )
        else:
            finding = (
                "Comparable-sales cannot be tested: no aligned global reported "
                "percentages exist for statement-derived revenue growth."
            )
    else:
        finding = _finding_with_counterexamples(
            f"{interpretation.observations.sample_size} identity-period "
            "observation(s) across "
            f"{len(interpretation.observations.periods_tested)} period-end "
            f"date(s). Verdict: {interpretation.verdict.replace('_', ' ')}.",
            observations,
        )
    return _base_test(
        interpretation,
        observations=observations,
        finding=finding,
        limitations=tuple(limitations),
        identity_notes=(),
    )


def word_productivity(
    interpretation: RevenueDriverThemeInterpretation,
) -> RevenueDriverHypothesisTest:
    codes = interpretation.qualification_codes
    limitations = [
        REVENUE_PER_STORE_SCOPE_NOTE,
        "Adjacent SPSF change/growth remain unavailable unless immediately "
        "adjacent semantically compatible reported observations exist.",
        *word_spsf_evidence_limits(
            interpretation.observations.spsf_missing_periods,
            interpretation.observations.spsf_unavailable,
            interpretation.observations.deferred_disagreements,
        ),
    ]
    if QUAL_NOT_OUTCOME in codes:
        limitations.append(_objective_sentence())
    observations = _worded_observations(interpretation, _productivity_note)
    bundle = interpretation.observations
    rps_notes = []
    if bundle.rps_increases or bundle.rps_declines:
        rps_notes.append(
            f"Period-end Revenue per Store rose in {bundle.rps_increases} aligned "
            f"period(s) and declined in {bundle.rps_declines}. This identity cannot "
            "independently demonstrate store productivity."
        )
    if not bundle.spsf_growth_available:
        finding = (
            "Sales-per-square-foot growth cannot be tested from admitted "
            f"history. Failed requirement: {FAILED_SPSF_GROWTH}. "
            + (" ".join(rps_notes) if rps_notes else "")
        ).strip()
    else:
        finding = (
            f"{len(bundle.periods_tested)} aligned SPSF-growth observation(s). "
            + (" ".join(rps_notes) if rps_notes else "")
            + f" Verdict: {interpretation.verdict.replace('_', ' ')}."
        ).strip()
    return _base_test(
        interpretation,
        observations=observations,
        finding=finding,
        limitations=tuple(limitations),
        identity_notes=(REVENUE_PER_STORE_SCOPE_NOTE,),
    )


def word_geographic(
    interpretation: RevenueDriverThemeInterpretation,
) -> RevenueDriverHypothesisTest:
    codes = interpretation.qualification_codes
    limitations = [
        "Revenue-growth contributions are an arithmetic decomposition of "
        "reported geographic revenue changes, not organic, constant-currency, "
        "or causal growth.",
        "Reported-currency geographic results are not substituted with "
        "constant-currency disclosures.",
    ]
    if QUAL_NOT_OUTCOME in codes:
        limitations.append(_objective_sentence())
    observations = _worded_observations(interpretation, _geographic_note)
    identities = interpretation.observations.geographic_identities
    unique_tested = interpretation.observations.periods_tested
    if interpretation.verdict == VERDICT_INSUFFICIENT:
        if not interpretation.observations.applicable:
            finding = (
                "Geographic growth cannot be tested: no admitted geographic "
                "segment history is available."
            )
        else:
            finding = (
                "Geographic growth cannot be tested: no aligned contribution "
                "observations exist."
            )
    else:
        finding = _finding_with_counterexamples(
            f"{len(unique_tested)} aligned period(s) and {len(identities)} "
            "admitted geographic identit"
            f"{'y' if len(identities) == 1 else 'ies'}. Findings use reported "
            "currency. Verdict: "
            f"{interpretation.verdict.replace('_', ' ')}.",
            observations,
        )
    return _base_test(
        interpretation,
        observations=observations,
        finding=finding,
        limitations=tuple(limitations),
        identity_notes=(),
    )


_THEME_WORDERS = {
    THEME_STORE_EXPANSION: word_store_expansion,
    THEME_COMPARABLE_SALES: word_comparable_sales,
    THEME_PRODUCTIVITY: word_productivity,
    THEME_GEOGRAPHIC_GROWTH: word_geographic,
}


def word_theme(
    interpretation: RevenueDriverThemeInterpretation,
) -> RevenueDriverHypothesisTest:
    return _THEME_WORDERS[interpretation.observations.theme](interpretation)


def _has_counterexample(test: RevenueDriverHypothesisTest) -> bool:
    return any(item.counterexample for item in test.observations) or test.rps_declines > 0


def word_identity_assessment(
    validity: RevenueIdentityValidity,
    test: RevenueDriverHypothesisTest,
    footprint: FootprintIntensityIdentity | None = None,
) -> MarginRelationshipAssessment:
    contradictions = test.finding if _has_counterexample(test) else "none required"
    if validity.name == "geographic revenue reconstruction":
        return MarginRelationshipAssessment(
            name=validity.name,
            kind=validity.kind,
            direction="reported geographic components reconstruct consolidated revenue",
            magnitude=(
                f"{validity.identity_count} geographic identities across "
                f"{validity.period_count} periods"
            ),
            reconstruction=(
                "sum of reported geographic net revenue versus reported "
                "consolidated revenue"
            ),
            residual=(
                f"largest absolute level residual is {validity.max_resid:.6f}"
                if validity.max_resid is not None
                else "residual unavailable"
            ),
            stability="the arithmetic split holds in every period with complete components",
            contradictions=contradictions,
            disclosure_support=(
                "reported-currency geographic segment net revenue; not organic "
                "or constant-currency"
            ),
            established=validity.established,
            limitation="" if validity.established else "reconstruction residual remains",
        )
    return MarginRelationshipAssessment(
        name=validity.name,
        kind=validity.kind,
        direction=(
            "store-count and company-wide revenue per store reconstruct "
            "consolidated revenue"
        ),
        magnitude=FOOTPRINT_IDENTITY_CONVENTION,
        reconstruction="Revenue = stores × company-wide revenue per store",
        residual=(
            f"largest absolute identity residual is {validity.max_resid:.6f}"
            if validity.max_resid is not None
            else "residual unavailable"
        ),
        stability="the identity holds whenever both factors are defined",
        contradictions=contradictions,
        disclosure_support=REVENUE_PER_STORE_SCOPE_NOTE,
        established=validity.established,
    )


def word_revenue_assessment(
    decision: RevenueAssessmentDecision,
    test: RevenueDriverHypothesisTest,
) -> MarginRelationshipAssessment:
    contradictions = test.finding if _has_counterexample(test) else "none required"
    if decision.name == "comparable-sales coincidence":
        return MarginRelationshipAssessment(
            name=decision.name,
            kind=decision.kind,
            direction=(
                "positive comparable-sales percentages coincided with revenue "
                "growth where aligned"
            ),
            magnitude=f"{test.sample_size} aligned observation(s)",
            reconstruction=(
                "not a new-store contribution and not an overlapping "
                "geography/channel add-on"
            ),
            residual="revenue-growth-minus-comparable-sales remains a descriptive difference",
            stability="definitions, populations, and calendars change and are not one series",
            contradictions=contradictions,
            disclosure_support=(
                "only compatible reported global comparable-sales identities are used"
            ),
            established=decision.established,
            limitation=test.failed_requirement or test.additional_evidence,
        )
    if decision.name == "sales-per-square-foot productivity":
        return MarginRelationshipAssessment(
            name=decision.name,
            kind=decision.kind,
            direction="adjacent SPSF growth is the disclosed productivity test",
            magnitude=f"{test.sample_size} aligned SPSF-growth observation(s)",
            reconstruction="company-wide revenue per store is not this test",
            residual="unavailable adjacent SPSF growth is not bridged",
            stability="calendar, definition, and disagreement gaps remain",
            contradictions=contradictions,
            disclosure_support=test.failed_requirement or ADDITIONAL_SPSF,
            established=decision.established,
            limitation=test.failed_requirement or ADDITIONAL_SPSF,
        )
    return MarginRelationshipAssessment(
        name=decision.name,
        kind=decision.kind,
        direction=test.finding,
        magnitude=f"{test.sample_size} aligned observation(s)",
        reconstruction="disclosure-led historical comparison, not a causal proof",
        residual="descriptive differences only",
        stability="period-by-period notes retain counterexamples",
        contradictions=contradictions,
        disclosure_support="; ".join(test.limitations[:2]) if test.limitations else "",
        established=decision.established,
        limitation=test.failed_requirement,
    )


def word_footprint_identity(
    footprint: FootprintIntensityIdentity | None,
) -> FootprintIntensityIdentity | None:
    if footprint is None:
        return None
    return FootprintIntensityIdentity(
        stores=footprint.stores,
        intensity=footprint.intensity,
        reconstructed_revenue=footprint.reconstructed_revenue,
        reconstruction_residual=footprint.reconstruction_residual,
        store_effect=footprint.store_effect,
        intensity_effect=footprint.intensity_effect,
        interaction=footprint.interaction,
        change_residual=footprint.change_residual,
        convention=FOOTPRINT_IDENTITY_CONVENTION,
        scope_note=REVENUE_PER_STORE_SCOPE_NOTE,
    )
