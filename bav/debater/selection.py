"""Driver question construction, strongest conclusions, and thesis compose."""

from __future__ import annotations

from bav.inferer.selection import (
    CLAIM_ATTRIBUTION,
    CLAIM_IDENTITY,
    CLAIM_LOCALIZATION,
    CLAIM_PROXY,
    CLAIM_REPORTED,
    CLAIM_UNRESOLVED,
    DriverInterpretation,
    geographic_materiality_rationale,
    interpret_driver_gates,
)
from bav.modeler.research.drivers_view import completed_reconstruction
from bav.modeler.research.geo_conditions import (
    OFFSET_GREATER,
    GeographicClaimConditions,
    geo_profit_at,
    geographic_claim_conditions,
    latest_index,
    period_labels,
    present,
)
from bav.modeler.research.records import ResearchClaim, ResearchQuestion

_NEUTRAL_GEO_CONCLUSION = (
    "Geographic evidence localizes revenue and profit changes without identifying causes."
)

def geographic_strongest_conclusion(conditions: GeographicClaimConditions) -> str:
    if (
        conditions.revenue_offset is not None
        and conditions.americas_profit_declined
        and conditions.consolidated_profit_weaker
        and conditions.corporate_burden_increased
    ):
        return (
            "International revenue offset was insufficient to offset the "
            "Americas profit decline and higher corporate/unallocated burden."
        )
    if (
        conditions.revenue_offset is not None
        and conditions.americas_profit_declined
        and conditions.consolidated_profit_weaker
    ):
        return (
            "International revenue offset was insufficient to offset the "
            "Americas profit decline."
        )
    if conditions.revenue_offset == OFFSET_GREATER:
        return (
            "International revenue more than offset the Americas revenue decline "
            "without establishing a profit offset."
        )
    return _NEUTRAL_GEO_CONCLUSION


def investigate_driver_questions(view) -> tuple[ResearchQuestion, ...]:
    """Build candidate questions from available verified series only."""
    latest = latest_index(view)
    if latest is None:
        return ()
    questions: list[ResearchQuestion] = []
    questions.extend(_growth_questions(view, latest))
    questions.extend(_geography_questions(view, latest))
    questions.extend(_margin_questions(view, latest))
    questions.extend(_cash_questions(view, latest))
    return tuple(questions)


def interpret_driver_selection(view) -> DriverInterpretation:
    questions = investigate_driver_questions(view)
    return interpret_driver_gates(view, questions)


def _growth_questions(view, latest: int) -> list[ResearchQuestion]:
    questions: list[ResearchQuestion] = []
    rev_g = view.revenue_growth[latest] if latest < len(view.revenue_growth) else None
    store_g = view.store_growth[latest] if latest < len(view.store_growth) else None
    store_term = (
        None
        if view.footprint_store_effect is None
        else view.footprint_store_effect[latest]
    )
    if present(rev_g) and present(store_g):
        diverged = store_g > rev_g
        questions.append(
            ResearchQuestion(
                identifier="footprint_intensity",
                question=(
                    "Whether continued store expansion is accompanied by stronger "
                    "company-wide revenue generation"
                ),
                entity=view.display_name,
                population="company-operated stores and consolidated revenue",
                periods=period_labels(view, (latest - 1, latest) if latest else (latest,)),
                outcome="consolidated revenue versus store-count growth",
                materiality_rationale=(
                    "Continuing footprint investment coinciding with slower company "
                    "revenue growth changes the expansion-economics question."
                    if diverged
                    else "Store-count and revenue growth are both observed and remain eligible."
                ),
                temporal_character=(
                    "latest-year divergence; persistence is indeterminate"
                    if diverged
                    else "latest-year comparison; persistence is indeterminate"
                ),
                magnitude="",
                mechanisms=(
                    "weaker demand",
                    "slower maturation of added capacity",
                    "channel mix",
                    "unequal-week comparison",
                ),
                alternative=(
                    "Opening dates, regional mix, digital revenue and calendar length "
                    "can produce the same divergence without weaker store productivity."
                ),
                discriminating_evidence=(
                    "Compatible store-only revenue, intra-year exposure, cohort "
                    "maturation, space and channel evidence."
                ),
                claims=(
                    ResearchClaim(
                        identifier="store_count_growth",
                        wording="",
                        claim_type=CLAIM_REPORTED,
                        measurement_role="operating KPI",
                        evidence_refs=("operating_kpi.period_end_count",),
                        transformation="adjacent growth of period-end count",
                        qualifiers=("period-end count is not average operating exposure",),
                        dependencies=("store_count",),
                        mechanism_support="none; count is an activity observation",
                        counterevidence="",
                        status="supported",
                    ),
                    ResearchClaim(
                        identifier="revenue_store_intensity",
                        wording="",
                        claim_type=CLAIM_PROXY,
                        measurement_role="proxy",
                        evidence_refs=("revenue_per_store.period_end_revenue_per_store",),
                        transformation="consolidated revenue / period-end store count",
                        qualifiers=(
                            "includes non-store revenue",
                            "period-end denominator",
                        ),
                        dependencies=("revenue", "store_count"),
                        mechanism_support="not established",
                        counterevidence="digital and other channels contribute to the numerator",
                        status="supported",
                    ),
                    ResearchClaim(
                        identifier="store_count_term",
                        wording="",
                        claim_type=CLAIM_IDENTITY,
                        measurement_role="mathematical decomposition",
                        evidence_refs=("revenue_driver.footprint_identity",),
                        transformation="prior intensity × store-count change",
                        qualifiers=("allocation convention is not unique",),
                        dependencies=("revenue", "store_count"),
                        mechanism_support="identity only; exact reconstruction is not causation",
                        counterevidence="",
                        status="supported" if present(store_term) else "unavailable",
                    ),
                ),
                strongest_conclusion=(
                    "Footprint grew faster than total-company revenue, warranting "
                    "investigation of expansion economics."
                    if diverged
                    else "Store-count and revenue growth are both observed on their stated bases."
                ),
                unresolved_requirement=(
                    "Store-only revenue, exposure through the year, cohort "
                    "maturation, space and channel evidence."
                ),
                reopening_condition=(
                    "A compatible store-only revenue series or intra-year exposure "
                    "measure becomes available."
                ),
                publication="",
                publication_reason="",
                overlap=("comparable_sales",),
            )
        )
    compsales = tuple(view.comparable_sales)
    populations = {point.population for point in compsales}
    bases = {point.basis for point in compsales}
    compatible = len(populations) <= 1 and len(bases) <= 1 and view.fifty_three_week_period is None
    if compsales:
        latest_comp = next(
            (point for point in reversed(compsales) if point.period == view.periods[latest]),
            compsales[-1],
        )
        questions.append(
            ResearchQuestion(
                identifier="comparable_sales",
                question="How much the existing business supports growth on its stated basis",
                entity=view.display_name,
                population=latest_comp.population,
                periods=tuple(
                    view.labels[view.periods.index(point.period)]
                    for point in compsales
                    if point.period in view.periods
                ),
                outcome="reported comparable sales",
                materiality_rationale=(
                    "Positive comparable sales on the latest stated basis qualify "
                    "the expansion discussion; they do not measure contribution "
                    "to consolidated growth."
                ),
                temporal_character="period-specific reported KPI; not a continuous series",
                magnitude="",
                mechanisms=("price", "units", "channel mix", "measured-population change"),
                alternative=(
                    "Price, units, mix and population changes can produce the same "
                    "reported comparable-sales observation."
                ),
                discriminating_evidence=(
                    "Documented equivalent populations and calendars, revenue weights, "
                    "and evidence separating price and volume."
                ),
                claims=(
                    ResearchClaim(
                        identifier="compsales_period",
                        wording="",
                        claim_type=CLAIM_REPORTED,
                        measurement_role="operating KPI",
                        evidence_refs=("management_kpi.comparable_sales_growth",),
                        transformation="reported percent; no cross-period join",
                        qualifiers=(
                            "definitions and comparison windows differ",
                            "53-week years are not equal-week measures",
                        ),
                        dependencies=("comparable_sales_population", "calendar_basis"),
                        mechanism_support="none",
                        counterevidence=(
                            ""
                            if compatible
                            else "Changing channel definitions and calendars block a continuous trend."
                        ),
                        status="supported",
                    ),
                    ResearchClaim(
                        identifier="compsales_trend",
                        wording="",
                        claim_type=CLAIM_UNRESOLVED,
                        measurement_role="rejected comparison",
                        evidence_refs=("management_kpi.comparable_sales_growth",),
                        transformation="blocked join of incompatible observations",
                        qualifiers=("definition", "calendar", "population"),
                        dependencies=("comparable_sales_population", "calendar_basis"),
                        mechanism_support="not available",
                        counterevidence="incompatible series",
                        status="blocked" if not compatible else "unsupported",
                    ),
                ),
                strongest_conclusion=(
                    "The latest comparable-sales observation is positive on its "
                    "stated basis and cannot be joined to earlier observations "
                    "as one trend."
                ),
                unresolved_requirement=(
                    "Equivalent populations, calendars and revenue weights before "
                    "any contribution or trend claim."
                ),
                reopening_condition=(
                    "Comparable-sales observations share population, "
                    "definition and calendar."
                ),
                publication="",
                publication_reason="",
                overlap=("footprint_intensity",),
            )
        )
    if getattr(view, "stores", ()) or getattr(view, "revenue_per_store", ()):
        questions.append(
            ResearchQuestion(
                identifier="sales_per_square_foot",
                question="Whether space productivity can be measured from available SPSF disclosures",
                entity=view.display_name,
                population="company-operated stores",
                periods=(),
                outcome="sales per square foot",
                materiality_rationale=(
                    "A productivity reading would change expansion economics, but "
                    "available SPSF observations are definition- and calendar-incompatible."
                ),
                temporal_character="incompatible historical observations",
                magnitude="",
                mechanisms=(),
                alternative="Company-wide revenue per store remains an intensity proxy only.",
                discriminating_evidence="Aligned SPSF definitions, calendars and store-only revenue.",
                claims=(
                    ResearchClaim(
                        identifier="spsf_blocked",
                        wording="",
                        claim_type=CLAIM_UNRESOLVED,
                        measurement_role="rejected comparison",
                        evidence_refs=("management_kpi.sales_per_square_foot",),
                        transformation="blocked",
                        qualifiers=("definition disagreement", "calendar misalignment"),
                        dependencies=("spsf_definition", "spsf_calendar"),
                        mechanism_support="not available",
                        counterevidence="filings disagree on definition and later years do not line up",
                        status="blocked",
                    ),
                ),
                strongest_conclusion="No productivity series is available on a comparable basis.",
                unresolved_requirement="Compatible SPSF observations and store-only revenue.",
                reopening_condition="SPSF observations share definition and calendar.",
                publication="",
                publication_reason="",
            )
        )
    return questions


def _geography_questions(view, latest: int) -> list[ResearchQuestion]:
    contrib = view.geo_contributions[latest] if latest < len(view.geo_contributions) else {}
    profit = geo_profit_at(view, latest)
    conditions = geographic_claim_conditions(view, latest)
    has_evidence = (
        any(present(value) for value in contrib.values())
        or any(present(value) for value in profit.values())
        or present(conditions.consolidated_profit)
    )
    if not has_evidence:
        return []
    return [
        ResearchQuestion(
            identifier="geographic_localization",
            question=(
                "Whether international growth offsets weaker Americas performance "
                "at both the revenue and profit levels"
            ),
            entity=view.display_name,
            population="reported geographic segments plus corporate/unallocated items",
            periods=period_labels(view, (latest - 1, latest) if latest else (latest,)),
            outcome="consolidated revenue and operating profit",
            materiality_rationale=geographic_materiality_rationale(conditions),
            temporal_character="latest adjacent year; persistence is not established",
            magnitude="",
            mechanisms=(
                "lower Americas demand",
                "cost pressure",
                "currency",
                "product or channel mix",
                "calendar",
                "cost allocation",
            ),
            alternative=(
                "Currency, mix, calendar effects and cost allocation can produce "
                "the same geographic pattern without identifying a regional mechanism."
            ),
            discriminating_evidence=(
                "Compatible regional price/volume, currency and cost evidence."
            ),
            claims=(
                ResearchClaim(
                    identifier="geo_revenue_localization",
                    wording="",
                    claim_type=CLAIM_LOCALIZATION,
                    measurement_role="segment localization",
                    evidence_refs=("geographic_segment.revenue_growth_contribution",),
                    transformation="arithmetic split of reported-currency revenue change",
                    qualifiers=(
                        "not organic growth",
                        "not constant-currency",
                        "not a cause",
                    ),
                    dependencies=("historical_segment.net_revenue",),
                    mechanism_support="none; localization is not attribution",
                    counterevidence="",
                    status="supported",
                ),
                ResearchClaim(
                    identifier="geo_profit_localization",
                    wording="",
                    claim_type=CLAIM_LOCALIZATION,
                    measurement_role="segment localization",
                    evidence_refs=(
                        "geographic_segment.operating_profit_amount_change",
                        "geographic_segment.reconciling_operating_profit_amount_change",
                    ),
                    transformation="adjacent amount change; reconciling items retained",
                    qualifiers=("not a standalone return", "not a combination-benefit claim"),
                    dependencies=("historical_segment.income_from_operations",),
                    mechanism_support="none",
                    counterevidence="",
                    status="supported" if present(conditions.consolidated_profit) else "unavailable",
                ),
            ),
            strongest_conclusion=geographic_strongest_conclusion(conditions),
            unresolved_requirement=(
                "Regional price/volume, currency and cost evidence before any "
                "organic-growth or mechanism claim."
            ),
            reopening_condition=(
                "Compatible regional volume, currency and allocated-cost series appear."
            ),
            publication="",
            publication_reason="",
        )
    ]


def _margin_questions(view, latest: int) -> list[ResearchQuestion]:
    om = (
        None
        if view.reported_operating_margin_change is None
        else view.reported_operating_margin_change[latest]
    )
    gm = (
        None
        if view.gross_margin_contribution is None
        else view.gross_margin_contribution[latest]
    )
    complete = completed_reconstruction(view, latest)
    attributions = tuple(view.attributions)
    latest_period = view.periods[latest]
    latest_attr = tuple(item for item in attributions if item.period == latest_period)
    questions: list[ResearchQuestion] = []
    if present(om) or present(gm):
        questions.append(
            ResearchQuestion(
                identifier="operating_margin_bridge",
                question="Which accounting movements explain the latest operating-margin change",
                entity=view.display_name,
                population="consolidated income statement",
                periods=period_labels(view, (latest - 1, latest) if latest else (latest,)),
                outcome="reported operating margin",
                materiality_rationale=(
                    "The latest operating-margin movement is material to the "
                    "consolidated operating-profit change."
                ),
                temporal_character=(
                    "latest-year accounting identity; earlier recovery includes "
                    "disappearing episodic charges"
                ),
                magnitude="",
                mechanisms=(
                    "lower pricing realization",
                    "higher merchandise or distribution costs",
                    "reduced cost absorption",
                    "mix",
                ),
                alternative=(
                    "Cost pressure and mix changes are credible alternatives; the "
                    "decomposition cannot identify their separate effects."
                ),
                discriminating_evidence=(
                    "Economic quantities linked to the relevant cost or revenue base; "
                    "no residual renamed as mix or execution."
                ),
                claims=(
                    ResearchClaim(
                        identifier="margin_identity",
                        wording="",
                        claim_type=CLAIM_IDENTITY,
                        measurement_role="accounting identity",
                        evidence_refs=("reported_margin.contribution",),
                        transformation="signed unrounded ratio contributions",
                        qualifiers=(
                            "identity is not a mechanism",
                            *(
                                ()
                                if complete
                                else ("exact reconstruction is not established",)
                            ),
                        ),
                        dependencies=("gross_margin", "sga", "impairment", "other_operating_items"),
                        mechanism_support="none",
                        counterevidence="",
                        status="supported" if complete else "partial",
                    ),
                ),
                strongest_conclusion=(
                    "The latest operating-margin change is reconstructed from disclosed components."
                    if complete
                    else (
                        "Disclosed components provide a partial explanation of the "
                        "latest operating-margin change; a residual remains."
                    )
                ),
                unresolved_requirement=(
                    "Evidence linking specific economic quantities to the relevant "
                    "cost or revenue base."
                ),
                reopening_condition=(
                    "A disclosed subcomponent series isolates tariff, markdown, mix "
                    "or absorption effects."
                ),
                publication="",
                publication_reason="",
                overlap=("management_margin_attribution",),
            )
        )
    if latest_attr:
        quantified = tuple(item for item in latest_attr if item.approximate_amount is not None)
        questions.append(
            ResearchQuestion(
                identifier="management_margin_attribution",
                question="Whether available management explanation resolves the margin mechanism",
                entity=view.display_name,
                population="management commentary on gross profit and margins",
                periods=tuple(view.labels[view.periods.index(item.period)] for item in latest_attr if item.period in view.periods),
                outcome="gross profit and operating margin",
                materiality_rationale=(
                    "A quantified attribution is material relative to the profit "
                    "movement, but it remains management's counterfactual estimate."
                    if quantified
                    else "Management attributes the latest-year margin movement; the mechanism is unresolved."
                ),
                temporal_character="episodic attributed commentary for the latest year",
                magnitude="",
                mechanisms=tuple(item.theme for item in latest_attr),
                alternative=(
                    "Demand-related markdowns, product mix, offsetting measures "
                    "and overlapping cost effects could alter the interpretation."
                ),
                discriminating_evidence=(
                    "The counterfactual, timing, overlap, offsets and corroborating "
                    "operational evidence."
                ),
                claims=(
                    ResearchClaim(
                        identifier="attributed_gross_profit_pressure",
                        wording="",
                        claim_type=CLAIM_ATTRIBUTION,
                        measurement_role="management attribution",
                        evidence_refs=tuple(
                            f"{item.source_file}:{item.page_reference}" for item in latest_attr
                        ),
                        transformation="source-bound disclosure; not a reconstructed bridge term",
                        qualifiers=(
                            "not independently verified",
                            "counterfactual scope",
                            "outside the accounting bridge",
                        ),
                        dependencies=tuple(item.source_file for item in latest_attr),
                        mechanism_support="not independently established",
                        counterevidence=(
                            "Year-on-year gross-profit change need not equal the "
                            "attributed counterfactual reduction."
                        ),
                        status="supported_as_attribution",
                    ),
                ),
                strongest_conclusion=(
                    "Management attributes latest-year pressure; the attribution "
                    "is documented and the mechanism remains independently unresolved."
                ),
                unresolved_requirement=(
                    "Counterfactual construction, timing, overlap, offsets and "
                    "corroborating operational evidence."
                ),
                reopening_condition=(
                    "An independently reconstructed causal series appears for the "
                    "attributed items."
                ),
                publication="",
                publication_reason="",
                overlap=("operating_margin_bridge",),
            )
        )
    elif present(om) or present(gm):
        questions.append(
            ResearchQuestion(
                identifier="management_margin_attribution",
                question="Whether a source-bound management explanation of the margin movement is available",
                entity=view.display_name,
                population="management commentary",
                periods=period_labels(view, (latest,)),
                outcome="gross profit and operating margin",
                materiality_rationale="An unresolved mechanism can remain consequential without a point estimate.",
                temporal_character="unavailable for the latest year",
                magnitude="",
                mechanisms=(),
                alternative="The accounting identity stands without a mechanism.",
                discriminating_evidence="A source-bound attribution with period, scope and locator.",
                claims=(),
                strongest_conclusion="No source-bound management attribution is available.",
                unresolved_requirement="Attributed commentary with locator and stated scope.",
                reopening_condition="A management attribution disclosure is available for the latest period.",
                publication="",
                publication_reason="",
            )
        )
    return questions


def _cash_questions(view, latest: int) -> list[ResearchQuestion]:
    cfo = None if view.cfo is None or latest >= len(view.cfo) else view.cfo[latest]
    ni = None if view.net_income is None or latest >= len(view.net_income) else view.net_income[latest]
    cfo_change = (
        None
        if view.cfo_change is None or latest >= len(view.cfo_change)
        else view.cfo_change[latest]
    )
    ni_change = (
        None
        if view.net_income_change is None or latest >= len(view.net_income_change)
        else view.net_income_change[latest]
    )
    remainder = (
        None
        if view.cfo_unexplained is None or latest >= len(view.cfo_unexplained)
        else view.cfo_unexplained[latest]
    )
    inventory = (
        None
        if view.inventory is None or latest >= len(view.inventory)
        else view.inventory[latest]
    )
    if not present(cfo) or not present(ni):
        return []
    weaker = present(cfo_change) and present(ni_change) and cfo_change < ni_change
    return [
        ResearchQuestion(
            identifier="cash_conversion",
            question=(
                "Whether reported earnings continue to translate into cash and "
                "whether working-capital behavior explains the change"
            ),
            entity=view.display_name,
            population="consolidated cash flow and income statement",
            periods=period_labels(view, (latest - 1, latest) if latest else (latest,)),
            outcome="operating cash flow versus net income",
            materiality_rationale=(
                "The cash movement is material and larger than the earnings movement."
                if weaker
                else "CFO and net income are both observed and remain eligible."
            ),
            temporal_character="latest adjacent year; not a manipulation finding",
            magnitude="",
            mechanisms=(
                "inventory accumulation",
                "growth preparation",
                "sourcing timing",
                "currency",
                "tax movements",
                "other settlement timing",
            ),
            alternative=(
                "Inventory, tax timing and other settlement items compete with a "
                "weak-demand explanation; the available CFO components need not "
                "explain the whole movement."
            ),
            discriminating_evidence=(
                "Missing reconciliation basis, inventory composition and turnover, "
                "tax timing and, if seasonality is asserted, intra-year observations."
            ),
            claims=(
                ResearchClaim(
                    identifier="cfo_versus_ni",
                    wording="",
                    claim_type=CLAIM_REPORTED,
                    measurement_role="derived diagnostic",
                    evidence_refs=("earnings_quality.operating_cash_flow", "net_income"),
                    transformation="adjacent change and CFO/net income",
                    qualifiers=("not manipulation", "not a complete explanation"),
                    dependencies=("operating_cash_flow", "net_income"),
                    mechanism_support="none",
                    counterevidence="",
                    status="supported",
                ),
                ResearchClaim(
                    identifier="cfo_remainder",
                    wording="",
                    claim_type=CLAIM_UNRESOLVED,
                    measurement_role="signed residual",
                    evidence_refs=("cash_flow.operating_components",),
                    transformation="reported CFO change minus summed adjacent operating-component changes",
                    qualifiers=("omitted disclosure is not a zero",),
                    dependencies=("cash_flow.component_lines",),
                    mechanism_support="not assigned",
                    counterevidence="",
                    status="supported" if present(remainder) else "unavailable",
                ),
                ResearchClaim(
                    identifier="inventory_observation",
                    wording="",
                    claim_type=CLAIM_REPORTED,
                    measurement_role="reported fact",
                    evidence_refs=("inventory_analysis.inventories",),
                    transformation="adjacent balance-sheet change",
                    qualifiers=("not automatically a cash-flow reconciliation",),
                    dependencies=("inventories",),
                    mechanism_support="not established",
                    counterevidence="",
                    status="supported" if present(inventory) else "unavailable",
                ),
            ),
            strongest_conclusion=(
                "Cash conversion weakened relative to earnings; the inventory "
                "question is open and the CFO remainder remains unexplained."
                if weaker
                else "CFO and net income are both observed on their stated bases."
            ),
            unresolved_requirement=(
                "The missing reconciliation basis, inventory composition and "
                "turnover evidence, and tax timing."
            ),
            reopening_condition=(
                "A complete CFO bridge or intra-year inventory observations appear."
            ),
            publication="",
            publication_reason="",
        )
    ]
