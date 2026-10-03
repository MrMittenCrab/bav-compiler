"""Composer Driver role, order, wording, and exhibit selection."""

from __future__ import annotations

from dataclasses import replace

from bav.composer.research.selection_roles import (
    PUBLICATION_APPENDIX,
    PUBLICATION_EXCLUDED,
    PUBLICATION_MAIN,
    ROLE_APPENDIX,
    ROLE_EXCLUDED,
    ROLE_PRINCIPAL,
    ROLE_SECONDARY,
)
from bav.debater.argument_selection import assign_driver_roles
from bav.inferer.selection import DriverInterpretation
from bav.modeler.research.drivers_view import (
    completed_intensity_growth,
    completed_reconstruction,
)
from bav.modeler.research.geo_conditions import geographic_claim_conditions, present
from bav.modeler.research.records import ResearchClaim, ResearchQuestion, ResearchSelection, SelectionDecision

_NEUTRAL_GEO_FIGURE = (
    "How did geographic revenue and operating-profit changes compare, "
    "including corporate/unallocated items?"
)


def geographic_figure_question(conditions) -> str:
    if conditions.revenue_offset is not None and conditions.americas_profit_declined:
        return (
            "Did international revenue growth offset Americas profit deterioration, "
            "including corporate/unallocated items?"
        )
    return _NEUTRAL_GEO_FIGURE


def _word_claim(claim: ResearchClaim) -> ResearchClaim:
    wording = {
        "store_count_growth": "Period-end company-operated store count changed as reported.",
        "revenue_store_intensity": (
            "Company-wide revenue per period-end store is a derived "
            "intensity proxy, not store productivity."
        ),
        "store_count_term": (
            "The store-count term in the footprint identity is an "
            "arithmetic allocation, not measured new-store revenue."
        ),
        "compsales_period": (
            "Each period's selected comparable-sales observation is "
            "positive on its stated basis."
        ),
        "compsales_trend": "A continuous deceleration claim across all observations is not supported.",
        "spsf_blocked": "Sales per square foot cannot support a productivity reading.",
        "geo_revenue_localization": "Reported geographic revenue changes localize where growth occurred.",
        "geo_profit_localization": (
            "Reported geographic operating-profit changes, including "
            "corporate/unallocated items, localize the profit movement."
        ),
        "attributed_gross_profit_pressure": (
            "Management's attributed explanation is preserved with its locator and scope."
        ),
        "cfo_versus_ni": (
            "Reported CFO and net income are compared as diagnostics, not as an earnings-quality judgment."
        ),
        "cfo_remainder": "An incomplete CFO reconciliation retains its signed unexplained remainder.",
        "inventory_observation": (
            "Balance-sheet inventory change is observed and is not substituted for the cash-flow inventory line."
        ),
    }.get(claim.identifier, claim.wording)
    return replace(claim, wording=wording)


def _word_margin_identity(claim: ResearchClaim, *, complete: bool, direction: str) -> ResearchClaim:
    if complete and direction:
        wording = (
            f"{direction[0].upper()}{direction[1:]} account for the "
            "reported operating-margin change as an identity."
        )
    else:
        wording = (
            "Disclosed component contributions provide a partial "
            "explanation of the reported operating-margin change; "
            "a residual remains."
        )
    return replace(claim, wording=wording)


def component_direction_phrase(gm, sga) -> str:
    parts: list[str] = []
    if present(gm):
        if gm < 0:
            parts.append("gross-margin contraction")
        elif gm > 0:
            parts.append("gross-margin expansion")
    if present(sga):
        if sga < 0:
            parts.append("a higher SG&A ratio")
        elif sga > 0:
            parts.append("a lower SG&A ratio")
    return " and ".join(parts)


def _margin_direction(view) -> str:
    latest = _latest_index(view)
    if latest is None:
        return ""
    gm = (
        None
        if view.gross_margin_contribution is None
        or latest >= len(view.gross_margin_contribution)
        else view.gross_margin_contribution[latest]
    )
    sga = (
        None
        if view.sga_ratio_contribution is None
        or latest >= len(view.sga_ratio_contribution)
        else view.sga_ratio_contribution[latest]
    )
    return component_direction_phrase(gm, sga)


def _latest_index(view) -> int | None:
    if not view.periods:
        return None
    return len(view.periods) - 1


def _intensity_change(view, latest: int):
    return completed_intensity_growth(view, latest)


def format_question_magnitude(view, question: ResearchQuestion, latest: int | None) -> str:
    """Format Interpreter-chosen comparisons without changing values or precision."""
    if latest is None:
        return ""
    if question.identifier == "footprint_intensity":
        rev_g = view.revenue_growth[latest] if latest < len(view.revenue_growth) else None
        store_g = view.store_growth[latest] if latest < len(view.store_growth) else None
        if not present(rev_g) or not present(store_g):
            return ""
        intensity = _intensity_change(view, latest)
        return (
            f"store-count growth {store_g:.4%} versus revenue growth {rev_g:.4%}"
            + (
                f"; company-wide revenue per store {intensity:.4%}"
                if intensity is not None
                else ""
            )
        )
    if question.identifier == "comparable_sales":
        compsales = tuple(view.comparable_sales)
        if not compsales:
            return ""
        latest_comp = next(
            (point for point in reversed(compsales) if point.period == view.periods[latest]),
            compsales[-1],
        )
        return f"{latest_comp.percent:.0f}% on the latest stated population and basis"
    if question.identifier == "sales_per_square_foot":
        return "unavailable as a comparable series"
    if question.identifier == "geographic_localization":
        conditions = geographic_claim_conditions(view, latest)
        if present(conditions.consolidated_profit):
            return f"consolidated operating-profit change {conditions.consolidated_profit}"
        return "geographic revenue contributions available"
    if question.identifier == "operating_margin_bridge":
        om = (
            None
            if view.reported_operating_margin_change is None
            else view.reported_operating_margin_change[latest]
        )
        if present(om):
            return f"operating-margin change {om:.4%}"
        return "component contributions available"
    if question.identifier == "management_margin_attribution":
        if not question.claims:
            return "unavailable"
        latest_period = view.periods[latest]
        quantified = tuple(
            item
            for item in view.attributions
            if item.period == latest_period and item.approximate_amount is not None
        )
        if quantified:
            return f"approximately {quantified[0].approximate_amount}"
        return "qualitative attribution only"
    if question.identifier == "cash_conversion":
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
        if present(cfo_change) and present(ni_change):
            return f"CFO change {cfo_change}; net-income change {ni_change}"
        return f"CFO {cfo}; net income {ni}"
    return ""


def word_driver_questions(
    view,
    interpretation: DriverInterpretation,
) -> tuple[ResearchQuestion, ...]:
    """Fill Composer-owned wording, publication, exhibit, and magnitude fields."""
    latest = _latest_index(view)
    worded: list[ResearchQuestion] = []
    for question in interpretation.questions:
        claims = question.claims
        publication = PUBLICATION_APPENDIX
        reason = question.publication_reason
        figure_purpose = None
        figure_question = None
        if question.identifier == "footprint_intensity":
            if interpretation.footprint_diverged:
                publication = PUBLICATION_MAIN
                reason = "Latest-year growth/intensity divergence is a material selected claim."
                figure_purpose = "growth"
                figure_question = "Did store-count growth outpace consolidated revenue growth?"
            else:
                reason = "The comparison is available but does not currently change the argument."
            claims = tuple(_word_claim(item) for item in claims)
        elif question.identifier == "comparable_sales":
            publication = PUBLICATION_APPENDIX
            reason = (
                "Period-specific comparable-sales observations remain auditable "
                "and are not a separate principal argument."
            )
            claims = tuple(_word_claim(item) for item in claims)
        elif question.identifier == "sales_per_square_foot":
            publication = PUBLICATION_EXCLUDED
            reason = (
                "The blocked comparison adds no argument value beyond the "
                "already-selected intensity-proxy boundary."
            )
            claims = tuple(_word_claim(item) for item in claims)
        elif question.identifier == "geographic_localization":
            publication = PUBLICATION_MAIN
            reason = (
                "Aligned revenue/profit contrast adds distinct information about "
                "where growth and profit changed."
            )
            figure_purpose = "geography"
            conditions = (
                geographic_claim_conditions(view, latest) if latest is not None else None
            )
            figure_question = (
                geographic_figure_question(conditions)
                if conditions is not None
                else _NEUTRAL_GEO_FIGURE
            )
            claims = tuple(_word_claim(item) for item in claims)
        elif question.identifier == "operating_margin_bridge":
            complete = latest is not None and completed_reconstruction(view, latest)
            if interpretation.margin_material:
                publication = PUBLICATION_MAIN
                reason = "The latest-year accounting bridge is a selected claim."
                figure_purpose = "margin"
                figure_question = (
                    "Which accounting components reconstruct the latest operating-margin change?"
                    if complete
                    else (
                        "Which disclosed accounting components partly explain "
                        "the latest operating-margin change?"
                    )
                )
            else:
                reason = "The margin identity is available but is not a material operating change."
            claims = tuple(
                _word_margin_identity(
                    item, complete=complete, direction=_margin_direction(view)
                )
                if item.identifier == "margin_identity"
                else _word_claim(item)
                for item in claims
            )
        elif question.identifier == "management_margin_attribution":
            if question.claims:
                publication = PUBLICATION_APPENDIX
                reason = "Combined with the accounting margin finding; no additional figure."
            else:
                publication = PUBLICATION_EXCLUDED
                reason = "Absent attribution is a research limitation, not a published finding."
            claims = tuple(_word_claim(item) for item in claims)
        elif question.identifier == "cash_conversion":
            if interpretation.cash_visible:
                publication = PUBLICATION_MAIN
                reason = "Cash conversion adds a distinct perspective from growth and margin."
                figure_purpose = "cash"
                figure_question = (
                    "Did reported earnings continue to translate into operating cash flow?"
                )
            else:
                publication = PUBLICATION_APPENDIX
                reason = "Cash conversion adds a distinct perspective from growth and margin."
            claims = tuple(_word_claim(item) for item in claims)
        worded.append(
            replace(
                question,
                claims=claims,
                magnitude=format_question_magnitude(view, question, latest),
                publication=publication,
                publication_reason=reason,
                figure_purpose=figure_purpose,
                figure_question=figure_question,
            )
        )
    return tuple(worded)


def select_driver_argument(
    view,
    interpretation: DriverInterpretation | None = None,
) -> ResearchSelection:
    """Assign principal, secondary and appendix roles from completed judgments."""
    if interpretation is None:
        raise ValueError("Composer selection requires completed Inferer/Debater judgments")
    investigated = word_driver_questions(view, interpretation)
    roles = assign_driver_roles(view, interpretation, investigated)
    decisions: list[SelectionDecision] = []
    by_id = {item.identifier: item for item in investigated}
    principals = [by_id[i] for i in roles.principal_ids if i in by_id]
    secondaries = [by_id[i] for i in roles.secondary_ids if i in by_id]
    appendix = [by_id[i] for i in roles.appendix_ids if i in by_id]
    figures = list(roles.figure_ids)
    footprint = by_id.get("footprint_intensity")
    compsales = by_id.get("comparable_sales")
    spsf = by_id.get("sales_per_square_foot")
    geo = by_id.get("geographic_localization")
    margin = by_id.get("operating_margin_bridge")
    attribution = by_id.get("management_margin_attribution")
    cash = by_id.get("cash_conversion")
    latest = _latest_index(view)

    if margin and margin.identifier in roles.principal_ids:
        complete = latest is not None and completed_reconstruction(view, latest)
        decisions.append(
            SelectionDecision(
                margin.identifier,
                ROLE_PRINCIPAL,
                (
                    "Material operating-margin movement reconstructs the latest profit outcome."
                    if complete
                    else (
                        "Material operating-margin movement is selected; disclosed "
                        "components provide a partial explanation and a residual remains."
                    )
                ),
            )
        )
    elif margin:
        decisions.append(
            SelectionDecision(
                margin.identifier,
                ROLE_APPENDIX,
                "The margin identity is available but is not a material operating change.",
            )
        )

    if attribution and attribution.identifier in roles.combined_ids:
        decisions.append(
            SelectionDecision(
                attribution.identifier,
                "combined",
                "Preserved with the accounting-margin finding; not an independent principal driver.",
            )
        )
    elif attribution:
        decisions.append(
            SelectionDecision(
                attribution.identifier,
                attribution.publication,
                attribution.publication_reason,
            )
        )

    if geo and geo.identifier in roles.principal_ids:
        decisions.append(
            SelectionDecision(
                geo.identifier,
                ROLE_PRINCIPAL,
                "Geographic revenue and profit localization explains where the operating outcome changed.",
            )
        )
    elif geo:
        decisions.append(
            SelectionDecision(
                geo.identifier,
                ROLE_SECONDARY,
                "Geographic evidence localizes results without independently explaining the operating outcome.",
            )
        )

    if footprint and footprint.identifier in roles.principal_ids:
        decisions.append(
            SelectionDecision(
                footprint.identifier,
                ROLE_PRINCIPAL,
                "Footprint versus company-wide revenue is the distinct available growth explanation.",
            )
        )
    elif footprint:
        decisions.append(
            SelectionDecision(
                footprint.identifier,
                ROLE_APPENDIX,
                "Expansion economics is available but is not distinctly explanatory once geographic localization is selected."
                if interpretation.geo_story
                else footprint.publication_reason,
            )
        )

    if compsales:
        decisions.append(
            SelectionDecision(
                compsales.identifier,
                ROLE_APPENDIX,
                "Period-specific comparable-sales observations remain auditable and are not a separate principal argument.",
            )
        )

    if spsf:
        decisions.append(SelectionDecision(spsf.identifier, ROLE_EXCLUDED, spsf.publication_reason))

    if cash and cash.identifier in roles.principal_ids:
        decisions.append(
            SelectionDecision(
                cash.identifier,
                ROLE_PRINCIPAL,
                "Cash conversion is the material available explanation of the latest outcome.",
            )
        )
    elif cash and cash.identifier in roles.secondary_ids:
        decisions.append(
            SelectionDecision(
                cash.identifier,
                ROLE_SECONDARY,
                "Cash conversion is a distinct diagnostic and does not independently carry the operating story.",
            )
        )
    elif cash:
        decisions.append(SelectionDecision(cash.identifier, ROLE_APPENDIX, cash.publication_reason))

    visible = principals + secondaries
    ordered = []
    seen = set()
    for item in investigated:
        replacement = next((sel for sel in visible + appendix if sel.identifier == item.identifier), item)
        if replacement.identifier in seen:
            continue
        seen.add(replacement.identifier)
        ordered.append(replacement)
    return ResearchSelection(
        questions=tuple(ordered),
        decisions=tuple(decisions),
        main_body_ids=tuple(item.identifier for item in visible),
        figure_ids=tuple(dict.fromkeys(figures)),
        principal_ids=tuple(item.identifier for item in principals),
        secondary_ids=tuple(item.identifier for item in secondaries),
        appendix_ids=tuple(item.identifier for item in appendix),
        calendar_limited=interpretation.calendar_limited,
    )
