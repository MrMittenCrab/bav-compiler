"""Composer Driver role, order, wording, and exhibit selection."""

from __future__ import annotations

from dataclasses import replace

from composer.research.selection_roles import (
    PUBLICATION_APPENDIX,
    PUBLICATION_EXCLUDED,
    PUBLICATION_MAIN,
    ROLE_APPENDIX,
    ROLE_EXCLUDED,
    ROLE_PRINCIPAL,
    ROLE_SECONDARY,
)
from interpreter.selection import DriverInterpretation
from modeler.research.drivers_view import margin_reconstruction_complete
from modeler.research.geo_conditions import geographic_claim_conditions, present
from modeler.research.records import ResearchClaim, ResearchQuestion, ResearchSelection, SelectionDecision

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


def _component_direction_phrase(gm, sga) -> str:
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
    latest = None
    for index in range(len(view.periods) - 1, -1, -1):
        latest = index
        break
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
    return _component_direction_phrase(gm, sga)


def word_driver_questions(
    view,
    interpretation: DriverInterpretation,
) -> tuple[ResearchQuestion, ...]:
    """Fill Composer-owned wording, publication, and exhibit fields."""
    latest = None
    for index in range(len(view.periods) - 1, -1, -1):
        latest = index
        break
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
            complete = latest is not None and margin_reconstruction_complete(view, latest)
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
        raise ValueError("Composer selection requires completed Interpreter judgments")
    investigated = word_driver_questions(view, interpretation)
    decisions: list[SelectionDecision] = []
    principals: list[ResearchQuestion] = []
    secondaries: list[ResearchQuestion] = []
    appendix: list[ResearchQuestion] = []
    figures: list[str] = []
    by_id = {item.identifier: item for item in investigated}
    footprint = by_id.get("footprint_intensity")
    compsales = by_id.get("comparable_sales")
    spsf = by_id.get("sales_per_square_foot")
    geo = by_id.get("geographic_localization")
    margin = by_id.get("operating_margin_bridge")
    attribution = by_id.get("management_margin_attribution")
    cash = by_id.get("cash_conversion")
    latest = None
    for index in range(len(view.periods) - 1, -1, -1):
        latest = index
        break

    if margin and interpretation.margin_material:
        principals.append(margin)
        complete = latest is not None and margin_reconstruction_complete(view, latest)
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
        if margin.figure_purpose:
            figures.append(margin.figure_purpose)
    elif margin:
        appendix.append(margin)
        decisions.append(
            SelectionDecision(
                margin.identifier,
                ROLE_APPENDIX,
                "The margin identity is available but is not a material operating change.",
            )
        )

    if attribution and attribution.claims and margin:
        appendix.append(attribution)
        decisions.append(
            SelectionDecision(
                attribution.identifier,
                "combined",
                "Preserved with the accounting-margin finding; not an independent principal driver.",
            )
        )
    elif attribution:
        if attribution.claims:
            appendix.append(attribution)
        decisions.append(
            SelectionDecision(
                attribution.identifier,
                attribution.publication,
                attribution.publication_reason,
            )
        )

    if geo and interpretation.geo_story:
        principals.append(geo)
        decisions.append(
            SelectionDecision(
                geo.identifier,
                ROLE_PRINCIPAL,
                "Geographic revenue and profit localization explains where the operating outcome changed.",
            )
        )
        if geo.figure_purpose:
            figures.append(geo.figure_purpose)
    elif geo:
        secondaries.append(geo)
        decisions.append(
            SelectionDecision(
                geo.identifier,
                ROLE_SECONDARY,
                "Geographic evidence localizes results without independently explaining the operating outcome.",
            )
        )

    if interpretation.footprint_diverged and footprint and not interpretation.geo_story:
        principals.append(footprint)
        decisions.append(
            SelectionDecision(
                footprint.identifier,
                ROLE_PRINCIPAL,
                "Footprint versus company-wide revenue is the distinct available growth explanation.",
            )
        )
        if footprint.figure_purpose:
            figures.append(footprint.figure_purpose)
    elif footprint:
        appendix.append(footprint)
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
        appendix.append(compsales)
        decisions.append(
            SelectionDecision(
                compsales.identifier,
                ROLE_APPENDIX,
                "Period-specific comparable-sales observations remain auditable and are not a separate principal argument.",
            )
        )

    if spsf:
        decisions.append(SelectionDecision(spsf.identifier, ROLE_EXCLUDED, spsf.publication_reason))

    if interpretation.cash_visible and cash and not principals:
        principals.append(cash)
        decisions.append(
            SelectionDecision(
                cash.identifier,
                ROLE_PRINCIPAL,
                "Cash conversion is the material available explanation of the latest outcome.",
            )
        )
        if cash.figure_purpose:
            figures.append(cash.figure_purpose)
    elif interpretation.cash_visible and cash:
        secondaries.append(cash)
        decisions.append(
            SelectionDecision(
                cash.identifier,
                ROLE_SECONDARY,
                "Cash conversion is a distinct diagnostic and does not independently carry the operating story.",
            )
        )
    elif cash:
        appendix.append(cash)
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
    )
