"""Rendered reported-margin assessments. Copies kind and established unchanged."""

from __future__ import annotations

from modeler.reported_margin import (
    AMOUNT_BRIDGE_FORMULA,
    ImpairmentChargeObservations,
    LatestAdjacentMovement,
    MarginIdentityValidity,
    MarginRelationshipAssessment,
)
from interpreter.reported_margin import (
    CONTRADICTION_BOTH_REDUCED,
    CONTRADICTION_DIRECTION_DIFFERS,
    DisclosedChargeInterpretation,
    LatestMovementInterpretation,
    UnsupportedMixInterpretation,
)

AMOUNT_BRIDGE_CONVENTION = (
    "Gross-profit change uses prior gross margin on the revenue change, "
    "prior revenue on the gross-margin change, and an explicit interaction "
    "equal to the revenue change times the gross-margin change. Operating-"
    "profit change then subtracts disclosed SG&A, impairment or asset-related "
    "charges, and other reported operating-item changes. Missing disclosure "
    "is omitted from the reconstruction, not treated as zero."
)

MIX_LIMIT = (
    "Face-of-statement components do not isolate mix, markdowns, freight, "
    "input costs, occupancy, or leverage in amounts that can be bridged "
    "independently to the reported margin change. Source filings may "
    "attribute those items in Item 7; the attributions remain management "
    "explanations unless a disclosed series can be folded without assuming "
    "undisclosed subcomponents."
)


def word_margin_identity(
    validity: MarginIdentityValidity,
) -> MarginRelationshipAssessment:
    return MarginRelationshipAssessment(
        name=validity.name,
        kind=validity.kind,
        direction=(
            "reconstructed operating margin equals reported operating margin "
            "when disclosed components are subtracted from gross margin"
        ),
        magnitude=(
            "levels and adjacent changes are reconciled in amounts and "
            "percentage points"
        ),
        reconstruction=(
            "operating margin = gross margin − SG&A/revenue − impairment or "
            "asset-related charges/revenue − other reported operating items/revenue"
        ),
        residual=(
            f"largest absolute operating-margin residual is {validity.max_resid:.6%}"
            if validity.max_resid is not None
            else "residual not defined"
        ),
        stability="the identity holds in every period with disclosed SG&A",
        contradictions="none in the reconstructed history",
        disclosure_support="income-statement components only; missing lines stay omitted",
        established=validity.established,
        limitation="" if validity.established else "reconstruction residual remains",
    )


def word_margin_contributions(
    validity: MarginIdentityValidity,
) -> MarginRelationshipAssessment:
    return MarginRelationshipAssessment(
        name=validity.name,
        kind=validity.kind,
        direction=(
            "signed component contributions reconstruct the reported "
            "operating-margin change"
        ),
        magnitude=(
            "Δgross margin, −Δ(SG&A/revenue), −Δ(impairment or asset-related "
            "charges/revenue), and −Δ(other reported operating items/revenue) "
            "are calculated from unrounded ratios"
        ),
        reconstruction=(
            "reconstructed contribution sum equals those signed terms; residual "
            "is reported operating-margin change minus the reconstructed sum"
        ),
        residual=(
            f"largest absolute contribution residual is {validity.max_resid:.6%}"
            if validity.max_resid is not None
            else "opening period has no adjacent comparison"
        ),
        stability=(
            "the identity is tested for every adjacent pair with disclosed components"
        ),
        contradictions=(
            "none required when the residual is a rounding or omitted-line remainder"
        ),
        disclosure_support=(
            "income-statement components only; missing adjacent comparisons "
            "stay unavailable"
        ),
        established=validity.established,
        limitation="" if validity.established else "contribution residual remains",
    )


def word_gross_profit_bridge(
    validity: MarginIdentityValidity,
) -> MarginRelationshipAssessment:
    return MarginRelationshipAssessment(
        name=validity.name,
        kind=validity.kind,
        direction=(
            "gross-profit change equals the revenue effect plus the "
            "gross-margin effect plus the interaction"
        ),
        magnitude=AMOUNT_BRIDGE_CONVENTION,
        reconstruction=AMOUNT_BRIDGE_FORMULA,
        residual=(
            f"largest absolute gross-profit residual is {validity.max_resid:.6f}"
            if validity.max_resid is not None
            else "opening period has no change"
        ),
        stability=(
            "the interaction identity holds for every adjacent pair with defined margins"
        ),
        contradictions="none",
        disclosure_support="reported revenue and gross profit",
        established=validity.established,
    )


def word_disclosed_charges(
    observations: ImpairmentChargeObservations,
    interpretation: DisclosedChargeInterpretation,
) -> MarginRelationshipAssessment:
    return MarginRelationshipAssessment(
        name="impairment or asset-related charges",
        kind=interpretation.kind,
        direction=(
            "separately disclosed impairment or restructuring charges reduce "
            "operating profit in the years they appear"
        ),
        magnitude=(
            "; ".join(
                f"{period.isoformat()} {amount:,.0f}"
                for period, amount in observations.charged
            )
            or "disclosed zeros only"
        ),
        reconstruction=(
            "charges enter the operating-margin identity only in periods that "
            "present the line"
        ),
        residual=(
            "reported zeros remain zeros; later years that still present the "
            "line keep the disclosed zero"
        ),
        stability="the charge is episodic, not a recurring operating burden",
        contradictions=(
            "none; later filings keep the line at zero rather than dropping it silently"
        ),
        disclosure_support=(
            "face-of-statement impairment or restructuring line with "
            "page-level locators in provenance"
        ),
        established=observations.established,
    )


def word_unsupported_mix(
    interpretation: UnsupportedMixInterpretation,
) -> MarginRelationshipAssessment:
    return MarginRelationshipAssessment(
        name="mix, markdowns, freight, costs, or leverage",
        kind=interpretation.kind,
        direction="not established",
        magnitude="not quantified",
        reconstruction="no source-supported component series",
        residual="not applicable",
        stability="not tested",
        contradictions="not tested",
        disclosure_support=MIX_LIMIT,
        established=interpretation.established,
        limitation=MIX_LIMIT,
    )


def word_latest_movement(
    movement: LatestAdjacentMovement,
    interpretation: LatestMovementInterpretation,
) -> MarginRelationshipAssessment:
    parts = []
    if movement.gm_move is not None:
        parts.append(f"Δgross margin {movement.gm_move * 100:+.2f} pp")
    if movement.sga_move is not None:
        parts.append(f"−Δ(SG&A/revenue) {movement.sga_move * 100:+.2f} pp")
    if movement.imp_move is not None:
        parts.append(
            f"−Δ(impairment or asset-related charges/revenue) "
            f"{movement.imp_move * 100:+.2f} pp"
        )
    if movement.other_move is not None:
        parts.append(
            f"−Δ(other reported operating items/revenue) "
            f"{movement.other_move * 100:+.2f} pp"
        )
    if interpretation.contradiction_class == CONTRADICTION_BOTH_REDUCED:
        contradictions = (
            "gross-margin and SG&A contributions both reduced operating margin"
        )
    elif interpretation.contradiction_class == CONTRADICTION_DIRECTION_DIFFERS:
        contradictions = (
            "component contribution directions differ from the "
            "reported operating-margin direction"
        )
    else:
        contradictions = "none required"
    return MarginRelationshipAssessment(
        name="latest adjacent operating-margin movement",
        kind=interpretation.kind,
        direction=(
            "operating margin fell" if movement.om_fell else "operating margin rose"
        ),
        magnitude=f"{movement.om_move * 100:+.2f} pp",
        reconstruction="; ".join(parts) if parts else "component change incomplete",
        residual="contribution residual is shown separately",
        stability="one adjacent pair; not a multi-year law",
        contradictions=contradictions,
        disclosure_support=(
            "income-statement identity only; Item 7 attributions are "
            "recorded separately after source-filing inspection"
        ),
        established=interpretation.established,
    )
