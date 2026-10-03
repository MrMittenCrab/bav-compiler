"""Overview opening wording for historical strategy synthesis."""

from __future__ import annotations

from bav.extractor.data.historical_strategy import (
    THEME_COMPARABLE_SALES,
    THEME_GEOGRAPHIC_GROWTH,
    THEME_PRODUCTIVITY,
    THEME_STORE_EXPANSION,
    HistoricalStrategyDisclosure,
    disclosure_locator,
)
from bav.modeler.engine.component_catalog import (
    COMPARABLE_SALES_SHEET_NAME,
    GEOGRAPHIC_SHEET_NAME,
    REVENUE_DRIVER_SHEET_NAME,
    REVENUE_PER_STORE_SHEET_NAME,
    SALES_PER_SQUARE_FOOT_SHEET_NAME,
    STORE_COUNT_SHEET_NAME,
)
from bav.inferer.historical_strategy import GAP_INSUFFICIENT, INFERENCE_CONTRADICTED, INFERENCE_INSUFFICIENT, INFERENCE_MIXED, INFERENCE_SUPPORTED, LIMIT_DEFERRED_SPSF
from bav.debater.historical_strategy import HistoricalStrategyJudgment, StrategyThemeJudgment
from bav.inferer.revenue_driver import VERDICT_CONTRADICTED, VERDICT_INSUFFICIENT, VERDICT_MIXED, VERDICT_SUPPORTED
from bav.modeler.revenue_driver import (
    RevenueDriverAnalysis,
    RevenueDriverHypothesisTest,
    strategy_synthesis_applicable,
)

THEME_LABELS = {
    THEME_STORE_EXPANSION: "Store expansion",
    THEME_COMPARABLE_SALES: "Comparable sales",
    THEME_PRODUCTIVITY: "Store productivity",
    THEME_GEOGRAPHIC_GROWTH: "Geographic expansion",
}
THEME_SCHEDULES = {
    THEME_STORE_EXPANSION: (
        REVENUE_DRIVER_SHEET_NAME,
        STORE_COUNT_SHEET_NAME,
        REVENUE_PER_STORE_SHEET_NAME,
    ),
    THEME_COMPARABLE_SALES: (
        REVENUE_DRIVER_SHEET_NAME,
        COMPARABLE_SALES_SHEET_NAME,
    ),
    THEME_PRODUCTIVITY: (
        REVENUE_DRIVER_SHEET_NAME,
        SALES_PER_SQUARE_FOOT_SHEET_NAME,
        REVENUE_PER_STORE_SHEET_NAME,
    ),
    THEME_GEOGRAPHIC_GROWTH: (
        REVENUE_DRIVER_SHEET_NAME,
        GEOGRAPHIC_SHEET_NAME,
    ),
}
UNTESTED_INITIATIVES = (
    "Disclosed initiatives that are not the subject of an admitted historical "
    "test remain untested. Consolidated revenue growth does not establish "
    "their success, and this opening does not claim comprehensive strategy "
    "execution."
)
WHAT_HISTORY_ESTABLISHES = (
    "The history establishes only the admitted descriptive coincidences, "
    "mixed geographic mix, and evidence gaps recorded below. It does not "
    "establish causal drivers, new-store contribution, organic growth, "
    "constant-currency performance, or comprehensive strategy execution. "
    "Strategic objectives remain plans rather than achieved outcomes."
)
DEFERRED_SPSF_LINK = (
    "The complete deferred sales-per-square-foot disagreement and detailed "
    "limitations remain on Revenue Driver Analysis; they stay audit-only and "
    "are not admitted observations in this opening."
)
PROFESSIONAL_FALLBACK = (
    "This workbook presents historical source-grounded financial analysis. "
    "Strategy and revenue-driver interpretation appear only when management "
    "disclosures and admitted operating evidence are supplied."
)


from dataclasses import dataclass


@dataclass(frozen=True)
class StrategyFindingInterpretation:
    """One theme: management statement, admitted finding, and qualified inference."""

    theme: str
    heading: str
    management_statement: str
    finding: str
    inference: str
    supporting_schedules: tuple[str, ...]
    counterexample: str


@dataclass(frozen=True)
class HistoricalStrategySynthesis:
    """Concise opening interpretation connecting findings to disclosed strategy."""

    lead: str
    interpretations: tuple[StrategyFindingInterpretation, ...]
    productivity_gap: str
    untested: str
    limits: str
    navigation: tuple[str, ...]


def format_management_statement(item: HistoricalStrategyDisclosure) -> str:
    role = item.role.replace("_", " ")
    return f'{item.text} [{disclosure_locator(item)}] ({role})'


def _management_statement(judgment: StrategyThemeJudgment) -> str:
    parts = [format_management_statement(item) for item in judgment.featured_disclosures]
    if judgment.objective_disclosures:
        additional = "; ".join(
            f"[{disclosure_locator(item)}] ({item.role.replace('_', ' ')})"
            for item in judgment.objective_disclosures
        )
        parts.append("Additional statements: " + additional + ".")
    return " ".join(parts)


def _join_labels(labels: list[str]) -> str:
    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} and {labels[1]}"
    return ", ".join(labels[:-1]) + f", and {labels[-1]}"


def _schedule_clause(theme: str) -> str:
    names = THEME_SCHEDULES.get(theme, (REVENUE_DRIVER_SHEET_NAME,))
    return f"See {_join_labels(list(names))}."


def _theme_label(theme: str) -> str:
    return THEME_LABELS.get(theme, theme.replace("_", " "))


def _lowered_label(theme: str) -> str:
    label = _theme_label(theme)
    return label[0].lower() + label[1:] if label else theme


def word_verdict_inference(
    test: RevenueDriverHypothesisTest,
    judgment: StrategyThemeJudgment,
) -> str:
    lowered = _lowered_label(test.theme)
    if judgment.inference == INFERENCE_SUPPORTED:
        base = (
            f"Admitted history is descriptively consistent with disclosed "
            f"{lowered} as a coincident of revenue growth over "
            f"{test.sample_size} aligned observation"
            f"{'' if test.sample_size == 1 else 's'}."
        )
    elif judgment.inference == INFERENCE_MIXED:
        base = (
            f"Admitted history is mixed for disclosed {lowered}: some aligned "
            "periods or segments coincide with revenue growth and others diverge."
        )
    elif judgment.inference == INFERENCE_CONTRADICTED:
        base = (
            f"Admitted history contradicts disclosed {lowered} as a coincident "
            "revenue descriptor over the tested periods."
        )
    else:
        failed = test.failed_requirement or "required admitted evidence"
        base = (
            f"Admitted history cannot test disclosed {lowered}. Failed "
            f"requirement: {failed}. The disclosure remains a management "
            "statement, not a demonstrated outcome."
        )
    extras = tuple(
        test.observations[index].note
        for index in judgment.counterexample_ids
        if test.observations[index].note
    )
    qualification = _qualification_sentences(judgment)
    return " ".join(part for part in (base, *extras, qualification) if part)


def _qualification_sentences(judgment: StrategyThemeJudgment) -> str:
    bits: list[str] = []
    for code in judgment.qualification_codes:
        if code == "descriptive_store":
            bits.append(
                "The revenue-versus-store-count difference is descriptive and is not "
                "new-store contribution, organic growth, or causal evidence."
            )
        elif code == "descriptive_compsales":
            bits.append(
                "The revenue-versus-comparable-sales difference is descriptive only. "
                "Reported and constant-currency series remain separate."
            )
        elif code == "compsales_ineligible":
            bits.append(
                "Historical comparable-sales-to-comparable-sales comparison "
                "remains ineligible."
            )
        elif code == "rps_not_productivity":
            bits.append(
                "Total-company revenue divided by company-operated stores is not "
                "independent productivity evidence."
            )
        elif code == "arithmetic_geo":
            bits.append(
                "Geographic contributions are an arithmetic decomposition of "
                "reported revenue, not organic, constant-currency, or causal growth."
            )
        elif code == "not_outcome":
            bits.append(
                "Strategic objectives and plans are management statements, not "
                "achieved historical outcomes."
            )
    return " ".join(bits)


def word_lead(
    tests: tuple[RevenueDriverHypothesisTest, ...],
    judgment: HistoricalStrategyJudgment,
) -> str:
    sentences: list[str] = []
    supported = [_lowered_label(theme) for theme in judgment.verdict_groups.get(VERDICT_SUPPORTED, ())]
    if supported:
        sentences.append(
            "Admitted history is descriptively consistent with "
            + _join_labels(supported)
            + " over aligned periods."
        )
    mixed = [_lowered_label(theme) for theme in judgment.verdict_groups.get(VERDICT_MIXED, ())]
    if mixed:
        sentences.append(
            _join_labels(mixed).capitalize()
            + " "
            + ("is" if len(mixed) == 1 else "are")
            + " mixed across periods or segments."
        )
    contradicted = [
        _lowered_label(theme)
        for theme in judgment.verdict_groups.get(VERDICT_CONTRADICTED, ())
    ]
    if contradicted:
        sentences.append(
            "Admitted history contradicts "
            + _join_labels(contradicted)
            + " as a coincident revenue descriptor."
        )
    insufficient = [
        _lowered_label(theme)
        for theme in judgment.verdict_groups.get(VERDICT_INSUFFICIENT, ())
    ]
    if insufficient:
        sentences.append(
            _join_labels(insufficient).capitalize()
            + " cannot be treated as a demonstrated historical revenue driver "
            "because the required admitted test is missing."
        )
    if judgment.has_counterexamples:
        sentences.append(
            "Period-specific store and geographic counterexamples prevent "
            "reading the history as lockstep store growth or uniformly "
            "positive geographic contributions."
        )
    sentences.append(
        "Taken together, the tests describe a historical growth pattern; they "
        "do not establish causal drivers, comprehensive strategy execution, "
        "or the success of untested initiatives."
    )
    return " ".join(sentences)


def word_productivity_gap(
    tests: tuple[RevenueDriverHypothesisTest, ...],
    judgment: HistoricalStrategyJudgment,
) -> str:
    productivity = next(
        (test for test in tests if test.theme == THEME_PRODUCTIVITY),
        None,
    )
    if productivity is None:
        return ""
    parts: list[str] = []
    if judgment.productivity_gap_kind == GAP_INSUFFICIENT:
        parts.append(
            "Disclosed sales-per-square-foot use cannot support a productivity "
            "contribution in this synthesis. Adjacent SPSF growth is unavailable "
            f"on admitted history (sample size {productivity.sample_size})."
        )
    else:
        parts.append(
            f"Store-productivity verdict: {productivity.verdict.replace('_', ' ')} "
            f"(sample size {productivity.sample_size})."
        )
    parts.append(
        "Period-end Revenue per Store is an identity using total-company "
        "revenue divided by company-operated stores and is not independent "
        "productivity evidence."
    )
    if judgment.has_deferred_spsf or LIMIT_DEFERRED_SPSF in judgment.limit_codes:
        parts.append(DEFERRED_SPSF_LINK)
    return " ".join(parts)


def _navigation(tests: tuple[RevenueDriverHypothesisTest, ...]) -> tuple[str, ...]:
    names: list[str] = []
    for test in tests:
        for name in THEME_SCHEDULES.get(test.theme, ()):
            if name not in names:
                names.append(name)
    if REVENUE_DRIVER_SHEET_NAME not in names:
        names.insert(0, REVENUE_DRIVER_SHEET_NAME)
    return tuple(names)


def compose_interpretations(
    tests: tuple[RevenueDriverHypothesisTest, ...],
    judgment: HistoricalStrategyJudgment,
) -> tuple[StrategyFindingInterpretation, ...]:
    by_theme = {item.theme: item for item in judgment.themes}
    rows: list[StrategyFindingInterpretation] = []
    for test in tests:
        theme_judgment = by_theme[test.theme]
        extras = tuple(
            test.observations[index].note
            for index in theme_judgment.counterexample_ids
            if test.observations[index].note
        )
        rows.append(
            StrategyFindingInterpretation(
                theme=test.theme,
                heading=THEME_LABELS.get(
                    test.theme, test.theme.replace("_", " ").title()
                ),
                management_statement=_management_statement(theme_judgment),
                finding=f"{test.finding} {_schedule_clause(test.theme)}",
                inference=word_verdict_inference(test, theme_judgment),
                supporting_schedules=THEME_SCHEDULES.get(
                    test.theme, (REVENUE_DRIVER_SHEET_NAME,)
                ),
                counterexample=" ".join(extras),
            )
        )
    return tuple(rows)


def compute_historical_strategy_synthesis(
    financials,
    analysis: RevenueDriverAnalysis | None = None,
    judgment: HistoricalStrategyJudgment | None = None,
) -> HistoricalStrategySynthesis:
    """Word completed historical-strategy judgments for the Overview opening."""
    if not strategy_synthesis_applicable(financials):
        raise ValueError("strategy synthesis requires admitted strategy disclosures")
    if analysis is None:
        raise ValueError("strategy synthesis requires a completed revenue-driver analysis")
    tests = analysis.tests
    if not tests:
        raise ValueError("strategy synthesis requires at least one driver test")
    if judgment is None:
        raise ValueError("strategy synthesis requires a completed historical-strategy judgment")
    return HistoricalStrategySynthesis(
        lead=word_lead(tests, judgment),
        interpretations=compose_interpretations(tests, judgment),
        productivity_gap=word_productivity_gap(tests, judgment),
        untested=UNTESTED_INITIATIVES,
        limits=WHAT_HISTORY_ESTABLISHES,
        navigation=_navigation(tests),
    )
